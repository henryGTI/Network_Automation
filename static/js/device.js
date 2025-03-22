// -*- coding: utf-8 -*-

// 전역 변수로 장비 목록 저장
let devicesList = [];
let isLoading = false;

// 벤더별 모델 매핑
const vendorModels = {
    'cisco': ['IOS', 'IOS-XE', 'NX-OS'],
    'juniper': ['JunOS'],
    'hp': ['ProCurve', 'Aruba'],
    'arista': ['EOS'],
    'handreamnet': ['HOS'],
    'coreedgenetworks': ['CEN-OS']
};

// 디버그 로깅 함수
function debugLog(message, data = null) {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${message}`);
    if (data) {
        console.log('데이터:', data);
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    debugLog('페이지 로드됨');
    setupDeviceForm(); // 장비 추가 폼 초기화
    loadDevices().then(() => {
        debugLog('초기 장비 목록 로드 완료');
        // 다른 탭의 초기화 함수 호출
        if (typeof initConfigTab === 'function') initConfigTab();
        if (typeof initLearningTab === 'function') initLearningTab();
    }).catch(error => {
        debugLog('초기 장비 목록 로드 실패', error);
    });
});

// 로딩 표시 함수
function showLoading() {
    const deviceList = document.getElementById('devices');
    if (!deviceList) return;
    
    deviceList.innerHTML = `
        <div class="text-center my-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">로딩중...</span>
            </div>
            <p class="mt-2">장비 목록을 불러오는 중...</p>
        </div>
    `;
}

// 벤더 이름 정규화 함수
function normalizeVendorName(vendor) {
    if (!vendor) return '';
    // 한글 "한드림넷"을 "handreamnet"으로 변환
    if (vendor === '한드림넷' || vendor === '\ud55c\ub4dc\ub9bc\ub137') {
        return 'handreamnet';
    }
    return vendor.toLowerCase();
}

// 장비 목록 로드 함수
async function loadDevices() {
    if (isLoading) {
        debugLog('이미 로딩 중입니다');
        return;
    }
    
    try {
        isLoading = true;
        showLoading();
        debugLog('장비 목록 로드 시작');
        
        const response = await fetch('/api/devices', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Cache-Control': 'no-cache'
            }
        });

        debugLog('서버 응답 받음', {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries())
        });

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('서버에서 JSON 형식의 응답을 받지 못했습니다.');
        }

        // 응답 복제 후 텍스트로 확인
        const responseClone = response.clone();
        const rawText = await responseClone.text();
        debugLog('서버 응답 원본', rawText);

        const result = await response.json();
        debugLog('파싱된 응답', result);

        if (!response.ok) {
            throw new Error(result.message || `HTTP error! status: ${response.status}`);
        }

        if (result.status === 'error') {
            throw new Error(result.message || '알 수 없는 오류가 발생했습니다.');
        }

        devicesList = (result.data || []).map(device => ({
            ...device,
            id: device.id || device.name,  // ID가 없으면 이름을 ID로 사용
            vendor: normalizeVendorName(device.vendor),
            model: device.model || ''
        }));
        
        if (!Array.isArray(devicesList)) {
            debugLog('장비 목록이 배열이 아님', devicesList);
            throw new Error('서버에서 올바른 형식의 장비 목록을 받지 못했습니다.');
        }

        debugLog('장비 목록 로드 성공', devicesList);
        updateDeviceUI();
        return devicesList;
    } catch (error) {
        debugLog('장비 목록 로드 실패', error);
        console.error('장비 목록 로드 실패:', error);
        showError(`장비 목록을 불러오는데 실패했습니다: ${error.message}`);
        devicesList = [];
        updateDeviceUI(); // 빈 목록으로 UI 업데이트
        return [];
    } finally {
        isLoading = false;
    }
}

// 에러 메시지 표시 함수
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger alert-dismissible fade show';
    errorDiv.innerHTML = `
        ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    const deviceList = document.getElementById('devices');
    if (deviceList) {
        deviceList.innerHTML = ''; // 기존 내용 제거
        deviceList.appendChild(errorDiv);
    }
}

