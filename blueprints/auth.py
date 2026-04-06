from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from models.user import UserModel
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# --- 1. 회원가입 ---
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    user_id = request.form.get('id')
    password = request.form.get('pw')
    name = request.form.get('name')
    email = request.form.get('email')

    if not all([user_id, password, name, email]):
        flash("모든 항목을 입력해주세요.")
        return redirect(url_for('auth.signup'))

    if UserModel.get_user_by_id(user_id):
        flash("이미 존재하는 아이디입니다.")
        return redirect(url_for('auth.signup'))

    success = UserModel.create_user(user_id, password, name, email)
    if success:
        flash("회원가입이 완료되었습니다. 로그인해주세요.")
        return redirect(url_for('auth.login'))
    else:
        flash("회원가입 중 오류가 발생했습니다.")
        return redirect(url_for('auth.signup'))


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


# --- 3. 로그인 / 로그아웃 ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    user_id = request.form.get('id')
    password = request.form.get('pw')

    if not user_id or not password:
        flash("아이디와 비밀번호를 모두 입력해주세요.")
        return redirect(url_for('auth.login'))

    user = UserModel.get_user_by_id(user_id)

    if user and check_password_hash(user['password'], password):
        session.clear()
        session['user_no'] = user['user_idx']
        session['user_id'] = user['user_id']
        session['user_name'] = user['name']
        session['user_role'] = user['role']
        return redirect(url_for('home'))
    else:
        flash("아이디 또는 비밀번호가 일치하지 않습니다.")
        return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


# --- 4. 아이디 찾기 ---
@auth_bp.route('/find-id', methods=['GET', 'POST'])
def find_id():
    if request.method == 'GET':
        return render_template('find_id.html')

    name = request.form.get('name')
    email = request.form.get('email')

    if not name or not email:
        flash("이름과 이메일을 모두 입력해주세요.")
        return redirect(url_for('auth.find_id'))

    user = UserModel.get_user_by_name_email(name, email)
    if user:
        flash(f"가입하신 아이디는 '{user['user_id']}' 입니다.")
    else:
        flash("입력하신 정보와 일치하는 계정을 찾을 수 없습니다.")
    return redirect(url_for('auth.find_id'))


# --- 5. 비밀번호 찾기 및 재설정 ---
@auth_bp.route('/find-pw', methods=['GET', 'POST'])
def find_pw():
    if request.method == 'GET':
        return render_template('find_pw.html')

    user_id = request.form.get('id')
    email = request.form.get('email')
    new_pw = request.form.get('new_pw')

    if not all([user_id, email, new_pw]):
        flash("모든 항목을 입력해주세요.")
        return redirect(url_for('auth.find_pw'))

    if len(new_pw) < 4:
        flash("비밀번호는 4자 이상이어야 합니다.")
        return redirect(url_for('auth.find_pw'))

    success = UserModel.reset_password_by_id_email(user_id, email, new_pw)
    if success:
        flash("비밀번호가 변경되었습니다. 새 비밀번호로 로그인해주세요.")
        return redirect(url_for('auth.login'))
    else:
        flash("아이디 또는 이메일 정보가 일치하지 않습니다.")
        return redirect(url_for('auth.find_pw'))
