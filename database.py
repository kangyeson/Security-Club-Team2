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

    return pymysql.connect(
        host=db_host,
        port=db_port,
        user='root',
        password=os.environ.get('DB_PASS', 'rkcjs123!'),
        database='security_lab',
        cursorclass=pymysql.cursors.DictCursor
    )

# DB 조회하여 해당 유저의 정보 조회
def get_user_by_id(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # SQL Injection 방지를 위해 반드시 파라미터화된 쿼리(%s)를 사용
            sql = "SELECT * FROM users WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            return cursor.fetchone()
    finally:
        conn.close()
