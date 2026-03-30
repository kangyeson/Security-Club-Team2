-- DB 생성 테스트 용, 추후 ORM 구현하여 삭제 예정
-- 1. 데이터베이스 선택 (docker-compose에 설정한 이름과 동일해야 함)
USE security_lab;

-- 2. 사용자 테이블 생성 (예시)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(10) DEFAULT 'user'
);

-- 3. 초기 관리자 계정 추가
INSERT INTO users (username, password, role) VALUES ('admin', 'password123', 'admin');
INSERT INTO users (username, password, role) VALUES ('guest', 'guest', 'user');