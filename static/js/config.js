// 전역 변수
let devices = [];
let selectedDevice = null;
let taskTypes = {};
let subtasks = {};

// 이벤트 리스너 관리를 위한 Map
const eventListenerMap = new Map();

// 이벤트 리스너 등록 함수
function addEventListenerOnce(element, eventType, handler) {
    if (!element) return;
    
    // 기존 리스너 제거
    const key = `${element.id}-${eventType}`;
    const oldHandler = eventListenerMap.get(key);
    if (oldHandler) {
        element.removeEventListener(eventType, oldHandler);
    }
    
    // 새 리스너 등록
    element.addEventListener(eventType, handler);
    eventListenerMap.set(key, handler);
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log('페이지 초기화 시작');
    initializeUI();
    loadInitialData();
});

// UI 초기화
function initializeUI() {
    console.log('UI 초기화');
    const taskType = document.getElementById('task-type');
    const subtask = document.getElementById('subtask');
    const generateScriptBtn = document.getElementById('generateScriptBtn');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const deviceList = document.getElementById('device-list');

    // disabled 설정
    if (taskType) taskType.disabled = true;
    if (subtask) subtask.disabled = true;
    if (generateScriptBtn) generateScriptBtn.disabled = true;
    if (addTaskBtn) addTaskBtn.disabled = true;

    // 작업 유형 변경 이벤트
    if (taskType) {
        taskType.onchange = async (e) => {
            const selectedType = e.target.value;
            if (selectedType) {
                await loadSubtasks(selectedType);
            } else {
                if (subtask) {
                    subtask.innerHTML = '<option value="">상세 작업을 선택하세요</option>';
                    subtask.disabled = true;
                }
            }
        };
    }

    // 상세 작업 변경 이벤트
    if (subtask) {
        subtask.onchange = async (e) => {
            const selectedSubtask = e.target.value;
            const selectedType = taskType?.value;
            if (selectedSubtask && selectedType) {
                await loadParameters(selectedType, selectedSubtask);
            }
        };
    }

    // 장비 목록 클릭 이벤트
    if (deviceList) {
        deviceList.onclick = (e) => {
            const deviceItem = e.target.closest('.list-group-item');
            if (deviceItem) {
                const deviceId = deviceItem.dataset.deviceId;
                selectDevice(deviceId);
            }
        };
    }
}

// 초기 데이터 로드
async function loadInitialData() {
    console.log('초기 데이터 로드 시작');
    try {
        await loadDevices();
        await loadTaskTypes();
    } catch (error) {
        console.error('초기 데이터 로드 중 오류:', error);
    }
}

// 장비 목록 로드
async function loadDevices() {
    console.log('장비 목록 로드 시작');
    try {
        showLoading();
        const response = await fetch('/api/devices');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('받은 장비 데이터 전체:', JSON.stringify(data, null, 2));
        
        // 데이터 구조 검증 및 변환
        let deviceList = [];
        if (data.devices) {
            deviceList = data.devices;
        } else if (data.status === 'success' && Array.isArray(data.data)) {
            deviceList = data.data;
        } else if (Array.isArray(data)) {
            deviceList = data;
        } else {
            console.error('예상치 못한 데이터 구조:', data);
            throw new Error('잘못된 장비 데이터 형식');
        }

        if (!Array.isArray(deviceList)) {
            console.error('장비 목록이 배열이 아닙니다:', deviceList);
            throw new Error('잘못된 장비 데이터 형식');
        }

        console.log('변환된 장비 목록:', deviceList);
        
        devices = deviceList.map(device => ({
            ...device,
            id: device.name // name을 id로 사용
        }));

        displayDevices();
        
        // 장비가 있으면 첫 번째 장비 자동 선택
        if (devices.length > 0) {
            selectDevice(devices[0].id);
        } else {
            console.log('장비 목록이 비어있습니다');
        }
    } catch (error) {
        console.error('장비 목록 로드 중 오류:', error);
        showToast('장비 목록을 불러오는데 실패했습니다', 'error');
    } finally {
        hideLoading();
    }
}

// 장비 목록 표시
function displayDevices() {
    console.log('장비 목록 표시 시작');
    const deviceList = document.getElementById('device-list');
    if (!deviceList) {
        console.error('장비 목록 컨테이너를 찾을 수 없습니다');
        return;
    }

    if (!Array.isArray(devices)) {
        console.error('장비 데이터가 배열이 아닙니다:', devices);
        return;
    }

    deviceList.innerHTML = devices.map(device => `
        <a href="#" class="list-group-item list-group-item-action" data-device-id="${device.name}">
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${device.name}</h6>
                <small>${device.vendor || '벤더 미지정'}</small>
            </div>
            <small class="text-muted">${device.ip}</small>
        </a>
    `).join('');

    // 장비 선택 이벤트 리스너 등록
    deviceList.querySelectorAll('.list-group-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const deviceId = item.dataset.deviceId;
            selectDevice(deviceId);
        });
    });

    console.log('장비 목록 표시 완료');
}

