// 자동 학습 시작 함수
async function startAutoLearning() {
    const vendor = document.getElementById('autoVendor').value;

    if (!vendor) {
        alert('벤더를 선택해주세요.');
        return;
    }

    try {
        // 학습 상태 표시
        const learningStatus = document.getElementById('learningStatus');
        if (learningStatus) {
            learningStatus.textContent = '자동 학습 진행 중...';
            learningStatus.className = 'alert alert-info';
            learningStatus.style.display = 'block';
        }

        const response = await fetch('/cli/learn', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                vendor: vendor
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.status === 'success') {
            learningStatus.textContent = result.message;
            learningStatus.className = 'alert alert-success';
        } else {
            throw new Error(result.message || '학습 중 오류가 발생했습니다.');
        }
    } catch (error) {
        console.error('자동 학습 오류:', error);
        const learningStatus = document.getElementById('learningStatus');
        if (learningStatus) {
            learningStatus.textContent = '학습 중 오류가 발생했습니다: ' + error.message;
            learningStatus.className = 'alert alert-danger';
            learningStatus.style.display = 'block';
        }
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

    try {
        const statusElement = document.getElementById('documentLearningStatus');
        if (statusElement) {
            statusElement.textContent = '문서 학습 진행 중...';
            statusElement.className = 'alert alert-info';
            statusElement.style.display = 'block';
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
                        task_type: taskType,
                        commands: commands
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                if (result.status === 'success') {
                    statusElement.textContent = result.message || '문서 학습이 완료되었습니다.';
                    statusElement.className = 'alert alert-success';
                } else {
                    throw new Error(result.message || '학습 중 오류가 발생했습니다.');
                }
            } catch (error) {
                console.error('문서 학습 오류:', error);
                statusElement.textContent = '학습 중 오류가 발생했습니다: ' + error.message;
                statusElement.className = 'alert alert-danger';
            }
        };

        reader.readAsText(file);
    } catch (error) {
        console.error('파일 읽기 오류:', error);
        const statusElement = document.getElementById('documentLearningStatus');
        if (statusElement) {
            statusElement.textContent = '파일 읽기 중 오류가 발생했습니다: ' + error.message;
            statusElement.className = 'alert alert-danger';
            statusElement.style.display = 'block';
        }
    }
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

// 전역 범위에서 모든 함수들을 먼저 정의
async function handleCreateScript(event) {
    event.preventDefault();
    try {
        const deviceName = document.getElementById('deviceName')?.value;
        const vendor = document.getElementById('vendor')?.value;
        
        if (!deviceName || !vendor) {
            throw new Error('장비 이름과 벤더 정보를 입력해주세요.');
        }

        const tasks = collectTasks();
        if (Object.keys(tasks).length === 0) {
            throw new Error('최소한 하나의 작업을 선택해주세요.');
        }

        const data = {
            device_name: deviceName,
            vendor: vendor,
            tasks: tasks
        };

        if (document.getElementById('ipConfig')?.checked) {
            data.tasks.ip_config = {
                enabled: true,
                interface_name: document.getElementById('ipInterface')?.value,
                ip_address: document.getElementById('scriptIpAddress')?.value,
                subnet_mask: document.getElementById('subnetMask')?.value
            };
        }

        fetch('/api/devices/script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('스크립트 생성 실패');
            }
            return response.json();
        })
        .then(result => {
            alert(result.message);
        })
        .catch(error => {
            console.error('스크립트 생성 오류:', error);
            alert(error.message);
        });
        
    } catch (error) {
        console.error('스크립트 생성 오류:', error);
        alert(error.message);
    }
}

function handleAddDevice(event) {
    event.preventDefault();
    const deviceName = document.getElementById('deviceName')?.value;
    const vendor = document.getElementById('vendor')?.value;

    if (!deviceName || !vendor) {
        alert('장비 이름과 벤더 정보를 입력해주세요.');
        return;
    }

    fetch('/api/devices', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            device_name: deviceName,
            vendor: vendor
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('장비 추가 실패');
        }
        return response.json();
    })
    .then(result => {
        alert(result.message);
        loadDeviceList();
    })
    .catch(error => {
        console.error('장비 추가 오류:', error);
        alert(error.message);
    });
}

function collectTasks() {
    const tasks = {};
    
    // VLAN 설정
    const vlanConfigCheckbox = document.getElementById('vlanConfig');
    if (vlanConfigCheckbox && vlanConfigCheckbox.checked) {
        const vlanId = document.getElementById('vlanId')?.value;
        const vlanName = document.getElementById('vlanName')?.value;
        
        if (!vlanId || !vlanName) {
            throw new Error('VLAN ID와 이름을 입력해주세요.');
        }
        
        tasks['VLAN 생성/삭제'] = {
            enabled: true,
            vlan_id: vlanId,
            vlan_name: vlanName
        };
    }

    // VLAN 인터페이스 설정
    const vlanInterfaceCheckbox = document.getElementById('vlanInterface');
    if (vlanInterfaceCheckbox && vlanInterfaceCheckbox.checked) {
        const interfaceName = document.getElementById('interfaceName')?.value;
        const interfaceMode = document.getElementById('interfaceMode')?.value;
        const interfaceVlanId = document.getElementById('interfaceVlanId')?.value;
        
        if (!interfaceName || !interfaceMode || !interfaceVlanId) {
            throw new Error('인터페이스 정보를 모두 입력해주세요.');
        }
        
        tasks['vlanInterface'] = {
            enabled: true,
            interface_name: interfaceName,
            mode: interfaceMode,
            vlan_id: interfaceVlanId
        };
    }

    console.log('수집된 작업 데이터:', tasks);
    return tasks;
}

