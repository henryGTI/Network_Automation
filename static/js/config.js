// 전역 변수
let devices = [];
let selectedDevice = null;
let taskTypes = {};
let subtasks = {};

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    // 초기 상태 설정
    document.getElementById('task-type').disabled = true;
    document.getElementById('subtask').disabled = true;
    document.getElementById('generateScriptBtn').disabled = true;
    document.querySelector('#task-form button[type="submit"]').disabled = true;

    // 이벤트 리스너 설정
    setupEventListeners();
    
    // 데이터 로드
    loadDevices();
    loadTaskTypes();
});

// 이벤트 리스너 설정
function setupEventListeners() {
    // 장비 선택 이벤트
    document.getElementById('device-list').addEventListener('click', (e) => {
        const deviceItem = e.target.closest('.list-group-item');
        if (deviceItem) {
            const deviceId = deviceItem.dataset.deviceId;
            selectDevice(deviceId);
        }
    });

    // 작업 유형 선택 이벤트
    document.getElementById('task-type').addEventListener('change', (e) => {
        const taskType = e.target.value;
        if (taskType) {
            loadSubtasks(taskType);
        }
    });

    // 하위 작업 선택 이벤트
    document.getElementById('subtask').addEventListener('change', (e) => {
        const subtask = e.target.value;
        const taskType = document.getElementById('task-type').value;
        if (subtask && taskType) {
            loadParameters(taskType, subtask);
        }
    });

    // 작업 추가 폼 제출 이벤트
    document.getElementById('task-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await addTask();
    });

    // 스크립트 생성 버튼 클릭 이벤트
    document.getElementById('generateScriptBtn').addEventListener('click', async () => {
        try {
            // 선택된 장비와 작업 유형 확인
            const selectedDevice = document.getElementById('deviceSelect').value;
            const selectedTasks = Array.from(document.querySelectorAll('input[name="task_type"]:checked'))
                .map(checkbox => checkbox.value);

            if (!selectedDevice) {
                showError('장비를 선택해주세요.');
                return;
            }

            if (selectedTasks.length === 0) {
                showError('작업 유형을 하나 이상 선택해주세요.');
                return;
            }

            // 파라미터 수집
            const parameters = {};
            for (const taskType of selectedTasks) {
                const taskParams = {};
                const paramInputs = document.querySelectorAll(`[data-task-type="${taskType}"] input`);
                for (const input of paramInputs) {
                    if (input.value) {
                        taskParams[input.name] = input.value;
                    }
                }
                if (Object.keys(taskParams).length > 0) {
                    parameters[taskType] = taskParams;
                }
            }

            // 서버로 데이터 전송
            const response = await fetch('/api/config/generate-script', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device_id: selectedDevice,
                    task_types: selectedTasks,
                    parameters: parameters
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                // 스크립트 표시
                const scriptArea = document.getElementById('scriptArea');
                scriptArea.value = result.data.script;
                
                // 실행 버튼 활성화
                document.getElementById('executeScriptBtn').disabled = false;
                
                showSuccess('스크립트가 생성되었습니다.');
            } else {
                showError(result.message);
            }
        } catch (error) {
            console.error('스크립트 생성 중 오류:', error);
            showError('스크립트 생성 중 오류가 발생했습니다.');
        }
    });
}

// 장비 목록 로드
async function loadDevices() {
    try {
        showLoading();
        const response = await fetch('/api/devices');
        const data = await response.json();
        
        if (data.status === 'success') {
            devices = data.data;
            displayDevices();
        } else {
            showError('장비 목록을 불러오는데 실패했습니다.');
        }
    } catch (error) {
        showError('장비 목록을 불러오는데 실패했습니다.');
        console.error('Error loading devices:', error);
    } finally {
        hideLoading();
    }
}

// 장비 목록 표시
function displayDevices() {
    const deviceList = document.getElementById('device-list');
    deviceList.innerHTML = devices.map(device => `
        <a href="#" class="list-group-item list-group-item-action" data-device-id="${device.id}">
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${device.name}</h6>
                <small>${device.vendor}</small>
            </div>
            <small>${device.ip}</small>
        </a>
    `).join('');
}

