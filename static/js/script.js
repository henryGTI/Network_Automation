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
    // 상단에 오류 메시지 표시
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger alert-dismissible fade show';
    errorDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle-fill"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // 기존 오류 메시지 제거
    const existingError = document.querySelector('.alert-danger');
    if (existingError) {
        existingError.remove();
    }
    
    // 새 오류 메시지 추가
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(errorDiv, container.firstChild);
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

// 스크립트 보기
async function viewScript(deviceName) {
    try {
        const response = await fetch(`/api/devices/${deviceName}/script`);
        if (!response.ok) throw new Error('스크립트 로드 실패');
        
        const scriptContent = await response.text();
        document.getElementById('scriptContent').textContent = scriptContent;
        
        $('#scriptViewModal').modal('show');
    } catch (error) {
        console.error('스크립트 보기 중 오류:', error);
        alert('스크립트 보기 중 오류가 발생했습니다: ' + error.message);
    }
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

// 장비 목록 로드 함수
async function loadDeviceList() {
    console.log('장비 목록 로드 시작');
    try {
        const response = await fetch('/api/devices', {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });

        const result = await response.json();
        console.log('받은 데이터:', result);

        if (!response.ok) {
            throw new Error(result.message || '장비 목록 로드 실패');
        }

        // 장비 목록 테이블 업데이트
        updateDeviceList(result.data);
        console.log('장비 목록 로드 완료');

    } catch (error) {
        console.error('장비 목록 로드 오류:', error);
        showMessage('장비 목록을 불러오는 중 오류가 발생했습니다.', 'danger');
    }
}

// 장비 목록 테이블 업데이트
function updateDeviceList(devices) {
    console.log('장비 목록 업데이트 시작');
    const tbody = document.querySelector('#deviceListBasic');
    if (!tbody) {
        console.error('장비 목록 테이블을 찾을 수 없습니다.');
        return;
    }

    // 데이터가 없거나 빈 배열인 경우
    if (!devices || devices.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">
                    <div class="text-muted">등록된 장비가 없습니다.</div>
                </td>
            </tr>
        `;
        return;
    }

    // 장비 목록 생성
    try {
        tbody.innerHTML = devices.map((device, index) => `
            <tr>
                <td class="text-center">${index + 1}</td>
                <td>${device.name || ''}</td>
                <td>${device.vendor || ''}</td>
                <td>${device.ip || ''}</td>
                <td class="text-center">
                    <button class="btn btn-sm btn-danger" 
                            onclick="deleteDevice('${device.name}')" 
                            title="장비 삭제">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
        console.log('장비 목록 업데이트 완료');
    } catch (error) {
        console.error('장비 목록 업데이트 중 오류:', error);
        showMessage('장비 목록 업데이트 중 오류가 발생했습니다.', 'danger');
    }
}

// 장비 선택 드롭다운 업데이트
function updateDeviceSelect(devices) {
    const select = document.getElementById('configDevice');
    if (!select) return;

    if (!Array.isArray(devices) || devices.length === 0) {
        select.innerHTML = '<option value="">등록된 장비가 없습니다</option>';
        select.disabled = true;
        return;
    }

    select.disabled = false;
    select.innerHTML = `
        <option value="">장비 선택</option>
        ${devices.map(device => `
            <option value="${device.name}">${device.name} (${device.ip})</option>
        `).join('')}
    `;
}

// 설정작업 탭 기능
function handleConfigTypeChange() {
    const configType = document.getElementById('configType').value;
    const paramsDiv = document.getElementById('configParams');
    
    if (!configType || !paramsDiv) return;

    // 작업 유형별 파라미터 폼 생성
    const paramsHTML = getConfigParamsHTML(configType);
    paramsDiv.innerHTML = paramsHTML;
}

// 작업 유형별 파라미터 폼 HTML 생성
function getConfigParamsHTML(configType) {
    const params = {
        vlan_config: [
            { name: 'vlan_id', label: 'VLAN ID', type: 'number' },
            { name: 'vlan_name', label: 'VLAN 이름', type: 'text' }
        ],
        interface_config: [
            { name: 'interface_name', label: '인터페이스', type: 'text' },
            { name: 'interface_desc', label: '설명', type: 'text' },
            { name: 'interface_status', label: '상태', type: 'select', options: ['no shutdown', 'shutdown'] }
        ],
        // 다른 설정 유형들의 파라미터도 추가...
    };

    if (!params[configType]) return '';

    return `
        <div class="row g-3">
            ${params[configType].map(param => `
                <div class="col-md-6">
                    <label for="${param.name}" class="form-label">${param.label}</label>
                    ${param.type === 'select' 
                        ? `<select class="form-select" id="${param.name}">
                            ${param.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
                           </select>`
                        : `<input type="${param.type}" class="form-control" id="${param.name}">`
                    }
                </div>
            `).join('')}
        </div>
    `;
}

// 스크립트 생성 처리
async function handleGenerateScript() {
    const device = document.getElementById('configDevice').value;
    const configType = document.getElementById('configType').value;
    
    if (!device || !configType) {
        alert('장비와 작업 유형을 선택해주세요.');
        return;
    }

    // 파라미터 수집
    const params = collectConfigParams(configType);

    try {
        const response = await fetch('/api/generate-script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                device,
                config_type: configType,
                params
            })
        });

        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || '스크립트 생성 실패');
        }

        // 생성된 스크립트 표시
        const scriptContent = document.getElementById('scriptContent');
        const scriptResult = document.getElementById('scriptResult');
        
        if (scriptContent && scriptResult) {
            scriptContent.textContent = result.script;
            scriptResult.style.display = 'block';
        }

    } catch (error) {
        console.error('스크립트 생성 오류:', error);
        alert('스크립트 생성 중 오류가 발생했습니다.');
    }
}

// 설정 파라미터 수집
function collectConfigParams(configType) {
    const params = {};
    const paramsDiv = document.getElementById('configParams');
    
    if (!paramsDiv) return params;

    // 모든 input과 select 요소의 값을 수집
    paramsDiv.querySelectorAll('input, select').forEach(element => {
        params[element.id] = element.value;
    });

    return params;
}

// 스크립트 실행 처리
async function handleExecuteScript() {
    const device = document.getElementById('configDevice').value;
    const scriptContent = document.getElementById('scriptContent').textContent;

    try {
        const response = await fetch('/api/execute-script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                device,
                script: scriptContent
            })
        });

        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || '스크립트 실행 실패');
        }

        alert('스크립트가 성공적으로 실행되었습니다.');

    } catch (error) {
        console.error('스크립트 실행 오류:', error);
        alert('스크립트 실행 중 오류가 발생했습니다.');
    }
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