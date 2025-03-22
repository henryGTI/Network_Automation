from flask import Blueprint, jsonify, request, current_app
from ..services.learning_service import LearningService
from app.models.cli_command import CLICommand
from app.data.command_templates import get_template, get_all_templates
from app import db
import logging
from app.utils.logger import setup_logger
from ..models.device import Device
from ..models.task_type import TaskType
from ..exceptions import CLILearningError, ValidationError

learning_bp = Blueprint('learning', __name__)
learning_service = LearningService()
logger = setup_logger(__name__)

@learning_bp.route('/api/learning/commands', methods=['GET'])
def get_commands():
    """학습된 CLI 명령어 목록을 반환합니다."""
    try:
        vendor = request.args.get('vendor')
        commands = learning_service.get_learned_commands(vendor)
        return jsonify(commands)
        
    except Exception as e:
        logger.error(f"명령어 조회 중 오류 발생: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': '명령어 목록을 불러오는데 실패했습니다.'
        }), 500

@learning_bp.route('/api/learning/commands', methods=['POST'])
def add_command():
    """새로운 CLI 명령어를 저장합니다."""
    try:
        logger.info("명령어 추가 요청")
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['vendor', 'device_type', 'task_type', 'subtask', 'command']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'필수 필드 누락: {field}'}), 400
                
        # 템플릿 검증
        template = get_template(data['vendor'], data['task_type'])
        if not template:
            return jsonify({'error': '지원되지 않는 벤더 또는 작업 유형입니다.'}), 400
            
        # 기존 명령어 확인
        existing = CLICommand.get_by_task(
            data['vendor'],
            data['device_type'],
            data['task_type'],
            data['subtask']
        )
        
        if existing:
            return jsonify({
                'status': 'error',
                'message': '이미 존재하는 명령어입니다'
            }), 409

        # 새 명령어 생성
        command = CLICommand(
            vendor=data['vendor'],
            device_type=data['device_type'],
            task_type=data['task_type'],
            subtask=data['subtask'],
            command=data['command'],
            parameters=data.get('parameters'),
            description=data.get('description')
        )
        
        db.session.add(command)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': command.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"명령어 추가 실패: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@learning_bp.route('/api/learning/commands/<int:command_id>', methods=['PUT'])
def update_command(command_id):
    """기존 CLI 명령어를 수정합니다."""
    try:
        command = CLICommand.query.get_or_404(command_id)
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['vendor', 'device_type', 'task_type', 'subtask', 'command']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'필수 필드 누락: {field}'}), 400
                
        # 템플릿 검증
        template = get_template(data['vendor'], data['task_type'])
        if not template:
            return jsonify({'error': '지원되지 않는 벤더 또는 작업 유형입니다.'}), 400
            
        # 명령어 업데이트
        command.vendor = data['vendor']
        command.device_type = data['device_type']
        command.task_type = data['task_type']
        command.subtask = data['subtask']
        command.command = data['command']
        command.parameters = data.get('parameters')
        command.description = data.get('description')
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'data': command.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"CLI 명령어 수정 중 오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'CLI 명령어 수정에 실패했습니다'
        }), 500

@learning_bp.route('/api/learning/commands/<int:command_id>', methods=['DELETE'])
def delete_command(command_id):
    """CLI 명령어를 삭제합니다."""
    try:
        command = CLICommand.query.get_or_404(command_id)
        db.session.delete(command)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'CLI 명령어가 삭제되었습니다'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"CLI 명령어 삭제 중 오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'CLI 명령어 삭제에 실패했습니다'
        }), 500

@learning_bp.route('/api/learning/templates', methods=['GET'])
def get_templates():
    """벤더별 명령어 템플릿 조회"""
    try:
        logger.info("템플릿 조회 요청")
        vendor = request.args.get('vendor')
        templates = get_all_templates(vendor)
        return jsonify(templates)
    except Exception as e:
        logger.error(f"템플릿 조회 중 오류 발생: {str(e)}")
        return jsonify({'error': str(e)}), 500

@learning_bp.route('/api/learning/generate-script', methods=['POST'])
def generate_script():
    """학습된 CLI 명령어를 기반으로 스크립트를 생성합니다."""
    try:
        logger.info("스크립트 생성 요청")
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['vendor', 'device_type', 'task_type', 'subtask', 'parameters']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'필수 필드 누락: {field}'}), 400
                
        # 템플릿 조회
        template = get_template(data['vendor'], data['task_type'])
        if not template:
            return jsonify({'error': '지원되지 않는 벤더 또는 작업 유형입니다.'}), 400
            
        # 스크립트 생성
        script = []
        for cmd in template['template']:
            try:
                script.append(cmd.format(**data['parameters']))
            except KeyError as e:
                return jsonify({'error': f'필수 파라미터 누락: {str(e)}'}), 400
                
        return jsonify({
            'script': script,
            'template': template
        })
    except Exception as e:
        logger.error(f"스크립트 생성 중 오류 발생: {str(e)}")
        return jsonify({'error': str(e)}), 500

@learning_bp.route('/api/learning/status', methods=['GET'])
def get_learning_status():
    """학습 상태를 반환합니다."""
    try:
        status = learning_service.check_learning_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"상태 조회 중 오류 발생: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': '학습 상태를 확인하는데 실패했습니다.'
        }), 500

@learning_bp.route('/api/learning/start', methods=['POST'])
def start_learning():
    """CLI 명령어 학습을 시작합니다."""
    try:
        data = request.get_json()
        if not data:
            raise ValidationError('요청 데이터가 없습니다.')
            
        device_id = data.get('device_id')
        task_types = data.get('task_types')
        
        if not device_id:
            raise ValidationError('장치 ID가 필요합니다.')
        if not task_types:
            raise ValidationError('작업 유형이 필요합니다.')
            
        # 장치 정보 조회
        device = Device.query.get(device_id)
        if not device:
            raise ValidationError('존재하지 않는 장치입니다.')
            
        # 학습 시작
        result = learning_service.start_learning(device.vendor)
        return jsonify({
            'status': 'success',
            'message': '명령어 학습이 완료되었습니다.',
            'data': result
        })
        
    except ValidationError as e:
        logger.warning(f"검증 오류: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
        
    except CLILearningError as e:
        logger.error(f"학습 오류: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': '서버 오류가 발생했습니다.'
        }), 500

@learning_bp.route('/api/learning/task-types', methods=['GET'])
def get_task_types():
    """작업 유형 목록을 반환합니다."""
    try:
        logger.info("작업 유형 조회 요청")
        task_types = TaskType.query.all()
        return jsonify([task_type.to_dict() for task_type in task_types])
    except Exception as e:
        logger.error(f"작업 유형 조회 중 오류 발생: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': '작업 유형 목록을 불러오는데 실패했습니다.'
        }), 500

@learning_bp.route('/api/learning/templates/<vendor>', methods=['GET'])
def get_vendor_templates(vendor):
    """벤더별 명령어 템플릿을 반환합니다."""
    try:
        templates = learning_service.get_vendor_templates(vendor)
        if not templates:
            return jsonify({
                'status': 'error',
                'message': '지원하지 않는 벤더입니다.'
            }), 400
            
        return jsonify(templates)
        
    except Exception as e:
        logger.error(f"템플릿 조회 중 오류 발생: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': '템플릿을 불러오는데 실패했습니다.'
        }), 500 