// 작업 유형 목록 로드
async function loadTaskTypes() {
    try {
        const response = await fetch('/api/config/task-types');
        const data = await response.json();
        
        if (data.status === 'success') {
            taskTypes = data.data;
            displayTaskTypes();
        } else {
            showError('작업 유형 목록을 불러오는데 실패했습니다.');
        }
    } catch (error) {
        showError('작업 유형 목록을 불러오는데 실패했습니다.');
        console.error('Error loading task types:', error);
    }
}

// 작업 유형 목록 표시
function displayTaskTypes() {
    const taskTypeSelect = document.getElementById('task-type');
    taskTypeSelect.innerHTML = '<option value="">작업 유형을 선택하세요</option>' +
        taskTypes.map(type => `
            <option value="${type}">${getTaskTypeLabel(type)}</option>
        `).join('');
}

// 작업 유형 레이블 생성
function getTaskTypeLabel(type) {
    const labels = {
        'vlan': 'VLAN 설정',
        'port': '포트 설정',
        'routing': '라우팅 설정',
        'security': '보안 설정',
        'stp_lacp': 'STP/LACP 설정',
        'qos': 'QoS 설정',
        'monitoring': '모니터링',
        'status': '상태 확인',
        'logging': '로깅',
        'backup': '백업/복구',
        'snmp': 'SNMP 설정',
        'automation': '자동화'
    };
    return labels[type] || type;
}

// 하위 작업 목록 로드
async function loadSubtasks(taskType) {
    try {
        const response = await fetch(`/api/config/subtasks/${taskType}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            subtasks[taskType] = data.data;
            displaySubtasks(taskType);
        } else {
            showError('하위 작업 목록을 불러오는데 실패했습니다.');
        }
    } catch (error) {
        showError('하위 작업 목록을 불러오는데 실패했습니다.');
        console.error('Error loading subtasks:', error);
    }
}

// 하위 작업 목록 표시
function displaySubtasks(taskType) {
    const subtaskSelect = document.getElementById('subtask');
    subtaskSelect.disabled = false;  // 하위 작업 선택 활성화
    subtaskSelect.innerHTML = '<option value="">상세 작업을 선택하세요</option>' +
        subtasks[taskType].map(subtask => `
            <option value="${subtask}">${getSubtaskLabel(taskType, subtask)}</option>
        `).join('');
    
    // 파라미터 컨테이너 초기화
    document.getElementById('parameters-container').innerHTML = '';
    // 작업 추가 버튼 비활성화
    document.querySelector('#task-form button[type="submit"]').disabled = true;
}

// 하위 작업 레이블 생성
function getSubtaskLabel(taskType, subtask) {
    const labels = {
        'vlan': {
            'create': 'VLAN 생성',
            'delete': 'VLAN 삭제',
            'interface_assign': '인터페이스 할당',
            'trunk': '트렁크 설정'
        },
        'port': {
            'mode': '포트 모드 설정',
            'speed': '속도/듀플렉스 설정',
            'status': '포트 상태 설정'
        },
        'routing': {
            'static': '정적 라우팅',
            'ospf': 'OSPF 설정',
            'eigrp': 'EIGRP 설정',
            'bgp': 'BGP 설정'
        },
        'security': {
            'port_security': '포트 보안',
            'ssh': 'SSH 설정',
            'aaa': 'AAA 설정',
            'acl': 'ACL 설정'
        },
        'stp_lacp': {
            'stp': 'STP 설정',
            'lacp': 'LACP 설정'
        },
        'qos': {
            'policy': '정책 설정',
            'rate_limit': '속도 제한',
            'service_policy': '서비스 정책'
        },
        'monitoring': {
            'route': '라우팅 테이블',
            'ospf': 'OSPF 상태',
            'bgp': 'BGP 상태'
        },
        'status': {
            'interface': '인터페이스 상태',
            'traffic': '트래픽 상태'
        },
        'logging': {
            'show': '로그 보기'
        },
        'backup': {
            'backup': '설정 백업',
            'restore': '설정 복구',
            'tftp': 'TFTP 전송'
        },
        'snmp': {
            'setup': 'SNMP 설정',
            'discovery': '장비 탐색'
        },
        'automation': {
            'deploy': '설정 배포',
            'verify': '설정 검증'
        }
    };
    return labels[taskType]?.[subtask] || subtask;
}

// 파라미터 정보 로드
async function loadParameters(taskType, subtask) {
    try {
        const response = await fetch(`/api/config/parameters/${taskType}/${subtask}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            displayParameters(data.data);
        } else {
            showError('파라미터 정보를 불러오는데 실패했습니다.');
        }
    } catch (error) {
        showError('파라미터 정보를 불러오는데 실패했습니다.');
        console.error('Error loading parameters:', error);
    }
}

