// 전역 변수
let devices = [];
let selectedDevice = null;
let taskTypes = {};
let subtasks = {};

// 이벤트 리스너 관리를 위한 Map
const eventListenerMap = new Map();

// 선택된 작업 유형과 상세 작업을 저장할 객체
const selectedTasks = new Map();

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
    
    // 브라우저 캐시 및 로컬 스토리지 초기화
    clearCacheAndLocalStorage();
    
    initializeUI();
    loadInitialData();
});

// 브라우저 캐시 및 로컬 스토리지 초기화
function clearCacheAndLocalStorage() {
    console.log('브라우저 캐시 및 로컬 스토리지 초기화');
    
    // 로컬 스토리지 초기화
    localStorage.clear();
    
    // 세션 스토리지 초기화
    sessionStorage.clear();
    
    // 작업 유형 및 상세 작업 초기화
    selectedTasks.clear();
    
    console.log('캐시 및 스토리지 초기화 완료');
}

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

    if (devices.length === 0) {
        deviceList.innerHTML = `
            <div class="list-group-item text-center text-muted py-5">
                <i class="bi bi-inbox-fill fs-2 d-block mb-2"></i>
                <p class="mb-0">등록된 장비가 없습니다</p>
            </div>
        `;
        return;
    }

    deviceList.innerHTML = devices.map(device => `
        <a href="#" class="list-group-item list-group-item-action" data-device-id="${device.id}">
            <div class="d-flex w-100 justify-content-between align-items-center">
                <div>
                    <h6 class="mb-1">${device.name}</h6>
                    <small class="text-muted d-block">${device.ip || '아이피 미지정'}</small>
                </div>
                <span class="badge bg-light text-dark">${device.vendor || '벤더 미지정'}</span>
            </div>
        </a>
    `).join('');

    // 장비 선택 이벤트 리스너는 한 번만 등록
    const items = deviceList.querySelectorAll('.list-group-item');
    items.forEach(item => {
        const deviceId = item.dataset.deviceId;
        item.onclick = (e) => {
            e.preventDefault();
            selectDevice(deviceId);
        };
    });

    console.log('장비 목록 표시 완료');
}

// 작업 유형 목록 로드
async function loadTaskTypes() {
    try {
        console.log('작업 유형 로딩 시작');
        
        // 기존 localStorage 데이터 초기화
        localStorage.removeItem('taskTypes');
        
        // 첫 번째로 작업 유형 테이블 초기화 요청 (reset=true)
        const timestamp = new Date().getTime();
        console.log('작업 유형 테이블 초기화 요청');
        const resetResponse = await fetch(`/config/api/task-types?reset=true&_=${timestamp}`, {
            cache: 'no-store',
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        });
        
        if (!resetResponse.ok) {
            console.warn('작업 유형 테이블 초기화 실패, 정상 로드 시도');
        } else {
            const resetData = await resetResponse.json();
            console.log('작업 유형 테이블 초기화 응답:', resetData);
        }
        
        // 작업 유형 데이터 로드 (이름만 요청)
        console.log('작업 유형 데이터 로드 요청');
        const response = await fetch(`/config/api/task-types?format=names_only&_=${timestamp}`, {
            cache: 'no-store',
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        let taskTypes = await response.json();
        console.log('받은 작업 유형 목록:', taskTypes);
        
        // 작업 유형이 객체 배열인 경우 이름만 추출
        if (Array.isArray(taskTypes) && taskTypes.length > 0 && typeof taskTypes[0] === 'object') {
            taskTypes = taskTypes.map(type => type.name || type);
        }
        
        // 작업 유형이 비어있으면 오류 표시
        if (!Array.isArray(taskTypes) || taskTypes.length === 0) {
            console.error('작업 유형 목록이 비어있거나 유효하지 않음:', taskTypes);
            showToast('작업 유형 목록을 불러오는데 실패했습니다', 'error');
            return;
        }
        
        const container = document.getElementById('task-type-container');
        if (!container) return;

        container.innerHTML = taskTypes.map(type => `
            <div class="form-check mb-2">
                <input class="form-check-input task-type-checkbox" type="checkbox" 
                       id="task-type-${type}" value="${type}">
                <label class="form-check-label" for="task-type-${type}">
                    ${type}
                </label>
            </div>
        `).join('');

        // 작업 유형 체크박스 이벤트 리스너 등록
        document.querySelectorAll('.task-type-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', handleTaskTypeChange);
        });
    } catch (error) {
        console.error('작업 유형을 불러오는 중 오류 발생:', error);
        showToast('작업 유형을 불러오는데 실패했습니다', 'error');
    }
}

