// 디버깅을 위한 로그
console.log('main.js loaded');

// 페이지 로드 시 실행될 초기화 함수
document.addEventListener('DOMContentLoaded', function() {
    console.log('페이지 로드됨');
    loadDeviceList();  // 장비 목록 로드
});

// 작업별 필요한 추가 입력 필드 정의
const taskInputFields = {
    'VLAN 설정': [
        { id: 'vlan_id', label: 'VLAN ID', type: 'number', placeholder: '1-4094' },
        { id: 'vlan_name', label: 'VLAN 이름', type: 'text', placeholder: 'VLAN 이름 입력' }
    ],
    '인터페이스 설정': [
        { id: 'interface', label: '인터페이스명', type: 'text', placeholder: 'ex: GigabitEthernet1/0/1' },
        { id: 'description', label: '설명', type: 'text', placeholder: '인터페이스 설명' },
        { id: 'interface_vlan', label: 'VLAN ID', type: 'number', placeholder: '적용할 VLAN ID' }
    ],
    'IP 설정': [
        { id: 'ip_interface', label: '인터페이스명', type: 'text', placeholder: '인터페이스 선택' },
        { id: 'ip_address', label: 'IP 주소', type: 'text', placeholder: 'ex: 192.168.1.1' },
        { id: 'subnet_mask', label: '서브넷 마스크', type: 'text', placeholder: 'ex: 255.255.255.0' }
    ],
    'OSPF 설정': [
        { id: 'process_id', label: 'Process ID', type: 'number', placeholder: 'OSPF Process ID' },
        { id: 'network', label: '네트워크 주소', type: 'text', placeholder: 'ex: 192.168.1.0' },
        { id: 'wildcard', label: 'Wildcard 마스크', type: 'text', placeholder: 'ex: 0.0.0.255' },
        { id: 'area', label: 'Area 번호', type: 'number', placeholder: 'ex: 0' }
    ],
    // ... 다른 작업들의 입력 필드 정의
};

// 체크박스 상태 변경 시 호출되는 함수
function toggleConfigInputs(checkbox) {
    const configInputs = document.getElementById('configInputs');
    const taskType = checkbox.value;
    const inputGroupId = `${taskType.replace(/\s+/g, '')}_inputs`;

    if (checkbox.checked) {
        // 해당 작업의 입력 필드가 이미 있는지 확인
        if (!document.getElementById(inputGroupId)) {
            const fields = taskInputFields[taskType];
            if (fields) {
                const inputGroup = document.createElement('div');
                inputGroup.id = inputGroupId;
                inputGroup.className = 'card mb-3';
                
                inputGroup.innerHTML = `
                    <div class="card-header">
                        <h5 class="mb-0">${taskType} 상세 설정</h5>
                    </div>
                    <div class="card-body">
                        ${fields.map(field => `
                            <div class="form-group">
                                <label for="${field.id}">${field.label}</label>
                                <input type="${field.type}" 
                                       class="form-control" 
                                       id="${field.id}" 
                                       placeholder="${field.placeholder}"
                                       required>
                            </div>
                        `).join('')}
                    </div>
                `;
                
                configInputs.appendChild(inputGroup);
            }
        }
    } else {
        // 체크 해제 시 해당 입력 필드 제거
        const inputGroup = document.getElementById(inputGroupId);
        if (inputGroup) {
            inputGroup.remove();
        }
    }
}

