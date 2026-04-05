# database.py
import os
import pymysql

def get_db_connection():

    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'gachon.arang.kr'),
        port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASS', 'rkcjs123!'),
        database=os.environ.get('DB_NAME', 'security_lab'),
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