// 작업 유형 선택 변경 처리
async function handleTaskTypeChange(e) {
    const taskType = e.target.value;
    const isChecked = e.target.checked;
    
    if (isChecked) {
        // 작업 유형이 선택되면 해당 상세 작업 목록 로드
        await loadSubtasks(taskType);
    } else {
        // 작업 유형이 해제되면 해당 상세 작업 제거
        selectedTasks.delete(taskType);
        updateSubtaskContainer(taskType);
    }
    
    updateGenerateScriptButton();
}

// 상세 작업 목록 로드
async function loadSubtasks(taskType) {
    console.log('상세 작업 로드 시작:', taskType);
    
    // 문자열 검증
    const safeTaskType = String(taskType || '');
    if (!safeTaskType) {
        console.error('작업 유형이 지정되지 않았습니다');
        return;
    }
    
    // 작업 유형 매핑 테이블
    const taskTypeMapping = {
        'VLAN 관리': 'VLAN 생성/삭제',
        '포트 설정': '인터페이스 설정',
        '인터페이스 구성': '인터페이스 설정',
        'VLAN 설정': 'VLAN 생성/삭제', 
        '보안': '보안 설정',
        '라우팅': '라우팅 설정',
        'SNMP': 'SNMP 설정'
    };
    
    // 작업 유형 매핑
    let mappedTaskType = safeTaskType;
    if (taskTypeMapping[safeTaskType]) {
        console.log(`${safeTaskType}를 ${taskTypeMapping[safeTaskType]}(으)로 매핑합니다.`);
        mappedTaskType = taskTypeMapping[safeTaskType];
    }
    
    try {
        console.log(`상세 작업 API 요청: /api/subtasks/${encodeURIComponent(mappedTaskType)}`);
        const response = await fetch(`/api/subtasks/${encodeURIComponent(mappedTaskType)}`);
        
        if (!response.ok) {
            console.error(`상세 작업 API 응답 오류: ${response.status} ${response.statusText}`);
            
            // 백업 접근 방법: '인터페이스 설정'으로 시도
            if (mappedTaskType !== '인터페이스 설정') {
                console.warn(`${mappedTaskType} 상세 작업 로드 실패, '인터페이스 설정'으로 시도...`);
                
                const backupResponse = await fetch(`/api/subtasks/인터페이스 설정`);
                if (backupResponse.ok) {
                    const backupData = await backupResponse.json();
                    console.log('백업 방법으로 받은 상세 작업:', backupData);
                    
                    // 이름만 추출하여 저장
                    if (selectedTasks.has(safeTaskType)) {
                        const taskData = selectedTasks.get(safeTaskType);
                        taskData.subtasks = extractSubtaskNames(backupData);
                    }
                    
                    updateSubtaskContainer(safeTaskType);
                    showToast(`${safeTaskType}의 상세 작업을 '인터페이스 설정'으로 대체했습니다.`, 'warning');
                    return;
                }
            }
            
            // 모든 백업 시도 실패
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('받은 상세 작업:', data);
        
        // 작업 데이터 저장 (이름만 추출)
        if (selectedTasks.has(safeTaskType)) {
            const taskData = selectedTasks.get(safeTaskType);
            taskData.subtasks = extractSubtaskNames(data);
        }
        
        updateSubtaskContainer(safeTaskType);
    } catch (error) {
        console.error(`${safeTaskType}의 상세 작업 로드 실패:`, error);
        showToast(`${safeTaskType}의 상세 작업을 불러오는데 실패했습니다.`, 'error');
    }
}

// 자세한 작업에서 이름만 추출하는 함수
function extractSubtaskNames(subtasks) {
    if (!subtasks || !Array.isArray(subtasks)) {
        console.error('상세 작업 목록이 유효하지 않습니다:', subtasks);
        return [];
    }
    
    return subtasks.map(subtask => {
        if (typeof subtask === 'string') {
            return subtask;
        } else if (typeof subtask === 'object' && subtask !== null) {
            return subtask.name || String(subtask);
        } else {
            return String(subtask);
        }
    }).filter(name => name && name !== '[object Object]');
}

// 상세 작업 목록 컨테이너 업데이트
function updateSubtaskContainer(taskType) {
    console.log('상세 작업 컨테이너 업데이트:', taskType);
    
    // 문자열 검증
    const safeTaskType = String(taskType || '');
    if (!safeTaskType) {
        console.error('작업 유형이 유효하지 않습니다');
        return;
    }
    
    // 작업 데이터 확인
    if (!selectedTasks.has(safeTaskType)) {
        console.error(`작업 유형 ${safeTaskType}에 대한 데이터가 없습니다`);
        return;
    }
    
    const taskData = selectedTasks.get(safeTaskType);
    const { subtasks = [], selected = new Set() } = taskData;
    
    // 상세 작업 컨테이너 찾기
    const container = document.getElementById(`subtasks-${safeTaskType}`);
    if (!container) {
        console.error(`작업 유형 ${safeTaskType}의 상세 작업 컨테이너를 찾을 수 없습니다`);
        return;
    }
    
    // 기존 내용 지우기
    container.innerHTML = '';
    
    // 상세 작업이 없는 경우 메시지 표시
    if (subtasks.length === 0) {
        container.innerHTML = '<p class="text-muted">사용 가능한 상세 작업이 없습니다.</p>';
        return;
    }
    
    // 상세 작업 체크박스 생성
    subtasks.forEach(subtask => {
        // 문자열 확인
        const subtaskName = typeof subtask === 'object' && subtask.name ? 
            String(subtask.name) : String(subtask);
        
        // 체크박스 생성
        const div = document.createElement('div');
        div.className = 'form-check mb-2';
        
        const input = document.createElement('input');
        input.className = 'form-check-input subtask-checkbox';
        input.type = 'checkbox';
        input.id = `subtask-${safeTaskType}-${subtaskName}`;
        input.checked = selected.has(subtaskName);
        input.value = subtaskName;
        input.dataset.taskType = safeTaskType;
        input.dataset.subtaskName = subtaskName;
        input.addEventListener('change', handleSubtaskChange);
        
        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = input.id;
        label.textContent = subtaskName;
        
        div.appendChild(input);
        div.appendChild(label);
        container.appendChild(div);
    });
}

// 상세 작업 선택 변경 처리
async function handleSubtaskChange(e) {
    // 항상 문자열 데이터만 사용
    const taskType = String(e.target.dataset.taskType || '');
    const subtaskName = String(e.target.dataset.subtaskName || e.target.value || '');
    const isChecked = e.target.checked;
    
    console.log('상세 작업 선택 변경:', taskType, subtaskName, isChecked);
    console.log('체크박스 데이터:', {
        id: e.target.id,
        value: e.target.value, 
        dataset: e.target.dataset,
        type: typeof subtaskName
    });
    
    if (!taskType) {
        console.error('작업 유형이 누락되었습니다.');
        return;
    }
    
    if (!subtaskName) {
        console.error('상세 작업명이 누락되었습니다.');
        return;
    }
    
    if (subtaskName === '[object Object]') {
        console.error('잘못된 상세 작업명(객체)이 전달되었습니다.');
        showToast('상세 작업 이름이 올바르지 않습니다.', 'error');
        return;
    }
    
    if (!selectedTasks.has(taskType)) {
        console.error(`작업 유형 ${taskType}에 대한 데이터가 없습니다.`);
        return;
    }
    
    const taskData = selectedTasks.get(taskType);
    if (isChecked) {
        taskData.selected.add(subtaskName);
        console.log(`loadParameters 호출: ${taskType}/${subtaskName} (${typeof taskType}/${typeof subtaskName})`);
        await loadParameters(taskType, subtaskName);
    } else {
        taskData.selected.delete(subtaskName);
        removeParameters(taskType, subtaskName);
    }
    
    updateGenerateScriptButton();
}

// 파라미터 로드
async function loadParameters(taskType, subtaskName) {
    console.log(`파라미터 로드: ${taskType}/${subtaskName} (${typeof taskType}/${typeof subtaskName})`);
    
    // 문자열 검증
    const safeTaskType = String(taskType || '');
    const safeSubtaskName = String(subtaskName || '');
    
    if (!safeTaskType || !safeSubtaskName) {
        console.error('파라미터 로드 실패: 작업 유형 또는 상세 작업명이 유효하지 않습니다', {
            taskType: safeTaskType,
            subtaskName: safeSubtaskName
        });
        return;
    }
    
    try {
        // API 요청에서 문자열 사용
        const response = await fetch(`/api/parameters/${safeTaskType}/${safeSubtaskName}`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: '서버 응답 오류' }));
            console.error(`파라미터 로드 실패: ${errorData.message || '서버 오류'}`, response.status);
            return;
        }
        
        const data = await response.json();
        console.log('로드된 파라미터:', data);
        
        if (!data || !Array.isArray(data.parameters)) {
            console.error('파라미터 데이터가 올바르지 않습니다', data);
            return;
        }
        
        // 파라미터 데이터 저장
        const taskData = selectedTasks.get(safeTaskType);
        if (taskData && taskData.parameters) {
            taskData.parameters[safeSubtaskName] = data.parameters;
        }
        
        // 모든 장치에 파라미터 필드 추가
        addParameterFieldsToDevices(safeTaskType, safeSubtaskName, data.parameters);
    } catch (error) {
        console.error('파라미터 로드 중 오류 발생:', error);
        showToast('파라미터 로드 중 오류가 발생했습니다.', 'error');
    }
}

