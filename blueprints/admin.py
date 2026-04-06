from flask import Blueprint, request, jsonify, session, g, render_template, abort, current_app
import pymysql
import os
import math
import uuid
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


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


@admin_bp.teardown_app_request
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ── 관리자 인증 데코레이터 ────────────────────────────────────────────────────

from functools import wraps

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
@admin_required
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
@admin_required
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
    where_clause = ''
    params = []

    if name_keyword:
        where_clause = 'WHERE name LIKE %s'
        params.append(f'%{name_keyword}%')

    offset = (page - 1) * per_page

    db = get_db()
    with db.cursor() as cursor:
        # 전체 건수
        cursor.execute(
            f'SELECT COUNT(*) AS total FROM users {where_clause}',
            params,
        )
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
            params + [per_page, offset],
        )
        users = cursor.fetchall()

    # datetime → 문자열 직렬화
    for user in users:
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
@admin_required
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
@admin_required
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
@admin_required
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


# ── 페이지: 공지 작성 ─────────────────────────────────────────────────────────
#
# GET /admin/notices/new

@admin_bp.route('/notices/new', methods=['GET'])
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
