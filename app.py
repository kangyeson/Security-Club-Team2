from flask import Flask, render_template
import pymysql.connections
import os

app = Flask(__name__)

def get_db_connection():
    # 환경변수 혹은 docker-compose의 서비스명을 주소로 사용
    conn = pymysql.connect(
        host='db',  # docker-compose.yml의 서비스 이름
        user='root',
        password=os.environ.get('DB_PASS', 'rkcjs123!'),
        database='hacking_lab'
    )
    return conn

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

if __name__ == '__main__':
    # host='0.0.0.0'이 아니면 도커 외부에서 접속 불가
    app.run(host='0.0.0.0', port=5000)
