from flask import Blueprint, jsonify, request, current_app
from ..services.config_service import ConfigService
from app.utils.logger import setup_logger

bp = Blueprint('config', __name__)
config_service = ConfigService()
logger = setup_logger(__name__)

@bp.route('/api/config/task-types', methods=['GET'])
def get_task_types():
    """작업 유형 목록을 반환합니다."""
    try:
        task_types = [
            'VLAN 관리',
            '포트 설정',
            '라우팅 설정',
            '보안 설정',
            'STP 및 LACP',
            'QoS 및 트래픽 제어',
            '라우팅 상태 모니터링',
            '네트워크 상태 점검',
            '로그 수집',
            '구성 백업 및 복원',
            'SNMP 및 모니터링',
            '자동화 스크립트 확장'
        ]
        return jsonify(task_types)
    except Exception as e:
        current_app.logger.error(f'작업 유형 조회 중 오류 발생: {str(e)}')
        return jsonify({'error': '작업 유형을 불러오는데 실패했습니다'}), 500

@bp.route('/api/config/subtasks/<task_type>', methods=['GET'])
def get_subtasks(task_type):
    """특정 작업 유형에 해당하는 상세 작업 목록을 반환합니다."""
    try:
        subtasks = {
            'VLAN 관리': [
                'VLAN 생성',
                'VLAN 삭제',
                '인터페이스 VLAN 할당',
                '트렁크 설정'
            ],
            '포트 설정': [
                '액세스 모드 설정',
                '트렁크 모드 설정',
                '포트 속도 설정',
                '포트 듀플렉스 설정',
                '인터페이스 활성화'
            ],
            '라우팅 설정': [
                '정적 라우팅',
                'OSPF 설정',
                'EIGRP 설정',
                'BGP 설정'
            ],
            '보안 설정': [
                'Port Security',
                'SSH/Telnet 제한',
                'AAA 인증',
                'ACL 설정'
            ],
            'STP 및 LACP': [
                'STP 설정',
                'LACP/포트 채널 구성'
            ],
            'QoS 및 트래픽 제어': [
                'QoS 정책 적용',
                '트래픽 제한',
                '서비스 정책 설정'
            ],
            '라우팅 상태 모니터링': [
                '라우팅 테이블 확인',
                'OSPF 이웃 확인',
                'BGP 상태 확인'
            ],
            '네트워크 상태 점검': [
                '인터페이스 상태 확인',
                '트래픽 모니터링'
            ],
            '로그 수집': [
                '시스템 로그 수집',
                '로그 파일 저장'
            ],
            '구성 백업 및 복원': [
                '설정 백업',
                '설정 복원'
            ],
            'SNMP 및 모니터링': [
                'SNMP 설정',
                'CDP/LLDP 정보 수집'
            ],
            '자동화 스크립트 확장': [
                '다중 장비 설정',
                '조건 검증'
            ]
        }
        
        if task_type not in subtasks:
            return jsonify({'error': '잘못된 작업 유형입니다'}), 400
            
        return jsonify(subtasks[task_type])
    except Exception as e:
        current_app.logger.error(f'상세 작업 목록 조회 중 오류 발생: {str(e)}')
        return jsonify({'error': '상세 작업 목록을 불러오는데 실패했습니다'}), 500

