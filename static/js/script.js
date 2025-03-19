// 자동 학습 시작 함수
async function startAutoLearning(vendor) {
    if (!vendor) {
        alert('벤더를 선택해주세요.');
        return;
    }

    const startButton = document.getElementById('startLearning');
    const progressDiv = document.getElementById('learningProgress');
    const resultDiv = document.getElementById('learningResult');

    try {
        // 버튼 비활성화
        startButton.disabled = true;
        startButton.textContent = '학습 중...';

        // 진행 상태 표시
        if (progressDiv) {
            progressDiv.style.display = 'block';
            progressDiv.querySelector('.progress-bar').style.width = '50%';
        }

        // API 호출
        const response = await fetch('/api/auto-learning', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vendor })
        });

        const data = await response.json();

        // 결과 표시
        if (resultDiv) {
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = `
                <div class="alert alert-${response.ok ? 'success' : 'danger'}">
                    ${response.ok ? '학습이 완료되었습니다.' : '학습 중 오류가 발생했습니다.'}
                </div>
            `;
        }

    } catch (error) {
        console.error('자동학습 오류:', error);
        if (resultDiv) {
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    오류 발생: ${error.message}
                </div>
            `;
        }
    } finally {
        // UI 상태 복원
        startButton.disabled = false;
        startButton.textContent = '자동 학습 시작';
        if (progressDiv) {
            progressDiv.querySelector('.progress-bar').style.width = '100%';
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

// 전역 변수
let isLearningInProgress = false;

// 디버깅을 위한 로그 함수
function log(message) {
    console.log(`[자동학습] ${message}`);
}

// 자동학습 관련 상수
const AUTO_LEARNING = {
    STATUS: {
        IDLE: '대기 중',
        LEARNING: '학습 중...',
        COMPLETED: '완료',
        ERROR: '오류'
    },
    VENDORS: ['cisco', 'juniper', 'hp', 'arista', 'handreamnet', 'coreedge']
};

// 작업 유형별 템플릿 정의
const taskTemplates = {
    vlan: `
        <form id="vlanForm" class="task-form">
            <div class="mb-3">
                <label class="form-label">VLAN 작업 선택</label>
                <select class="form-select" name="vlanAction" id="vlanAction">
                    <option value="">작업을 선택하세요</option>
                    <option value="create">VLAN 생성</option>
                    <option value="delete">VLAN 삭제</option>
                    <option value="assign">인터페이스 VLAN 할당</option>
                    <option value="trunk">트렁크 설정</option>
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label">VLAN ID</label>
                <input type="number" class="form-control" name="vlanId" min="1" max="4094" required>
            </div>
            <div class="mb-3 vlan-name-group">
                <label class="form-label">VLAN 이름</label>
                <input type="text" class="form-control" name="vlanName">
            </div>
            <div class="mb-3 interface-group">
                <label class="form-label">인터페이스</label>
                <input type="text" class="form-control" name="interface" placeholder="예: GigabitEthernet0/1">
            </div>
        </form>
    `,
    
    port: `
        <form id="portForm" class="task-form">
            <div class="mb-3">
                <label class="form-label">포트 작업 선택</label>
                <select class="form-select" name="portAction" id="portAction" required>
                    <option value="">작업을 선택하세요</option>
                    <option value="mode">액세스/트렁크 모드 설정</option>
                    <option value="speed">포트 속도/듀플렉스 조정</option>
                    <option value="status">인터페이스 활성화/비활성화</option>
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label">인터페이스</label>
                <input type="text" class="form-control" name="interface" placeholder="예: GigabitEthernet0/1" required>
            </div>
            <div class="mb-3 port-settings">
                <!-- 동적으로 추가될 설정 필드 -->
            </div>
        </form>
    `,

    routing: `
        <form id="routingForm" class="task-form">
            <div class="mb-3">
                <label class="form-label">라우팅 프로토콜</label>
                <select class="form-select" name="routingProtocol" id="routingProtocol" required>
                    <option value="">프로토콜을 선택하세요</option>
                    <option value="static">Static Route</option>
                    <option value="ospf">OSPF</option>
                    <option value="eigrp">EIGRP</option>
                    <option value="bgp">BGP</option>
                </select>
            </div>
            <div id="routingDetails">
                <!-- 선택된 프로토콜에 따라 동적으로 변경됨 -->
            </div>
        </form>
    `,

    security: `
        <form id="securityForm" class="task-form">
            <div class="mb-3">
                <label class="form-label">보안 설정 유형</label>
                <select class="form-select" name="securityType" id="securityType" required>
                    <option value="">설정 유형을 선택하세요</option>
                    <option value="port-security">Port Security</option>
                    <option value="ssh">SSH 설정</option>
                    <option value="acl">ACL 설정</option>
                    <option value="aaa">AAA 인증</option>
                </select>
            </div>
            <div id="securityDetails">
                <!-- 선택된 보안 유형에 따라 동적으로 변경됨 -->
            </div>
        </form>
    `
    // 다른 작업 유형들도 비슷한 방식으로 추가...
};

// 작업 유형 변경 이벤트 핸들러
function handleTaskTypeChange() {
    console.log('작업 유형 변경 감지');
    const taskType = document.getElementById('taskType');
    const taskDetails = document.getElementById('taskDetails');
    const generateScriptBtn = document.getElementById('generateScript');

    if (!taskType || !taskDetails) {
        console.error('필요한 DOM 요소를 찾을 수 없습니다.');
        return;
    }

    console.log('선택된 작업 유형:', taskType.value);

    if (taskType.value && taskTemplates[taskType.value]) {
        taskDetails.innerHTML = taskTemplates[taskType.value];
        generateScriptBtn.disabled = false;

        // 작업 유형별 추가 이벤트 리스너 설정
        setupTaskSpecificListeners(taskType.value);
    } else {
        taskDetails.innerHTML = '<p class="text-muted">작업 유형을 선택하세요.</p>';
        generateScriptBtn.disabled = true;
    }
}

// 작업 유형별 추가 이벤트 리스너 설정
function setupTaskSpecificListeners(taskType) {
    console.log('작업별 리스너 설정:', taskType);
    
    switch (taskType) {
        case 'vlan':
            setupVlanListeners();
            break;
        case 'port':
            setupPortListeners();
            break;
        case 'routing':
            setupRoutingListeners();
            break;
        case 'security':
            setupSecurityListeners();
            break;
        // 다른 작업 유형들에 대한 처리 추가...
    }
}

// VLAN 관련 이벤트 리스너
function setupVlanListeners() {
    const vlanAction = document.getElementById('vlanAction');
    if (vlanAction) {
        vlanAction.addEventListener('change', function() {
            const vlanNameGroup = document.querySelector('.vlan-name-group');
            const interfaceGroup = document.querySelector('.interface-group');

            // 선택된 작업에 따라 필요한 필드 표시/숨김
            switch (this.value) {
                case 'create':
                    vlanNameGroup.style.display = 'block';
                    interfaceGroup.style.display = 'none';
                    break;
                case 'assign':
                case 'trunk':
                    vlanNameGroup.style.display = 'none';
                    interfaceGroup.style.display = 'block';
                    break;
                case 'delete':
                    vlanNameGroup.style.display = 'none';
                    interfaceGroup.style.display = 'none';
                    break;
            }
        });
    }
}

// 포트 설정 관련 이벤트 리스너
function setupPortListeners() {
    const portAction = document.getElementById('portAction');
    if (portAction) {
        portAction.addEventListener('change', function() {
            const portSettings = document.querySelector('.port-settings');
            let settingsHTML = '';

            switch (this.value) {
                case 'mode':
                    settingsHTML = `
                        <div class="mb-3">
                            <label class="form-label">포트 모드</label>
                            <select class="form-select" name="portMode" required>
                                <option value="access">Access</option>
                                <option value="trunk">Trunk</option>
                            </select>
                        </div>
                    `;
                    break;
                case 'speed':
                    settingsHTML = `
                        <div class="mb-3">
                            <label class="form-label">속도 설정</label>
                            <select class="form-select" name="portSpeed" required>
                                <option value="auto">Auto</option>
                                <option value="10">10 Mbps</option>
                                <option value="100">100 Mbps</option>
                                <option value="1000">1 Gbps</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">듀플렉스 모드</label>
                            <select class="form-select" name="portDuplex" required>
                                <option value="auto">Auto</option>
                                <option value="full">Full</option>
                                <option value="half">Half</option>
                            </select>
                        </div>
                    `;
                    break;
                case 'status':
                    settingsHTML = `
                        <div class="mb-3">
                            <label class="form-label">포트 상태</label>
                            <select class="form-select" name="portStatus" required>
                                <option value="up">활성화 (no shutdown)</option>
                                <option value="down">비활성화 (shutdown)</option>
                            </select>
                        </div>
                    `;
                    break;
            }
            portSettings.innerHTML = settingsHTML;
        });
    }
}

// 페이지 로드 시 실행되는 초기화 함수
document.addEventListener('DOMContentLoaded', function() {
    console.log('페이지 초기화 시작');
    
    // 자동학습 관련 요소 초기화
    const startButton = document.getElementById('startLearning');
    const vendorSelect = document.getElementById('learningVendor');
    
    if (startButton && vendorSelect) {
        // 벤더 선택 시 버튼 활성화/비활성화
        vendorSelect.addEventListener('change', function() {
            startButton.disabled = !this.value;
        });
        
        // 자동학습 시작 버튼 클릭 이벤트
        startButton.addEventListener('click', function(event) {
            event.preventDefault();
            handleAutoLearning(vendorSelect.value);
        });
    }

    // 장비 추가 폼 이벤트 리스너 등록
    const deviceForm = document.getElementById('deviceForm');
    if (deviceForm) {
        deviceForm.addEventListener('submit', handleDeviceSubmit);
    }

    // 초기 장비 목록 로드
    loadDeviceList();
    
    // 백업 목록 로드
    loadBackupList();
    
    // 작업 유형 변경 이벤트 리스너 등록
    const taskType = document.getElementById('taskType');
    if (taskType) {
        taskType.addEventListener('change', handleTaskTypeChange);
        console.log('작업 유형 선택 이벤트 리스너 등록됨');
    }
    
    console.log('페이지 초기화 완료');
});

function showProgress(show) {
    const progressDiv = document.getElementById('learningProgress');
    if (progressDiv) {
        progressDiv.style.display = show ? 'block' : 'none';
        const progressBar = progressDiv.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = show ? '50%' : '0%';
        }
    }
}

function showResult(success, message) {
    const resultDiv = document.getElementById('learningResult');
    if (resultDiv) {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `
            <div class="alert alert-${success ? 'success' : 'danger'}">
                <i class="bi bi-${success ? 'check-circle' : 'exclamation-triangle'}"></i>
                ${message}
            </div>
        `;
    }
}

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
async function deleteDevice(name) {
    if (!name || !confirm(`'${name}' 장비와 관련된 모든 스크립트를 삭제하시겠습니까?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/devices/${name}`, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json'
            }
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || '장비 삭제 실패');
        }

        // 장비 목록 새로고침
        await loadDeviceList();

        alert(result.message);
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

// 스크립트 생성 버튼 이벤트 핸들러
document.getElementById('generateScript')?.addEventListener('click', async function() {
    console.log('스크립트 생성 시작');
    
    try {
        const deviceSelect = document.getElementById('deviceSelect');
        const taskType = document.getElementById('taskType');
        
        if (!deviceSelect || !taskType) {
            throw new Error('필수 DOM 요소를 찾을 수 없습니다.');
        }

        if (!deviceSelect.value || !taskType.value) {
            showMessage('장비와 작업 유형을 선택해주세요.', 'warning');
            return;
        }

        // 파라미터 수집 및 검증
        const params = collectTaskParameters(taskType.value);
        console.log('수집된 파라미터:', params);

        const formData = {
            device: deviceSelect.value,
            taskType: taskType.value,
            params: params
        };

        console.log('전송할 데이터:', formData);

        const response = await fetch('/api/generate-script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        console.log('서버 응답:', result);

        if (!response.ok) {
            throw new Error(result.message || '스크립트 생성 실패');
        }

        // 생성된 스크립트 표시
        const scriptDisplay = document.getElementById('generatedScript');
        if (scriptDisplay) {
            scriptDisplay.textContent = result.script;
            document.getElementById('executeScript').disabled = false;
            showMessage('스크립트가 생성되었습니다.', 'success');
        } else {
            throw new Error('스크립트 표시 영역을 찾을 수 없습니다.');
        }

    } catch (error) {
        console.error('스크립트 생성 오류:', error);
        showMessage(error.message, 'danger');
    }
});

// 작업 유형별 파라미터 수집 함수
function collectTaskParameters(taskType) {
    console.log('파라미터 수집 시작:', taskType);
    
    const params = {};
    const taskForm = document.querySelector('.task-form');
    
    if (!taskForm) {
        console.error('작업 폼을 찾을 수 없습니다.');
        return params;
    }

    // 폼 데이터 수집 및 검증
    const formData = new FormData(taskForm);
    for (let [key, value] of formData.entries()) {
        // 값이 비어있지 않은 경우에만 파라미터에 추가
        if (value.trim()) {
            params[key] = value.trim();
        }
    }

    // 작업 유형별 필수 파라미터 검증
    if (taskType === 'vlan') {
        if (!params.vlanAction) {
            throw new Error('VLAN 작업 유형을 선택해주세요.');
        }
        if (!params.vlanId) {
            throw new Error('VLAN ID를 입력해주세요.');
        }
        // VLAN ID 범위 검증
        const vlanId = parseInt(params.vlanId);
        if (isNaN(vlanId) || vlanId < 1 || vlanId > 4094) {
            throw new Error('VLAN ID는 1-4094 범위여야 합니다.');
        }
        // 인터페이스 필수 여부 검증
        if (['assign', 'trunk'].includes(params.vlanAction) && !params.interface) {
            throw new Error('인터페이스를 지정해주세요.');
        }
    }

    console.log('수집된 파라미터:', params);
    return params;
}

// 장비 추가 폼 제출 처리
async function handleDeviceSubmit(event) {
    event.preventDefault();
    
    const formData = {
        name: document.getElementById('deviceName').value.trim(),
        vendor: document.getElementById('deviceVendor').value.trim(),
        ip: document.getElementById('deviceIP').value.trim()
    };

    try {
        const response = await fetch('/api/devices', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || '장비 추가 실패');
        }

        // 성공 메시지 표시
        showMessage('장비가 성공적으로 추가되었습니다.', 'success');
        
        // 폼 초기화
        document.getElementById('deviceForm').reset();
        
        // 장비 목록 새로고침
        await loadDeviceList();

    } catch (error) {
        console.error('장비 추가 오류:', error);
        showMessage(error.message, 'danger');
    }
}

// 장비 목록 로드 및 드롭다운 업데이트 함수
async function loadDeviceList() {
    console.log('장비 목록 로드 시작');
    try {
        const response = await fetch('/api/devices');
        const result = await response.json();
        console.log('받은 데이터:', result);

        if (!response.ok) {
            throw new Error(result.message || '장비 목록 로드 실패');
        }

        // 기본 정보 탭의 테이블 업데이트
        updateDeviceTable(result.data);
        
        // 설정 작업 탭의 드롭다운 업데이트
        updateDeviceDropdown(result.data);
        
        console.log('장비 목록 로드 완료');

    } catch (error) {
        console.error('장비 목록 로드 오류:', error);
        showMessage('장비 목록을 불러오는 중 오류가 발생했습니다.', 'danger');
    }
}

// 장비 목록 테이블 업데이트 함수
function updateDeviceTable(devices) {
    const tbody = document.getElementById('deviceListBasic');
    if (!tbody) {
        console.log('장비 목록 테이블 요소를 찾을 수 없습니다.');
        return;
    }

    if (!Array.isArray(devices) || devices.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">
                    <div class="text-muted">등록된 장비가 없습니다.</div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = devices.map((device, index) => `
        <tr>
            <td>${index + 1}</td>
            <td>${device.name || ''}</td>
            <td>${device.vendor || ''}</td>
            <td>${device.ip || ''}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="deleteDevice('${device.name}')">
                    삭제
                </button>
            </td>
        </tr>
    `).join('');
}

// 설정 작업 탭의 장비 선택 드롭다운 업데이트 함수
function updateDeviceDropdown(devices) {
    const deviceSelect = document.getElementById('deviceSelect');
    if (!deviceSelect) {
        console.log('장비 선택 드롭다운 요소를 찾을 수 없습니다.');
        return;
    }

    // 기존 옵션 제거 (첫 번째 기본 옵션 유지)
    while (deviceSelect.options.length > 1) {
        deviceSelect.remove(1);
    }

    // 장비 목록이 비어있는 경우 처리
    if (!Array.isArray(devices) || devices.length === 0) {
        deviceSelect.innerHTML = '<option value="">등록된 장비가 없습니다</option>';
        return;
    }

    // 장비 목록 추가
    devices.forEach(device => {
        const option = document.createElement('option');
        option.value = device.name;
        option.textContent = `${device.name} (${device.ip})`;
        deviceSelect.appendChild(option);
    });
}

// 자동학습 처리 함수
async function handleAutoLearning(vendor) {
    if (!vendor) {
        alert('벤더를 선택해주세요.');
        return;
    }

    const startButton = document.getElementById('startLearning');
    const progressDiv = document.getElementById('learningProgress');
    const resultDiv = document.getElementById('learningResult');

    try {
        // 버튼 비활성화 및 상태 표시
        startButton.disabled = true;
        startButton.textContent = '학습 중...';

        // 진행 상태 표시
        if (progressDiv) {
            progressDiv.style.display = 'block';
            progressDiv.querySelector('.progress-bar').style.width = '50%';
        }

        // API 호출
        const response = await fetch('/api/auto-learning', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ vendor })
        });

        const data = await response.json();

        // 결과 표시
        if (resultDiv) {
            resultDiv.style.display = 'block';
            if (response.ok) {
                resultDiv.innerHTML = `
                    <div class="alert alert-success">
                        <i class="bi bi-check-circle"></i> 
                        ${vendor} 벤더의 자동학습이 완료되었습니다.
                    </div>
                `;
            } else {
                throw new Error(data.message || '자동학습 실패');
            }
        }

    } catch (error) {
        console.error('자동학습 오류:', error);
        if (resultDiv) {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> 
                    오류 발생: ${error.message}
                </div>
            `;
        }
    } finally {
        // UI 상태 복원
        startButton.disabled = false;
        startButton.textContent = '자동 학습 시작';
        if (progressDiv) {
            progressDiv.querySelector('.progress-bar').style.width = '100%';
        }
    }
}

