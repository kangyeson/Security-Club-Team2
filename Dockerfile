# 도커가 파이썬 환경을 자동으로 구성하게 만드는 파일
# 1. 베이스 이미지 설정 (파이썬 3.11 사용)
FROM python:3.11-slim

# 2. 컨테이너 내부의 작업 디렉토리 설정
WORKDIR /app

# 3. 라이브러리 설치를 위해 목록 복사
COPY requirements.txt .

# 4. 필요한 라이브러리 설치 (flask, mysql-connector-python 등)
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드를 컨테이너로 복사
COPY . .

# 6. Flask가 외부 포트와 통신할 수 있게 설정 (기본 5000번)
EXPOSE 5000

# 7. 서버 실행
CMD ["python", "app.py"]