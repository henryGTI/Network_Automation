document.addEventListener('DOMContentLoaded', function() {
    initLearningTab();
});

function initLearningTab() {
    // 장비 목록 로드
    updateLearningDeviceSelect();

    // 학습 시작 버튼 이벤트 리스너
    document.getElementById('startLearning').addEventListener('click', startLearning);
}

function updateLearningDeviceSelect() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('learningDevice');
            select.innerHTML = '<option value="">장비 선택</option>';
            data.devices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.name;
                option.textContent = `${device.name} (${device.ip})`;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('장비 목록 로드 오류:', error));
}

function startLearning() {
    const deviceName = document.getElementById('learningDevice').value;
    const command = document.getElementById('learningCommand').value;

    if (!deviceName) {
        alert('장비를 선택해주세요.');
        return;
    }

    if (!command) {
        alert('실행할 명령어를 입력해주세요.');
        return;
    }

    const data = {
        device: deviceName,
        command: command
    };

    fetch('/api/learn-command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('learningOutput').value = data.result;
        } else {
            alert('학습 중 오류가 발생했습니다: ' + data.message);
        }
    })
    .catch(error => {
        console.error('학습 오류:', error);
        alert('학습 중 오류가 발생했습니다.');
    });
} 