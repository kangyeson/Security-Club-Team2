# 웹해킹 실습 프로젝트

## 📌 프로젝트 소개
웹 취약점(XSS, SQL Injection 등)을 실습하기 위한 웹 애플리케이션

## 🛠 기술 스택
- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- DB: SQLite (또는 MySQL)

## 📁 프로젝트 구조
 ```
 project/
├── backend/
│	├── app.py
│	├── models/
│	│   ├── user.py
│	│   └── post.py
│	├── blueprints/
│	│   ├── auth/
│	│   │   └── routes.py
│	│   └── board/
│	│       └── routes.py
│	└── db/
├──frontend/
│        ├── templates/
│        │   ├── index.html
│        │   └── login.html
│        └── static/
│            ├── css/
│            │   ├── common.css
│            │   ├── index.css
│            │   └── login.css
│            └── js/
│                ├── common.js
│                ├── index.js
│                └── login.js
├── requirements.txt
└── README.md
 ```