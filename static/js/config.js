// 작업 유형별 설정 템플릿
const taskTemplates = {
    vlan: `
        <div class="mb-3">
            <label class="form-label">VLAN 작업 선택</label>
            <select class="form-select" name="vlanAction">
                <option value="">작업을 선택하세요</option>
                <option value="create">VLAN 생성</option>
                <option value="delete">VLAN 삭제</option>
                <option value="assign">인터페이스 VLAN 할당</option>
                <option value="trunk">트렁크 설정</option>
            </select>
        </div>
        <div class="mb-3">
            <label class="form-label">VLAN ID</label>
            <input type="number" class="form-control" name="vlanId" min="1" max="4094">
        </div>
        <div class="mb-3 vlan-name-group">
            <label class="form-label">VLAN 이름</label>
            <input type="text" class="form-control" name="vlanName">
        </div>
        <div class="mb-3 interface-group">
            <label class="form-label">인터페이스</label>
            <input type="text" class="form-control" name="interface" placeholder="예: GigabitEthernet0/1">
        </div>
    `,
    
    port: `
        <div class="mb-3">
            <label class="form-label">포트 작업 선택</label>
            <select class="form-select" name="portAction">
                <option value="">작업을 선택하세요</option>
                <option value="mode">액세스/트렁크 모드 설정</option>
                <option value="speed">포트 속도/듀플렉스 조정</option>
                <option value="status">인터페이스 활성화/비활성화</option>
            </select>
        </div>
        <div class="mb-3">
            <label class="form-label">인터페이스</label>
            <input type="text" class="form-control" name="interface" placeholder="예: GigabitEthernet0/1">
        </div>
        <div class="mb-3 port-settings">
            <!-- 동적으로 추가될 설정 필드 -->
        </div>
    `
}; 

document.addEventListener('DOMContentLoaded', function() {
    initConfigTab();
});

function initConfigTab() {
    // 작업 유형 체크박스 이벤트 리스너
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', updateConfigForm);
    });

    // 스크립트 생성 버튼 이벤트 리스너
    document.getElementById('generateScript').addEventListener('click', generateScript);

    // 장비 목록 로드
    updateDeviceSelect();
}

function updateDeviceSelect() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('deviceSelect');
            select.innerHTML = '';
            data.devices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.name;
                option.textContent = `${device.name} (${device.ip})`;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('장비 목록 로드 오류:', error));
}

function updateConfigForm() {
    const configDetails = document.getElementById('config-details');
    configDetails.innerHTML = '';

    // VLAN 설정 폼
    if (document.getElementById('vlanCheck').checked) {
        configDetails.innerHTML += `
            <div class="mb-3 config-section">
                <h4>VLAN 설정</h4>
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">VLAN ID</label>
                        <input type="number" class="form-control" name="vlan-id">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">VLAN 이름</label>
                        <input type="text" class="form-control" name="vlan-name">
                    </div>
                </div>
            </div>
        `;
    }

    // 포트 설정 폼
    if (document.getElementById('portCheck').checked) {
        configDetails.innerHTML += `
            <div class="mb-3 config-section">
                <h4>포트 설정</h4>
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">포트 범위</label>
                        <input type="text" class="form-control" name="port-range" placeholder="예: 1/1-24">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">포트 모드</label>
                        <select class="form-select" name="port-mode">
                            <option value="access">Access</option>
                            <option value="trunk">Trunk</option>
                        </select>
                    </div>
                </div>
            </div>
        `;
    }

    // 라우팅 설정 폼
    if (document.getElementById('routingCheck').checked) {
        configDetails.innerHTML += `
            <div class="mb-3 config-section">
                <h4>라우팅 설정</h4>
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">라우팅 프로토콜</label>
                        <select class="form-select" name="routing-protocol">
                            <option value="static">Static</option>
                            <option value="ospf">OSPF</option>
                            <option value="bgp">BGP</option>
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">네트워크 주소</label>
                        <input type="text" class="form-control" name="network-address" placeholder="예: 192.168.1.0/24">
                    </div>
                </div>
            </div>
        `;
    }
}

function generateScript() {
    const selectedDevices = Array.from(document.getElementById('deviceSelect').selectedOptions)
        .map(option => option.value);

    if (selectedDevices.length === 0) {
        alert('장비를 선택해주세요.');
        return;
    }

    const config = {
        devices: selectedDevices,
        tasks: {}
    };

    // VLAN 설정 수집
    if (document.getElementById('vlanCheck').checked) {
        config.tasks.vlan = {
            id: document.querySelector('input[name="vlan-id"]').value,
            name: document.querySelector('input[name="vlan-name"]').value
        };
    }

    // 포트 설정 수집
    if (document.getElementById('portCheck').checked) {
        config.tasks.port = {
            range: document.querySelector('input[name="port-range"]').value,
            mode: document.querySelector('select[name="port-mode"]').value
        };
    }

    // 라우팅 설정 수집
    if (document.getElementById('routingCheck').checked) {
        config.tasks.routing = {
            protocol: document.querySelector('select[name="routing-protocol"]').value,
            network: document.querySelector('input[name="network-address"]').value
        };
    }

    // API 호출
    fetch('/api/generate-script', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('generatedScript').value = data.script;
        } else {
            alert('스크립트 생성 중 오류가 발생했습니다: ' + data.message);
        }
    })
    .catch(error => {
        console.error('스크립트 생성 오류:', error);
        alert('스크립트 생성 중 오류가 발생했습니다.');
    });
} 