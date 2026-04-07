from flask import Blueprint, request, jsonify, session
from blueprints.db import get_db

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