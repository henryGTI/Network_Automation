// -*- coding: utf-8 -*-
document.addEventListener('DOMContentLoaded', function() {
    console.log('페이지 로드됨');
    loadDevices();
    setupDeviceForm();
});

function loadDevices() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(data => {
            console.log('장비 목록:', data);
            displayDevices(data.devices);
        })
        .catch(error => console.error('장비 목록 로드 오류:', error));
}

function displayDevices(devices) {
    const deviceList = document.getElementById('devices');
    deviceList.innerHTML = '';
    
    if (devices.length === 0) {
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
    devices.forEach(device => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${device.name}</td>
            <td>${device.ip}</td>
            <td>${device.vendor}</td>
            <td>${device.model}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editDevice('${device.name}')">수정</button>
                <button class="btn btn-sm btn-danger" onclick="deleteDevice('${device.name}')">삭제</button>
            </td>
        `;
        tbody.appendChild(row);
    });

    deviceList.appendChild(table);
}

function deleteDevice(name) {
    if (!confirm(`${name} 장비를 삭제하시겠습니까?`)) return;

    fetch(`/api/devices/${name}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadDevices();
        }
        alert(data.message);
    })
    .catch(error => console.error('장비 삭제 오류:', error));
}

function editDevice(name) {
    const devices = document.querySelectorAll('table tbody tr');
    let device;
    devices.forEach(row => {
        if (row.cells[0].textContent === name) {
            device = {
                name: row.cells[0].textContent,
                ip: row.cells[1].textContent,
                vendor: row.cells[2].textContent,
                model: row.cells[3].textContent
            };
        }
    });

    if (!device) return;

    // 수정 폼 생성
    const form = document.createElement('form');
    form.innerHTML = `
        <h3>장비 수정</h3>
        <div>
            <label for="edit-name">이름:</label>
            <input type="text" id="edit-name" value="${device.name}" readonly>
        </div>
        <div>
            <label for="edit-ip">IP:</label>
            <input type="text" id="edit-ip" value="${device.ip}" required>
        </div>
        <div>
            <label for="edit-vendor">벤더:</label>
            <select id="edit-vendor" required>
                <option value="handreamnet" ${device.vendor === 'handreamnet' ? 'selected' : ''}>Handreamnet</option>
                <option value="coreedge" ${device.vendor === 'coreedge' ? 'selected' : ''}>CoreEdge</option>
            </select>
        </div>
        <div>
            <label for="edit-model">모델:</label>
            <input type="text" id="edit-model" value="${device.model}" required>
        </div>
        <button type="submit">수정</button>
        <button type="button" onclick="cancelEdit(this.form)">취소</button>
    `;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const updatedDevice = {
            name: document.getElementById('edit-name').value,
            ip: document.getElementById('edit-ip').value,
            vendor: document.getElementById('edit-vendor').value,
            model: document.getElementById('edit-model').value
        };

        fetch(`/api/devices/${name}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatedDevice)
        })
        .then(response => response.json().then(data => ({status: response.status, body: data})))
        .then(({status, body}) => {
            if (status === 200) {
                loadDevices();
                form.remove();
            }
            alert(body.message);
        })
        .catch(error => {
            console.error('장비 수정 오류:', error);
            alert('장비 수정 중 오류가 발생했습니다.');
        });
    });

    const deviceList = document.getElementById('devices');
    deviceList.insertBefore(form, deviceList.firstChild);
}

function cancelEdit(form) {
    form.remove();
}

function setupDeviceForm() {
    const deviceForm = document.getElementById('device-form');
    const addForm = document.createElement('form');
    addForm.className = 'device-add-form';
    
    addForm.innerHTML = `
        <h3 class="mb-3">장비 추가</h3>
        <div class="row">
            <div class="col-md-3">
                <div class="form-group">
                    <label for="name">장비 이름</label>
                    <input type="text" class="form-control" id="name" required>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="ip">IP 주소</label>
                    <input type="text" class="form-control" id="ip" required>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="vendor">벤더</label>
                    <select class="form-control" id="vendor" required>
                        <option value="">선택하세요</option>
                        <option value="handreamnet">Handreamnet</option>
                        <option value="coreedge">CoreEdge</option>
                    </select>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="model">모델</label>
                    <input type="text" class="form-control" id="model" required>
                </div>
            </div>
        </div>
        <div class="text-end mt-3">
            <button type="submit" class="btn btn-primary">추가</button>
        </div>
    `;

    addForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const device = {
            name: document.getElementById('name').value,
            ip: document.getElementById('ip').value,
            vendor: document.getElementById('vendor').value,
            model: document.getElementById('model').value
        };

        fetch('/api/devices', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(device)
        })
        .then(response => response.json().then(data => ({status: response.status, body: data})))
        .then(({status, body}) => {
            if (status === 200) {
                loadDevices();
                addForm.reset();
            }
            alert(body.message);
        })
        .catch(error => {
            console.error('장비 추가 오류:', error);
            alert('장비 추가 중 오류가 발생했습니다.');
        });
    });

    deviceForm.appendChild(addForm);
}
