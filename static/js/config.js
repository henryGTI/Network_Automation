document.addEventListener('DOMContentLoaded', function() {
    // 체크박스 이벤트 리스너 설정
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateConfigDetails();
        });
    });

    // 스크립트 생성 버튼 이벤트 리스너
    const generateButton = document.getElementById('generateScript');
    if (generateButton) {
        generateButton.addEventListener('click', generateScript);
    }
});

function updateConfigDetails() {
    const selectedTasks = [];
    const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
    
    checkboxes.forEach(checkbox => {
        selectedTasks.push(checkbox.value);
    });

    // 선택된 작업 표시
    const configDetails = document.getElementById('configDetails');
    if (configDetails) {
        configDetails.textContent = `선택된 작업: ${selectedTasks.join(', ')}`;
    }
}

function generateScript() {
    const selectedTasks = [];
    const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
    
    checkboxes.forEach(checkbox => {
        selectedTasks.push(checkbox.value);
    });

    if (selectedTasks.length === 0) {
        alert('작업을 하나 이상 선택해주세요.');
        return;
    }

    // 여기에 스크립트 생성 로직 추가
    alert('스크립트가 생성되었습니다: ' + selectedTasks.join(', '));
}
