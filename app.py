import os
from flask import Flask, render_template
from blueprints.auth.routes import auth_bp

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# 블루프린트 등록
app.register_blueprint(auth_bp)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == '__main__':
    # host='0.0.0.0'이 아니면 도커 외부에서 접속 불가
    app.run(host='0.0.0.0', port=5000)
