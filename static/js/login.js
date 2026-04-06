// login_ui.js
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');

    loginForm.addEventListener('submit', (e) => {
        const userId = document.getElementById('user_id').value;
        const userPw = document.getElementById('user_pw').value;

        if (!userId || !userPw) {
            e.preventDefault();
            const card = document.querySelector('.login-card');
            card.style.animation = 'shake 0.5s';
            setTimeout(() => { card.style.animation = ''; }, 500);
            alert("아이디와 비밀번호를 모두 입력해주세요.");
        }
    });
});