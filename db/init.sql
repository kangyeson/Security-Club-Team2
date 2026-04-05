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
-- admin / user01~12: 테스트용 평문 비밀번호
-- guest: 팀원 구현 계정 (werkzeug scrypt 해시)
INSERT INTO users (user_id, password, name, role, email) VALUES
    ('admin',  'scrypt:32768:8:1$JK9wQKyNcO1CdC34$f06950e284be512e2bc84ed92d98765119bc63196721058bfb5b43428d26eb5028e0c5915753b458c35b16122f39e035b7b8452ca468c14a84fd1b9abf141bac', '관리자', 'ADMIN', 'admin@security.lab'),
    ('user01', 'scrypt:32768:8:1$dXmibb1NKYdE77L4$4166107512b42442123caa3e68e56bb91122521d06ae8d56c935a75efd072feaf30d527a2b909db7bb49dfcf300da8c9ae6981de6a1c7d8cd5344b1a543af21a', '홍길동', 'USER',  'user01@security.lab'),
    ('user02', 'scrypt:32768:8:1$dXmibb1NKYdE77L4$4166107512b42442123caa3e68e56bb91122521d06ae8d56c935a75efd072feaf30d527a2b909db7bb49dfcf300da8c9ae6981de6a1c7d8cd5344b1a543af21a', '김철수', 'USER',  'user02@security.lab'),
    ('user03', 'scrypt:32768:8:1$dXmibb1NKYdE77L4$4166107512b42442123caa3e68e56bb91122521d06ae8d56c935a75efd072feaf30d527a2b909db7bb49dfcf300da8c9ae6981de6a1c7d8cd5344b1a543af21a', '이영희', 'USER',  'user03@security.lab'),
    ('user04', 'scrypt:32768:8:1$dXmibb1NKYdE77L4$4166107512b42442123caa3e68e56bb91122521d06ae8d56c935a75efd072feaf30d527a2b909db7bb49dfcf300da8c9ae6981de6a1c7d8cd5344b1a543af21a', '박민준', 'USER',  'user04@security.lab'),
    ('user05', 'scrypt:32768:8:1$dXmibb1NKYdE77L4$4166107512b42442123caa3e68e56bb91122521d06ae8d56c935a75efd072feaf30d527a2b909db7bb49dfcf300da8c9ae6981de6a1c7d8cd5344b1a543af21a', '최수진', 'USER',  'user05@security.lab'),
    ('user06', 'scrypt:32768:8:1$dXmibb1NKYdE77L4$4166107512b42442123caa3e68e56bb91122521d06ae8d56c935a75efd072feaf30d527a2b909db7bb49dfcf300da8c9ae6981de6a1c7d8cd5344b1a543af21a', '정도윤', 'USER',  'user06@security.lab'),
    ('user07', 'scrypt:32768:8:1$dXmibb1NKYdE77L4$4166107512b42442123caa3e68e56bb91122521d06ae8d56c935a75efd072feaf30d527a2b909db7bb49dfcf300da8c9ae6981de6a1c7d8cd5344b1a543af21a', '강지우', 'USER',  'user07@security.lab'),
    ('user08', 'scrypt:32768:8:1$dXmibb1NKYdE77L4$4166107512b42442123caa3e68e56bb91122521d06ae8d56c935a75efd072feaf30d527a2b909db7bb49dfcf300da8c9ae6981de6a1c7d8cd5344b1a543af21a', '윤서연', 'USER',  'user08@security.lab'),
    ('user09', 'scrypt:32768:8:1$dXmibb1NKYdE77L4$4166107512b42442123caa3e68e56bb91122521d06ae8d56c935a75efd072feaf30d527a2b909db7bb49dfcf300da8c9ae6981de6a1c7d8cd5344b1a543af21a', '임현우', 'USER',  'user09@security.lab'),
    ('user10', 'scrypt:32768:8:1$dXmibb1NKYdE77L4$4166107512b42442123caa3e68e56bb91122521d06ae8d56c935a75efd072feaf30d527a2b909db7bb49dfcf300da8c9ae6981de6a1c7d8cd5344b1a543af21a', '한소희', 'USER',  'user10@security.lab'),
    ('user11', 'scrypt:32768:8:1$dXmibb1NKYdE77L4$4166107512b42442123caa3e68e56bb91122521d06ae8d56c935a75efd072feaf30d527a2b909db7bb49dfcf300da8c9ae6981de6a1c7d8cd5344b1a543af21a', '오태양', 'USER',  'user11@security.lab'),
    ('user12', 'scrypt:32768:8:1$dXmibb1NKYdE77L4$4166107512b42442123caa3e68e56bb91122521d06ae8d56c935a75efd072feaf30d527a2b909db7bb49dfcf300da8c9ae6981de6a1c7d8cd5344b1a543af21a', '신예원', 'USER',  'user12@security.lab'),
    ('guest',  'scrypt:32768:8:1$EFk8kM1aFW6RFjZ4$946627173bd038456e98e5edd4131ecc17600ec44bbc62ec82a435875c93d18253b7fbd42a7a8445453418588d5cfa19763fc829d670b35865866516282f319d', '게스트', 'USER', 'guest@security-lab.kr');
