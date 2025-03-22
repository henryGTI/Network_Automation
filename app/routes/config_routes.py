from flask import Blueprint, jsonify, request
from ..services.config_service import ConfigService

bp = Blueprint('config', __name__)
config_service = ConfigService()

@bp.route('/api/config/task-types', methods=['GET'])
def get_task_types():
    """작업 유형 목록 조회"""
    return jsonify({
        'status': 'success',
        'data': config_service.get_task_types()
    })

@bp.route('/api/config/subtasks/<task_type>', methods=['GET'])
def get_subtasks(task_type):
    """작업 유형별 하위 작업 목록 조회"""
    subtasks = config_service.get_subtasks(task_type)
    if not subtasks:
        return jsonify({
            'status': 'error',
            'message': '유효하지 않은 작업 유형입니다.'
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': subtasks
    })

@bp.route('/api/config/parameters/<task_type>/<subtask>', methods=['GET'])
def get_parameters(task_type, subtask):
    """작업 유형별 필요한 파라미터 정보 조회"""
    parameters = config_service.get_task_parameters(task_type, subtask)
    return jsonify({
        'status': 'success',
        'data': parameters
    })

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