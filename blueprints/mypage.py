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

@mypage_bp.route('/profile', methods=['POST'])
@login_required
def update_profile():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()

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
            cursor.execute(
                'UPDATE users SET name = %s, email = %s WHERE user_idx = %s',
                (name, email, user_no),
            )
        db.commit()
        session['user_name'] = name
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
