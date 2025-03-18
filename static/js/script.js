// 자동 학습 시작 함수
async function startAutoLearning() {
    const vendor = document.getElementById('autoVendor').value;
    const taskType = document.getElementById('autoTaskType').value;

    if (!vendor || !taskType) {
        alert('벤더와 작업 유형을 선택해주세요.');
        return;
    }

    try {
        const response = await fetch('/cli/learn', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                vendor: vendor,
                taskType: taskType,
                commands: []
            })
        });

        const result = await response.json();
        if (result.status === 'success') {
            document.getElementById('learningResult').textContent = result.message;
            document.getElementById('learningResult').style.display = 'block';
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('learningStatus').textContent = '학습 중 오류가 발생했습니다: ' + error.message;
        document.getElementById('learningStatus').style.display = 'block';
    }
}

// 문서 학습 시작 함수
async function startDocumentLearning() {
    const vendor = document.getElementById('uploadVendor').value;
    const taskType = document.getElementById('uploadTaskType').value;
    const file = document.getElementById('commandFile').files[0];

    if (!vendor || !taskType || !file) {
        alert('모든 필드를 입력해주세요.');
        return;
    }

    const reader = new FileReader();
    reader.onload = async function(e) {
        try {
            const commands = e.target.result.split('\n').filter(line => line.trim());
            
            const response = await fetch('/cli/learn', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    vendor: vendor,
                    taskType: taskType,
                    commands: commands
                })
            });

            const result = await response.json();
            if (result.status === 'success') {
                document.getElementById('learningResult').textContent = result.message;
                document.getElementById('learningResult').style.display = 'block';
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Error:', error);
            document.getElementById('learningStatus').textContent = '학습 중 오류가 발생했습니다: ' + error.message;
            document.getElementById('learningStatus').style.display = 'block';
        }
    };

    reader.readAsText(file);
}

// 장비 목록 로드
async function loadDeviceList() {
    try {
        const response = await fetch('/api/devices');
        const result = await response.json();
        
        if (result.status === 'success') {
            updateDeviceList(result.data || []);
        } else {
            console.error('장비 목록 로드 실패:', result.message);
            updateDeviceList([]);
        }
    } catch (error) {
        console.error('장비 목록 로드 중 오류:', error);
        updateDeviceList([]);
    }
}

