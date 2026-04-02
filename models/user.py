from database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

class UserModel:
    @staticmethod
    def create_user(user_id, password, name, email):
        """새로운 사용자를 DB에 INSERT 합니다."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # 비밀번호 해싱 (보안의 핵심)
        hashed_password = generate_password_hash(password)

        try:
            # 안전한 방식 (Prepared Statement 적용)
            # 향후 SQLi 취약점 버전을 만들려면 이 부분을 f-string으로 바꾸면 됨
            sql = """
                INSERT INTO users (user_id, password, name, email, role, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, 'USER', NOW(), NOW())
            """
            cursor.execute(sql, (user_id, hashed_password, name, email))
            conn.commit()
            return True
        except Exception as e:
            print(f"DB Insert Error: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_user_by_id(user_id):
        """아이디 중복 확인 및 로그인 시 사용합니다."""
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            sql = "SELECT * FROM users WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            user = cursor.fetchone()
            return user  # 딕셔너리 형태로 반환됨 (DictCursor 덕분)
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def verify_password(stored_password, provided_password):
        """DB의 해시된 비번과 사용자가 입력한 비번을 비교"""
        return check_password_hash(stored_password, provided_password)