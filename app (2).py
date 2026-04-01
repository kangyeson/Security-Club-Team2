"""
===========================================
 관리자(Admin) 영역 - 회원관리 모듈
 Day 1: 회원 리스트 조회 API
 - 회원 목록 API 개발
 - 페이지네이션
 - 검색/필터 기능 구현
 - JWT 인증/권한
 - 요청/응답 로깅
===========================================
"""

from flask import Flask, request, jsonify, g
from datetime import datetime, timedelta
from functools import wraps
import random
import logging
import uuid
import hashlib
import hmac
import json
import base64
import os

app = Flask(__name__)

# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
TOKEN_EXPIRY_HOURS = 24


# ─────────────────────────────────────────
# 로깅 설정
# ─────────────────────────────────────────
def setup_logging():
    """파일 + 콘솔 로깅 설정"""

    log_format = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1) 파일 핸들러 - 모든 로그를 파일에 저장
    file_handler = logging.FileHandler("admin_api.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_format)

    # 2) 콘솔 핸들러 - 터미널에도 출력
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)

    # 3) 로거 등록
    logger = logging.getLogger("admin_api")
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()


# ─────────────────────────────────────────
# JWT 토큰 유틸리티 (외부 라이브러리 없이 구현)
# ─────────────────────────────────────────
def base64url_encode(data):
    """Base64 URL-safe 인코딩"""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def base64url_decode(s):
    """Base64 URL-safe 디코딩"""
    padding = 4 - len(s) % 4
    s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_token(admin_id, admin_name, role):
    """
    JWT 토큰 생성

    Args:
        admin_id: 관리자 ID
        admin_name: 관리자 이름
        role: 권한 ("super_admin" 또는 "admin")

    Returns:
        JWT 토큰 문자열
    """
    header = {"alg": "HS256", "typ": "JWT"}

    payload = {
        "admin_id": admin_id,
        "admin_name": admin_name,
        "role": role,
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)).timestamp()),
    }

    header_b64 = base64url_encode(json.dumps(header).encode())
    payload_b64 = base64url_encode(json.dumps(payload).encode())
    signature = hmac.new(
        SECRET_KEY.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256
    ).digest()
    signature_b64 = base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_token(token):
    """
    JWT 토큰 검증

    Returns:
        성공 시 payload 딕셔너리, 실패 시 None
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts

        expected_sig = hmac.new(
            SECRET_KEY.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()
        actual_sig = base64url_decode(signature_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload = json.loads(base64url_decode(payload_b64))

        if payload.get("exp", 0) < int(datetime.utcnow().timestamp()):
            return None

        return payload

    except Exception:
        return None


# ─────────────────────────────────────────
# 인증 데코레이터
# ─────────────────────────────────────────
def admin_required(f):
    """
    관리자 인증 데코레이터
    - 모든 관리자(admin, super_admin) 접근 가능
    - 요청 헤더에 Authorization: Bearer <token> 필요
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            logger.warning(f"인증 실패 | 토큰 없음 | IP: {request.remote_addr} | {request.method} {request.path}")
            return jsonify({"success": False, "error": "인증 토큰이 필요합니다."}), 401

        token = auth_header[7:]
        payload = verify_token(token)

        if payload is None:
            logger.warning(f"인증 실패 | 유효하지 않은 토큰 | IP: {request.remote_addr} | {request.method} {request.path}")
            return jsonify({"success": False, "error": "유효하지 않거나 만료된 토큰입니다."}), 401

        g.admin_id = payload["admin_id"]
        g.admin_name = payload["admin_name"]
        g.admin_role = payload["role"]

        return f(*args, **kwargs)
    return decorated


def super_admin_required(f):
    """
    최고 관리자 전용 데코레이터
    - super_admin 권한만 접근 가능
    """
    @wraps(f)
    @admin_required
    def decorated(*args, **kwargs):
        if g.admin_role != "super_admin":
            logger.warning(
                f"권한 부족 | {g.admin_name}(ID:{g.admin_id}, role:{g.admin_role}) | "
                f"{request.method} {request.path}"
            )
            return jsonify({"success": False, "error": "최고 관리자 권한이 필요합니다."}), 403
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────
# 요청/응답 로깅 미들웨어
# ─────────────────────────────────────────
@app.before_request
def log_request():
    """모든 요청 시작 시 로깅"""
    g.request_id = str(uuid.uuid4())[:8]
    g.request_start = datetime.utcnow()

    logger.info(
        f"[{g.request_id}] 요청 시작 | {request.method} {request.full_path} | "
        f"IP: {request.remote_addr}"
    )


