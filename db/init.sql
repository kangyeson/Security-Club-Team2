-- 데이터베이스 선택
USE security_lab;

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    user_idx    BIGINT       NOT NULL AUTO_INCREMENT,
    user_id     VARCHAR(50)  NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    name        VARCHAR(20)  NOT NULL,
    role        ENUM('USER', 'ADMIN') NOT NULL DEFAULT 'USER',
    email       VARCHAR(100),
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_idx)
);

-- 첨부파일 테이블
CREATE TABLE IF NOT EXISTS file (
    file_id     BIGINT       NOT NULL AUTO_INCREMENT,
    file_name   VARCHAR(255),
    file_path   VARCHAR(500),
    PRIMARY KEY (file_id)
);

-- 게시글 테이블
CREATE TABLE IF NOT EXISTS board (
    board_id    BIGINT       NOT NULL AUTO_INCREMENT,
    user_idx    BIGINT       NOT NULL,
    file_id     BIGINT,
    title       VARCHAR(200) NOT NULL,
    content     TEXT,
    view        INT          NOT NULL DEFAULT 0,
    type        ENUM('NORMAL', 'NOTICE') NOT NULL DEFAULT 'NORMAL',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (board_id),
    FOREIGN KEY (user_idx) REFERENCES users(user_idx),
    FOREIGN KEY (file_id)  REFERENCES file(file_id)
);

-- 게시글 추천 테이블
CREATE TABLE IF NOT EXISTS board_like (
    user_idx   BIGINT   NOT NULL,
    board_id   BIGINT   NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_idx, board_id),
    FOREIGN KEY (user_idx) REFERENCES users(user_idx) ON DELETE CASCADE,
    FOREIGN KEY (board_id) REFERENCES board(board_id) ON DELETE CASCADE
);

-- 댓글 테이블
CREATE TABLE IF NOT EXISTS comment (
    comment_id  BIGINT       NOT NULL AUTO_INCREMENT,
    user_idx    BIGINT       NOT NULL,
    board_id    BIGINT       NOT NULL,
    parent_id   BIGINT,
    content     TEXT         NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (comment_id),
    FOREIGN KEY (user_idx)  REFERENCES users(user_idx),
    FOREIGN KEY (board_id)  REFERENCES board(board_id),
    FOREIGN KEY (parent_id) REFERENCES comment(comment_id)
);

-- 초기 계정 데이터
-- ⚠️ 실습용 의도적 취약점: 평문 비밀번호 저장 (SQL Injection 시연을 위해)
INSERT INTO users (user_id, password, name, role, email) VALUES
    ('admin',  'admin1234', '관리자', 'ADMIN', 'admin@security.lab'),
    ('user01', 'user01',    '홍길동', 'USER',  'user01@security.lab'),
    ('user02', 'user02',    '김철수', 'USER',  'user02@security.lab'),
    ('user03', 'user03',    '이영희', 'USER',  'user03@security.lab'),
    ('user04', 'user04',    '박민준', 'USER',  'user04@security.lab'),
    ('user05', 'user05',    '최수진', 'USER',  'user05@security.lab'),
    ('user06', 'user06',    '정도윤', 'USER',  'user06@security.lab'),
    ('user07', 'user07',    '강지우', 'USER',  'user07@security.lab'),
    ('user08', 'user08',    '윤서연', 'USER',  'user08@security.lab'),
    ('user09', 'user09',    '임현우', 'USER',  'user09@security.lab'),
    ('user10', 'user10',    '한소희', 'USER',  'user10@security.lab'),
    ('user11', 'user11',    '오태양', 'USER',  'user11@security.lab'),
    ('user12', 'user12',    '신예원', 'USER',  'user12@security.lab'),
    ('guest',  'guest',     '게스트', 'USER',  'guest@security-lab.kr');
