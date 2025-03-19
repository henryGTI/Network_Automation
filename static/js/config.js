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