// 메시지 표시 함수
function showMessage(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    const container = document.querySelector('.container');
    if (container) {
        // 기존 알림 제거
        const existingAlert = container.querySelector('.alert');
        if (existingAlert) {
            existingAlert.remove();
        }
        container.insertBefore(alertDiv, container.firstChild);
    }

    // 3초 후 자동으로 메시지 제거
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// 백업 관리 기능 추가
async function loadBackupList() {
    try {
        const response = await fetch('/api/backups');
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || '백업 목록 로드 실패');
        }

        updateBackupList(result.data);

    } catch (error) {
        console.error('백업 목록 로드 오류:', error);
        showMessage('백업 목록을 불러오는 중 오류가 발생했습니다.', 'danger');
    }
}

function updateBackupList(backups) {
    const tbody = document.getElementById('backupList');
    if (!tbody) return;

    if (!backups || backups.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">
                    <div class="text-muted">백업 데이터가 없습니다.</div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = backups.map(backup => `
        <tr>
            <td>${backup.device_name}</td>
            <td>${backup.backup_date}</td>
            <td>
                <button class="btn btn-sm btn-primary" 
                        onclick="restoreBackup('${backup.id}')"
                        title="백업 복원">
                    <i class="bi bi-arrow-clockwise"></i> 복원
                </button>
                <button class="btn btn-sm btn-danger" 
                        onclick="deleteBackup('${backup.id}')"
                        title="백업 삭제">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function restoreBackup(backupId) {
    const confirmDialog = document.createElement('div');
    confirmDialog.className = 'modal fade';
    confirmDialog.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">백업 복원 확인</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>선택한 백업을 복원하시겠습니까?</p>
                    <p class="text-warning">
                        <i class="bi bi-exclamation-triangle"></i> 
                        기존 데이터가 있다면 덮어쓰기됩니다.
                    </p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">취소</button>
                    <button type="button" class="btn btn-primary" id="confirmRestore">복원</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(confirmDialog);
    const modal = new bootstrap.Modal(confirmDialog);
    modal.show();

    document.getElementById('confirmRestore').onclick = async () => {
        modal.hide();
        try {
            const response = await fetch(`/api/backups/${backupId}/restore`, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json'
                }
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || '백업 복원 실패');
            }

            showMessage(result.message, 'success');
            
            // 장비 목록과 백업 목록 새로고침
            await Promise.all([
                loadDeviceList(),
                loadBackupList()
            ]);

        } catch (error) {
            console.error('백업 복원 오류:', error);
            showMessage(`백업 복원 중 오류가 발생했습니다: ${error.message}`, 'danger');
        } finally {
            document.body.removeChild(confirmDialog);
        }
    };

    confirmDialog.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(confirmDialog);
    });
}

async function deleteBackup(backupId) {
    if (!confirm('이 백업을 삭제하시겠습니까?')) {
        return;
    }

    try {
        const response = await fetch(`/api/backups/${backupId}`, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json'
            }
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || '백업 삭제 실패');
        }

        showMessage(result.message, 'success');
        await loadBackupList();

    } catch (error) {
        console.error('백업 삭제 오류:', error);
        showMessage(`백업 삭제 중 오류가 발생했습니다: ${error.message}`, 'danger');
    }
} 