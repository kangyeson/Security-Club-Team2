from flask import Blueprint, request, jsonify, session
from blueprints.db import get_db
from flask import request, redirect, session
import pymysql
import os

# 'comment'라는 고유 네임스페이스를 가진 블루프린트 생성
comment_bp = Blueprint('comment', __name__)

@comment_bp.route('/board/<int:board_id>/comments', methods=['POST'])
def add_comment(board_id):
    # 1. 인증 확인
    user_no = session.get('user_no')
    if not user_no:
        return jsonify({'error': '로그인이 필요한 서비스입니다.'}), 401
    
    # 2. 데이터 처리 및 유효성 검사
    data = request.get_json()
    content = data.get('content', '').strip()
    parent_id = data.get('parent_id') #  대댓글을 위한 부모 ID 받기 (일반 댓글이면 None이 들어옴)
    
    if not content:
        return jsonify({'error': '댓글 내용을 입력해주세요.'}), 400

    # 3. 데이터베이스 저장
    db = get_db()
    try:
        with db.cursor() as cursor:
            #  SQL 쿼리에 parent_id가 들어갈 자리(%s) 추가
            sql = "INSERT INTO comment (board_id, user_idx, content, parent_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (board_id, user_no, content, parent_id))
        db.commit()
        return jsonify({'message': 'success'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'DB 오류: {str(e)}'}), 500


# 댓글 수정 기능

@comment_bp.route('/comments/<int:comment_id>/update', methods=['POST'])
def update_comment_no_js(comment_id):
    # 1. 로그인 확인
    user_idx = session.get('user_no')
    if not user_idx:
        return "로그인이 필요합니다.", 401

    # 2. 폼 데이터(수정된 내용) 가져오기
    new_content = request.form.get('content')
    if not new_content or not new_content.strip():
        return "내용을 입력해주세요.", 400

    # 3. 데이터베이스 연결 (이 부분이 빠져있었습니다!)
    conn = pymysql.connect(
        host=os.environ.get('DB_HOST', 'gachon.arang.kr'),
        port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASS', 'rkcjs123!'),
        database=os.environ.get('DB_NAME', 'security_lab'),
        charset='utf8mb4'
    )

    # 4. DB 업데이트 실행
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE comment 
        SET content = %s 
        WHERE comment_id = %s AND user_idx = %s
    ''', (new_content.strip(), comment_id, user_idx))
    
    # 5. 변경사항 저장 및 연결 종료
    conn.commit()
    cursor.close()
    conn.close()
    
    # 6. 이전 페이지로 되돌아가기
    return redirect(request.referrer)


# 댓글 삭제 기능
@comment_bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
def delete_my_comment_no_js(comment_id):
    # 1. 로그인 확인
    user_idx = session.get('user_no')
    if not user_idx:
        return "로그인이 필요합니다.", 401

    # 2. 데이터베이스 연결 (db.py의 연결 정보 적용)
    conn = pymysql.connect(
        host=os.environ.get('DB_HOST', 'gachon.arang.kr'),
        port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASS', 'rkcjs123!'),
        database=os.environ.get('DB_NAME', 'security_lab'),
        charset='utf8mb4'
    )

    # 3. DB 삭제 실행
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM comment 
        WHERE comment_id = %s AND user_idx = %s
    ''', (comment_id, user_idx))
    
    # 4. 변경사항 저장 및 연결 종료
    conn.commit()
    cursor.close()
    conn.close()
    
    # 5. 이전 페이지로 되돌아가기
    return redirect(request.referrer)