// 모든 장비에 파라미터 필드 추가
function addParameterFieldsToDevices(taskType, subtaskName, parameters) {
    console.log(`파라미터 필드 추가: ${taskType}/${subtaskName}`, parameters);
    
    if (!parameters || !Array.isArray(parameters)) {
        console.error('유효하지 않은 파라미터 데이터:', parameters);
        return;
    }
    
    const paramContainer = document.getElementById(`parameters-${taskType}-${subtaskName}`);
    if (!paramContainer) {
        console.error(`파라미터 컨테이너를 찾을 수 없음: parameters-${taskType}-${subtaskName}`);
        return;
    }
    
    // 기존 폼 초기화
    paramContainer.innerHTML = '';
    
    // 파라미터가 없으면 안내 메시지 표시
    if (parameters.length === 0) {
        paramContainer.innerHTML = '<p class="text-muted">이 작업에 필요한 파라미터가 없습니다.</p>';
        return;
    }
    
    // 폼 생성
    parameters.forEach(param => {
        const formGroup = document.createElement('div');
        formGroup.className = 'mb-3';
        
        const label = document.createElement('label');
        label.className = 'form-label';
        label.htmlFor = `param-${taskType}-${subtaskName}-${param.name}`;
        label.textContent = param.label || param.name;
        
        const input = document.createElement('input');
        input.type = param.type || 'text';
        input.className = 'form-control parameter-input';
        input.id = `param-${taskType}-${subtaskName}-${param.name}`;
        input.name = param.name;
        input.dataset.taskType = taskType;
        input.dataset.subtaskName = subtaskName;
        
        if (param.required) {
            input.required = true;
            label.innerHTML += ' <span class="text-danger">*</span>';
        }
        
        if (param.placeholder) {
            input.placeholder = param.placeholder;
        }
        
        if (param.min !== undefined) {
            input.min = param.min;
        }
        
        if (param.max !== undefined) {
            input.max = param.max;
        }
        
        formGroup.appendChild(label);
        formGroup.appendChild(input);
        paramContainer.appendChild(formGroup);
    });
}

