import math
import os
import uuid
from functools import wraps

import pymysql
from flask import (Blueprint, abort, current_app, g, redirect,
                   render_template, request, session, url_for, flash)
from werkzeug.utils import secure_filename

board_bp = Blueprint('board', __name__, url_prefix='/board')


# ── DB 연결 헬퍼 ─────────────────────────────────────────────────────────────

def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(
            host=os.environ.get('DB_HOST', 'gachon.arang.kr'),
            port=int(os.environ.get('DB_PORT', 3306)),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASS', 'rkcjs123!'),
            database=os.environ.get('DB_NAME', 'security_lab'),
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4',
        )
    return g.db


@board_bp.teardown_app_request
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ── 로그인 필수 데코레이터 ────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('로그인이 필요합니다.')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── 파일 저장 헬퍼 ────────────────────────────────────────────────────────────

def save_uploaded_file(file_obj):
    """업로드된 파일을 저장하고 (original_name, stored_path) 를 반환."""
    original_name = secure_filename(file_obj.filename)
    unique_name = f'{uuid.uuid4().hex}_{original_name}'
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_obj.save(os.path.join(upload_dir, unique_name))
    return original_name, f'/static/uploads/{unique_name}'


# ── 게시글 목록 ───────────────────────────────────────────────────────────────
# GET /board/?page=1&title=검색어

@board_bp.route('/', methods=['GET'])
def board_list():
    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        page = 1

    title_keyword = request.args.get('title', '').strip()
    per_page = 15
    offset = (page - 1) * per_page

    where_clause = ''
    params = []
    if title_keyword:
        where_clause = 'WHERE b.title LIKE %s'
        params.append(f'%{title_keyword}%')

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            f'SELECT COUNT(*) AS total FROM board b {where_clause}',
            params,
        )
        total = cursor.fetchone()['total']

        cursor.execute(
            f'''
            SELECT
                b.board_id, b.title, b.view, b.type, b.created_at,
                u.name AS author_name, u.role AS author_role
            FROM board b
            JOIN users u ON b.user_idx = u.user_idx
            {where_clause}
            ORDER BY
                CASE WHEN b.type = 'NOTICE' THEN 0 ELSE 1 END ASC,
                b.created_at DESC
            LIMIT %s OFFSET %s
            ''',
            params + [per_page, offset],
        )
        posts = cursor.fetchall()

    for post in posts:
        if post['created_at']:
            post['created_at'] = post['created_at'].strftime('%Y-%m-%d')

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return render_template(
        'board/list.html',
        posts=posts,
        page=page,
        total_pages=total_pages,
        total=total,
        title_keyword=title_keyword,
    )


# ── 게시글 상세 ───────────────────────────────────────────────────────────────
# GET /board/<board_id>

@board_bp.route('/<int:board_id>', methods=['GET'])
def board_detail(board_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute('UPDATE board SET view = view + 1 WHERE board_id = %s', (board_id,))

        cursor.execute(
            '''
            SELECT
                b.board_id, b.title, b.content, b.view, b.type,
                b.created_at, b.updated_at, b.user_idx AS author_idx,
                u.name AS author_name, u.role AS author_role,
                f.file_name, f.file_path
            FROM board b
            JOIN users u ON b.user_idx = u.user_idx
            LEFT JOIN file f ON b.file_id = f.file_id
            WHERE b.board_id = %s
            ''',
            (board_id,),
        )
        post = cursor.fetchone()

    db.commit()

    if post is None:
        abort(404)

    for key in ('created_at', 'updated_at'):
        if post.get(key):
            post[key] = post[key].strftime('%Y-%m-%d %H:%M:%S')

    return render_template(
        'board/detail.html',
        post=post,
        current_user_no=session.get('user_no'),
        current_role=session.get('user_role'),
    )


# ── 게시글 작성 ───────────────────────────────────────────────────────────────
# GET  /board/write
# POST /board/write

@board_bp.route('/write', methods=['GET', 'POST'])
@login_required
def board_write():
    if request.method == 'GET':
        return render_template('board/write.html', mode='write', post=None)

    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()

    if not title:
        flash('제목을 입력해주세요.')
        return redirect(url_for('board.board_write'))
    if not content:
        flash('내용을 입력해주세요.')
        return redirect(url_for('board.board_write'))

    uploaded = request.files.get('file')
    db = get_db()
    try:
        file_id = None
        if uploaded and uploaded.filename:
            original_name, stored_path = save_uploaded_file(uploaded)
            with db.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO file (file_name, file_path) VALUES (%s, %s)',
                    (original_name, stored_path),
                )
                file_id = cursor.lastrowid

        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO board (user_idx, title, content, type, file_id) VALUES (%s, %s, %s, 'NORMAL', %s)",
                (session['user_no'], title, content, file_id),
            )
            board_id = cursor.lastrowid

        db.commit()
    except Exception as e:
        db.rollback()
        flash(f'게시글 등록 중 오류가 발생했습니다: {e}')
        return redirect(url_for('board.board_write'))

    return redirect(url_for('board.board_detail', board_id=board_id))


