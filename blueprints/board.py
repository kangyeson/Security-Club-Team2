from flask import Blueprint, request, render_template, g, session, abort
import pymysql
import os
import math

board_bp = Blueprint('board', __name__, url_prefix='/board')


# ── DB 연결 헬퍼 ─────────────────────────────────────────────────────────────

def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(
            host=os.environ.get('DB_HOST', 'db'),
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


# ── 페이지: 게시판 목록 ────────────────────────────────────────────────────────
#
# GET /board/
#   Query params:
#     page  (int, default 1)
#     title (str, optional) — 제목 검색 (부분 일치)
#
# 정렬 기준:
#   1. NOTICE 타입 → 항상 최상단 고정
#   2. 그 안에서 created_at DESC
#   3. NORMAL 글은 이후 created_at DESC

@board_bp.route('/', methods=['GET'])
def board_list():
    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        page = 1

    title_keyword = request.args.get('title', '').strip()
    per_page = 15
    offset   = (page - 1) * per_page

    # 제목 검색 조건
    where_clause = ''
    params = []
    if title_keyword:
        where_clause = 'WHERE b.title LIKE %s'
        params.append(f'%{title_keyword}%')

    db = get_db()
    with db.cursor() as cursor:
        # 전체 게시글 수 (검색 조건 반영)
        cursor.execute(
            f'SELECT COUNT(*) AS total FROM board b {where_clause}',
            params,
        )
        total = cursor.fetchone()['total']

        # NOTICE 먼저, 그 다음 최신순
        cursor.execute(
            f'''
            SELECT
                b.board_id,
                b.title,
                b.view,
                b.type,
                b.created_at,
                u.name       AS author_name,
                u.role       AS author_role
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

    is_admin = session.get('role') == 'ADMIN'
    return render_template(
        'board/list.html',
        posts=posts,
        page=page,
        total_pages=total_pages,
        total=total,
        is_admin=is_admin,
        title_keyword=title_keyword,
    )


# ── 페이지: 게시글 상세 ───────────────────────────────────────────────────────
#
# GET /board/<board_id>
#   - 조회수 1 증가
#   - 관리자 세션이면 is_admin=True 전달 → 수정 버튼 표시

@board_bp.route('/<int:board_id>', methods=['GET'])
def board_detail(board_id):
    db = get_db()
    with db.cursor() as cursor:
        # 조회수 증가
        cursor.execute('UPDATE board SET view = view + 1 WHERE board_id = %s', (board_id,))

        cursor.execute(
            '''
            SELECT
                b.board_id,
                b.title,
                b.content,
                b.view,
                b.type,
                b.created_at,
                b.updated_at,
                u.name      AS author_name,
                u.role      AS author_role,
                f.file_name AS file_name,
                f.file_path AS file_path
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
        if post[key]:
            post[key] = post[key].strftime('%Y-%m-%d %H:%M:%S')

    is_admin = session.get('role') == 'ADMIN'
    return render_template('board/detail.html', post=post, is_admin=is_admin)
