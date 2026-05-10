from functools import wraps

from flask import (Blueprint, redirect, render_template,
                   request, session, url_for, flash)
from werkzeug.security import check_password_hash, generate_password_hash
from blueprints.db import get_db

mypage_bp = Blueprint('mypage', __name__, url_prefix='/mypage')


# ── 로그인 필수 데코레이터 ────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('로그인이 필요합니다.')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── 마이페이지 메인 ───────────────────────────────────────────────────────────
# GET /mypage

@mypage_bp.route('/', methods=['GET'])
@login_required
def mypage():
    user_no = session.get('user_no')
    db = get_db()
    with db.cursor() as cursor:
        # 프로필 정보
        cursor.execute(
            'SELECT user_id, name, email FROM users WHERE user_idx = %s',
            (user_no,),
        )
        profile = cursor.fetchone()

        # 내가 작성한 게시글
        cursor.execute(
            '''
            SELECT b.board_id, b.title, b.type, b.view, b.created_at
            FROM board b
            WHERE b.user_idx = %s
            ORDER BY b.created_at DESC
            ''',
            (user_no,),
        )
        my_posts = cursor.fetchall()

        # 내가 추천한 게시글
        cursor.execute(
            '''
            SELECT b.board_id, b.title, b.type, b.view, b.created_at,
                   u.name AS author_name
            FROM board b
            JOIN board_like bl ON b.board_id = bl.board_id
            JOIN users u ON b.user_idx = u.user_idx
            WHERE bl.user_idx = %s
            ORDER BY bl.created_at DESC
            ''',
            (user_no,),
        )
        liked_posts = cursor.fetchall()

    for post in list(my_posts) + list(liked_posts):
        if post.get('created_at'):
            post['created_at'] = post['created_at'].strftime('%Y-%m-%d')

    return render_template(
        'mypage.html',
        profile=profile,
        my_posts=my_posts,
        liked_posts=liked_posts,
    )


# ── 프로필 수정 (닉네임, 이메일) ──────────────────────────────────────────────
# POST /mypage/profile
#
# ⚠️ 실습용 의도적 Mass Assignment 취약점 (OWASP A01:2021)
# 클라이언트가 보낸 role 파라미터를 검증 없이 그대로 UPDATE에 반영.
# → USER 권한 사용자가 role=ADMIN 파라미터를 추가하면 본인 계정이 관리자로 승격.
#
# PoC:
#   curl -X POST http://target/mypage/profile \
#     -H "Cookie: session=<USER세션>" \
#     -d "name=hacker&email=hacker@x.com&role=ADMIN"
#   → DB의 본인 row.role = 'ADMIN' 으로 변경 → 재로그인 시 /admin/* 전체 접근 가능
#
# 조치 방안:
#   - 화이트리스트 기반으로 수정 가능 필드(name, email)만 허용
#   - role / user_idx / password 같은 권한·식별 필드는 절대 클라이언트 입력으로 받지 않음

@mypage_bp.route('/profile', methods=['POST'])
@login_required
def update_profile():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    # ⚠️ 클라이언트에서 role 을 직접 수신 — 검증 없음
    role = request.form.get('role', '').strip()

    if not name:
        flash('닉네임을 입력해주세요.')
        return redirect(url_for('mypage.mypage'))
    if not email:
        flash('이메일을 입력해주세요.')
        return redirect(url_for('mypage.mypage'))

    user_no = session.get('user_no')
    db = get_db()
    try:
        with db.cursor() as cursor:
            if role:
                # ⚠️ 검증 없이 role 까지 UPDATE → 권한 상승 가능
                cursor.execute(
                    'UPDATE users SET name = %s, email = %s, role = %s WHERE user_idx = %s',
                    (name, email, role, user_no),
                )
            else:
                cursor.execute(
                    'UPDATE users SET name = %s, email = %s WHERE user_idx = %s',
                    (name, email, user_no),
                )
        db.commit()
        session['user_name'] = name
        # 세션의 role 도 함께 갱신 (재로그인 없이 바로 권한 상승 효과 확인 가능)
        if role:
            session['user_role'] = role
        flash('프로필이 수정되었습니다.')
    except Exception as e:
        db.rollback()
        flash(f'수정 중 오류가 발생했습니다: {e}')

    return redirect(url_for('mypage.mypage'))


# ── 비밀번호 변경 ─────────────────────────────────────────────────────────────
# POST /mypage/password

@mypage_bp.route('/password', methods=['POST'])
@login_required
def update_password():
    current_pw = request.form.get('current_pw', '')
    new_pw = request.form.get('new_pw', '')
    confirm_pw = request.form.get('confirm_pw', '')

    if not all([current_pw, new_pw, confirm_pw]):
        flash('모든 비밀번호 항목을 입력해주세요.')
        return redirect(url_for('mypage.mypage'))
    if new_pw != confirm_pw:
        flash('새 비밀번호가 일치하지 않습니다.')
        return redirect(url_for('mypage.mypage'))
    if len(new_pw) < 4:
        flash('비밀번호는 4자 이상이어야 합니다.')
        return redirect(url_for('mypage.mypage'))

    user_no = session.get('user_no')
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            'SELECT password FROM users WHERE user_idx = %s',
            (user_no,),
        )
        user = cursor.fetchone()

    if not user or not check_password_hash(user['password'], current_pw):
        flash('현재 비밀번호가 올바르지 않습니다.')
        return redirect(url_for('mypage.mypage'))

    try:
        with db.cursor() as cursor:
            cursor.execute(
                'UPDATE users SET password = %s WHERE user_idx = %s',
                (generate_password_hash(new_pw), user_no),
            )
        db.commit()
        flash('비밀번호가 변경되었습니다.')
    except Exception as e:
        db.rollback()
        flash(f'변경 중 오류가 발생했습니다: {e}')

    return redirect(url_for('mypage.mypage'))
