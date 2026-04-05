from database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

class UserModel:
    @staticmethod
    def create_user(user_id, password, name, email):
        """새로운 사용자를 DB에 INSERT 합니다."""
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_password = generate_password_hash(password)
        try:
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
        """아이디로 사용자 조회 (로그인, 중복확인 등에 사용)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT * FROM users WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_user_by_no(user_no):
        """PK(user_idx)로 사용자 조회."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT * FROM users WHERE user_idx = %s"
            cursor.execute(sql, (user_no,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_user_by_name_email(name, email):
        """아이디 찾기: 이름과 이메일로 사용자 조회."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT * FROM users WHERE name = %s AND email = %s"
            cursor.execute(sql, (name, email))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def reset_password_by_id_email(user_id, email, new_password):
        """비밀번호 재설정: 아이디와 이메일이 일치하면 비밀번호 변경."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 먼저 아이디+이메일로 사용자 확인
            sql = "SELECT user_idx FROM users WHERE user_id = %s AND email = %s"
            cursor.execute(sql, (user_id, email))
            user = cursor.fetchone()
            if not user:
                return False

            hashed = generate_password_hash(new_password)
            sql = "UPDATE users SET password = %s, updated_at = NOW() WHERE user_id = %s"
            cursor.execute(sql, (hashed, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"DB Update Error: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def verify_password(stored_password, provided_password):
        """DB의 해시된 비번과 사용자가 입력한 비번을 비교."""
        return check_password_hash(stored_password, provided_password)