// UI 업데이트 함수
function updateDeviceUI() {
    const deviceList = document.getElementById('devices');
    if (!deviceList) {
        console.error('devices 요소를 찾을 수 없습니다.');
        return;
    }
    
    deviceList.innerHTML = '';
    
    if (!Array.isArray(devicesList) || devicesList.length === 0) {
        deviceList.innerHTML = '<div class="alert alert-info">등록된 장비가 없습니다.</div>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'table table-striped table-hover';
    table.innerHTML = `
        <thead class="table-light">
            <tr>
                <th>이름</th>
                <th>IP</th>
                <th>벤더</th>
                <th>모델</th>
                <th>작업</th>
            </tr>
        </thead>
        <tbody>
        </tbody>
    `;

    const tbody = table.querySelector('tbody');
    devicesList.forEach(device => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${escapeHtml(device.name)}</td>
            <td>${escapeHtml(device.ip)}</td>
            <td>${escapeHtml(device.vendor)}</td>
            <td>${escapeHtml(device.model)}</td>
            <td>
                <button class="btn btn-sm btn-primary me-1" onclick="editDevice('${escapeHtml(device.name)}')">수정</button>
                <button class="btn btn-sm btn-danger" onclick="deleteDevice('${escapeHtml(device.name)}')">삭제</button>
            </td>
        `;
        tbody.appendChild(row);
    });

    deviceList.appendChild(table);
}

// HTML 이스케이프 함수
function escapeHtml(unsafe) {
    if (unsafe === null || unsafe === undefined) return '';
    return unsafe
        .toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// 장비 삭제 함수
function deleteDevice(name) {
    if (!confirm(`${name} 장비를 삭제하시겠습니까?`)) return;

    fetch(`/api/devices/${encodeURIComponent(name)}`, {
        method: 'DELETE',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => response.json().then(data => ({status: response.status, body: data})))
    .then(({status, body}) => {
        if (status === 200 && body.status === 'success') {
            loadDevices();
            showSuccess(body.message || '장비가 삭제되었습니다.');
        } else {
            throw new Error(body.message || '장비 삭제 중 오류가 발생했습니다.');
        }
    })
    .catch(error => {
        console.error('장비 삭제 오류:', error);
        showError(error.message);
    });
}

// 성공 메시지 표시 함수
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'alert alert-success alert-dismissible fade show';
    successDiv.innerHTML = `
        ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    const deviceList = document.getElementById('devices');
    if (deviceList) {
        deviceList.insertBefore(successDiv, deviceList.firstChild);
    }
}

function editDevice(name) {
    const device = devicesList.find(d => d.name === name);
    if (!device) {
        showError('장비를 찾을 수 없습니다.');
        return;
    }

    debugLog('수정할 장비 정보', device);

    // 기존 수정 폼이 있다면 제거
    const existingForm = document.querySelector('.edit-device-form');
    if (existingForm) {
        existingForm.remove();
    }

    // 수정 폼 생성
    const form = document.createElement('form');
    form.className = 'edit-device-form mt-3';
    const formId = `edit-form-${Date.now()}`;
    form.id = formId;
    
    form.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h3 class="card-title mb-0">장비 수정</h3>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="${formId}-name">이름</label>
                            <input type="text" class="form-control" id="${formId}-name" value="${escapeHtml(device.name)}" readonly>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="${formId}-ip">IP</label>
                            <input type="text" class="form-control" id="${formId}-ip" value="${escapeHtml(device.ip)}" required>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="${formId}-vendor">벤더</label>
                            <select class="form-control" id="${formId}-vendor" required>
                                <option value="">선택하세요</option>
                                ${Object.entries(vendorModels).map(([vendor, models]) => 
                                    `<option value="${vendor}" ${device.vendor === vendor ? 'selected' : ''}>${vendor.charAt(0).toUpperCase() + vendor.slice(1)}</option>`
                                ).join('')}
                            </select>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="${formId}-model">모델</label>
                            <select class="form-control" id="${formId}-model" required>
                                <option value="">벤더를 먼저 선택하세요</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="text-end mt-3">
                    <button type="button" class="btn btn-secondary" onclick="cancelEdit(this.form)">취소</button>
                    <button type="submit" class="btn btn-primary">수정</button>
                </div>
            </div>
        </div>
    `;

    // 벤더 선택 시 모델 옵션 업데이트
    const vendorSelect = form.querySelector(`#${formId}-vendor`);
    const modelSelect = form.querySelector(`#${formId}-model`);
    
    function updateModelOptions(selectedVendor, selectedModel = '') {
        modelSelect.innerHTML = '<option value="">모델을 선택하세요</option>';
        
        if (selectedVendor && vendorModels[selectedVendor]) {
            vendorModels[selectedVendor].forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                option.selected = model === selectedModel;
                modelSelect.appendChild(option);
            });
        }
    }
    
    // 초기 모델 옵션 설정
    if (device.vendor) {
        updateModelOptions(device.vendor, device.model);
    }
    
    vendorSelect.addEventListener('change', function() {
        updateModelOptions(this.value);
    });

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const originalName = this.querySelector(`#${formId}-name`).value.trim();
        const updatedDevice = {
            name: originalName,
            ip: this.querySelector(`#${formId}-ip`).value.trim(),
            vendor: normalizeVendorName(this.querySelector(`#${formId}-vendor`).value.trim()),
            model: this.querySelector(`#${formId}-model`).value.trim()
        };

        debugLog('장비 수정 요청', updatedDevice);

        // 입력값 검증
        if (!updatedDevice.name || !updatedDevice.ip || !updatedDevice.vendor || !updatedDevice.model) {
            showError('모든 필드를 입력해주세요.');
            return;
        }

        // IP 주소 형식 검증
        const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
        if (!ipPattern.test(updatedDevice.ip)) {
            showError('올바른 IP 주소 형식이 아닙니다.');
            return;
        }

        fetch(`/api/devices/${encodeURIComponent(originalName)}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(updatedDevice)
        })
        .then(response => response.json().then(data => ({status: response.status, body: data})))
        .then(({status, body}) => {
            debugLog('장비 수정 응답', { status, body });
            if (status === 200 && body.status === 'success') {
                loadDevices();
                form.remove();
                showSuccess(body.message || '장비가 수정되었습니다.');
            } else {
                throw new Error(body.message || '장비 수정 중 오류가 발생했습니다.');
            }
        })
        .catch(error => {
            console.error('장비 수정 오류:', error);
            showError(error.message || '장비 수정 중 오류가 발생했습니다.');
        });
    });

    const deviceList = document.getElementById('devices');
    if (deviceList) {
        deviceList.insertBefore(form, deviceList.firstChild);
    }
}

function cancelEdit(form) {
    form.remove();
}

function setupDeviceForm() {
    const deviceForm = document.getElementById('device-form');
    if (!deviceForm) {
        console.error('device-form 요소를 찾을 수 없습니다.');
        return;
    }

    const addForm = document.createElement('form');
    addForm.className = 'device-add-form';
    const formId = 'add-form';
    
    addForm.innerHTML = `
        <h3 class="mb-3">장비 추가</h3>
        <div class="row">
            <div class="col-md-3">
                <div class="form-group">
                    <label for="${formId}-name">장비 이름</label>
                    <input type="text" class="form-control" id="${formId}-name" required>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="${formId}-ip">IP 주소</label>
                    <input type="text" class="form-control" id="${formId}-ip" required>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="${formId}-vendor">벤더</label>
                    <select class="form-control" id="${formId}-vendor" required>
                        <option value="">선택하세요</option>
                        ${Object.entries(vendorModels).map(([vendor, models]) => 
                            `<option value="${vendor}">${vendor.charAt(0).toUpperCase() + vendor.slice(1)}</option>`
                        ).join('')}
                    </select>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="${formId}-model">모델</label>
                    <select class="form-control" id="${formId}-model" required>
                        <option value="">벤더를 먼저 선택하세요</option>
                    </select>
                </div>
            </div>
        </div>
        <div class="text-end mt-3">
            <button type="submit" class="btn btn-primary">추가</button>
        </div>
    `;

    // 벤더 선택 시 모델 옵션 업데이트
    const vendorSelect = addForm.querySelector(`#${formId}-vendor`);
    const modelSelect = addForm.querySelector(`#${formId}-model`);
    
    vendorSelect.addEventListener('change', function() {
        const selectedVendor = this.value;
        modelSelect.innerHTML = '<option value="">모델을 선택하세요</option>';
        
        if (selectedVendor && vendorModels[selectedVendor]) {
            vendorModels[selectedVendor].forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
        }
    });

    addForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const device = {
            name: this.querySelector(`#${formId}-name`).value.trim(),
            ip: this.querySelector(`#${formId}-ip`).value.trim(),
            vendor: normalizeVendorName(this.querySelector(`#${formId}-vendor`).value.trim()),
            model: this.querySelector(`#${formId}-model`).value.trim()
        };

        debugLog('장비 추가 요청', device);

        // 입력값 검증
        if (!device.name || !device.ip || !device.vendor || !device.model) {
            showError('모든 필드를 입력해주세요.');
            return;
        }

        // IP 주소 형식 검증
        const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
        if (!ipPattern.test(device.ip)) {
            showError('올바른 IP 주소 형식이 아닙니다.');
            return;
        }

        fetch('/api/devices', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(device)
        })
        .then(response => response.json().then(data => ({status: response.status, body: data})))
        .then(({status, body}) => {
            if (status === 200 && body.status === 'success') {
                loadDevices();
                this.reset();
                modelSelect.innerHTML = '<option value="">벤더를 먼저 선택하세요</option>';
                showSuccess(body.message || '장비가 추가되었습니다.');
            } else {
                throw new Error(body.message || '장비 추가 중 오류가 발생했습니다.');
            }
        })
        .catch(error => {
            console.error('장비 추가 오류:', error);
            showError(error.message);
        });
    });

    deviceForm.appendChild(addForm);
}