# ── 게시글 수정 ───────────────────────────────────────────────────────────────
# GET  /board/<id>/edit
# POST /board/<id>/edit

@board_bp.route('/<int:board_id>/edit', methods=['GET', 'POST'])
@login_required
def board_edit(board_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            '''
            SELECT b.board_id, b.title, b.content, b.type, b.user_idx,
                   b.file_id, f.file_name, f.file_path
            FROM board b
            LEFT JOIN file f ON b.file_id = f.file_id
            WHERE b.board_id = %s
            ''',
            (board_id,),
        )
        post = cursor.fetchone()

    if post is None:
        abort(404)

    if post['type'] == 'NOTICE' and session.get('user_role') != 'ADMIN':
        abort(403)

    if post['user_idx'] != session.get('user_no') and session.get('user_role') != 'ADMIN':
        abort(403)

    if request.method == 'GET':
        return render_template('board/write.html', mode='edit', post=post)

    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()

    if not title:
        flash('제목을 입력해주세요.')
        return redirect(url_for('board.board_edit', board_id=board_id))
    if not content:
        flash('내용을 입력해주세요.')
        return redirect(url_for('board.board_edit', board_id=board_id))

    try:
        new_file_id = post['file_id']
        uploaded = request.files.get('file')
        if uploaded and uploaded.filename:
            original_name, stored_path = save_uploaded_file(uploaded)
            with db.cursor() as cursor:
                if new_file_id:
                    cursor.execute(
                        'UPDATE file SET file_name = %s, file_path = %s WHERE file_id = %s',
                        (original_name, stored_path, new_file_id),
                    )
                else:
                    cursor.execute(
                        'INSERT INTO file (file_name, file_path) VALUES (%s, %s)',
                        (original_name, stored_path),
                    )
                    new_file_id = cursor.lastrowid

        with db.cursor() as cursor:
            cursor.execute(
                'UPDATE board SET title = %s, content = %s, file_id = %s WHERE board_id = %s',
                (title, content, new_file_id, board_id),
            )

        db.commit()
    except Exception as e:
        db.rollback()
        flash(f'수정 중 오류가 발생했습니다: {e}')
        return redirect(url_for('board.board_edit', board_id=board_id))

    return redirect(url_for('board.board_detail', board_id=board_id))


# ── 게시글 삭제 ───────────────────────────────────────────────────────────────
# POST /board/<id>/delete

@board_bp.route('/<int:board_id>/delete', methods=['POST'])
@login_required
def board_delete(board_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute('SELECT board_id, file_id, user_idx FROM board WHERE board_id = %s', (board_id,))
        post = cursor.fetchone()

    if post is None:
        abort(404)

    if post['user_idx'] != session.get('user_no') and session.get('user_role') != 'ADMIN':
        abort(403)

    try:
        with db.cursor() as cursor:
            # 댓글 FK 정리 후 게시글 삭제
            cursor.execute('UPDATE comment SET parent_id = NULL WHERE board_id = %s', (board_id,))
            cursor.execute('DELETE FROM comment WHERE board_id = %s', (board_id,))
            cursor.execute('DELETE FROM board WHERE board_id = %s', (board_id,))
            if post['file_id']:
                cursor.execute('DELETE FROM file WHERE file_id = %s', (post['file_id'],))
        db.commit()
    except Exception as e:
        db.rollback()
        flash(f'삭제 중 오류가 발생했습니다: {e}')
        return redirect(url_for('board.board_detail', board_id=board_id))

    return redirect(url_for('board.board_list'))