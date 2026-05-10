from flask import Blueprint, request, jsonify, session, render_template, abort, current_app
import os
import math
import uuid
from werkzeug.utils import secure_filename
from blueprints.db import get_db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ── 인증 데코레이터 ──────────────────────────────────────────────────────────
# ⚠️ 실습용 의도적 Broken Access Control 취약점 (OWASP A01:2021)
#
# 원래는 admin_required 로 ADMIN 역할을 검증해야 하지만,
# 권한 체크를 제거하고 로그인 여부만 검사하는 login_required 로 교체.
# → USER 권한으로 로그인한 일반 사용자도 /admin/* 의 모든 기능에 접근 가능.
#
# PoC 시나리오:
#   1) USER 계정으로 로그인 (예: user01/user01)
#   2) GET /admin/users?per_page=100  → 전체 회원 목록 탈취
#   3) DELETE /admin/users/1          → 관리자 계정도 삭제 가능
#   4) POST /admin/notices            → 공지 임의 작성
#
# 조치 방안: admin_required 데코레이터 복구 + Blueprint.before_request 로 이중화

from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': '로그인이 필요합니다.'}), 401
        return f(*args, **kwargs)
    return decorated


# ⚠️ 아래 admin_required 는 정의만 남겨두었으나 라우트에서 사용하지 않음.
# 실습 후 안전한 코드로 되돌릴 때 다시 부착해야 한다.
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user_role') != 'ADMIN':
            return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
        return f(*args, **kwargs)
    return decorated


# ── 페이지: 회원 목록 ─────────────────────────────────────────────────────────
#
# GET /admin/users/list

@admin_bp.route('/users/list', methods=['GET'])
@login_required  # ⚠️ 의도적 취약점: 원래는 @admin_required
def user_list_page():
    return render_template('admin/user_list.html')


# ── API: 회원 목록 조회 ───────────────────────────────────────────────────────
#
# GET /admin/users
#   Query params:
#     page     (int, default 1)   — 현재 페이지
#     per_page (int, default 10)  — 페이지당 항목 수 (최대 100)
#     name     (str, optional)    — 이름 검색 (부분 일치)
#
# Response:
#   {
#     "users": [ { user_idx, user_id, password, name, role, email,
#                  created_at, updated_at }, ... ],
#     "pagination": { page, per_page, total, total_pages }
#   }

@admin_bp.route('/users', methods=['GET'])
@login_required  # ⚠️ 의도적 취약점: 원래는 @admin_required
def get_users():
    # ── 파라미터 파싱 ──────────────────────────────────────────────────────
    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        return jsonify({'error': 'page는 정수여야 합니다.'}), 400

    try:
        per_page = min(100, max(1, int(request.args.get('per_page', 10))))
    except ValueError:
        return jsonify({'error': 'per_page는 정수여야 합니다.'}), 400

    name_keyword = request.args.get('name', '').strip()

    # ── 쿼리 구성 ──────────────────────────────────────────────────────────
    # ⚠️ 실습용 의도적 SQL Injection 취약점 (OWASP A03:2021)
    # name 검색어를 그대로 LIKE 패턴에 삽입 → UNION/Boolean-based SQLi 가능
    # PoC: ?name=%' UNION SELECT 1,user_id,password,name,role,email,NOW(),NOW() FROM users --
    where_clause = ''
    if name_keyword:
        where_clause = f"WHERE name LIKE '%{name_keyword}%'"

    offset = (page - 1) * per_page

    db = get_db()
    with db.cursor() as cursor:
        # 전체 건수
        cursor.execute(f'SELECT COUNT(*) AS total FROM users {where_clause}')
        total = cursor.fetchone()['total']

        # 페이지 데이터
        cursor.execute(
            f'''
            SELECT user_idx, user_id, password, name, role, email,
                   created_at, updated_at
            FROM users
            {where_clause}
            ORDER BY name ASC
            LIMIT %s OFFSET %s
            ''',
            [per_page, offset],
        )
        users = cursor.fetchall()

    # datetime → 문자열 직렬화, password 해시 제거
    for user in users:
        user.pop('password', None)
        for key in ('created_at', 'updated_at'):
            if user[key] is not None:
                user[key] = user[key].strftime('%Y-%m-%d %H:%M:%S')

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return jsonify({
        'users': users,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
        },
    }), 200


# ── 페이지: 회원 상세 프로필 ──────────────────────────────────────────────────
#
# GET /admin/users/<user_idx>/profile

@admin_bp.route('/users/<int:user_idx>/profile', methods=['GET'])
@login_required  # ⚠️ [IDOR/BAC] @admin_required 제거 — 로그인한 모든 사용자가 타 사용자 프로필 조회 가능
def user_profile_page(user_idx):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            '''
            SELECT user_idx, user_id, password, name, role, email,
                   created_at, updated_at
            FROM users
            WHERE user_idx = %s
            ''',
            (user_idx,),
        )
        user = cursor.fetchone()

    if user is None:
        abort(404)

    for key in ('created_at', 'updated_at'):
        if user[key] is not None:
            user[key] = user[key].strftime('%Y-%m-%d %H:%M:%S')

    return render_template('admin/user_detail.html', user=user)