// 작업 유형 목록 로드
async function loadTaskTypes() {
    try {
        console.log('작업 유형 로딩 시작');
        const response = await fetch('/api/config/task-types');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const taskTypes = await response.json();
        console.log('받은 작업 유형:', taskTypes);
        
        const taskTypeSelect = document.getElementById('task-type');
        if (!taskTypeSelect) return;

        taskTypeSelect.innerHTML = '<option value="">작업 유형을 선택하세요</option>';
        
        taskTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            switch(type) {
                case '포트 설정':
                    option.title = '네트워크 포트 관련 설정을 수행합니다';
                    break;
                case 'VLAN 설정':
                    option.title = 'VLAN 생성 및 설정을 수행합니다';
                    break;
            }
            taskTypeSelect.appendChild(option);
        });

        // 이벤트 리스너 등록
        const key = 'taskType-change';
        if (!eventListenerMap.has(key)) {
            const handler = async (e) => {
                const selectedType = e.target.value;
                console.log('선택된 작업 유형:', selectedType);
                
                const subtaskSelect = document.getElementById('subtask');
                if (!subtaskSelect) return;

                if (selectedType) {
                    await loadSubtasks(selectedType);
                } else {
                    subtaskSelect.innerHTML = '<option value="">상세 작업을 선택하세요</option>';
                    subtaskSelect.disabled = true;
                    document.getElementById('parameters-container').innerHTML = '';
                }
            };
            taskTypeSelect.addEventListener('change', handler);
            eventListenerMap.set(key, handler);
        }
    } catch (error) {
        console.error('작업 유형을 불러오는 중 오류 발생:', error);
        showToast('작업 유형을 불러오는데 실패했습니다', 'error');
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
        console.log('상세 작업 로딩 시작:', taskType);
        const response = await fetch(`/api/config/subtasks/${encodeURIComponent(taskType)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const subtasks = await response.json();
        console.log('받은 상세 작업:', subtasks);
        
        const subtaskSelect = document.getElementById('subtask');
        if (!subtaskSelect) return;

        subtaskSelect.innerHTML = '<option value="">상세 작업을 선택하세요</option>';
        subtaskSelect.disabled = false;
        
        subtasks.forEach(subtask => {
            const option = document.createElement('option');
            option.value = subtask;
            option.textContent = subtask;
            switch(subtask) {
                case '포트 상태 설정':
                    option.title = '포트의 활성화/비활성화 상태를 설정합니다';
                    break;
                case 'VLAN 생성':
                    option.title = '새로운 VLAN을 생성하고 설정합니다';
                    break;
            }
            subtaskSelect.appendChild(option);
        });

        // 이벤트 리스너 등록
        const key = 'subtask-change';
        if (!eventListenerMap.has(key)) {
            const handler = async (e) => {
                const selectedSubtask = e.target.value;
                console.log('선택된 상세 작업:', selectedSubtask);
                
                if (selectedSubtask) {
                    await loadParameters(taskType, selectedSubtask);
                } else {
                    document.getElementById('parameters-container').innerHTML = '';
                }
            };
            subtaskSelect.addEventListener('change', handler);
            eventListenerMap.set(key, handler);
        }
    } catch (error) {
        console.error('상세 작업을 불러오는 중 오류 발생:', error);
        showToast('상세 작업을 불러오는데 실패했습니다', 'error');
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
        console.log('파라미터 로딩 시작:', taskType, subtask);
        const response = await fetch(`/api/config/parameters/${encodeURIComponent(taskType)}/${encodeURIComponent(subtask)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const parameters = await response.json();
        console.log('받은 파라미터:', parameters);
        
        const container = document.getElementById('parameters-container');
        if (!container) return;

        container.innerHTML = '';

        parameters.forEach(param => {
            const div = document.createElement('div');
            div.className = 'form-group mb-3';
            
            const label = document.createElement('label');
            label.textContent = param.name;
            if (param.required) {
                label.innerHTML += ' <span class="text-danger">*</span>';
            }
            
            let input;
            if (param.type === 'select') {
                input = document.createElement('select');
                input.className = 'form-control';
                param.options.forEach(option => {
                    const opt = document.createElement('option');
                    opt.value = option;
                    opt.textContent = option;
                    input.appendChild(opt);
                });
            } else {
                input = document.createElement('input');
                input.type = param.type || 'text';
                input.className = 'form-control';
                if (param.pattern) {
                    input.pattern = param.pattern;
                }
                if (param.placeholder) {
                    input.placeholder = param.placeholder;
                }
            }
            
            input.id = `param-${param.name}`;
            input.name = param.name;
            input.required = param.required;
            
            const helpText = document.createElement('small');
            helpText.className = 'form-text text-muted';
            helpText.textContent = param.description || '';

            div.appendChild(label);
            div.appendChild(input);
            div.appendChild(helpText);
            container.appendChild(div);
        });
    } catch (error) {
        console.error('파라미터를 불러오는 중 오류 발생:', error);
        showToast('파라미터를 불러오는데 실패했습니다', 'error');
    }
}

// 장비 선택
function selectDevice(deviceId) {
    console.log('장비 선택:', deviceId);
    console.log('현재 장비 목록:', devices);
    
    const device = devices.find(d => d.id === deviceId);
    if (!device) {
        console.error('선택한 장비를 찾을 수 없습니다:', deviceId);
        return;
    }

    selectedDevice = device;
    console.log('선택된 장비:', selectedDevice);
    
    // 선택된 장비 시각적 표시
    document.querySelectorAll('.list-group-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.deviceId === deviceId) {
            item.classList.add('active');
        }
    });

    // 작업 유형 선택 활성화
    const taskTypeSelect = document.getElementById('task-type');
    if (taskTypeSelect) {
        taskTypeSelect.disabled = false;
    }

    // 스크립트 생성 버튼 활성화
    const generateScriptBtn = document.getElementById('generateScriptBtn');
    if (generateScriptBtn) {
        generateScriptBtn.disabled = false;
    }

    // 작업 목록 로드
    loadTasks(deviceId);
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

