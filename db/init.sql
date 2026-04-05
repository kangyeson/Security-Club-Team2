-- 1. 데이터베이스 선택 (docker-compose의 MYSQL_DATABASE 값과 동일해야 함)
USE security_lab;

-- 2. 사용자 테이블 생성 (최신 ERD 반영)
CREATE TABLE IF NOT EXISTS users (
    user_idx BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(20) NOT NULL,
    role ENUM('USER', 'ADMIN') DEFAULT 'USER',
    email VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. 초기 관리자/게스트 계정 추가
-- admin 비밀번호: admin123 / guest 비밀번호: guest123
-- (werkzeug.security.generate_password_hash 로 생성된 실제 해시값)
INSERT INTO users (user_id, password, name, role, email)
VALUES ('admin', 'scrypt:32768:8:1$9TwGfIeQ0Idp1JuK$5115efbb8a85b707b8eec57c632864b0c9408a9d2436594cb37b718f3a566e13992cd7b7b112b91d8a0f15d3a27a5fcd07e995975dd59e4b53aa7b3a4705c11b', '관리자', 'ADMIN', 'admin@security-lab.kr');

INSERT INTO users (user_id, password, name, role, email)
VALUES ('guest', 'scrypt:32768:8:1$EFk8kM1aFW6RFjZ4$946627173bd038456e98e5edd4131ecc17600ec44bbc62ec82a435875c93d18253b7fbd42a7a8445453418588d5cfa19763fc829d670b35865866516282f319d', '게스트', 'USER', 'guest@security-lab.kr');