@bp.route('/api/config/parameters/<task_type>/<subtask>', methods=['GET'])
def get_parameters(task_type, subtask):
    """특정 작업에 필요한 파라미터 목록을 반환합니다."""
    try:
        parameters = {
            'VLAN 관리': {
                'VLAN 생성': [
                    {'name': 'vlan_id', 'type': 'number', 'label': 'VLAN ID', 'required': True, 'min': 1, 'max': 4094},
                    {'name': 'vlan_name', 'type': 'text', 'label': 'VLAN 이름', 'required': True}
                ],
                '인터페이스 VLAN 할당': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                    {'name': 'vlan_id', 'type': 'number', 'label': 'VLAN ID', 'required': True, 'min': 1, 'max': 4094}
                ]
            },
            '포트 설정': {
                '액세스 모드 설정': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                    {'name': 'vlan_id', 'type': 'number', 'label': 'VLAN ID', 'required': True, 'min': 1, 'max': 4094}
                ]
            },
            '라우팅 설정': {
                '정적 라우팅': [
                    {'name': 'network_address', 'type': 'text', 'label': '네트워크 주소', 'required': True, 'placeholder': '예: 192.168.1.0'},
                    {'name': 'subnet_mask', 'type': 'text', 'label': '서브넷 마스크', 'required': True, 'placeholder': '예: 255.255.255.0'},
                    {'name': 'next_hop', 'type': 'text', 'label': '다음 홉 주소', 'required': True, 'placeholder': '예: 192.168.1.1'}
                ]
            }
        }
        
        if task_type not in parameters or subtask not in parameters[task_type]:
            return jsonify({'error': '잘못된 작업 유형 또는 상세 작업입니다'}), 400
            
        return jsonify(parameters[task_type][subtask])
    except Exception as e:
        current_app.logger.error(f'파라미터 목록 조회 중 오류 발생: {str(e)}')
        return jsonify({'error': '파라미터 목록을 불러오는데 실패했습니다'}), 500

@bp.route('/api/config/tasks', methods=['GET'])
def get_tasks():
    """작업 목록 조회"""
    device_id = request.args.get('device_id')
    tasks = config_service.get_tasks(device_id)
    
    if device_id:
        return jsonify({
            'status': 'success',
            'data': [task.to_dict() for task in tasks]
        })
    
    return jsonify({
        'status': 'success',
        'data': {
            device_id: [task.to_dict() for task in device_tasks]
            for device_id, device_tasks in tasks.items()
        }
    })

@bp.route('/api/config/tasks', methods=['POST'])
def add_task():
    """새로운 작업 추가"""
    data = request.get_json()
    
    required_fields = ['device_id', 'task_type', 'subtask']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'status': 'error',
                'message': f'필수 필드가 누락되었습니다: {field}'
            }), 400
    
    task = config_service.add_task(
        device_id=data['device_id'],
        task_type=data['task_type'],
        subtask=data['subtask'],
        parameters=data.get('parameters')
    )
    
    return jsonify({
        'status': 'success',
        'message': '작업이 추가되었습니다.',
        'data': task.to_dict()
    }), 201

@bp.route('/api/config/tasks/<device_id>/<int:task_index>', methods=['PUT'])
def update_task_status(device_id, task_index):
    """작업 상태 업데이트"""
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({
            'status': 'error',
            'message': '상태 정보가 누락되었습니다.'
        }), 400
    
    success = config_service.update_task_status(
        device_id=device_id,
        task_index=task_index,
        status=data['status'],
        result=data.get('result'),
        error=data.get('error')
    )
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': '작업을 찾을 수 없습니다.'
        }), 404
    
    return jsonify({
        'status': 'success',
        'message': '작업 상태가 업데이트되었습니다.'
    })

@bp.route('/api/config/tasks/<device_id>/<int:task_index>', methods=['DELETE'])
def delete_task(device_id, task_index):
    """작업 삭제"""
    success = config_service.delete_task(device_id, task_index)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': '작업을 찾을 수 없습니다.'
        }), 404
    
    return jsonify({
        'status': 'success',
        'message': '작업이 삭제되었습니다.'
    })

@bp.route('/api/config/tasks/<device_id>', methods=['DELETE'])
def clear_tasks(device_id):
    """장비의 모든 작업 삭제"""
    success = config_service.clear_tasks(device_id)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': '장비를 찾을 수 없습니다.'
        }), 404
    
    return jsonify({
        'status': 'success',
        'message': '모든 작업이 삭제되었습니다.'
    })

@bp.route('/api/config/generate-script', methods=['POST'])
def generate_script():
    """스크립트 생성"""
    try:
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['device_id', 'task_types', 'subtask_type', 'vendor', 'parameters']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'필수 필드가 누락되었습니다: {field}'
                }), 400
        
        # 스크립트 생성
        script = config_service.generate_script(
            device_id=data['device_id'],
            task_types=data['task_types'],
            subtask_type=data['subtask_type'],
            vendor=data['vendor'],
            parameters=data['parameters']
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'script': script
            }
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"스크립트 생성 중 오류: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"스크립트 생성 실패: {str(e)}"
        }), 500 