// 파라미터 폼 생성 함수 분리
function createParameterForm(taskType, subtask, parameters) {
    console.log('파라미터 폼 생성 시작:', taskType, subtask);
    console.log('파라미터 데이터:', JSON.stringify(parameters));
    
    const container = document.getElementById('parameters-container');
    if (!container) {
        console.error('파라미터 컨테이너 엘리먼트를 찾을 수 없음');
        return;
    }

    // 이미 존재하는 섹션 삭제 (중복 방지)
    const sectionId = `params-${taskType}-${subtask}`.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9\-_]/g, '');
    const existingSection = document.getElementById(sectionId);
    if (existingSection) {
        console.log('기존 파라미터 섹션 제거:', sectionId);
        existingSection.remove();
    }

    const paramSection = document.createElement('div');
    paramSection.id = sectionId;
    paramSection.className = 'mb-4 border p-3 rounded bg-light';
    
    try {
        let paramHtml = `<h6 class="border-bottom pb-2 mb-3">${taskType} - ${subtask}</h6>`;
        
        // 파라미터 배열을 순회하면서 HTML 생성
        for (const param of parameters) {
            // 파라미터가 객체인지 확인
            if (!param || typeof param !== 'object') {
                console.warn('유효하지 않은 파라미터 항목:', param);
                continue;
            }
            
            // 필수 필드 확인
            const paramName = param.name || '';
            if (!paramName) {
                console.warn('파라미터 이름이 없는 항목:', param);
                continue;
            }
            
            // ID 생성 및 특수문자 처리
            const paramId = `param-${taskType}-${subtask}-${paramName}`
                .replace(/\s+/g, '-')
                .replace(/[^a-zA-Z0-9\-_]/g, '');
            
            // 파라미터 레이블 결정
            const label = param.label || paramName;
            const required = param.required === true;
            
            // 정규식 패턴 처리
            let patternAttr = '';
            if (param.pattern) {
                try {
                    // 정규식 유효성 검사
                    new RegExp(param.pattern);
                    // 하이픈이 문자 클래스 끝에 오도록 패턴 수정
                    const escapedPattern = param.pattern
                        .replace(/\\/g, '\\\\')
                        .replace(/"/g, '\\"')
                        .replace(/\[([^\]]*)-([^\]]*)\]/g, '[$1\\-$2]');
                    patternAttr = `pattern="${escapedPattern}"`;
                } catch (e) {
                    console.warn('잘못된 정규식 패턴:', param.pattern);
                    patternAttr = '';
                }
            }
            
            // 파라미터 입력 필드 HTML 생성
            paramHtml += `
                <div class="mb-3">
                    <label for="${paramId}" class="form-label">
                        ${label}${required ? ' <span class="text-danger">*</span>' : ''}
                    </label>`;
            
            // select 필드 또는 input 필드 생성
            if (param.type === 'select' && Array.isArray(param.options)) {
                paramHtml += `
                    <select class="form-select" 
                            id="${paramId}"
                            name="${paramName}"
                            data-param-name="${paramName}"
                            ${required ? 'required' : ''}>
                        <option value="">선택하세요</option>
                        ${param.options.map(opt => {
                            const optValue = typeof opt === 'object' ? (opt.value || '') : opt;
                            const optLabel = typeof opt === 'object' ? (opt.label || optValue) : opt;
                            return `<option value="${optValue}">${optLabel}</option>`;
                        }).join('')}
                    </select>`;
            } else {
                // 기본적으로 text 입력 필드
                const inputType = param.type || 'text';
                paramHtml += `
                    <input type="${inputType}"
                           class="form-control"
                           id="${paramId}"
                           name="${paramName}"
                           data-param-name="${paramName}"
                           placeholder="${param.placeholder || ''}"
                           ${patternAttr}
                           ${required ? 'required' : ''}>`;
            }
            
            // 설명 추가
            if (param.description) {
                paramHtml += `
                    <div class="form-text">
                        ${param.description}
                        ${patternAttr ? `<br><small class="text-muted">형식: ${param.pattern}</small>` : ''}
                    </div>`;
            }
            
            paramHtml += `</div>`;
        }
        
        // 생성된 HTML을 섹션에 설정
        paramSection.innerHTML = paramHtml;
    } catch (error) {
        console.error('파라미터 폼 HTML 생성 오류:', error);
        paramSection.innerHTML = `
            <div class="alert alert-danger">
                <strong>오류:</strong> 파라미터 폼을 생성하는 중 오류가 발생했습니다.
                <br>${error.message}
            </div>`;
    }
    
    // 섹션을 컨테이너에 추가
    container.appendChild(paramSection);
    console.log('파라미터 폼 생성 완료:', sectionId);
    
    // 입력값 유효성 검사 이벤트 리스너 추가
    try {
        const inputs = paramSection.querySelectorAll('input[pattern]');
        inputs.forEach(input => {
            input.addEventListener('input', (e) => {
                const pattern = new RegExp(input.pattern);
                if (input.value && !pattern.test(input.value)) {
                    input.classList.add('is-invalid');
                    if (!input.nextElementSibling?.classList.contains('invalid-feedback')) {
                        const feedback = document.createElement('div');
                        feedback.className = 'invalid-feedback';
                        feedback.textContent = `올바른 형식으로 입력해주세요. (${input.pattern})`;
                        input.parentNode.insertBefore(feedback, input.nextSibling);
                    }
                } else {
                    input.classList.remove('is-invalid');
                    const feedback = input.nextElementSibling;
                    if (feedback?.classList.contains('invalid-feedback')) {
                        feedback.remove();
                    }
                }
            });
        });
    } catch (error) {
        console.error('이벤트 리스너 등록 중 오류:', error);
    }
}

