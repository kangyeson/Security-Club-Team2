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
-- 주의: 비밀번호는 반드시 파이썬 werkzeug.security로 생성한 '해시값'을 넣어야 로그인 로직과 호환됨
-- 아래는 'admin123', 'guest123'을 임의로 해싱한 예시 값입니다.
INSERT INTO users (user_id, password, name, role)
VALUES ('admin', 'scrypt:32768:8:1$xYzA...가짜해시값...$1234', '관리자', 'ADMIN');

INSERT INTO users (user_id, password, name, role)
VALUES ('guest', 'scrypt:32768:8:1$aBcd...가짜해시값...$5678', '게스트', 'USER');