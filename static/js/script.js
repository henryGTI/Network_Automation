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

// API 엔드포인트 정의
const API_ENDPOINTS = {
    DEVICES: '/api/devices',
    CREATE_SCRIPT: '/api/devices/script',
    EXECUTE_SCRIPT: (deviceName) => `/api/devices/${deviceName}/execute`,
    DELETE_DEVICE: (deviceName) => `/api/devices/${deviceName}`,
    VIEW_SCRIPT: (deviceName) => `/api/devices/script/${deviceName}`
};

// DOM 요소 참조
const elements = {
    createScriptBtn: null,
    configCheckboxes: null,
    deviceTableBody: null,
    scriptDisplay: null
};

// 페이지 초기화 함수
async function initializePage() {
    console.log('페이지 초기화 시작');
    try {
        await initializeElements();
        await setupEventListeners();
        await loadDeviceList(); // 초기 장비 목록 로드
        console.log('페이지 초기화 완료');
    } catch (error) {
        console.error('페이지 초기화 중 오류:', error);
        showError('페이지 초기화 중 오류가 발생했습니다: ' + error.message);
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', initializePage);

// DOM 요소 초기화
function initializeElements() {
    elements.createScriptBtn = document.querySelector('#createScriptBtn');
    elements.configCheckboxes = document.querySelectorAll('.config-checkbox');
    elements.deviceTableBody = document.querySelector('#deviceTableBody');
    elements.scriptDisplay = document.querySelector('#scriptDisplay');
}

// 이벤트 리스너 설정
function setupEventListeners() {
    if (elements.createScriptBtn) {
        elements.createScriptBtn.addEventListener('click', handleCreateScript);
        console.log('스크립트 생성 버튼 리스너 등록됨');
    }

    elements.configCheckboxes?.forEach(checkbox => {
        checkbox.addEventListener('change', handleConfigChange);
        console.log(`체크박스 리스너 등록됨: ${checkbox.id}`);
    });

    setupModal();
}

// 모달 설정
function setupModal() {
    const modal = document.querySelector('#scriptModal');
    if (modal) {
        modal.addEventListener('show.bs.modal', function() {
            this.removeAttribute('aria-hidden');
        });

        modal.addEventListener('hidden.bs.modal', function() {
            if (document.activeElement && this.contains(document.activeElement)) {
                elements.createScriptBtn?.focus();
            }
        });
    }
}

// 체크박스 변경 처리
function handleConfigChange(event) {
    const checkbox = event.target;
    const configId = checkbox.getAttribute('data-config');
    
    if (!configId) {
        console.warn('data-config 속성이 없습니다');
        return;
    }

    const inputsDiv = document.getElementById(`${configId}Inputs`);
    if (inputsDiv) {
        inputsDiv.style.display = checkbox.checked ? 'block' : 'none';
        console.log(`${configId} 입력 필드 표시 상태:`, checkbox.checked);
    }
}

// 선택된 작업 수집
function collectTasks() {
    const tasks = {};
    const checkedBoxes = document.querySelectorAll('input[type="checkbox"]:checked');
    
    checkedBoxes.forEach(box => {
        const taskName = box.getAttribute('data-task-name');
        const configId = box.getAttribute('data-config');
        
        if (taskName) {
            // VLAN 설정의 경우 추가 정보 수집
            if (configId === 'vlan') {
                const vlanInputs = document.getElementById('vlanInputs');
                if (vlanInputs) {
                    tasks[taskName] = {
                        enabled: true,
                        // 여기에 VLAN 관련 추가 설정을 넣을 수 있습니다
                    };
                } else {
                    tasks[taskName] = { enabled: true };
                }
            } else {
                tasks[taskName] = { enabled: true };
            }
        } else if (box.id) {
            // data-task-name이 없는 경우 체크박스 ID를 사용
            tasks[box.id] = { enabled: true };
        }
    });
    return tasks;
}

// 스크립트 생성 처리
async function handleCreateScript() {
    console.log('스크립트 생성 시작');
    try {
        const deviceName = document.getElementById('deviceName')?.value;
        const vendor = document.getElementById('vendor')?.value;
        const ipAddress = document.getElementById('ipAddress')?.value;
        const username = document.getElementById('username')?.value;
        const password = document.getElementById('password')?.value;

        // 필수 필드 검증
        if (!deviceName || !vendor || !ipAddress || !username || !password) {
            alert('모든 필수 정보를 입력해주세요.');
            return;
        }

        const tasks = collectTasks();
        if (Object.keys(tasks).length === 0) {
            alert('최소한 하나의 작업을 선택해주세요.');
            return;
        }

        const deviceInfo = {
            device_name: deviceName,
            vendor: vendor,
            ip_address: ipAddress,
            username: username,
            password: password,
            tasks: tasks
        };

        console.log('전송할 데이터:', deviceInfo);

        const response = await fetch(API_ENDPOINTS.CREATE_SCRIPT, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(deviceInfo)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || '스크립트 생성 실패');
        }

        const data = await response.json();
        if (data.status === 'success') {
            alert('스크립트가 성공적으로 생성되었습니다.');
            
            // 스크립트 내용 표시
            const scriptDisplay = document.getElementById('generatedScript');
            if (scriptDisplay && data.script) {
                scriptDisplay.textContent = data.script;
            }
            
            await loadDeviceList();
        } else {
            throw new Error(data.message || '스크립트 생성 실패');
        }
        
    } catch (error) {
        console.error('스크립트 생성 오류:', error);
        showError('스크립트 생성 중 오류가 발생했습니다: ' + error.message);
    }
}

// 장비 목록 로드 함수
async function loadDeviceList() {
    try {
        const response = await fetch(API_ENDPOINTS.DEVICES);
        const result = await response.json();
        
        console.log('서버 응답:', result);
        
        if (result.status === 'success') {
            const deviceTableBody = document.getElementById('deviceTableBody');
            deviceTableBody.innerHTML = '';
            
            if (!result.data || result.data.length === 0) {
                const emptyRow = document.createElement('tr');
                emptyRow.innerHTML = '<td colspan="4" class="text-center">저장된 장비가 없습니다.</td>';
                deviceTableBody.appendChild(emptyRow);
                return;
            }

            result.data.forEach(device => {
                if (!device || !device.device_name) {
                    console.warn('유효하지 않은 장비 데이터:', device);
                    return;
                }

                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${device.device_name || ''}</td>
                    <td>${device.device_type || ''}</td>
                    <td>${device.vendor || ''}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="viewScript('${device.device_name}')">보기</button>
                        <button class="btn btn-sm btn-success" onclick="executeScript('${device.device_name}')">실행</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteDevice('${device.device_name}')">삭제</button>
                    </td>
                `;
                deviceTableBody.appendChild(row);
            });
        } else {
            throw new Error(result.message || '장비 목록을 불러오는데 실패했습니다.');
        }
    } catch (error) {
        console.error('장비 목록 로드 오류:', error);
        const errorMessage = document.getElementById('errorMessage');
        if (errorMessage) {
            errorMessage.textContent = `장비 목록을 불러오는데 실패했습니다: ${error.message}`;
            errorMessage.style.display = 'block';
        }
    }
}

// 스크립트 보기 함수
async function viewDeviceScript(deviceName) {
    if (!deviceName) {
        console.error('장비 이름이 필요합니다');
        showError('장비 이름이 지정되지 않았습니다.');
        return;
    }

    try {
        console.log(`스크립트 조회 시작: ${deviceName}`);
        const response = await fetch(API_ENDPOINTS.VIEW_SCRIPT(deviceName));
        
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error(`'${deviceName}' 장비의 스크립트를 찾을 수 없습니다.`);
            }
            throw new Error('스크립트 조회 실패');
        }

        const data = await response.json();
        const scriptDisplay = document.getElementById('scriptDisplay');
        
        if (!scriptDisplay) {
            throw new Error('스크립트 표시 영역을 찾을 수 없습니다.');
        }

        if (data.status === 'success' && data.data) {
            scriptDisplay.innerHTML = `
                <div class="mb-3">
                    <h5>장비 정보</h5>
                    <pre class="bg-light p-2">${JSON.stringify(data.data.device_info || {}, null, 2)}</pre>
                </div>
                <div class="mb-3">
                    <h5>명령어</h5>
                    <pre class="bg-light p-2">${Array.isArray(data.data.commands) ? data.data.commands.join('\n') : ''}</pre>
                </div>
                <div>
                    <h5>생성 시간</h5>
                    <pre class="bg-light p-2">${data.data.generated_at || ''}</pre>
                </div>
            `;
        } else {
            scriptDisplay.textContent = `'${deviceName}' 장비의 스크립트 데이터가 없습니다.`;
        }
    } catch (error) {
        console.error('스크립트 보기 중 오류:', error);
        showError(error.message);
    }
}

// 스크립트 실행 함수
async function executeScript(deviceName) {
    if (!deviceName) {
        console.error('장비 이름이 필요합니다');
        showError('장비 이름이 지정되지 않았습니다.');
        return;
    }

    if (!confirm(`'${deviceName}' 장비의 스크립트를 실행하시겠습니까?`)) {
        return;
    }

    try {
        console.log(`스크립트 실행 시작: ${deviceName}`);
        const response = await fetch(API_ENDPOINTS.EXECUTE_SCRIPT(deviceName), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            if (response.status === 404) {
                throw new Error(`'${deviceName}' 장비를 찾을 수 없습니다.`);
            }
            throw new Error(`스크립트 실행 실패 (HTTP ${response.status})`);
        }

        const data = await response.json();
        if (data.status === 'success') {
            alert(`'${deviceName}' 장비의 스크립트가 성공적으로 실행되었습니다.`);
        } else {
            throw new Error(data.message || '스크립트 실행 실패');
        }
        
    } catch (error) {
        console.error('스크립트 실행 오류:', error);
        showError(error.message);
    }
}

// 장비 삭제 함수
async function deleteDevice(deviceName) {
    if (!deviceName) {
        console.error('장비 이름이 필요합니다');
        showError('장비 이름이 지정되지 않았습니다.');
        return;
    }

    if (!confirm(`'${deviceName}' 장비를 삭제하시겠습니까?`)) {
        return;
    }

    try {
        console.log(`장비 삭제 시작: ${deviceName}`);
        const response = await fetch(API_ENDPOINTS.DELETE_DEVICE(deviceName), {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            if (response.status === 404) {
                throw new Error(`'${deviceName}' 장비를 찾을 수 없습니다.`);
            }
            throw new Error(`장비 삭제 실패 (HTTP ${response.status})`);
        }

        const data = await response.json();
        if (data.status === 'success') {
            alert(`'${deviceName}' 장비가 삭제되었습니다.`);
            await loadDeviceList();
        } else {
            throw new Error(data.message || '장비 삭제 실패');
        }
        
    } catch (error) {
        console.error('장비 삭제 오류:', error);
        showError(error.message);
    }
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

// 에러 메시지 표시
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    } else {
        alert(message);
    }
} 