async function loadDeviceList() {
    try {
        const response = await fetch('/api/devices');
        if (!response.ok) {
            throw new Error('장비 목록을 가져오는데 실패했습니다.');
        }
        
        const data = await response.json();
        console.log('로드된 장비 목록:', data);

        // 데이터가 배열이 아닌 경우 처리
        const devices = Array.isArray(data) ? data : (data.devices || []);
        
        updateDeviceTable(devices);
    } catch (error) {
        console.error('장비 목록 로드 오류:', error);
        updateDeviceTable([]); // 빈 배열로 테이블 업데이트
    }
}

function updateDeviceTable(devices) {
    const tableBody = document.getElementById('deviceTableBody');
    if (!tableBody) {
        console.error('장비 목록 테이블을 찾을 수 없습니다.');
        return;
    }

    if (devices.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="3" class="text-center">등록된 장비가 없습니다.</td>
            </tr>`;
        return;
    }

    tableBody.innerHTML = devices.map((device, index) => `
        <tr>
            <td>${index + 1}</td>
            <td>${device.device_name || '-'}</td>
            <td>${device.vendor || '-'}</td>
        </tr>
    `).join('');
}

// 페이지 초기화 함수
function initializePage() {
    console.log('페이지 초기화 시작');
    try {
        // 스크립트 생성 버튼
        const createScriptBtn = document.getElementById('createScriptBtn');
        if (createScriptBtn) {
            createScriptBtn.addEventListener('click', handleCreateScript);
        }

        // 장비 추가 버튼
        const addDeviceBtn = document.getElementById('addDeviceBtn');
        if (addDeviceBtn) {
            addDeviceBtn.addEventListener('click', handleAddDevice);
        }

        // 장비 목록 로드
        loadDeviceList();
        
        console.log('페이지 초기화 완료');
    } catch (error) {
        console.error('페이지 초기화 중 오류:', error);
    }
}

// DOMContentLoaded 이벤트에서 초기화 함수 호출
document.addEventListener('DOMContentLoaded', initializePage);

// 장비 보기 함수
async function viewDevice(deviceName) {
    try {
        const response = await fetch(`/api/devices/${deviceName}`);
        if (!response.ok) {
            throw new Error('장비 정보를 불러오는데 실패했습니다.');
        }
        
        const deviceInfo = await response.json();
        alert(JSON.stringify(deviceInfo, null, 2));
    } catch (error) {
        console.error('장비 정보 조회 오류:', error);
        alert(error.message);
    }
}

// 스크립트 실행 함수
async function executeScript(deviceName) {
    try {
        if (!confirm(`${deviceName}의 스크립트를 실행하시겠습니까?`)) {
            return;
        }

        const response = await fetch(`/api/devices/${deviceName}/execute`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('스크립트 실행 실패');
        }

        const result = await response.json();
        alert(result.message);
    } catch (error) {
        console.error('스크립트 실행 오류:', error);
        alert(error.message);
    }
}

// 장비 삭제 함수
async function deleteDevice(deviceName) {
    try {
        if (!confirm(`${deviceName}을(를) 삭제하시겠습니까?`)) {
            return;
        }

        const response = await fetch(`/api/devices/${deviceName}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('장비 삭제 실패');
        }

        const result = await response.json();
        alert(result.message);
        loadDeviceList(); // 장비 목록 새로고침
    } catch (error) {
        console.error('장비 삭제 오류:', error);
        alert(error.message);
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

async function validateData(data) {
    try {
        const response = await fetch('/api/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.status === 'success') {
            alert('데이터가 유효합니다.');
        } else {
            alert('데이터 검증 중 오류가 발생했습니다: ' + result.message);
        }
    } catch (error) {
        console.error('데이터 검증 중 오류:', error);
        alert('데이터 검증 중 오류가 발생했습니다: ' + error.message);
    }
}

async function handleAutoLearning(event) {
    event.preventDefault();
    try {
        const vendor = document.getElementById('learningVendor').value;

        if (!vendor) {
            alert('벤더를 선택해주세요.');
            return;
        }

        const data = {
            vendor: vendor
        };

        // 로딩 표시
        const commandList = document.getElementById('commandList');
        commandList.innerHTML = `
            <div class="text-center my-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">자동학습 중입니다...</p>
            </div>
        `;

        const response = await fetch('/api/auto-learning', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || '자동학습 처리 실패');
        }

        // 결과 표시
        if (commandList) {
            let html = `
                <div class="alert alert-success mb-4">
                    <i class="bi bi-check-circle-fill me-2"></i>
                    ${vendor.toUpperCase()} 장비 자동학습이 완료되었습니다.
                </div>
                <div class="row row-cols-1 row-cols-md-2 g-4">
            `;
            
            for (const [taskName, taskInfo] of Object.entries(result.tasks)) {
                html += `
                    <div class="col">
                        <div class="card h-100 border-0 shadow-sm">
                            <div class="card-header bg-light">
                                <h5 class="card-title mb-0">
                                    <i class="bi bi-gear-fill me-2"></i>
                                    ${taskInfo.name}
                                </h5>
                            </div>
                            <div class="card-body p-0">
                                <div class="list-group list-group-flush">
                                    ${taskInfo.show_commands.map(cmd => 
                                        `<div class="list-group-item">
                                            <code class="text-primary">${cmd}</code>
                                        </div>`
                                    ).join('')}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            html += '</div>';
            commandList.innerHTML = html;
        }
        
    } catch (error) {
        console.error('자동학습 처리 오류:', error);
        const commandList = document.getElementById('commandList');
        if (commandList) {
            commandList.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    ${error.message}
                </div>
            `;
        }
    }
}

// 이벤트 리스너 등록
document.getElementById('autoLearningBtn')?.addEventListener('click', handleAutoLearning); 