// 파라미터 제거
function removeParameters(taskType, subtaskName) {
    console.log(`파라미터 제거: ${taskType}/${subtaskName}`);
    
    // 문자열 검증
    const safeTaskType = String(taskType || '');
    const safeSubtaskName = String(subtaskName || '');
    
    if (!safeTaskType || !safeSubtaskName) {
        console.error('작업 유형 또는 상세 작업명이 유효하지 않습니다');
        return;
    }
    
    // 작업 데이터에서 제거
    if (selectedTasks.has(safeTaskType)) {
        const taskData = selectedTasks.get(safeTaskType);
        if (taskData.parameters) {
            delete taskData.parameters[safeSubtaskName];
        }
    }
    
    // DOM에서 파라미터 컨테이너 초기화
    const paramContainer = document.getElementById(`parameters-${safeTaskType}-${safeSubtaskName}`);
    if (paramContainer) {
        paramContainer.innerHTML = '';
    }
}

// 스크립트 생성 버튼 상태 업데이트
function updateGenerateScriptButton() {
    const btn = document.getElementById('generateScriptBtn');
    if (!btn) return;
    
    let hasSelectedSubtasks = false;
    for (const [_, data] of selectedTasks.entries()) {
        if (data.selected.size > 0) {
            hasSelectedSubtasks = true;
            break;
        }
    }
    
    btn.disabled = !hasSelectedSubtasks;
}