// 파라미터 입력 필드 표시
function displayParameters(parameters) {
    const container = document.getElementById('parameters-container');
    container.innerHTML = parameters.map(param => `
        <div class="mb-3">
            <label for="${param}" class="form-label">${getParameterLabel(param)}</label>
            <input type="text" class="form-control" id="${param}" name="${param}" required>
        </div>
    `).join('');
    
    // 작업 추가 버튼 활성화
    document.querySelector('#task-form button[type="submit"]').disabled = false;
}

// 파라미터 레이블 생성
function getParameterLabel(param) {
    const labels = {
        'vlan_id': 'VLAN ID',
        'vlan_name': 'VLAN 이름',
        'interface': '인터페이스',
        'mode': '모드',
        'speed': '속도',
        'duplex': '듀플렉스',
        'status': '상태',
        'network': '네트워크',
        'mask': '서브넷 마스크',
        'next_hop': '다음 홉',
        'process_id': '프로세스 ID',
        'area': '영역',
        'as_number': 'AS 번호',
        'neighbor': '이웃',
        'remote_as': '원격 AS',
        'max_mac': '최대 MAC 주소 수',
        'violation': '위반 동작',
        'version': '버전',
        'timeout': '타임아웃',
        'authentication': '인증 방식',
        'method': '방법',
        'server_group': '서버 그룹',
        'service': '서비스',
        'name': '이름',
        'type': '유형',
        'entries': '항목',
        'priority': '우선순위',
        'channel_group': '채널 그룹',
        'interfaces': '인터페이스',
        'policy_name': '정책 이름',
        'class_map': '클래스 맵',
        'actions': '동작',
        'rate': '속도',
        'burst': '버스트',
        'direction': '방향',
        'filename': '파일 이름',
        'server': '서버',
        'community': '커뮤니티',
        'access': '접근 권한',
        'protocol': '프로토콜',
        'config_file': '설정 파일',
        'devices': '장비 목록',
        'condition': '조건',
        'action': '동작'
    };
    
    return labels[param] || param;
}

// 장비 선택
function selectDevice(deviceId) {
    const device = devices.find(d => d.id === parseInt(deviceId));
    if (device) {
        selectedDevice = device;
        
        // 선택된 장비 시각적 표시
        document.querySelectorAll('.list-group-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.deviceId === deviceId) {
                item.classList.add('active');
            }
        });

        // 작업 추가 폼 활성화
        document.getElementById('task-type').disabled = false;
        
        // 작업 목록 로드
        loadTasks(deviceId);
        
        // 스크립트 생성 버튼 활성화
        document.getElementById('generateScriptBtn').disabled = false;
    }
}

