from flask import Blueprint, jsonify, request
from app.services.device_service import DeviceService
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('device', __name__)
device_service = DeviceService()

@bp.route('/api/devices', methods=['GET'])
def get_devices():
    try:
        devices = device_service.get_all_devices()
        return jsonify({
            'status': 'success',
            'data': devices
        })
    except Exception as e:
        logger.error(f"장비 목록 조회 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '장비 목록을 불러오는데 실패했습니다',
            'error': str(e)
        }), 500

@bp.route('/api/devices', methods=['POST'])
def add_device():
    try:
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': '요청 데이터가 없습니다'
            }), 400
            
        result = device_service.add_device(data)
        if isinstance(result, tuple) and len(result) == 2:
            error_response = {
                'status': 'error',
                'message': result[0].get('error', '알 수 없는 오류가 발생했습니다')
            }
            return jsonify(error_response), result[1]
        
        return jsonify({
            'status': 'success',
            'message': '장비가 추가되었습니다',
            'data': result
        })
    except Exception as e:
        logger.error(f"장비 추가 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '장비 추가 중 오류가 발생했습니다',
            'error': str(e)
        }), 500

@bp.route('/api/devices/<name>', methods=['PUT'])
def update_device(name):
    try:
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': '요청 데이터가 없습니다'
            }), 400
            
        result = device_service.update_device_by_name(name, data)
        if isinstance(result, tuple) and len(result) == 2:
            error_response = {
                'status': 'error',
                'message': result[0].get('error', '알 수 없는 오류가 발생했습니다')
            }
            return jsonify(error_response), result[1]
        
        return jsonify({
            'status': 'success',
            'message': '장비가 수정되었습니다',
            'data': result
        })
    except Exception as e:
        logger.error(f"장비 수정 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '장비 수정 중 오류가 발생했습니다',
            'error': str(e)
        }), 500

@bp.route('/api/devices/<name>', methods=['DELETE'])
def delete_device(name):
    try:
        result = device_service.delete_device_by_name(name)
        if isinstance(result, tuple) and len(result) == 2:
            error_response = {
                'status': 'error',
                'message': result[0].get('error', '알 수 없는 오류가 발생했습니다')
            }
            return jsonify(error_response), result[1]
        
        return jsonify({
            'status': 'success',
            'message': '장비가 삭제되었습니다'
        })
    except Exception as e:
        logger.error(f"장비 삭제 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '장비 삭제 중 오류가 발생했습니다',
            'error': str(e)
        }), 500