// 스크립트 미리보기 업데이트
function updateScriptPreview(script) {
    const preview = document.getElementById('script-preview');
    if (!preview) return;

    if (!script) {
        preview.innerHTML = '<div class="text-muted">스크립트가 생성되지 않았습니다.</div>';
        return;
    }

    preview.textContent = script;
}

// 스크립트 복사 기능
function copyScript() {
    const scriptContent = document.getElementById('scriptContent');
    if (!scriptContent) return;

    const text = scriptContent.textContent;
    if (!text) {
        showToast('복사할 스크립트가 없습니다', 'warning');
        return;
    }

    navigator.clipboard.writeText(text)
        .then(() => showToast('스크립트가 클립보드에 복사되었습니다', 'success'))
        .catch(() => showToast('스크립트 복사에 실패했습니다', 'error'));
}

// 작업 목록 표시 개선
function displayTasks(tasks) {
    const taskList = document.getElementById('task-list');
    if (!Array.isArray(tasks)) {
        console.error('Invalid tasks data:', tasks);
        return;
    }

    if (tasks.length === 0) {
        taskList.innerHTML = `
            <div class="list-group-item text-center text-muted py-5">
                <i class="bi bi-inbox-fill fs-2 mb-2"></i>
                <p class="mb-0">등록된 작업이 없습니다</p>
            </div>
        `;
        return;
    }

    taskList.innerHTML = tasks.map((task, index) => `
        <div class="list-group-item">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <div class="d-flex align-items-center mb-1">
                        <span class="badge bg-${getStatusBadgeColor(task.status)} me-2">
                            ${getStatusText(task.status)}
                        </span>
                        <h6 class="mb-0">${getTaskTypeLabel(task.task_type)}</h6>
                    </div>
                    <p class="mb-1 text-muted small">${getSubtaskLabel(task.task_type, task.subtask)}</p>
                </div>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteTask('${task.device_id}', ${index})">
                    <i class="bi bi-trash me-1"></i>삭제
                </button>
            </div>
            ${renderParameters(task.parameters)}
        </div>
    `).join('');
}

