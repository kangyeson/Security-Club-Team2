# database.py
import os
import pymysql

def get_db_connection():
    # 서버(도커 내부)에서는 'db'를 보고, 로컬에서는 '127.0.0.1'을 봄
    # 환경변수 'DEPLOYMENT'가 설정되어 있지 않으면 로컬 모드로 동작
    if os.environ.get('DEPLOYMENT') == 'SERVER':
        db_host = 'db'
        db_port = 3306
    else:
        db_host = '127.0.0.1'
        db_port = 3308  # 로컬 테스트용

    print(f"Connecting to {db_host}:{db_port}");
    conn = pymysql.connect(
        host=db_host,
        port=db_port,
        user='root',
        password=os.environ.get('DB_PASS', 'rkcjs123!'),
        database='security_lab',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn