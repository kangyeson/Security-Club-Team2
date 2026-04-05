from flask import Flask, render_template, session, jsonify
import os

app = Flask(__name__)

# ── 기본 설정 ─────────────────────────────────────────────────────────────────
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# 파일 업로드 최대 크기: 50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# 업로드 폴더 생성 (없으면 자동 생성)
UPLOAD_DIR = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── 블루프린트 등록 ────────────────────────────────────────────────────────────
from blueprints.admin import admin_bp   # /admin/*  (관리자 API + 페이지)
from blueprints.board import board_bp   # /board/*  (게시판 목록·상세)

app.register_blueprint(admin_bp)
app.register_blueprint(board_bp)


# ── 템플릿 전역 컨텍스트 ──────────────────────────────────────────────────────
# 모든 템플릿에서 is_admin 변수를 별도 전달 없이 바로 사용 가능
@app.context_processor
def inject_user():
    return {
        'is_admin':      session.get('role') == 'ADMIN',
        'current_user':  session.get('user_id'),
        'current_role':  session.get('role'),
    }


# ── 페이지 라우트 ──────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')


# ── 에러 핸들러 ───────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(_):
    # API 요청(JSON)이면 JSON, 페이지 요청이면 HTML 반환
    if _wants_json():
        return jsonify({'error': '요청한 리소스를 찾을 수 없습니다.'}), 404
    return render_template('error.html', code=404, message='페이지를 찾을 수 없습니다.'), 404

@app.errorhandler(403)
def forbidden(_):
    if _wants_json():
        return jsonify({'error': '접근 권한이 없습니다.'}), 403
    return render_template('error.html', code=403, message='접근 권한이 없습니다.'), 403

@app.errorhandler(413)
def request_entity_too_large(_):
    return jsonify({'error': '파일 크기가 너무 큽니다. 최대 50MB까지 업로드 가능합니다.'}), 413

@app.errorhandler(500)
def internal_error(_):
    if _wants_json():
        return jsonify({'error': '서버 내부 오류가 발생했습니다.'}), 500
    return render_template('error.html', code=500, message='서버 오류가 발생했습니다.'), 500


def _wants_json():
    """요청이 JSON 응답을 원하는지 확인 (API 클라이언트 vs 브라우저)"""
    from flask import request
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json'


# ── 실행 진입점 ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