// 저장 함수 수정
async function saveDeviceInfo() {
    // 기본 정보 수집
    const basicInfo = {
        vendor: document.getElementById('vendor').value,
        device_name: document.getElementById('deviceName').value,
        username: document.getElementById('username').value,
        password: document.getElementById('password').value,
        ip_address: document.getElementById('ipAddress').value
    };

    // 선택된 작업 및 추가 설정 정보 수집
    const selectedTasks = {};
    document.querySelectorAll('input[name="tasks"]:checked').forEach(checkbox => {
        const taskType = checkbox.value;
        const taskInputs = {};
        
        // 해당 작업의 입력 필드 값 수집
        const inputGroupId = `${taskType.replace(/\s+/g, '')}_inputs`;
        const inputGroup = document.getElementById(inputGroupId);
        if (inputGroup) {
            inputGroup.querySelectorAll('input').forEach(input => {
                taskInputs[input.id] = input.value;
            });
        }
        
        selectedTasks[taskType] = taskInputs;
    });

    // 전체 데이터 구성
    const deviceInfo = {
        ...basicInfo,
        tasks: selectedTasks
    };

    try {
        const response = await fetch('/api/device/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(deviceInfo)
        });

        if (response.ok) {
            alert('장비 정보가 저장되었습니다.');
            loadDeviceList();
        } else {
            throw new Error('저장 실패');
        }
    } catch (error) {
        console.error('저장 중 오류:', error);
        alert('저장 중 오류가 발생했습니다.');
    }
}

// 장비 목록 로드 함수
async function loadDeviceList() {
    try {
        console.log('장비 목록 로드 시작');
        const response = await fetch('/api/devices');
        const devices = await response.json();
        console.log('받은 장비 목록:', devices);
        
        const tableBody = document.getElementById('deviceList');
        if (!tableBody) {
            console.error('deviceList 요소를 찾을 수 없음');
            return;
        }
        
        tableBody.innerHTML = '';

        devices.forEach(device => {
            const tasksList = device.tasks ? Object.keys(device.tasks).join(', ') : '';
            
            const row = document.createElement('tr');
            row.setAttribute('data-device', device.device_name);
            row.innerHTML = `
                <td>${device.device_name}</td>
                <td>${device.vendor}</td>
                <td>${device.username}</td>
                <td>${device.password}</td>
                <td>${device.ip_address}</td>
                <td>${tasksList}</td>
                <td class="button-group">
                    <button class="action-btn script-btn" 
                            onclick="generateScript('${device.device_name}')"
                            title="설정 스크립트를 생성합니다">
                        <i class="fas fa-code"></i>
                    </button>
                    <button class="action-btn view-btn" 
                            onclick="viewScript('${device.device_name}')"
                            title="생성된 스크립트를 확인합니다">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="action-btn execute-btn" 
                            onclick="executeConfig('${device.device_name}')"
                            disabled
                            title="먼저 스크립트를 생성해주세요">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="action-btn stop-btn" 
                            onclick="stopExecution('${device.device_name}')"
                            disabled
                            title="실행 중지">
                        <i class="fas fa-stop"></i>
                    </button>
                    <button class="action-btn delete-btn" 
                            onclick="deleteDevice('${device.device_name}')"
                            title="장비를 삭제합니다">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
            
            // 스크립트 파일 존재 여부 확인
            checkScriptExists(device.device_name);
        });
    } catch (error) {
        console.error('장비 목록 로드 중 오류:', error);
    }
}

// 장비 삭제 함수
async function deleteDevice(deviceName) {
    if (!confirm('정말 삭제하시겠습니까?')) {
        return;
    }

    try {
        // tasks 디렉토리의 JSON 파일 삭제 요청
        const response = await fetch(`/api/device/delete/${deviceName}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('삭제되었습니다.');
            loadDeviceList();  // 목록 새로고침
        } else {
            throw new Error('삭제 실패');
        }
    } catch (error) {
        console.error('삭제 중 오류:', error);
        alert('삭제 중 오류가 발생했습니다.');
    }
}

// HTML 이스케이프 함수
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// 입력값 검증 함수
function validateDeviceData(data) {
    if (!data.vendor || !data.device_name || !data.login_id || 
        !data.login_pw || !data.ip_address) {
        alert('모든 기본 정보를 입력해주세요.');
        return false;
    }

    if (!validateIpAddress(data.ip_address)) {
        alert('올바른 IP 주소 형식이 아닙니다.');
        return false;
    }

    if (!Object.values(data.config_types).some(value => value)) {
        alert('최소 하나의 설정 작업을 선택해주세요.');
        return false;
    }

    return true;
}

// IP 주소 검증 함수
function validateIpAddress(ipAddress) {
    const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipPattern.test(ipAddress)) return false;
    
    const parts = ipAddress.split('.');
    return parts.every(part => {
        const num = parseInt(part, 10);
        return num >= 0 && num <= 255;
    });
}