# ── API: 회원 삭제 ────────────────────────────────────────────────────────────
#
# DELETE /admin/users/<user_idx>
#   연관 데이터 삭제 순서 (FK 제약):
#     1. 유저 게시글에 달린 댓글 전체 삭제
#     2. 유저가 다른 게시글에 작성한 댓글 삭제
#     3. 유저 게시글에 연결된 file_id 수집
#     4. 유저 게시글 삭제
#     5. 수집한 파일 삭제
#     6. 유저 삭제

@admin_bp.route('/users/<int:user_idx>', methods=['DELETE'])
@login_required  # ⚠️ 의도적 취약점: 원래는 @admin_required
def delete_user(user_idx):
    db = get_db()
    try:
        with db.cursor() as cursor:
            # 존재 여부 확인
            cursor.execute('SELECT user_idx FROM users WHERE user_idx = %s', (user_idx,))
            if cursor.fetchone() is None:
                return jsonify({'error': '존재하지 않는 회원입니다.'}), 404

            # 1. 유저 게시글에 달린 댓글 전체 삭제 (다른 유저 댓글 포함, 자기참조 고려)
            cursor.execute(
                'DELETE FROM comment WHERE board_id IN (SELECT board_id FROM board WHERE user_idx = %s)',
                (user_idx,),
            )

            # 2. 유저가 다른 게시글에 작성한 댓글 삭제
            cursor.execute('DELETE FROM comment WHERE user_idx = %s', (user_idx,))

            # 3. 유저 게시글에 연결된 file_id 수집
            cursor.execute(
                'SELECT file_id FROM board WHERE user_idx = %s AND file_id IS NOT NULL',
                (user_idx,),
            )
            file_ids = [row['file_id'] for row in cursor.fetchall()]

            # 4. 유저 게시글 삭제
            cursor.execute('DELETE FROM board WHERE user_idx = %s', (user_idx,))

            # 5. 파일 삭제
            if file_ids:
                placeholders = ','.join(['%s'] * len(file_ids))
                cursor.execute(f'DELETE FROM file WHERE file_id IN ({placeholders})', file_ids)

            # 6. 유저 삭제
            cursor.execute('DELETE FROM users WHERE user_idx = %s', (user_idx,))

        db.commit()
        return jsonify({'message': '회원 및 연관 데이터가 삭제되었습니다.'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': f'삭제 중 오류가 발생했습니다: {str(e)}'}), 500


# ── API: 게시글 삭제 ──────────────────────────────────────────────────────────
#
# DELETE /admin/board/<board_id>
#   - 관리자 전용
#   - 연관 데이터 삭제 순서 (FK 제약):
#     1. 해당 게시글의 댓글 삭제
#     2. 게시글에 연결된 file_id 수집
#     3. 게시글 삭제
#     4. 파일 삭제

@admin_bp.route('/board/<int:board_id>', methods=['DELETE'])
@login_required  # ⚠️ 의도적 취약점: 원래는 @admin_required
def delete_board(board_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            # 존재 여부 확인
            cursor.execute('SELECT board_id, file_id FROM board WHERE board_id = %s', (board_id,))
            post = cursor.fetchone()
            if post is None:
                return jsonify({'error': '존재하지 않는 게시글입니다.'}), 404

            file_id = post['file_id']

            # 1. 댓글 삭제 (자기참조 대댓글 포함 — 부모 먼저 끊기 위해 parent_id NULL 처리 후 삭제)
            cursor.execute('UPDATE comment SET parent_id = NULL WHERE board_id = %s', (board_id,))
            cursor.execute('DELETE FROM comment WHERE board_id = %s', (board_id,))

            # 2. 게시글 삭제
            cursor.execute('DELETE FROM board WHERE board_id = %s', (board_id,))

            # 3. 연결 파일 삭제
            if file_id:
                cursor.execute('DELETE FROM file WHERE file_id = %s', (file_id,))

        db.commit()
        return jsonify({'message': '게시글이 삭제되었습니다.'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': f'삭제 중 오류가 발생했습니다: {str(e)}'}), 500


# ── API: 댓글 삭제 ────────────────────────────────────────────────────────────
#
# DELETE /admin/comments/<comment_id>
#   - 관리자 전용
#   - 자식 대댓글이 있으면 함께 삭제 (부모 먼저 끊기 위해 parent_id NULL 처리 후 삭제)

@admin_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@login_required  # ⚠️ 의도적 취약점: 원래는 @admin_required
def delete_comment(comment_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            # 존재 여부 확인
            cursor.execute('SELECT comment_id FROM comment WHERE comment_id = %s', (comment_id,))
            if cursor.fetchone() is None:
                return jsonify({'error': '존재하지 않는 댓글입니다.'}), 404

            # 1. 자식 대댓글의 parent_id NULL 처리 후 삭제
            cursor.execute('UPDATE comment SET parent_id = NULL WHERE parent_id = %s', (comment_id,))
            cursor.execute('DELETE FROM comment WHERE parent_id = %s', (comment_id,))

            # 2. 본인 댓글 삭제
            cursor.execute('DELETE FROM comment WHERE comment_id = %s', (comment_id,))

        db.commit()
        return jsonify({'message': '댓글이 삭제되었습니다.'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': f'삭제 중 오류가 발생했습니다: {str(e)}'}), 500


# ── 페이지: 공지 작성 ─────────────────────────────────────────────────────────
#
# GET /admin/notices/new

@admin_bp.route('/notices/new', methods=['GET'])
@login_required  # ⚠️ 의도적 취약점: 원래는 @admin_required
def notice_write_page():
    return render_template('admin/notice_write.html')


# ── API: 공지 작성 ─────────────────────────────────────────────────────────────
#
# POST /admin/notices  (multipart/form-data)
#   Fields: title, content, file (optional)
#   - 제목 앞에 [공지사항] 자동 추가
#   - 파일 첨부 시 static/uploads/ 에 저장 후 file 테이블 삽입
#   - board.type = 'NOTICE' 로 저장
#   - 성공 → 201 { board_id, message }

@admin_bp.route('/notices', methods=['POST'])
@login_required  # ⚠️ 의도적 취약점: 원래는 @admin_required
def create_notice():
    title   = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()

    if not title:
        return jsonify({'error': '제목을 입력해주세요.'}), 400
    if not content:
        return jsonify({'error': '내용을 입력해주세요.'}), 400

    user_idx = session.get('user_no')
    if not user_idx:
        return jsonify({'error': '세션 정보가 없습니다. 다시 로그인해주세요.'}), 401

    full_title = f'[공지사항] {title}'
    uploaded   = request.files.get('file')

    db = get_db()
    try:
        file_id = None

        # ── 파일 첨부 처리 ──────────────────────────────────────────────────
        if uploaded and uploaded.filename:
            original_name = secure_filename(uploaded.filename)
            unique_name   = f'{uuid.uuid4().hex}_{original_name}'
            upload_dir    = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            uploaded.save(os.path.join(upload_dir, unique_name))

            with db.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO file (file_name, file_path) VALUES (%s, %s)',
                    (original_name, f'/static/uploads/{unique_name}'),
                )
                file_id = cursor.lastrowid

        # ── 게시글 삽입 ─────────────────────────────────────────────────────
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO board (user_idx, title, content, type, file_id) VALUES (%s, %s, %s, 'NOTICE', %s)",
                (user_idx, full_title, content, file_id),
            )
            board_id = cursor.lastrowid

        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'공지 등록 중 오류가 발생했습니다: {str(e)}'}), 500

    return jsonify({'message': '공지가 등록되었습니다.', 'board_id': board_id}), 201


# ── API: 공지 수정 ─────────────────────────────────────────────────────────────
#
# PATCH /admin/notices/<board_id>
#   Body (JSON): { title, content }
#   - NOTICE 타입 게시글만 수정 가능
#   - 성공 → 200 { message }

@admin_bp.route('/notices/<int:board_id>', methods=['PATCH'])
@login_required  # ⚠️ 의도적 취약점: 원래는 @admin_required
def update_notice(board_id):
    data = request.get_json(silent=True) or {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()

    if not title:
        return jsonify({'error': '제목을 입력해주세요.'}), 400
    if not content:
        return jsonify({'error': '내용을 입력해주세요.'}), 400

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                'SELECT board_id, type FROM board WHERE board_id = %s',
                (board_id,),
            )
            post = cursor.fetchone()

            if post is None:
                return jsonify({'error': '게시글을 찾을 수 없습니다.'}), 404
            if post['type'] != 'NOTICE':
                return jsonify({'error': '공지 게시글이 아닙니다.'}), 400

            cursor.execute(
                'UPDATE board SET title = %s, content = %s WHERE board_id = %s',
                (title, content, board_id),
            )
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'수정 중 오류가 발생했습니다: {str(e)}'}), 500

    return jsonify({'message': '공지가 수정되었습니다.'}), 200


# ── API: 단일 회원 조회 ───────────────────────────────────────────────────────
#
# GET /admin/users/<user_idx>

@admin_bp.route('/users/<int:user_idx>', methods=['GET'])
@login_required  # ⚠️ 의도적 취약점: 원래는 @admin_required
def get_user(user_idx):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            '''
            SELECT user_idx, user_id, password, name, role, email,
                   created_at, updated_at
            FROM users
            WHERE user_idx = %s
            ''',
            (user_idx,),
        )
        user = cursor.fetchone()

    if user is None:
        return jsonify({'error': '존재하지 않는 회원입니다.'}), 404

    for key in ('created_at', 'updated_at'):
        if user[key] is not None:
            user[key] = user[key].strftime('%Y-%m-%d %H:%M:%S')

    return jsonify({'user': user}), 200
