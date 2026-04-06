// XSS 테스트 영역: 입력값을 innerHTML로 직접 출력 (의도적 취약점)
function reflectInput() {
    const input = document.getElementById('testInput').value;
    document.getElementById('result').innerHTML = input;
}