// 장비 목록 업데이트
function updateDeviceList(devices) {
    const deviceList = document.getElementById('deviceList');
    if (!deviceList) {
        console.error('deviceList element not found');
        return;
    }

    if (!Array.isArray(devices) || devices.length === 0) {
        deviceList.innerHTML = '<tr><td colspan="7" class="text-center">저장된 장비가 없습니다.</td></tr>';
        return;
    }

    deviceList.innerHTML = devices.map(device => `
        <tr>
            <td>${device.device_name || ''}</td>
            <td>${device.vendor || ''}</td>
            <td>${device.username || ''}</td>
            <td>${device.password || ''}</td>
            <td>${device.ip_address || ''}</td>
            <td>${device.tasks ? Object.keys(device.tasks).join(', ') : ''}</td>
            <td>
                <button class="btn btn-sm" style="background-color: #0D6EFD;" onclick="viewDeviceScript('${device.device_name}')" title="스크립트 보기">
                    <i class="fas fa-code" style="color: white;"></i>
                </button>
                <button class="btn btn-sm" style="background-color: #0DCAF0;" onclick="viewScript('${device.device_name}')" title="보기">
                    <i class="fas fa-eye" style="color: white;"></i>
                </button>
                <button class="btn btn-sm" style="background-color: #198754;" onclick="executeScript('${device.device_name}')" title="실행">
                    <i class="fas fa-play" style="color: white;"></i>
                </button>
                <button class="btn btn-sm" style="background-color: #FFC107;" onclick="saveScript('${device.device_name}')" title="저장">
                    <i class="fas fa-save" style="color: white;"></i>
                </button>
                <button class="btn btn-sm" style="background-color: #DC3545;" onclick="deleteDevice('${device.device_name}')" title="삭제">
                    <i class="fas fa-trash" style="color: white;"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// 스크립트 보기
async function viewDeviceScript(deviceName) {
    try {
        const response = await fetch(`/api/device/scripts/${deviceName}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            const scriptData = result.data;
            const scriptDisplay = document.getElementById('scriptDisplay');
            
            if (scriptDisplay) {
                scriptDisplay.innerHTML = `
                    <div class="mb-3">
                        <h5>장비 정보</h5>
                        <pre class="bg-light p-2">${JSON.stringify(scriptData.device_info || {}, null, 2)}</pre>
                    </div>
                    <div class="mb-3">
                        <h5>명령어</h5>
                        <pre class="bg-light p-2">${Array.isArray(scriptData.commands) ? scriptData.commands.join('\n') : ''}</pre>
                    </div>
                    <div>
                        <h5>생성 시간</h5>
                        <pre class="bg-light p-2">${scriptData.generated_at || ''}</pre>
                    </div>
                `;

                const scriptModal = new bootstrap.Modal(document.getElementById('scriptModal'));
                scriptModal.show();
            }
        } else {
            alert('스크립트를 불러오는데 실패했습니다: ' + (result.message || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('스크립트 보기 중 오류:', error);
        alert('스크립트를 불러오는 중 오류가 발생했습니다.');
    }
}

// 스크립트 실행
async function executeScript(deviceName) {
    if (!confirm('스크립트를 실행하시겠습니까?')) {
        return;
    }

    try {
        const response = await fetch(`/api/script/execute/${deviceName}`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            alert('스크립트가 실행되었습니다.');
        } else {
            alert('스크립트 실행 실패: ' + (result.message || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('스크립트 실행 중 오류:', error);
        alert('스크립트 실행 중 오류가 발생했습니다.');
    }
}

// 장비 삭제
async function deleteDevice(deviceName) {
    if (!confirm('이 장비를 삭제하시겠습니까?')) {
        return;
    }

    try {
        const response = await fetch(`/api/device/${deviceName}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            alert('장비가 삭제되었습니다.');
            loadDeviceList();
        } else {
            alert('장비 삭제 실패: ' + (result.message || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('장비 삭제 중 오류:', error);
        alert('장비 삭제 중 오류가 발생했습니다.');
    }
}

// 설정 입력 필드 토글 함수
function toggleConfigInputs() {
    const configCheckboxes = ['vlanConfig', 'ipConfig', 'interfaceConfig'];
    
    configCheckboxes.forEach(checkboxId => {
        const checkbox = document.getElementById(checkboxId);
        const inputsDiv = document.getElementById(checkboxId.replace('Config', 'Inputs'));
        
        checkbox.addEventListener('change', function() {
            inputsDiv.classList.toggle('d-none', !this.checked);
        });
    });
}

// 장비 정보 저장 함수
async function configureDevice(deviceInfo) {
    try {
        const response = await fetch('/api/device/configure', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(deviceInfo)
        });

        const result = await response.json();
        if (response.ok) {
            alert('설정이 성공적으로 적용되었습니다.\n\n' + result.output);
        } else {
            alert('설정 실패: ' + result.message);
        }
    } catch (error) {
        alert('설정 적용 중 오류가 발생했습니다: ' + error.message);
    }
}

async function saveDeviceInfo() {
    const deviceInfo = {
        device_name: document.getElementById('deviceName').value,
        vendor: document.getElementById('vendorSelect').value,
        username: document.getElementById('username').value,
        password: document.getElementById('password').value,
        ip_address: document.getElementById('ipAddress').value,
        tasks: {}
    };

    // VLAN 설정
    if (document.getElementById('vlanConfig').checked) {
        const vlanInputs = document.getElementById('vlanInputs').getElementsByTagName('input');
        deviceInfo.tasks.vlan = {
            id: vlanInputs[0].value,
            name: vlanInputs[1].value
        };
    }

    // IP 설정
    if (document.getElementById('ipConfig').checked) {
        const ipInputs = document.getElementById('ipInputs').getElementsByTagName('input');
        deviceInfo.tasks.ip = {
            address: ipInputs[0].value,
            subnet: ipInputs[1].value
        };
    }

    // 인터페이스 설정
    if (document.getElementById('interfaceConfig').checked) {
        const interfaceInputs = document.getElementById('interfaceInputs');
        deviceInfo.tasks.interface = {
            name: interfaceInputs.getElementsByTagName('input')[0].value,
            status: interfaceInputs.getElementsByTagName('select')[0].value
        };
    }

    // 장비 설정 적용
    await configureDevice(deviceInfo);
    
    // 장비 목록 새로고침
    loadDeviceList();
}

// 페이지 로드 시 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', function() {
    toggleConfigInputs();
    loadDeviceList();
    // 탭 전환 초기화
    var triggerTabList = [].slice.call(document.querySelectorAll('button[data-bs-toggle="tab"]'))
    triggerTabList.forEach(function(triggerEl) {
        new bootstrap.Tab(triggerEl)
    });

    // 드롭다운 항목 선택 시 이벤트 처리
    document.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const selectedValue = this.getAttribute('data-value');
            const selectedText = this.textContent;
            
            // 드롭다운 버튼 텍스트 업데이트
            document.getElementById('configDropdown').textContent = selectedText;
            
            // 선택된 값 저장
            document.getElementById('configDropdown').setAttribute('data-selected', selectedValue);
        });
    });

    // 메인 카테고리 체크박스 이벤트
    document.querySelectorAll('.main-category').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const subOptions = this.closest('.form-check').querySelectorAll('.sub-option');
            subOptions.forEach(option => {
                option.checked = this.checked;
            });
        });
    });

    // 서브 옵션 체크박스 이벤트
    document.querySelectorAll('.sub-option').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const mainCategory = this.closest('.form-check').querySelector('.main-category');
            const subOptions = this.closest('.form-check').querySelectorAll('.sub-option');
            mainCategory.checked = Array.from(subOptions).some(option => option.checked);
        });
    });
});

// 설정 모드 변경 처리
document.getElementById('configMode').addEventListener('change', function() {
    document.getElementById('singleCommandDiv').style.display = 'none';
    document.getElementById('multiCommandDiv').style.display = 'none';
    document.getElementById('scriptFileDiv').style.display = 'none';
    
    document.getElementById(this.value + 'CommandDiv').style.display = 'block';
});

// 기본 show 명령어 실행 함수들
async function showRunning() {
    await executeNetmikoCommand('show_running');
}

async function showInterfaces() {
    await executeNetmikoCommand('show_interfaces');
}

async function showVersion() {
    await executeNetmikoCommand('show_version');
}

async function showVlans() {
    await executeNetmikoCommand('show_vlans');
}

// 단일 명령어 실행
async function executeSingleCommand() {
    const command = document.getElementById('singleCommand').value;
    if (!command) {
        alert('명령어를 입력하세요.');
        return;
    }
    await executeNetmikoCommand('single', command);
}

// 다중 명령어 실행
async function executeMultiCommands() {
    const commands = document.getElementById('multiCommands').value;
    if (!commands) {
        alert('명령어를 입력하세요.');
        return;
    }
    await executeNetmikoCommand('multi', commands);
}

// 스크립트 파일 실행
async function executeScriptFile() {
    const fileInput = document.getElementById('scriptFile');
    if (!fileInput.files.length) {
        alert('스크립트 파일을 선택하세요.');
        return;
    }

    const formData = new FormData();
    formData.append('script', fileInput.files[0]);
    
    try {
        const response = await fetch('/api/device/execute_script', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        displayOutput(result);
    } catch (error) {
        displayOutput({ status: 'error', message: error.message });
    }
}

// Netmiko 명령어 실행 함수
async function executeNetmikoCommand(type, command = '') {
    const deviceInfo = {
        device_name: document.getElementById('deviceName').value,
        vendor: document.getElementById('vendorSelect').value,
        ip_address: document.getElementById('ipAddress').value,
        username: document.getElementById('username').value,
        password: document.getElementById('password').value,
        command_type: type,
        command: command
    };

    try {
        const response = await fetch('/api/device/execute_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(deviceInfo)
        });

        const result = await response.json();
        displayOutput(result);
    } catch (error) {
        displayOutput({ status: 'error', message: error.message });
    }
}

// 실행 결과 표시 함수
function displayOutput(result) {
    const outputDiv = document.getElementById('commandOutput');
    if (result.status === 'success') {
        outputDiv.innerHTML = `<span class="text-success">성공:</span>\n${result.output}`;
    } else {
        outputDiv.innerHTML = `<span class="text-danger">오류:</span>\n${result.message}`;
    }
}

// 기본정보 불러오기
function loadBasicInfo() {
    const deviceName = document.getElementById('deviceName').value;
    const vendor = document.getElementById('vendorSelect').value;
    const ipAddress = document.getElementById('ipAddress').value;
    const username = document.getElementById('username').value;
    
    if (!deviceName || !vendor || !ipAddress || !username) {
        alert('기본 정보 탭에서 모든 필수 정보를 입력해주세요.');
        return;
    }

    document.getElementById('selectedDeviceInfo').innerHTML = `
        <div class="row">
            <div class="col-md-3"><strong>장비명:</strong> ${deviceName}</div>
            <div class="col-md-3"><strong>벤더:</strong> ${vendor}</div>
            <div class="col-md-3"><strong>IP:</strong> ${ipAddress}</div>
            <div class="col-md-3"><strong>사용자:</strong> ${username}</div>
        </div>
    `;
}

// 설정 카테고리 변경 시 해당하는 옵션 표시
function showConfigForm() {
    const category = document.getElementById('configCategory').value;
    
    // 모든 옵션 숨기기
    document.querySelectorAll('.config-options').forEach(options => {
        options.classList.add('d-none');
    });
    
    // 선택된 카테고리의 옵션 표시
    const selectedOptions = document.getElementById(category + 'Options');
    if (selectedOptions) {
        selectedOptions.classList.remove('d-none');
    }
}

// 스크립트 생성
async function generateScript() {
    // 선택된 모든 옵션 수집
    const selectedOptions = {};
    document.querySelectorAll('.category-group').forEach(group => {
        const categoryName = group.querySelector('.category-check').id;
        const selectedSubOptions = Array.from(group.querySelectorAll('.sub-options input:checked'))
            .map(checkbox => checkbox.id);
        
        if (selectedSubOptions.length > 0) {
            selectedOptions[categoryName] = selectedSubOptions;
        }
    });

    if (Object.keys(selectedOptions).length === 0) {
        alert('하나 이상의 설정 옵션을 선택해주세요.');
        return;
    }

    try {
        const response = await fetch('/api/generate_script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                options: selectedOptions
            })
        });

        const result = await response.json();
        if (response.ok) {
            document.getElementById('generatedScript').textContent = result.script;
            document.getElementById('executeBtn').disabled = false;
        } else {
            alert('스크립트 생성 실패: ' + result.message);
        }
    } catch (error) {
        alert('스크립트 생성 중 오류 발생: ' + error.message);
    }
}

// 스크립트 실행
async function executeScript() {
    try {
        const response = await fetch('/api/execute_script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                deviceName: document.getElementById('deviceName').value,
                vendor: document.getElementById('vendorSelect').value,
                ip_address: document.getElementById('ipAddress').value,
                username: document.getElementById('username').value,
                password: document.getElementById('password').value,
                script: document.getElementById('generatedScript').textContent
            })
        });

        const result = await response.json();
        if (response.ok) {
            document.getElementById('executionResult').textContent = result.output;
        } else {
            alert('스크립트 실행 실패: ' + result.message);
        }
    } catch (error) {
        alert('스크립트 실행 중 오류 발생: ' + error.message);
    }
} 