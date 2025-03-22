from flask import Blueprint, jsonify, request
from ..services.learning_service import LearningService

bp = Blueprint('learning', __name__)
learning_service = LearningService()

@bp.route('/api/learning/commands', methods=['GET'])
def get_commands():
    """명령어 목록 조회"""
    vendor = request.args.get('vendor')
    query = request.args.get('query')
    
    if query:
        commands = learning_service.search_commands(query, vendor)
    else:
        commands = learning_service.get_commands(vendor)
    
    return jsonify({
        'status': 'success',
        'data': [cmd.to_dict() for cmd in commands]
    })

@bp.route('/api/learning/commands', methods=['POST'])
def add_command():
    """새로운 명령어 추가"""
    data = request.get_json()
    
    required_fields = ['vendor', 'command', 'description']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'status': 'error',
                'message': f'필수 필드가 누락되었습니다: {field}'
            }), 400
    
    command = learning_service.add_command(
        vendor=data['vendor'],
        command=data['command'],
        description=data['description'],
        mode=data.get('mode'),
        parameters=data.get('parameters'),
        examples=data.get('examples')
    )
    
    return jsonify({
        'status': 'success',
        'message': '명령어가 추가되었습니다.',
        'data': command.to_dict()
    }), 201

@bp.route('/api/learning/commands/<vendor>/<path:command>', methods=['DELETE'])
def delete_command(vendor, command):
    """명령어 삭제"""
    success = learning_service.delete_command(vendor, command)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': '명령어를 찾을 수 없습니다.'
        }), 404
    
    return jsonify({
        'status': 'success',
        'message': '명령어가 삭제되었습니다.'
    })

@bp.route('/api/learning/commands/<vendor>', methods=['DELETE'])
def clear_commands(vendor):
    """벤더의 모든 명령어 삭제"""
    success = learning_service.clear_commands(vendor)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': '벤더를 찾을 수 없습니다.'
        }), 404
    
    return jsonify({
        'status': 'success',
        'message': '모든 명령어가 삭제되었습니다.'
    })

@bp.route('/api/learning/status', methods=['GET'])
def get_learning_status():
    """학습 상태 확인"""
    status = learning_service.check_learning_status()
    return jsonify({
        'status': 'success',
        'data': status
    }) 