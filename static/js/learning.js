document.addEventListener('DOMContentLoaded', function() {
    // 디바이스 목록 로드
    updateLearningDeviceSelect();

    // 학습 시작 버튼 이벤트 리스너
    const startButton = document.getElementById('startLearning');
    if (startButton) {
        startButton.addEventListener('click', startLearning);
    }
});

function updateLearningDeviceSelect() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(devices => {
            const select = document.getElementById('deviceSelect');
            if (select) {
                select.innerHTML = '';
                devices.forEach(device => {
                    const option = document.createElement('option');
                    option.value = device.name;
                    option.textContent = `${device.name} (${device.ip})`;
                    select.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('디바이스 목록 로드 실패:', error);
        });
}

function startLearning() {
    const deviceSelect = document.getElementById('deviceSelect');
    const commandInput = document.getElementById('commandInput');
    const resultArea = document.getElementById('learningResult');

    if (!deviceSelect.value) {
        alert('디바이스를 선택해주세요.');
        return;
    }

    if (!commandInput.value) {
        alert('명령어를 입력해주세요.');
        return;
    }

    const data = {
        device: deviceSelect.value,
        command: commandInput.value
    };

    fetch('/api/learn-command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (resultArea) {
            resultArea.value = result.message || result.error;
        }
    })
    .catch(error => {
        console.error('학습 실행 실패:', error);
        if (resultArea) {
            resultArea.value = '오류가 발생했습니다: ' + error.message;
        }
    });
}