@app.after_request
def log_response(response):
    """모든 응답 완료 시 로깅"""
    duration = (datetime.utcnow() - g.request_start).total_seconds()

    admin_info = ""
    if hasattr(g, "admin_name"):
        admin_info = f" | 관리자: {g.admin_name}(ID:{g.admin_id})"

    logger.info(
        f"[{g.request_id}] 요청 완료 | {request.method} {request.full_path} | "
        f"상태: {response.status_code} | 소요: {duration:.3f}초{admin_info}"
    )

    return response


# ─────────────────────────────────────────
# 더미 데이터 생성 (실제로는 DB 연동)
# ─────────────────────────────────────────
def generate_dummy_members(count=50):
    """테스트용 더미 회원 데이터 생성"""
    statuses = ["active", "inactive", "banned"]
    roles = ["user", "premium", "vip"]
    names = [
        "김민수", "이영희", "박철수", "최지영", "정대현",
        "한소연", "오준혁", "윤서아", "장민호", "임수진",
        "강태우", "서예린", "조성민", "배지현", "류하준",
        "신미래", "권도윤", "홍채은", "문재호", "양수빈",
    ]

    members = []
    for i in range(1, count + 1):
        name = names[(i - 1) % len(names)]
        created = datetime(2025, 1, 1) + timedelta(days=random.randint(0, 400))
        members.append({
            "id": i,
            "username": f"user{i:03d}",
            "name": name,
            "email": f"user{i:03d}@example.com",
            "phone": f"010-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
            "status": random.choice(statuses),
            "role": random.choice(roles),
            "created_at": created.strftime("%Y-%m-%d"),
            "last_login": (created + timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d"),
        })
    return members


# 더미 관리자 계정 (실제로는 DB + 비밀번호 해싱)
ADMIN_ACCOUNTS = {
    "admin": {
        "id": 1,
        "name": "관리자",
        "password": "admin1234",
        "role": "super_admin",
    },
    "manager": {
        "id": 2,
        "name": "매니저",
        "password": "manager1234",
        "role": "admin",
    },
}

MEMBERS = generate_dummy_members(50)


# ─────────────────────────────────────────
# 로그인 API (토큰 발급)
# ─────────────────────────────────────────
@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    """
    관리자 로그인 API

    Request Body (JSON):
        username (str): 관리자 아이디
        password (str): 비밀번호

    Returns:
        JSON: JWT 토큰 + 관리자 정보
    """
    data = request.get_json(silent=True)

    if not data:
        logger.warning(f"로그인 실패 | 요청 본문 없음 | IP: {request.remote_addr}")
        return jsonify({"success": False, "error": "JSON 요청 본문이 필요합니다."}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        logger.warning(f"로그인 실패 | 빈 입력값 | IP: {request.remote_addr}")
        return jsonify({"success": False, "error": "아이디와 비밀번호를 입력해주세요."}), 400

    account = ADMIN_ACCOUNTS.get(username)
    if not account or account["password"] != password:
        logger.warning(f"로그인 실패 | 잘못된 계정정보 | 시도: '{username}' | IP: {request.remote_addr}")
        return jsonify({"success": False, "error": "아이디 또는 비밀번호가 올바르지 않습니다."}), 401

    token = create_token(account["id"], account["name"], account["role"])

    logger.info(f"로그인 성공 | {account['name']}(ID:{account['id']}, role:{account['role']}) | IP: {request.remote_addr}")

    return jsonify({
        "success": True,
        "data": {
            "token": token,
            "admin": {
                "id": account["id"],
                "name": account["name"],
                "role": account["role"],
            },
            "expires_in": f"{TOKEN_EXPIRY_HOURS}시간",
        },
    }), 200


# ─────────────────────────────────────────
# 회원 리스트 조회 API (인증 필요)
# ─────────────────────────────────────────
@app.route("/api/admin/members", methods=["GET"])
@admin_required
def get_member_list():
    """
    회원 리스트 조회 API (인증 필요)

    Headers:
        Authorization: Bearer <token>

    Query Parameters:
        page (int)       : 페이지 번호 (기본값: 1)
        per_page (int)   : 페이지당 항목 수 (기본값: 10, 최대: 100)
        search (str)     : 검색어 (이름, 이메일, 아이디 대상)
        status (str)     : 상태 필터 (active / inactive / banned)
        role (str)       : 역할 필터 (user / premium / vip)
        sort_by (str)    : 정렬 기준 (id, name, created_at, last_login)
        order (str)      : 정렬 방향 (asc / desc, 기본값: asc)
    """

    # ── 1) 파라미터 파싱 ──
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    search = request.args.get("search", "", type=str).strip()
    status = request.args.get("status", "", type=str).strip()
    role = request.args.get("role", "", type=str).strip()
    sort_by = request.args.get("sort_by", "id", type=str).strip()
    order = request.args.get("order", "asc", type=str).strip()

    # ── 2) 입력값 검증 ──
    if page < 1:
        return jsonify({"success": False, "error": "page는 1 이상이어야 합니다."}), 400

    if per_page < 1 or per_page > 100:
        return jsonify({"success": False, "error": "per_page는 1~100 사이여야 합니다."}), 400

    valid_sort_fields = ["id", "name", "created_at", "last_login"]
    if sort_by not in valid_sort_fields:
        return jsonify({"success": False, "error": f"sort_by는 {valid_sort_fields} 중 하나여야 합니다."}), 400

    if order not in ["asc", "desc"]:
        return jsonify({"success": False, "error": "order는 'asc' 또는 'desc'여야 합니다."}), 400

    # ── 3) 검색 필터링 ──
    filtered = MEMBERS[:]

    if search:
        search_lower = search.lower()
        filtered = [
            m for m in filtered
            if search_lower in m["name"].lower()
            or search_lower in m["email"].lower()
            or search_lower in m["username"].lower()
        ]

    # ── 4) 상태 필터 ──
    if status:
        valid_statuses = ["active", "inactive", "banned"]
        if status not in valid_statuses:
            return jsonify({"success": False, "error": f"status는 {valid_statuses} 중 하나여야 합니다."}), 400
        filtered = [m for m in filtered if m["status"] == status]

    # ── 5) 역할 필터 ──
    if role:
        valid_roles = ["user", "premium", "vip"]
        if role not in valid_roles:
            return jsonify({"success": False, "error": f"role은 {valid_roles} 중 하나여야 합니다."}), 400
        filtered = [m for m in filtered if m["role"] == role]

    # ── 6) 정렬 ──
    reverse = (order == "desc")
    filtered.sort(key=lambda m: m[sort_by], reverse=reverse)

    # ── 7) 페이지네이션 ──
    total_items = len(filtered)
    total_pages = max(1, (total_items + per_page - 1) // per_page)

    if page > total_pages:
        return jsonify({"success": False, "error": f"page가 전체 페이지 수({total_pages})를 초과합니다."}), 400

    start = (page - 1) * per_page
    end = start + per_page
    page_items = filtered[start:end]

    # ── 8) 응답 생성 ──
    logger.info(
        f"[{g.request_id}] 회원 조회 | 관리자: {g.admin_name} | "
        f"검색: '{search or '-'}' | 상태: '{status or '-'}' | 역할: '{role or '-'}' | "
        f"결과: {total_items}건 중 {len(page_items)}건 반환 (page {page}/{total_pages})"
    )

    response = {
        "success": True,
        "data": {
            "members": page_items,
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_prev": page > 1,
                "has_next": page < total_pages,
            },
        },
        "filters_applied": {
            "search": search or None,
            "status": status or None,
            "role": role or None,
            "sort_by": sort_by,
            "order": order,
        },
    }

    return jsonify(response), 200


# ─────────────────────────────────────────
# Day 2: 회원 세부 정보 조회 API (인증 필요)
# ─────────────────────────────────────────
@app.route("/api/admin/members/<int:member_id>", methods=["GET"])
@admin_required
def get_member_detail(member_id):
    """
    회원 세부 정보 조회 API (인증 필요)

    Headers:
        Authorization: Bearer <token>

    Path Parameters:
        member_id (int): 조회할 회원의 ID

    Returns:
        JSON: 회원 상세 정보 + 활동 내역
    """

    # ── 1) 회원 검색 ──
    member = None
    for m in MEMBERS:
        if m["id"] == member_id:
            member = m
            break

    if member is None:
        logger.warning(
            f"[{g.request_id}] 회원 조회 실패 | 관리자: {g.admin_name} | "
            f"존재하지 않는 회원 ID: {member_id}"
        )
        return jsonify({"success": False, "error": f"ID {member_id}에 해당하는 회원을 찾을 수 없습니다."}), 404

    # ── 2) 상세 프로필 정보 구성 ──
    profile = {
        **member,
        "profile": {
            "bio": f"{member['name']}님의 자기소개입니다.",
            "address": random.choice([
                "서울특별시 강남구", "서울특별시 마포구", "경기도 성남시",
                "부산광역시 해운대구", "대전광역시 유성구", "인천광역시 연수구",
            ]),
            "birth_date": f"{random.randint(1980, 2005)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "gender": random.choice(["male", "female"]),
            "profile_image": f"https://example.com/profiles/user{member['id']:03d}.jpg",
        },
    }

    # ── 3) 활동 내역 생성 (더미) ──
    activity_types = ["login", "post_create", "post_delete", "comment", "profile_update", "report"]
    activity_labels = {
        "login": "로그인",
        "post_create": "게시글 작성",
        "post_delete": "게시글 삭제",
        "comment": "댓글 작성",
        "profile_update": "프로필 수정",
        "report": "신고 접수",
    }

    activities = []
    base_date = datetime(2026, 3, 1)
    for i in range(10):
        act_type = random.choice(activity_types)
        act_date = base_date + timedelta(days=random.randint(0, 28), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        activities.append({
            "id": i + 1,
            "type": act_type,
            "label": activity_labels[act_type],
            "detail": f"{activity_labels[act_type]} 활동이 기록되었습니다.",
            "ip_address": f"192.168.{random.randint(0,255)}.{random.randint(1,254)}",
            "timestamp": act_date.strftime("%Y-%m-%d %H:%M:%S"),
        })

    activities.sort(key=lambda a: a["timestamp"], reverse=True)

    # ── 4) 회원 통계 요약 ──
    member_stats = {
        "total_posts": random.randint(0, 150),
        "total_comments": random.randint(0, 500),
        "total_reports_received": random.randint(0, 10),
        "total_reports_sent": random.randint(0, 5),
        "login_count_30days": random.randint(0, 30),
        "days_since_registration": (datetime(2026, 3, 30) - datetime.strptime(member["created_at"], "%Y-%m-%d")).days,
    }

    # ── 5) 응답 생성 ──
    logger.info(
        f"[{g.request_id}] 회원 상세 조회 | 관리자: {g.admin_name} | "
        f"대상: {member['name']}(ID:{member_id}, status:{member['status']})"
    )

    return jsonify({
        "success": True,
        "data": {
            "member": profile,
            "activities": activities,
            "stats": member_stats,
        },
    }), 200


# ─────────────────────────────────────────
# 회원 통계 API (인증 필요)
# ─────────────────────────────────────────
@app.route("/api/admin/members/stats", methods=["GET"])
@admin_required
def get_member_stats():
    """회원 통계 API (인증 필요)"""
    total = len(MEMBERS)
    status_count = {}
    role_count = {}

    for m in MEMBERS:
        status_count[m["status"]] = status_count.get(m["status"], 0) + 1
        role_count[m["role"]] = role_count.get(m["role"], 0) + 1

    logger.info(f"[{g.request_id}] 회원 통계 조회 | 관리자: {g.admin_name} | 전체 회원: {total}명")

    return jsonify({
        "success": True,
        "data": {
            "total_members": total,
            "by_status": status_count,
            "by_role": role_count,
        },
    }), 200


# ─────────────────────────────────────────
# 에러 핸들러
# ─────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 Not Found | {request.method} {request.path} | IP: {request.remote_addr}")
    return jsonify({"success": False, "error": "요청한 리소스를 찾을 수 없습니다."}), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"500 Internal Error | {request.method} {request.path} | {str(e)}")
    return jsonify({"success": False, "error": "서버 내부 오류가 발생했습니다."}), 500


# ─────────────────────────────────────────
# 서버 실행
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print(" Admin 회원관리 API 서버 시작")
    print(" http://127.0.0.1:5000")
    print("=" * 60)
    print()
    print(" [API 엔드포인트]")
    print(" POST /api/admin/login              - 로그인 (토큰 발급)")
    print(" GET  /api/admin/members             - 회원 리스트 조회 (인증 필요)")
    print(" GET  /api/admin/members/<id>        - 회원 세부 정보 조회 (인증 필요)")
    print(" GET  /api/admin/members/stats       - 회원 통계 (인증 필요)")
    print()
    print(" [테스트 계정]")
    print(" 최고관리자:  admin / admin1234     (super_admin)")
    print(" 일반관리자:  manager / manager1234 (admin)")
    print()
    print(" [사용법]")
    print(" 1단계 - 로그인:")
    print('   curl -X POST http://127.0.0.1:5000/api/admin/login \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"username":"admin","password":"admin1234"}\'')
    print()
    print(" 2단계 - 토큰으로 API 호출:")
    print('   curl http://127.0.0.1:5000/api/admin/members \\')
    print('     -H "Authorization: Bearer <발급받은_토큰>"')
    print()
    print('   curl http://127.0.0.1:5000/api/admin/members/1 \\')
    print('     -H "Authorization: Bearer <발급받은_토큰>"')
    print()
    print(" [로그 파일]")
    print(" admin_api.log 파일에 모든 요청 기록이 저장됩니다.")
    print("=" * 60)

    app.run(debug=True)