// 벤더 이름 변환 함수
function getVendorName(vendor) {
    const vendorNames = {
        'cisco': '시스코',
        'juniper': '주니퍼',
        'hp': 'HP',
        'arista': '아리스타'
    };
    return vendorNames[vendor.toLowerCase()] || vendor;
}

// 에러 표시 함수
function showError(message) {
    const deviceList = document.getElementById('deviceList');
    if (deviceList) {
        deviceList.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-danger">${message}</td>
            </tr>`;
    }
}

// 폼 초기화 함수
function resetForms() {
    document.getElementById('vendor').value = '';
    document.getElementById('deviceName').value = '';
    document.getElementById('loginId').value = '';
    document.getElementById('loginPw').value = '';
    document.getElementById('ipAddress').value = '';
    
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => checkbox.checked = false);
}

// VLAN 설정 저장 함수
async function saveVlanConfig() {
    const config = {
        vendor: document.getElementById('vendor').value,
        task_type: document.getElementById('taskType').value,
        vlan_id: document.getElementById('vlanId').value,
        interface: document.getElementById('interface').value,
        host: document.getElementById('ipAddress').value,
        username: document.getElementById('username').value,
        password: document.getElementById('password').value,
        secret: document.getElementById('secret').value
    };

    try {
        const response = await fetch('/api/config/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });

        if (response.ok) {
            alert('설정이 성공적으로 저장되었습니다.');
            loadDeviceList();  // 디바이스 목록 새로고침
        } else {
            throw new Error('설정 저장 실패');
        }
    } catch (error) {
        console.error('설정 저장 중 오류 발생:', error);
        alert('설정 저장 중 오류가 발생했습니다.');
    }
}

// VLAN ID 유효성 검사
function validateVlanId(vlanId) {
    const id = parseInt(vlanId);
    return !isNaN(id) && id >= 1 && id <= 4094;
}

// 인터페이스 이름 유효성 검사
function validateInterface(interfaceName) {
    const pattern = /^(GigabitEthernet|FastEthernet|Ethernet)\d+\/\d+\/\d+$/;
    return pattern.test(interfaceName);
}

// 설정 실행 함수 추가
async function executeConfig(deviceName) {
    try {
        // 실행 버튼 비활성화 및 중지 버튼 활성화
        const executeBtn = document.querySelector(`tr[data-device="${deviceName}"] .execute-btn`);
        const stopBtn = document.querySelector(`tr[data-device="${deviceName}"] .stop-btn`);
        if (executeBtn) executeBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;

        // 전역 변수로 실행 상태 저장
        window.executionStatus = window.executionStatus || {};
        window.executionStatus[deviceName] = true;

        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ device_name: deviceName })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || '실행에 실패했습니다.');
        }

        // 실행 완료 후 버튼 상태 복원
        if (executeBtn) executeBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
        
        alert('설정이 성공적으로 실행되었습니다.');
        
    } catch (error) {
        console.error('실행 중 오류:', error);
        alert('실행 중 오류가 발생했습니다: ' + error.message);
        
        // 오류 발생 시 버튼 상태 복원
        const executeBtn = document.querySelector(`tr[data-device="${deviceName}"] .execute-btn`);
        const stopBtn = document.querySelector(`tr[data-device="${deviceName}"] .stop-btn`);
        if (executeBtn) executeBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
    }
}

// 실행 중지 함수 추가
async function stopExecution(deviceName) {
    try {
        // 실행 상태 변경
        if (window.executionStatus) {
            window.executionStatus[deviceName] = false;
        }

        const response = await fetch('/api/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ device_name: deviceName })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || '중지에 실패했습니다.');
        }

        // 버튼 상태 업데이트
        const executeBtn = document.querySelector(`tr[data-device="${deviceName}"] .execute-btn`);
        const stopBtn = document.querySelector(`tr[data-device="${deviceName}"] .stop-btn`);
        if (executeBtn) executeBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
        
        alert('실행이 중지되었습니다.');
        
    } catch (error) {
        console.error('중지 중 오류:', error);
        alert('중지 중 오류가 발생했습니다: ' + error.message);
    }
}

// 제조사별 CLI 자동화 함수
async function showVendorCLI() {
    try {
        const response = await fetch('/api/cli/vendors');
        const result = await response.json();
        
        if (result.success) {
            // CLI 자동화 모달 표시
            const modal = new bootstrap.Modal(document.getElementById('cliModal'));
            document.getElementById('cliVendorList').innerHTML = result.vendors.map(vendor => `
                <button class="btn btn-outline-primary m-2" onclick="executeCLI('${vendor}')">${vendor}</button>
            `).join('');
            modal.show();
        } else {
            alert('CLI 자동화 정보를 불러오는데 실패했습니다.');
        }
    } catch (error) {
        console.error('CLI 자동화 오류:', error);
        alert('CLI 자동화 실행 중 오류가 발생했습니다.');
    }
}

// CLI 학습 함수 - 개선된 버전
async function learnCLI(vendor, taskType, commands) {
    try {
        console.log('CLI 학습 시작:', { vendor, taskType, commands });

        const response = await fetch('/api/cli/learn', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                vendor: vendor,
                task_type: taskType,
                commands: commands
            })
        });

        const data = await response.json();
        console.log('CLI 학습 응답:', data);

        if (!response.ok) {
            throw new Error(data.message || 'CLI 학습에 실패했습니다.');
        }

        return data;

    } catch (error) {
        console.error('CLI 학습 중 오류:', error);
        throw error;
    }
}

// 학습 버튼 클릭 핸들러 - 개선된 버전
async function handleLearnClick() {
    try {
        const learnButton = event.target;
        const vendor = document.getElementById('cliVendor').value;
        const taskType = document.getElementById('cliTaskType').value;
        const commandsText = document.getElementById('cliCommands').value;
        const commands = commandsText.split('\n').filter(cmd => cmd.trim());

        // 입력 검증
        if (!vendor || !taskType || commands.length === 0) {
            alert('모든 필드를 입력해주세요.');
            return;
        }

        // 버튼 상태 변경
        learnButton.disabled = true;
        const originalText = learnButton.textContent;
        learnButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 학습 중...';

        // CLI 학습 실행
        const result = await learnCLI(vendor, taskType, commands);
        
        // 성공 메시지 표시
        alert('CLI 명령어가 성공적으로 학습되었습니다.');
        
        // 입력 필드 초기화
        document.getElementById('cliCommands').value = '';
        
    } catch (error) {
        alert('CLI 학습 중 오류가 발생했습니다: ' + error.message);
    } finally {
        // 버튼 상태 복원
        const learnButton = event.target;
        learnButton.disabled = false;
        learnButton.textContent = '학습';
    }
}

// 학습된 명령어 목록 업데이트 함수
async function updateLearnedCommandsList() {
    try {
        const response = await fetch('/api/cli/learned');
        const data = await response.json();

        const listContainer = document.getElementById('learnedCommandsList');
        listContainer.innerHTML = '';

        if (data.learned_commands) {
            Object.entries(data.learned_commands).forEach(([vendor, tasks]) => {
                const vendorSection = document.createElement('div');
                vendorSection.className = 'mb-3';
                vendorSection.innerHTML = `
                    <h6 class="text-primary">${vendor.toUpperCase()}</h6>
                    <ul class="list-group">
                        ${Object.entries(tasks.tasks || {}).map(([taskType, info]) => `
                            <li class="list-group-item">
                                <strong>${taskType}</strong>
                                <small class="text-muted d-block">학습일시: ${new Date(info.learned_at).toLocaleString()}</small>
                            </li>
                        `).join('')}
                    </ul>
                `;
                listContainer.appendChild(vendorSection);
            });
        }
    } catch (error) {
        console.error('학습된 명령어 목록 조회 중 오류:', error);
    }
}

// 페이지 로드 시 학습된 명령어 목록 표시
document.addEventListener('DOMContentLoaded', () => {
    updateLearnedCommandsList();
});

// 스크립트 생성 함수
async function generateScript(deviceName) {
    try {
        console.log(`스크립트 생성 시작: ${deviceName}`);  // 디버깅용 로그
        
        const response = await fetch('/api/script/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ device_name: deviceName })
        });
        
        const data = await response.json();
        console.log('스크립트 생성 응답:', data);  // 디버깅용 로그
        
        if (!response.ok) {
            throw new Error(data.message || '스크립트 생성에 실패했습니다.');
        }
        
        // 성공 메시지 표시
        alert('스크립트가 생성되었습니다.');
        
        // 실행 버튼 활성화
        const executeBtn = document.querySelector(`tr[data-device="${deviceName}"] .execute-btn`);
        if (executeBtn) {
            executeBtn.disabled = false;
        }
        
        // 스크립트 내용 즉시 표시
        viewScript(deviceName);
        
    } catch (error) {
        console.error('스크립트 생성 중 오류:', error);
        alert('스크립트 생성 중 오류가 발생했습니다: ' + error.message);
    }
}

// 스크립트 파일 존재 여부 확인
async function checkScriptExists(deviceName) {
    try {
        const response = await fetch(`/api/device/script-exists/${deviceName}`);
        const result = await response.json();
        updateButtonStates(deviceName, result.exists);
    } catch (error) {
        console.error('스크립트 확인 중 오류:', error);
    }
}

// 버튼 상태 업데이트
function updateButtonStates(deviceName, scriptExists) {
    const row = document.querySelector(`tr[data-device="${deviceName}"]`);
    if (row) {
        const executeBtn = row.querySelector('.execute-btn');
        if (executeBtn) {
            executeBtn.disabled = !scriptExists;
            executeBtn.title = scriptExists ? 
                '생성된 스크립트로 설정을 실행합니다' : 
                '먼저 스크립트를 생성해주세요';
        }
    }
}

// 스크립트 내용 확인 함수
async function viewScript(deviceName) {
    try {
        console.log(`스크립트 조회 시작: ${deviceName}`);  // 디버깅용 로그
        
        const response = await fetch(`/api/script/${deviceName}`);
        console.log('응답 상태:', response.status);  // 디버깅용 로그
        
        const data = await response.json();
        console.log('받은 데이터:', data);  // 디버깅용 로그
        
        if (!response.ok) {
            throw new Error(data.message || '스크립트를 불러올 수 없습니다.');
        }
        
        // 모달에 데이터 표시
        document.getElementById('modalDeviceName').textContent = deviceName;
        
        // JSON 데이터를 보기 좋게 포맷팅
        const formattedScript = JSON.stringify(data, null, 2);
        document.getElementById('scriptContent').textContent = formattedScript;
        
        // 모달 표시
        const scriptModal = new bootstrap.Modal(document.getElementById('scriptModal'));
        scriptModal.show();
    } catch (error) {
        console.error('스크립트 조회 중 오류:', error);
        alert('스크립트 조회 중 오류가 발생했습니다: ' + error.message);
    }
}

// 자동 학습 시작 함수
async function startAutoLearning() {
    const button = document.querySelector('.auto-learn-btn');
    const statusDiv = document.getElementById('learningStatus');
    const resultsDiv = document.getElementById('learningResults');
    const vendor = document.getElementById('autoVendor')?.value;
    const taskType = document.getElementById('autoTaskType')?.value;

    try {
        if (!vendor || !taskType) {
            alert('벤더와 작업 유형을 선택해주세요.');
            return;
        }

        // 버튼 상태 변경
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 학습 중...';
        statusDiv.innerHTML = '<div class="alert alert-info">자동 학습 진행 중...</div>';

        const response = await fetch('/api/cli/auto-learn', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ vendor, task_type: taskType })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || '자동 학습에 실패했습니다.');
        }

        // 학습 결과 표시
        statusDiv.innerHTML = '<div class="alert alert-success">자동 학습이 완료되었습니다.</div>';
        if (data.results && data.results.length > 0) {
            resultsDiv.innerHTML = `
                <h6>학습된 명령어:</h6>
                <pre class="bg-light p-3">${data.results.join('\n')}</pre>
            `;
        }

    } catch (error) {
        console.error('자동 학습 중 오류:', error);
        statusDiv.innerHTML = `<div class="alert alert-danger">오류: ${error.message}</div>`;
    } finally {
        // 버튼 상태 복원
        button.disabled = false;
        button.innerHTML = '자동 학습 시작';
    }
}

// 문서 학습 시작 함수
async function startDocLearning() {
    const button = document.querySelector('.doc-learn-btn');
    const statusDiv = document.getElementById('learningStatus');
    const resultsDiv = document.getElementById('learningResults');
    const vendor = document.getElementById('docVendor')?.value;
    const taskType = document.getElementById('docTaskType')?.value;
    const fileInput = document.getElementById('docFile');
    const file = fileInput?.files[0];

    try {
        if (!vendor || !taskType || !file) {
            alert('모든 필드를 입력해주세요.');
            return;
        }

        // 버튼 상태 변경
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 학습 중...';
        statusDiv.innerHTML = '<div class="alert alert-info">문서 학습 진행 중...</div>';

        const formData = new FormData();
        formData.append('vendor', vendor);
        formData.append('task_type', taskType);
        formData.append('file', file);

        const response = await fetch('/api/cli/doc-learn', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || '문서 학습에 실패했습니다.');
        }

        // 학습 결과 표시
        statusDiv.innerHTML = '<div class="alert alert-success">문서 학습이 완료되었습니다.</div>';
        if (data.results && data.results.length > 0) {
            resultsDiv.innerHTML = `
                <h6>학습된 명령어:</h6>
                <pre class="bg-light p-3">${data.results.join('\n')}</pre>
            `;
        }

    } catch (error) {
        console.error('문서 학습 중 오류:', error);
        statusDiv.innerHTML = `<div class="alert alert-danger">오류: ${error.message}</div>`;
    } finally {
        // 버튼 상태 복원
        button.disabled = false;
        button.innerHTML = '문서 학습 시작';
        fileInput.value = ''; // 파일 입력 초기화
    }
}

// 학습 상태 업데이트 함수
function updateLearningStatus(status) {
    const statusDiv = document.getElementById('learningStatus');
    statusDiv.innerHTML = `
        <div class="alert alert-info">
            ${status}
        </div>
    `;
}

// 학습 결과 업데이트 함수
function updateLearningResults(results) {
    const resultsDiv = document.getElementById('learningResults');
    if (Array.isArray(results) && results.length > 0) {
        resultsDiv.innerHTML = `
            <h6>학습된 명령어:</h6>
            <pre class="bg-light p-3">${results.join('\n')}</pre>
        `;
    } else {
        resultsDiv.innerHTML = '<div class="alert alert-warning">학습된 결과가 없습니다.</div>';
    }
}
    