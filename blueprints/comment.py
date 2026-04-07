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
    
    # 2. 데이터 유효성 검사
    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': '댓글 내용을 입력해주세요.'}), 400

    # 3. 데이터베이스 저장
    db = get_db()
    try:
        with db.cursor() as cursor:
            sql = "INSERT INTO comment (board_id, user_idx, content) VALUES (%s, %s, %s)"
            cursor.execute(sql, (board_id, user_no, content))
        db.commit()
        return jsonify({'message': 'success'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'DB 오류: {str(e)}'}), 500