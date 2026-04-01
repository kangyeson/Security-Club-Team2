from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from models.user import UserModel

# auth라는 이름의 블루프린트 생성
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# --- 1. 회원가입 화면 및 기능 ---
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    if request.method == 'POST':
        # form 데이터 받아오기
        user_id = request.form.get('id')
        password = request.form.get('pw')
        name = request.form.get('name')
        email = request.form.get('email')

        # 서버 측 유효성 검사 (프론트엔드를 우회하는 공격 대비)
        if not all([user_id, password, name, email]):
            return "모든 항목을 입력해주세요.", 400

        # 중복 검사 (서버에서 한 번 더)
        if UserModel.get_user_by_id(user_id):
            return "이미 존재하는 아이디입니다.", 400

        # DB 저장 시도
        success = UserModel.create_user(user_id, password, name, email)

        if success:
            # 가입 성공 시 로그인 페이지로 이동
            return redirect(url_for('auth.login'))
        else:
            return "회원가입 중 오류가 발생했습니다.", 500


# --- 2. 아이디 중복 확인 API (Ajax 용) ---
@auth_bp.route('/check-id', methods=['GET'])
def check_id():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"available": False, "message": "아이디를 입력하세요."})

    user = UserModel.get_user_by_id(user_id)
    if user:
        return jsonify({"available": False, "message": "이미 사용 중인 아이디입니다."})
    else:
        return jsonify({"available": True, "message": "사용 가능한 아이디입니다."})


@auth_bp.route('/login')
def login():
    return render_template('login.html')


@auth_bp.route('/find-id')
def find_id():
    return render_template('find_id.html')


@auth_bp.route('/find-pw')
def find_pw():
    return render_template('find_pw.html')