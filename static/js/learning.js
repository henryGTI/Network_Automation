// 전역 변수
let commands = {};  // 벤더별 명령어 저장
let selectedVendor = '';  // 선택된 벤더

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
    loadCommands();
    setupEventListeners();
});

// 이벤트 리스너 설정
function setupEventListeners() {
    // 벤더 선택 이벤트
    const vendorSelect = document.getElementById('vendor-select');
    if (vendorSelect) {
        vendorSelect.addEventListener('change', function() {
            selectedVendor = this.value;
            displayCommands(commands[selectedVendor] || []);
        });
    }

    // 명령어 검색 이벤트
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            searchCommands(this.value);
        }, 300));
    }

    // 명령어 추가 폼 제출 이벤트
    const addForm = document.getElementById('add-command-form');
    if (addForm) {
        addForm.addEventListener('submit', function(e) {
            e.preventDefault();
            addCommand(this);
        });
    }
}

// 명령어 목록 로드
async function loadCommands() {
    try {
        showLoading();
        const response = await fetch('/api/learning/commands');
        const result = await response.json();
        
        if (result.status === 'success') {
            commands = result.data;
            updateVendorSelect();
            if (selectedVendor) {
                displayCommands(commands[selectedVendor] || []);
            }
        } else {
            showError('명령어 목록을 불러오는데 실패했습니다.');
        }
    } catch (error) {
        console.error('명령어 로드 오류:', error);
        showError('명령어 목록을 불러오는데 실패했습니다.');
    } finally {
        hideLoading();
    }
}

// 벤더 선택 옵션 업데이트
function updateVendorSelect() {
    const vendorSelect = document.getElementById('vendor-select');
    if (!vendorSelect) return;

    vendorSelect.innerHTML = '<option value="">벤더 선택</option>';
    Object.keys(commands).forEach(vendor => {
        const option = document.createElement('option');
        option.value = vendor;
        option.textContent = vendor.charAt(0).toUpperCase() + vendor.slice(1);
        if (vendor === selectedVendor) {
            option.selected = true;
        }
        vendorSelect.appendChild(option);
    });
}

// 명령어 목록 표시
function displayCommands(commandList) {
    const container = document.getElementById('commands-container');
    if (!container) return;

    if (!Array.isArray(commandList)) {
        commandList = [];
    }

    container.innerHTML = commandList.length === 0 ? 
        '<p class="text-center">등록된 명령어가 없습니다.</p>' :
        `<div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>명령어</th>
                        <th>설명</th>
                        <th>모드</th>
                        <th>작업</th>
                    </tr>
                </thead>
                <tbody>
                    ${commandList.map(cmd => `
                        <tr>
                            <td>${escapeHtml(cmd.command)}</td>
                            <td>${escapeHtml(cmd.description)}</td>
                            <td>${escapeHtml(cmd.mode || '-')}</td>
                            <td>
                                <button class="btn btn-sm btn-danger" onclick="deleteCommand('${escapeHtml(cmd.vendor)}', '${escapeHtml(cmd.command)}')">
                                    삭제
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>`;
}

// 명령어 검색
async function searchCommands(query) {
    if (!query) {
        if (selectedVendor) {
            displayCommands(commands[selectedVendor] || []);
        }
        return;
    }

    try {
        showLoading();
        const response = await fetch(`/api/learning/commands?query=${encodeURIComponent(query)}${selectedVendor ? `&vendor=${encodeURIComponent(selectedVendor)}` : ''}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            displayCommands(result.data);
        } else {
            showError('명령어 검색에 실패했습니다.');
        }
    } catch (error) {
        console.error('명령어 검색 오류:', error);
        showError('명령어 검색에 실패했습니다.');
    } finally {
        hideLoading();
    }
}

// 새 명령어 추가
async function addCommand(form) {
    const formData = {
        vendor: form.querySelector('#command-vendor').value,
        command: form.querySelector('#command-text').value,
        description: form.querySelector('#command-description').value,
        mode: form.querySelector('#command-mode').value,
        parameters: form.querySelector('#command-parameters').value
            .split('\n')
            .map(p => p.trim())
            .filter(p => p),
        examples: form.querySelector('#command-examples').value
            .split('\n')
            .map(e => e.trim())
            .filter(e => e)
    };

    try {
        showLoading();
        const response = await fetch('/api/learning/commands', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        if (response.ok && result.status === 'success') {
            showSuccess('명령어가 추가되었습니다.');
            form.reset();
            await loadCommands();
        } else {
            showError(result.message || '명령어 추가에 실패했습니다.');
        }
    } catch (error) {
        console.error('명령어 추가 오류:', error);
        showError('명령어 추가에 실패했습니다.');
    } finally {
        hideLoading();
    }
}

// 명령어 삭제
async function deleteCommand(vendor, command) {
    if (!confirm('이 명령어를 삭제하시겠습니까?')) {
        return;
    }

    try {
        showLoading();
        const response = await fetch(`/api/learning/commands/${encodeURIComponent(vendor)}/${encodeURIComponent(command)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        if (response.ok && result.status === 'success') {
            showSuccess('명령어가 삭제되었습니다.');
            await loadCommands();
        } else {
            showError(result.message || '명령어 삭제에 실패했습니다.');
        }
    } catch (error) {
        console.error('명령어 삭제 오류:', error);
        showError('명령어 삭제에 실패했습니다.');
    } finally {
        hideLoading();
    }
}

// 유틸리티 함수
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'block';
    }
}

function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'none';
    }
}

function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alert, container.firstChild);
    }
}

function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alert, container.firstChild);
    }
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