// 작업 목록 로드
async function loadTasks(deviceId) {
    try {
        showLoading();
        const response = await fetch(`/api/config/tasks?device_id=${deviceId}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            displayTasks(data.data);
        } else {
            showError('작업 목록을 불러오는데 실패했습니다.');
        }
    } catch (error) {
        showError('작업 목록을 불러오는데 실패했습니다.');
        console.error('Error loading tasks:', error);
    } finally {
        hideLoading();
    }
}

// 작업 목록 표시
function displayTasks(tasks) {
    const taskList = document.getElementById('task-list');
    if (!Array.isArray(tasks)) {
        console.error('Invalid tasks data:', tasks);
        return;
    }

    taskList.innerHTML = tasks.map((task, index) => `
        <div class="card mb-2">
            <div class="card-body p-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-0">${getTaskTypeLabel(task.task_type)}</h6>
                        <small class="text-muted">${getSubtaskLabel(task.task_type, task.subtask)}</small>
                    </div>
                    <div class="d-flex align-items-center">
                        <span class="badge bg-${getStatusBadgeColor(task.status)} me-2">
                            ${getStatusText(task.status)}
                        </span>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteTask('${task.device_id}', ${index})">
                            삭제
                        </button>
                    </div>
                </div>
                ${renderParameters(task.parameters)}
            </div>
        </div>
    `).join('');
}

// 파라미터 렌더링
function renderParameters(parameters) {
    if (!parameters || Object.keys(parameters).length === 0) {
        return '';
    }

    return `
        <div class="mt-2 pt-2 border-top">
            <small class="text-muted">파라미터:</small>
            <div class="ps-2">
                ${Object.entries(parameters).map(([key, value]) => `
                    <small class="d-block">
                        <span class="fw-bold">${getParameterLabel(key)}:</span> ${value}
                    </small>
                `).join('')}
            </div>
        </div>
    `;
}

// 작업 추가
async function addTask() {
    if (!selectedDevice) {
        showError('장비를 선택해주세요.');
        return;
    }

    const form = document.getElementById('task-form');
    const taskType = form.querySelector('#task-type').value;
    const subtask = form.querySelector('#subtask').value;
    
    if (!taskType || !subtask) {
        showError('작업 유형과 상세 작업을 선택해주세요.');
        return;
    }

    // 파라미터 수집 최적화
    const parameters = {};
    const paramInputs = form.querySelectorAll('#parameters-container input');
    let hasEmptyRequired = false;

    for (const input of paramInputs) {
        if (input.required && !input.value.trim()) {
            hasEmptyRequired = true;
            input.classList.add('is-invalid');
        } else {
            input.classList.remove('is-invalid');
            if (input.value.trim()) {
                parameters[input.name] = input.value.trim();
            }
        }
    }

    if (hasEmptyRequired) {
        showError('필수 파라미터를 모두 입력해주세요.');
        return;
    }

    const requestData = {
        device_id: selectedDevice.id,
        task_type: taskType,
        subtask: subtask,
        parameters: parameters
    };

    try {
        showLoading();
        
        // 네트워크 요청 최적화
        const response = await fetch('/api/config/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showSuccess('작업이 추가되었습니다.');
            
            // 폼 초기화
            form.reset();
            document.querySelector('#task-form button[type="submit"]').disabled = true;
            document.getElementById('parameters-container').innerHTML = '';
            document.getElementById('subtask').innerHTML = '<option value="">상세 작업을 선택하세요</option>';
            
            // 작업 목록 갱신
            await loadTasks(selectedDevice.id);
        } else {
            showError(data.message || '작업 추가에 실패했습니다.');
        }
    } catch (error) {
        console.error('Error adding task:', error);
        showError('작업 추가에 실패했습니다.');
    } finally {
        hideLoading();
    }
}

// 작업 삭제
async function deleteTask(deviceId, taskIndex) {
    if (!confirm('이 작업을 삭제하시겠습니까?')) {
        return;
    }

    try {
        showLoading();
        const response = await fetch(`/api/config/tasks/${deviceId}/${taskIndex}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showSuccess('작업이 삭제되었습니다.');
            loadTasks(deviceId);
        } else {
            showError(data.message || '작업 삭제에 실패했습니다.');
        }
    } catch (error) {
        showError('작업 삭제에 실패했습니다.');
        console.error('Error deleting task:', error);
    } finally {
        hideLoading();
    }
}

// 상태 뱃지 색상 반환
function getStatusBadgeColor(status) {
    const colors = {
        'pending': 'warning',
        'running': 'info',
        'completed': 'success',
        'failed': 'danger'
    };
    return colors[status] || 'secondary';
}

// 상태 텍스트 반환
function getStatusText(status) {
    const texts = {
        'pending': '대기중',
        'running': '실행중',
        'completed': '완료',
        'failed': '실패'
    };
    return texts[status] || status;
}

// 유틸리티 함수
function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showError(message) {
    const toast = document.getElementById('toast');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    
    toastTitle.textContent = '오류';
    toastMessage.textContent = message;
    toastTitle.classList.add('text-danger');
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

function showSuccess(message) {
    const toast = document.getElementById('toast');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    
    toastTitle.textContent = '성공';
    toastMessage.textContent = message;
    toastTitle.classList.remove('text-danger');
    toastTitle.classList.add('text-success');
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}
