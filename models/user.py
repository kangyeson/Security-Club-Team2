from blueprints.db import get_db

class UserModel:
    @staticmethod
    def create_user(user_id, password, name, email):
        """새로운 사용자를 DB에 INSERT 합니다.
        ⚠️ 실습용 의도적 취약점: 비밀번호를 평문으로 저장 (SQLi 시연용)."""
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO users (user_id, password, name, email, role, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, 'USER', NOW(), NOW())
                """
                cursor.execute(sql, (user_id, password, name, email))
            conn.commit()
            return True
        except Exception as e:
            print(f"DB Insert Error: {e}")
            conn.rollback()
            return False

    @staticmethod
    def get_user_by_id(user_id):
        """아이디로 사용자 조회 (로그인, 중복확인 등에 사용)."""
        conn = get_db()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM users WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            return cursor.fetchone()

    @staticmethod
    def get_user_by_no(user_no):
        """PK(user_idx)로 사용자 조회."""
        conn = get_db()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM users WHERE user_idx = %s"
            cursor.execute(sql, (user_no,))
            return cursor.fetchone()

    @staticmethod
    def get_user_by_name_email(name, email):
        """아이디 찾기: 이름과 이메일로 사용자 조회."""
        conn = get_db()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM users WHERE name = %s AND email = %s"
            cursor.execute(sql, (name, email))
            return cursor.fetchone()

    @staticmethod
    def reset_password_by_id_email(user_id, email, new_password):
        """비밀번호 재설정: 아이디와 이메일이 일치하면 비밀번호 변경.
        ⚠️ 실습용 의도적 취약점: 평문 저장."""
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT user_idx FROM users WHERE user_id = %s AND email = %s"
                cursor.execute(sql, (user_id, email))
                user = cursor.fetchone()
                if not user:
                    return False

                sql = "UPDATE users SET password = %s, updated_at = NOW() WHERE user_id = %s"
                cursor.execute(sql, (new_password, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"DB Update Error: {e}")
            conn.rollback()
            return False

    @staticmethod
    def verify_password(stored_password, provided_password):
        """⚠️ 실습용 의도적 취약점: 평문 비교."""
        return stored_password == provided_password