// showToast 함수 수정
function showToast(message, type = 'error') {
    const toast = document.getElementById('toast');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    
    if (toast && toastTitle && toastMessage) {
        toastTitle.textContent = type === 'error' ? '오류' : '알림';
        toastMessage.textContent = message;
        toastTitle.className = type === 'error' ? 'text-danger' : 'text-success';
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
}

// validateParameters 함수 수정
function validateParameters() {
    const container = document.getElementById('parameters-container');
    if (!container) return true;

    const inputs = container.querySelectorAll('input, select');
    let isValid = true;
    
    inputs.forEach(input => {
        if (input.required && !input.value) {
            isValid = false;
            input.classList.add('is-invalid');
        } else {
            input.classList.remove('is-invalid');
        }
        
        if (input.pattern && input.value) {
            const regex = new RegExp(input.pattern);
            if (!regex.test(input.value)) {
                isValid = false;
                input.classList.add('is-invalid');
            }
        }
    });
    
    return isValid;
}

// 스크립트 생성 함수
async function generateScript() {
    try {
        // 선택된 장비 확인
        if (!selectedDevice) {
            showToast('장비를 선택해주세요', 'warning');
            return;
        }

        // 작업 목록 수집
        const taskList = document.querySelectorAll('.task-item');
        if (taskList.length === 0) {
            showToast('생성할 작업이 없습니다', 'warning');
            return;
        }

        // 작업 데이터 수집
        const tasks = Array.from(taskList).map(task => {
            const taskType = task.dataset.taskType;
            const subtask = task.dataset.subtask;
            const parameters = {};
            
            // 파라미터 수집
            task.querySelectorAll('input, select').forEach(input => {
                parameters[input.name] = input.value;
            });

            return {
                task_type: taskType,
                subtask: subtask,
                parameters: parameters
            };
        });

        // 서버로 데이터 전송
        const response = await fetch('/api/config/generate-script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                device_id: selectedDevice,
                tasks: tasks
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        // 스크립트 표시
        const scriptArea = document.getElementById('script-area');
        if (scriptArea) {
            scriptArea.value = result.script;
            scriptArea.style.display = 'block';
        }

        // 실행 버튼 활성화
        const executeBtn = document.getElementById('executeScriptBtn');
        if (executeBtn) {
            executeBtn.disabled = false;
        }

        showToast('스크립트가 생성되었습니다', 'success');
    } catch (error) {
        console.error('스크립트 생성 중 오류:', error);
        showToast('스크립트 생성 중 오류가 발생했습니다', 'error');
    }
}
