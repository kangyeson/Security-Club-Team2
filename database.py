import pymysql
import os

def get_db_connection():
    # 환경변수 혹은 docker-compose의 서비스명을 주소로 사용
    conn = pymysql.connect(
        host='db',  # docker-compose.yml의 서비스 이름
        user='root',
        password=os.environ.get('DB_PASS', 'rkcjs123!'),
        database='hacking_lab'
    )
    return conn