// 파라미터 렌더링 개선
function renderParameters(parameters) {
    if (!parameters || Object.keys(parameters).length === 0) {
        return '';
    }

    return `
        <div class="mt-2 pt-2 border-top">
            <div class="row g-2">
                ${Object.entries(parameters).map(([key, value]) => `
                    <div class="col-md-6">
                        <div class="d-flex align-items-center">
                            <span class="badge bg-light text-dark me-2">${getParameterLabel(key)}</span>
                            <span class="text-break">${value}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// 작업 추가
async function addTask() {
    const form = document.getElementById('task-form');
    if (!form || !validateParameters()) return;
    
    const deviceId = selectedDevice.id;
    if (!deviceId) {
        showError('장비를 선택해주세요.');
        return;
    }
    
    const taskType = document.getElementById('task-type').value;
    const subtask = document.getElementById('subtask').value;
    
    if (!taskType || !subtask) {
        showError('작업 유형과 상세 작업을 선택해주세요.');
        return;
    }
    
    // 파라미터 수집
    const parameters = {};
    const paramInputs = document.querySelectorAll('#parameters-container .form-control');
    
    paramInputs.forEach(input => {
        if (input.id.startsWith('param-')) {
            const paramName = input.id.replace('param-', '');
            parameters[paramName] = input.value;
        }
    });
    
    const requestData = {
        device_id: deviceId,
        task_type: taskType,
        subtask: subtask,
        parameters: parameters
    };

    try {
        showLoading();
        
        // 네트워크 요청 최적화
        const response = await fetch('/config/api/tasks', {
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
        console.error('작업 추가 중 오류 발생:', error);
        showError('서버 통신 중 오류가 발생했습니다.');
    } finally {
        hideLoading();
    }
}

// 작업 삭제
async function deleteTask(deviceId, taskIndex) {
    if (!confirm('정말로 이 작업을 삭제하시겠습니까?')) return;
    
    try {
        showLoading();
        
        const response = await fetch(`/config/api/tasks/${deviceId}/${taskIndex}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showSuccess('작업이 삭제되었습니다.');
            await loadTasks(deviceId);
        } else {
            showError(data.message || '작업 삭제에 실패했습니다.');
        }
    } catch (error) {
        console.error('작업 삭제 중 오류 발생:', error);
        showError('서버 통신 중 오류가 발생했습니다.');
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

// validateParameters 함수 개선
function validateParameters() {
    const container = document.getElementById('parameters-container');
    if (!container) return true;

    const inputs = container.querySelectorAll('input, select');
    let isValid = true;
    
    inputs.forEach(input => {
        // 필수 입력 검사
        if (input.required && !input.value.trim()) {
            isValid = false;
            input.classList.add('is-invalid');
            showInvalidFeedback(input, '이 필드는 필수입니다.');
            return;
        }

        // 패턴 검사
        if (input.pattern && input.value.trim()) {
            try {
                const regex = new RegExp(input.pattern);
                if (!regex.test(input.value.trim())) {
                    isValid = false;
                    input.classList.add('is-invalid');
                    showInvalidFeedback(input, `올바른 형식으로 입력해주세요. (${input.pattern})`);
                    return;
                }
            } catch (e) {
                console.warn('잘못된 정규식 패턴:', input.pattern);
            }
        }

        input.classList.remove('is-invalid');
        removeInvalidFeedback(input);
    });
    
    return isValid;
}

// 유효성 검사 피드백 표시
function showInvalidFeedback(input, message) {
    if (!input.nextElementSibling?.classList.contains('invalid-feedback')) {
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        input.parentNode.insertBefore(feedback, input.nextSibling);
    }
}

// 유효성 검사 피드백 제거
function removeInvalidFeedback(input) {
    const feedback = input.nextElementSibling;
    if (feedback?.classList.contains('invalid-feedback')) {
        feedback.remove();
    }
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

// 장비 선택
function selectDevice(deviceId) {
    console.log('장비 선택:', deviceId);
    
    if (!deviceId) {
        console.error('장비 ID가 제공되지 않았습니다');
        return;
    }

    const device = devices.find(d => d.id === deviceId);
    if (!device) {
        console.error('선택한 장비를 찾을 수 없습니다:', deviceId);
        showToast('선택한 장비를 찾을 수 없습니다', 'error');
        return;
    }

    selectedDevice = device;
    console.log('선택된 장비:', selectedDevice);

    // UI 업데이트
    updateDeviceSelection(deviceId);
    
    // 작업 유형 선택 활성화
    const taskTypeContainer = document.getElementById('task-type-container');
    if (taskTypeContainer) {
        const checkboxes = taskTypeContainer.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => checkbox.disabled = false);
    }
}

// 장비 선택 UI 업데이트
function updateDeviceSelection(deviceId) {
    const deviceItems = document.querySelectorAll('#device-list .list-group-item');
    deviceItems.forEach(item => {
        if (item.dataset.deviceId === deviceId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}
