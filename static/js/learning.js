// 전역 변수
let currentCommand = null;
let templates = {};

// DOM 로드 완료 후 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeUI();
    loadTemplates();
    loadCommands();
});

// UI 초기화
function initializeUI() {
    // 이벤트 리스너 등록
    document.getElementById('vendor').addEventListener('change', handleVendorChange);
    document.getElementById('device-type').addEventListener('change', handleDeviceTypeChange);
    document.getElementById('task-type').addEventListener('change', handleTaskTypeChange);
    document.getElementById('command-form').addEventListener('submit', handleSubmit);
    document.getElementById('clearBtn').addEventListener('click', clearForm);
}

// 템플릿 로드
async function loadTemplates() {
    try {
        const response = await fetch('/api/learning/templates');
        if (!response.ok) throw new Error('템플릿 로드 실패');
        templates = await response.json();
    } catch (error) {
        showToast('오류', '템플릿 로드 중 오류가 발생했습니다.', 'error');
    }
}

// CLI 명령어 목록 로드
async function loadCommands() {
    try {
        const response = await fetch('/api/learning/commands');
        if (!response.ok) throw new Error('명령어 목록 로드 실패');
        const commands = await response.json();
        displayCommands(commands);
    } catch (error) {
        showToast('오류', '명령어 목록 로드 중 오류가 발생했습니다.', 'error');
    }
}

// 명령어 목록 표시
function displayCommands(commands) {
    const commandList = document.getElementById('command-list');
    commandList.innerHTML = '';
    
    commands.forEach(cmd => {
        const item = document.createElement('a');
        item.className = 'list-group-item list-group-item-action';
        item.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${cmd.vendor} - ${cmd.task_type}</h6>
                <small>${new Date(cmd.created_at).toLocaleDateString()}</small>
            </div>
            <p class="mb-1">${cmd.subtask}</p>
        `;
        item.addEventListener('click', () => loadCommand(cmd));
        commandList.appendChild(item);
    });
}

// 명령어 로드
function loadCommand(command) {
    currentCommand = command;
    
    // 폼 필드 채우기
    document.getElementById('vendor').value = command.vendor;
    document.getElementById('device-type').value = command.device_type;
    document.getElementById('task-type').value = command.task_type;
    document.getElementById('subtask').value = command.subtask;
    document.getElementById('command').value = command.command;
    document.getElementById('description').value = command.description || '';
    
    // 파라미터 표시
    displayParameters(command.parameters || {});
}

// 벤더 변경 처리
function handleVendorChange(event) {
    const vendor = event.target.value;
    if (!vendor) return;
    
    // 장비 유형 옵션 업데이트
    const deviceTypeSelect = document.getElementById('device-type');
    deviceTypeSelect.innerHTML = '<option value="">선택하세요</option>';
    
    // 작업 유형 옵션 업데이트
    const taskTypeSelect = document.getElementById('task-type');
    taskTypeSelect.innerHTML = '<option value="">선택하세요</option>';
    
    if (templates[vendor]) {
        Object.entries(templates[vendor]).forEach(([key, value]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = value.name;
            taskTypeSelect.appendChild(option);
        });
    }
}

// 장비 유형 변경 처리
function handleDeviceTypeChange(event) {
    // 필요한 경우 장비 유형별 추가 로직 구현
}

// 작업 유형 변경 처리
function handleTaskTypeChange(event) {
    const vendor = document.getElementById('vendor').value;
    const taskType = event.target.value;
    
    if (!vendor || !taskType || !templates[vendor] || !templates[vendor][taskType]) {
        return;
    }
    
    const template = templates[vendor][taskType];
    displayParameters(template.parameters || {});
}

// 파라미터 표시
function displayParameters(parameters) {
    const container = document.getElementById('parameters-container');
    container.innerHTML = '';
    
    Object.entries(parameters).forEach(([key, value]) => {
        const div = document.createElement('div');
        div.className = 'mb-3';
        div.innerHTML = `
            <label class="form-label">${key}</label>
            <input type="text" class="form-control" name="${key}" value="${value}">
        `;
        container.appendChild(div);
    });
}

// 폼 제출 처리
async function handleSubmit(event) {
    event.preventDefault();
    
    const formData = {
        vendor: document.getElementById('vendor').value,
        device_type: document.getElementById('device-type').value,
        task_type: document.getElementById('task-type').value,
        subtask: document.getElementById('subtask').value,
        command: document.getElementById('command').value,
        description: document.getElementById('description').value,
        parameters: {}
    };
    
    // 파라미터 수집
    const parameterInputs = document.querySelectorAll('#parameters-container input');
    parameterInputs.forEach(input => {
        formData.parameters[input.name] = input.value;
    });
    
    try {
        const url = currentCommand 
            ? `/api/learning/commands/${currentCommand.id}`
            : '/api/learning/commands';
            
        const method = currentCommand ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) throw new Error('명령어 저장 실패');
        
        showToast('성공', '명령어가 저장되었습니다.', 'success');
        clearForm();
        loadCommands();
    } catch (error) {
        showToast('오류', '명령어 저장 중 오류가 발생했습니다.', 'error');
    }
}

// 폼 초기화
function clearForm() {
    currentCommand = null;
    document.getElementById('command-form').reset();
    document.getElementById('parameters-container').innerHTML = '';
}

// 토스트 메시지 표시
function showToast(title, message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    
    toastTitle.textContent = title;
    toastMessage.textContent = message;
    
    // 토스트 타입에 따른 스타일 설정
    toast.className = 'toast';
    toast.classList.add(`bg-${type}`);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}
