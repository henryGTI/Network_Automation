from flask import Blueprint, jsonify, request, render_template
from app.models.device import Device
from app.database import db
from app.utils.logger import setup_logger
from app.services.device_service import DeviceService

logger = setup_logger(__name__)
device_bp = Blueprint('device', __name__, url_prefix='/device')  # url_prefix 복원
device_service = DeviceService()

@device_bp.route('/')
def index():
    """장비 관리 페이지 렌더링"""
    logger.info("장비 관리 페이지 요청")
    return render_template('device/index.html')

# 프론트엔드 호환성을 위한 경로 설정
@device_bp.route('/api/devices', methods=['GET'])
def get_devices():
    """장비 목록을 조회합니다."""
    try:
        logger.info("장비 목록 조회 요청")
        devices = device_service.get_all_devices()
        
        # 필드명 변환: ip -> ip_address
        for device in devices:
            if 'ip' in device:
                device['ip_address'] = device['ip']
                # del device['ip']  # 원래 필드를 제거할지 여부 결정
            
            # vendor, device_type 등 다른 누락된 필드도 확인하여 기본값 설정
            if 'vendor' not in device:
                device['vendor'] = device.get('vendor_type', '')
            
            if 'device_type' not in device:
                device['device_type'] = device.get('model', '')
        
        # 이미 dictionary 형태의 객체 리스트이므로 to_dict() 호출 없이 직접 반환
        return jsonify(devices)
    except Exception as e:
        logger.error(f"장비 목록 조회 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# 프론트엔드 호환성을 위한 경로 설정
@device_bp.route('/api/devices', methods=['POST'])
def add_device():
    """새 장비를 추가합니다."""
    try:
        logger.info("장비 추가 요청")
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['name', 'ip_address', 'vendor', 'device_type', 'username', 'password']
        for field in required_fields:
            if field not in data:
                logger.warning(f"필수 필드 누락: {field}")
                return jsonify({'status': 'error', 'message': f'{field} 필드가 필요합니다.'}), 400
        
        # IP 주소 중복 검사 (DB)
        if Device.query.filter_by(ip_address=data['ip_address']).first():
            logger.warning(f"중복된 IP 주소 (DB): {data['ip_address']}")
            return jsonify({'status': 'error', 'message': '이미 등록된 IP 주소입니다.'}), 400
            
        # IP 주소 중복 검사 (파일)
        if device_service.check_duplicate_ip(data['ip_address']):
            logger.warning(f"중복된 IP 주소 (파일): {data['ip_address']}")
            return jsonify({'status': 'error', 'message': '이미 등록된 IP 주소입니다.'}), 400
        
        # 1. DB에 저장
        device = Device(
            name=data['name'],
            ip_address=data['ip_address'],
            vendor=data['vendor'],
            device_type=data['device_type'],
            username=data['username'],
            password=data['password']
        )
        
        db.session.add(device)
        db.session.commit()
        
        # 2. 파일에도 저장
        device_data = {
            'name': data['name'],
            'ip': data['ip_address'],  # 주의: 파일 저장시 'ip'로 필드명 변환
            'vendor': data['vendor'],
            'model': data['device_type'],  # 주의: 파일 저장시 'model'로 필드명 변환
            'username': data['username'],
            'password': data['password']
        }
        
        file_result = device_service.add_device(device_data)
        
        # 파일 저장 실패 시 DB 롤백하고 오류 반환
        if isinstance(file_result, tuple) and file_result[1] == 400:
            db.session.delete(device)
            db.session.commit()
            logger.error(f"파일 저장 실패: {file_result[0].get('error')}")
            return jsonify({'status': 'error', 'message': f"파일 저장 실패: {file_result[0].get('error')}"}), 400
        
        logger.info(f"장비 추가 성공: {device.name} ({device.ip_address})")
        return jsonify({
            'status': 'success',
            'message': '장비가 추가되었습니다.',
            'device': device.to_dict()
        })
    except Exception as e:
        logger.error(f"장비 추가 실패: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 프론트엔드 호환성을 위한 경로 설정
@device_bp.route('/api/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """장비 상세 정보를 조회합니다."""
    try:
        logger.info(f"장비 상세 조회 요청: {device_id}")
        
        # DB에서 조회 시도
        device = Device.query.get(device_id)
        
        # DB에 없으면 파일에서 조회
        if not device:
            devices = device_service.get_all_devices()
            device_data = next((d for d in devices if d.get('id') == device_id), None)
            
            if not device_data:
                logger.warning(f"장비를 찾을 수 없음: {device_id}")
                return jsonify({
                    'status': 'error',
                    'message': '장비를 찾을 수 없습니다.'
                }), 404
            
            # 필드명 변환
            if 'ip' in device_data:
                device_data['ip_address'] = device_data['ip']
            
            return jsonify(device_data)
        
        return jsonify(device.to_dict())
    except Exception as e:
        logger.error(f"장비 상세 조회 실패: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 프론트엔드 호환성을 위한 경로 설정
@device_bp.route('/api/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    """장비 정보를 수정합니다."""
    try:
        logger.info(f"장비 수정 요청: {device_id}")
        device = Device.query.get(device_id)
        
        if not device:
            # 파일 기반 DB에서 장비 업데이트 시도
            data = request.get_json()
            
            device_data = {
                'name': data.get('name'),
                'ip': data.get('ip_address'),
                'vendor': data.get('vendor'),
                'model': data.get('device_type'),
                'username': data.get('username'),
                'password': data.get('password')
            }
            
            result = device_service.update_device_by_name(device_data['name'], device_data)
            
            if isinstance(result, tuple) and result[1] == 400:
                logger.warning(f"장비 수정 실패: {result[0].get('error')}")
                return jsonify({'status': 'error', 'message': result[0].get('error')}), 400
            
            logger.info(f"장비 수정 성공: {device_data['name']}")
            return jsonify({
                'status': 'success',
                'message': '장비가 수정되었습니다.',
                'device': result
            })
        
        data = request.get_json()
        
        # IP 주소 중복 검사 (자신 제외)
        if 'ip_address' in data and data['ip_address'] != device.ip_address:
            if Device.query.filter_by(ip_address=data['ip_address']).first():
                return jsonify({'status': 'error', 'message': '이미 등록된 IP 주소입니다.'}), 400
        
        for key, value in data.items():
            if hasattr(device, key):
                setattr(device, key, value)
        
        db.session.commit()
        
        logger.info(f"장비 수정 성공: {device.name}")
        return jsonify({
            'status': 'success',
            'message': '장비가 수정되었습니다.',
            'device': device.to_dict()
        })
    except Exception as e:
        logger.error(f"장비 수정 실패: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 프론트엔드 호환성을 위한 경로 설정
@device_bp.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """장비를 삭제합니다."""
    try:
        logger.info(f"장비 삭제 요청: {device_id}")
        device = Device.query.get(device_id)
        
        if not device:
            # 파일 기반 DB에서 장비 정보 찾기
            devices = device_service.get_all_devices()
            device_data = next((d for d in devices if d.get('id') == device_id), None)
            
            if not device_data:
                logger.warning(f"장비를 찾을 수 없음: {device_id}")
                return jsonify({
                    'status': 'error',
                    'message': '장비를 찾을 수 없습니다.'
                }), 404
            
            # 파일 기반 DB에서 장비 삭제
            result = device_service.delete_device_by_name(device_data['name'])
            
            if isinstance(result, tuple) and result[1] == 400:
                logger.warning(f"장비 삭제 실패: {result[0].get('error')}")
                return jsonify({'status': 'error', 'message': result[0].get('error')}), 400
            
            logger.info(f"장비 삭제 성공: {device_data['name']}")
            return jsonify({
                'status': 'success',
                'message': '장비가 삭제되었습니다.'
            })
        
        db.session.delete(device)
        db.session.commit()
        
        logger.info(f"장비 삭제 성공: {device.name}")
        return jsonify({
            'status': 'success',
            'message': '장비가 삭제되었습니다.'
        })
    except Exception as e:
        logger.error(f"장비 삭제 실패: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
