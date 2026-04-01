document.addEventListener('DOMContentLoaded', function() {
    const pwInput = document.getElementById('user_pw');
    const pwConfirmInput = document.getElementById('user_pw_confirm');
    const pwMsg = document.getElementById('pw_msg');

    const btnCheckId = document.getElementById('btn_check_id');
    const idInput = document.getElementById('user_id');
    const idMsg = document.getElementById('id_msg');
    const signupForm = document.getElementById('signupForm');

    let isIdChecked = false; // 아이디 중복 확인 여부 상태 변수

    // 1. 비밀번호 실시간 일치 확인
    function checkPasswordMatch() {
        const pw = pwInput.value;
        const confirmPw = pwConfirmInput.value;

        if (confirmPw === '') {
            pwMsg.textContent = '';
            return;
        }

        if (pw === confirmPw) {
            pwMsg.textContent = '비밀번호가 일치합니다.';
            pwMsg.className = 'validation-msg text-success';
        } else {
            pwMsg.textContent = '비밀번호가 일치하지 않습니다.';
            pwMsg.className = 'validation-msg text-danger';
        }
    }

    pwInput.addEventListener('input', checkPasswordMatch);
    pwConfirmInput.addEventListener('input', checkPasswordMatch);

    // 2. 아이디 중복 확인 (가짜 로직 - Mock)
    btnCheckId.addEventListener('click', function() {
        const userId = idInput.value.trim();

        if (userId.length < 4) {
            idMsg.textContent = '아이디는 4자 이상 입력해주세요.';
            idMsg.className = 'validation-msg text-danger';
            isIdChecked = false;
            return;
        }

        // TODO: 나중에 fetch('/auth/check-id') 로 실제 백엔드와 연결할 부분입니다.
        // 지금은 'admin'만 무조건 중복이라고 가정하는 가짜 로직입니다.
        if (userId === 'admin') {
            idMsg.textContent = '이미 사용 중인 아이디입니다.';
            idMsg.className = 'validation-msg text-danger';
            isIdChecked = false;
        } else {
            idMsg.textContent = '사용 가능한 아이디입니다.';
            idMsg.className = 'validation-msg text-success';
            isIdChecked = true;
        }
    });

    // 3. 폼 제출 시 최종 검사
    signupForm.addEventListener('submit', function(event) {
        if (!isIdChecked) {
            event.preventDefault(); // 폼 전송 막기
            alert('아이디 중복 확인을 해주세요.');
            idInput.focus();
            return;
        }

        if (pwInput.value !== pwConfirmInput.value) {
            event.preventDefault();
            alert('비밀번호가 일치하지 않습니다.');
            pwConfirmInput.focus();
            return;
        }
    });
});