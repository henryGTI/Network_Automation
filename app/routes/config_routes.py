from flask import Blueprint, jsonify, request, current_app
from ..services.config_service import ConfigService

bp = Blueprint('config', __name__)
config_service = ConfigService()

@bp.route('/api/config/task-types', methods=['GET'])
def get_task_types():
    """작업 유형 목록을 반환합니다."""
    try:
        task_types = ['포트 설정', 'VLAN 설정', 'ACL 설정', '라우팅 설정']
        return jsonify(task_types)
    except Exception as e:
        current_app.logger.error(f'작업 유형 조회 중 오류 발생: {str(e)}')
        return jsonify({'error': '작업 유형을 불러오는데 실패했습니다'}), 500

@bp.route('/api/config/subtasks/<task_type>', methods=['GET'])
def get_subtasks(task_type):
    """특정 작업 유형에 해당하는 상세 작업 목록을 반환합니다."""
    try:
        subtasks = {
            '포트 설정': ['포트 상태 설정', '포트 속도 설정', '포트 듀플렉스 설정'],
            'VLAN 설정': ['VLAN 생성', 'VLAN 삭제', 'VLAN 포트 할당'],
            'ACL 설정': ['ACL 생성', 'ACL 규칙 추가', 'ACL 적용'],
            '라우팅 설정': ['정적 라우팅 설정', 'OSPF 설정', 'BGP 설정']
        }
        return jsonify(subtasks.get(task_type, []))
    except Exception as e:
        current_app.logger.error(f'상세 작업 조회 중 오류 발생: {str(e)}')
        return jsonify({'error': '상세 작업을 불러오는데 실패했습니다'}), 500

@bp.route('/api/config/parameters/<task_type>/<subtask>', methods=['GET'])
def get_parameters(task_type, subtask):
    """특정 상세 작업에 필요한 파라미터 목록을 반환합니다."""
    try:
        parameters = {
            '포트 설정': {
                '포트 상태 설정': [
                    {
                        'name': '인터페이스',
                        'type': 'text',
                        'required': True,
                        'pattern': '^[a-zA-Z]+[0-9](/[0-9]+)?$',
                        'placeholder': 'ex) gi0/1',
                        'description': '설정할 인터페이스 이름을 입력하세요'
                    },
                    {
                        'name': '상태',
                        'type': 'select',
                        'required': True,
                        'options': ['up', 'down'],
                        'description': '포트의 관리 상태를 선택하세요'
                    }
                ],
                '포트 속도 설정': [
                    {
                        'name': '인터페이스',
                        'type': 'text',
                        'required': True,
                        'pattern': '^[a-zA-Z]+[0-9](/[0-9]+)?$',
                        'placeholder': 'ex) gi0/1',
                        'description': '설정할 인터페이스 이름을 입력하세요'
                    },
                    {
                        'name': '속도',
                        'type': 'select',
                        'required': True,
                        'options': ['auto', '10', '100', '1000'],
                        'description': '포트의 속도를 선택하세요 (Mbps)'
                    }
                ]
            },
            'VLAN 설정': {
                'VLAN 생성': [
                    {
                        'name': 'VLAN ID',
                        'type': 'number',
                        'required': True,
                        'pattern': '^[1-9][0-9]{0,3}$',
                        'placeholder': '1-4094',
                        'description': 'VLAN ID를 입력하세요 (1-4094)'
                    },
                    {
                        'name': 'VLAN 이름',
                        'type': 'text',
                        'required': True,
                        'pattern': '^[a-zA-Z0-9_-]{1,32}$',
                        'placeholder': 'ex) vlan10',
                        'description': 'VLAN의 이름을 입력하세요'
                    }
                ]
            }
            # 다른 작업 유형과 상세 작업에 대한 파라미터 정의 추가
        }
        
        task_params = parameters.get(task_type, {}).get(subtask, [])
        return jsonify(task_params)
    except Exception as e:
        current_app.logger.error(f'파라미터 조회 중 오류 발생: {str(e)}')
        return jsonify({'error': '파라미터를 불러오는데 실패했습니다'}), 500

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
        required_fields = ['device_id', 'task_types']
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
            parameters=data.get('parameters', {})
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