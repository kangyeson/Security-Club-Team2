# 🖥️ Community Board — 커뮤니티 게시판

Docker + PostgreSQL + FastAPI + React 기반 풀스택 커뮤니티 게시판

---

## 🚀 빠른 시작 (Docker)

```bash
# 프로젝트 디렉토리에서 실행
docker-compose up --build
```

| 서비스 | URL |
|--------|-----|
| 프론트엔드 | http://localhost:3000 |
| 백엔드 API | http://localhost:8000 |
| API 문서 (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

### 기본 관리자 계정
- **아이디**: `admin`
- **비밀번호**: `admin1234`

---

## 📋 구현 기능 목록

### 회원 관련
| 기능 | API | 설명 |
|------|-----|------|
| 회원가입 | `POST /api/auth/register` | 아이디/이메일/닉네임/비밀번호/전화번호 |
| 로그인 | `POST /api/auth/login` | JWT 토큰 발급 |
| 아이디 찾기 | `POST /api/auth/find-username` | 이메일로 마스킹된 아이디 반환 |
| 비밀번호 찾기 | `POST /api/auth/find-password` | 재설정 토큰 발급 |
| 비밀번호 재설정 | `POST /api/auth/reset-password` | 토큰으로 비밀번호 변경 |
| 회원정보 조회 | `GET /api/auth/me` | 내 정보 조회 |
| 회원정보 수정 | `PUT /api/auth/me` | 닉네임/이메일/전화번호 변경 |
| 비밀번호 변경 | `POST /api/auth/change-password` | 현재 비밀번호 확인 후 변경 |

### 게시판 관련
| 기능 | API | 설명 |
|------|-----|------|
| 게시글 목록 | `GET /api/posts` | 페이징/카테고리/검색/공지 우선 |
| 게시글 작성 | `POST /api/posts` | 마크다운 지원, 카테고리 선택 |
| 게시글 수정 | `PUT /api/posts/:id` | 작성자/관리자만 가능 |
| 게시글 삭제 | `DELETE /api/posts/:id` | 소프트 삭제 |
| 조회수 | 자동 | 게시글 조회 시 자동 증가 |
| 추천(좋아요) | `POST /api/posts/:id/like` | 토글 방식 |
| 댓글 목록 | `GET /api/posts/:id/comments` | 트리 구조 (대댓글 포함) |
| 댓글 작성 | `POST /api/posts/:id/comments` | 대댓글 지원 (parent_id) |
| 댓글 수정 | `PUT /api/posts/:id/comments/:cid` | 작성자/관리자만 |
| 댓글 삭제 | `DELETE /api/posts/:id/comments/:cid` | 소프트 삭제 |
| 파일 업로드 | `POST /api/posts/:id/attachments` | 다중 파일, 10MB 제한 |
| 파일 다운로드 | `GET /api/attachments/:id/download` | 다운로드 횟수 카운트 |
| 공지사항 | 게시글 속성 | 관리자만 설정, 목록 상단 고정 |

### 관리자 관련
| 기능 | API | 설명 |
|------|-----|------|
| 대시보드 통계 | `GET /api/admin/stats` | 회원/게시글/공지 통계 |
| 회원 목록 | `GET /api/admin/users` | 검색/페이징 |
| 회원 권한 변경 | `PUT /api/admin/users/:id` | role/활성상태 변경 |
| 회원 비활성화 | `DELETE /api/admin/users/:id` | 계정 비활성화 |
| 게시글 관리 | `GET /api/admin/posts` | 전체 게시글 (삭제 포함) |
| 게시글 삭제 | `DELETE /api/admin/posts/:id` | 관리자 삭제 |
| 게시글 복구 | `PUT /api/admin/posts/:id/restore` | 삭제된 글 복구 |
| 공지 토글 | `PUT /api/admin/posts/:id/toggle-notice` | 공지 등록/해제 |

### 추가 구현 사항
- ✅ **마크다운 문법 지원**: 작성 시 마크다운 입력, 미리보기, HTML 렌더링
- ✅ **Docker Compose**: PostgreSQL + FastAPI + React(Nginx) 3-컨테이너 구성
- ✅ **PostgreSQL (RDBMS)**: 관계형 DB 스키마, 인덱스, FK, 제약조건

---

## 🏗️ 기술 스택

### Backend
- **FastAPI** — 비동기 REST API
- **SQLAlchemy 2.0** — 비동기 ORM (asyncpg)
- **PostgreSQL 16** — RDBMS
- **JWT (python-jose)** — 인증/인가
- **Passlib + bcrypt** — 비밀번호 해싱
- **Markdown + Bleach** — 마크다운 렌더링 & XSS 방지

### Frontend
- **React 18** — SPA
- **React Router 6** — 클라이언트 라우팅
- **Axios** — HTTP 클라이언트
- **react-markdown** — 마크다운 렌더링
- **Nginx** — 정적 파일 서빙 & API 프록시

### Infrastructure
- **Docker Compose** — 멀티 컨테이너 오케스트레이션
- **PostgreSQL 16 Alpine** — 경량 DB 이미지
- **Nginx Alpine** — 프론트엔드 서빙

---

## 📁 프로젝트 구조

```
community-board/
├── docker-compose.yml
├── db/
│   └── init.sql                 # DB 스키마 & 초기 데이터
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # FastAPI 앱 엔트리
│       ├── config.py            # 환경 설정
│       ├── database.py          # DB 연결
│       ├── models/
│       │   └── models.py        # SQLAlchemy 모델
│       ├── schemas/
│       │   └── schemas.py       # Pydantic 스키마
│       ├── routers/
│       │   ├── auth.py          # 인증 API
│       │   ├── posts.py         # 게시글 API
│       │   ├── comments.py      # 댓글 API
│       │   ├── files.py         # 파일 업/다운로드 API
│       │   └── admin.py         # 관리자 API
│       └── utils/
│           └── auth.py          # JWT/비밀번호 유틸
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── public/
    │   └── index.html
    └── src/
        ├── index.js
        ├── App.js
        ├── api.js               # Axios 인스턴스
        ├── context/
        │   └── AuthContext.js    # 인증 상태 관리
        ├── components/
        │   └── Header.js
        ├── pages/
        │   ├── PostList.js      # 게시글 목록
        │   ├── PostDetail.js    # 게시글 상세
        │   ├── PostForm.js      # 글 작성/수정
        │   ├── Login.js
        │   ├── Register.js
        │   ├── FindAccount.js   # ID/PW 찾기
        │   ├── Profile.js       # 내 정보 관리
        │   └── AdminDashboard.js
        └── styles/
            └── global.css
```

---

## ⚙️ 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://admin:admin1234@db:5432/community` | DB 연결 문자열 |
| `SECRET_KEY` | `your-super-secret-key-change-in-production` | JWT 서명 키 |
| `UPLOAD_DIR` | `/app/uploads` | 파일 업로드 경로 |

> ⚠️ 프로덕션 배포 시 `SECRET_KEY`와 DB 비밀번호를 반드시 변경하세요.

---

## 🗄️ DB 스키마

- **users** — 회원 (아이디, 이메일, 비밀번호, 닉네임, 역할, 활성 상태)
- **posts** — 게시글 (제목, 내용, 마크다운HTML, 카테고리, 공지, 조회/추천/댓글수)
- **post_likes** — 추천 (중복 방지 UNIQUE 제약)
- **comments** — 댓글 (대댓글: parent_id 자기참조)
- **attachments** — 첨부파일 (원본명, 저장명, 크기, MIME, 다운로드 수)
- **password_reset_tokens** — 비밀번호 재설정 토큰

---

## 🔒 권한 체계

| 역할 | 설명 |
|------|------|
| `user` | 일반 회원 — 글/댓글 CRUD (자신의 것만) |
| `admin` | 관리자 — 모든 글/댓글 관리, 공지 설정, 회원 관리 |
| `superadmin` | 최고 관리자 — admin 권한 부여/해제 가능 |
