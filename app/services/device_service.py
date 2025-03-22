from app.models.device import Device
from app.utils.file_handler import FileHandler
import re
from datetime import datetime
import shutil
import logging

logger = logging.getLogger(__name__)

class DeviceService:
    def __init__(self):
        self.file_handler = FileHandler()

    def validate_device_data(self, device_data):
        required_fields = ['name', 'ip', 'vendor', 'model']
        for field in required_fields:
            if field not in device_data:
                raise ValueError(f"필수 필드 누락: {field}")

    def validate_ip_address(self, ip):
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            raise ValueError("잘못된 IP 주소 형식")
        
        # IP 주소 각 부분이 0-255 범위인지 확인
        parts = ip.split('.')
        for part in parts:
            if not 0 <= int(part) <= 255:
                raise ValueError("IP 주소 범위 오류")

    def check_duplicate_ip(self, ip, exclude_name=None):
        devices = self.get_all_devices()
        return any(device['ip'] == ip and device['name'] != exclude_name for device in devices)

    def backup_devices(self):
        try:
            backup_file = f"{self.file_handler.devices_file}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.file_handler.devices_file, backup_file)
            return True
        except Exception as e:
            logger.error(f"백업 실패: {str(e)}")
            return False

    def get_all_devices(self):
        try:
            devices = self.file_handler.load_devices()
            if not devices:
                logger.info("등록된 장비가 없습니다.")
            return devices
        except Exception as e:
            logger.error(f"디바이스 목록 로드 실패: {str(e)}")
            return []

    def find_device_by_name(self, name):
        devices = self.get_all_devices()
        return next((device for device in devices if device['name'] == name), None)

    def add_device(self, device_data):
        try:
            self.validate_device_data(device_data)
            self.validate_ip_address(device_data['ip'])
            
            # 이름 중복 체크
            if self.find_device_by_name(device_data['name']):
                raise ValueError("이미 등록된 장비 이름")
            
            # IP 중복 체크
            if self.check_duplicate_ip(device_data['ip']):
                raise ValueError("이미 등록된 IP 주소")

            devices = self.file_handler.load_devices()
            new_id = len(devices) + 1
            
            # 파일에 저장할 때는 정해진 필드 형식을 사용
            device_dict = {
                'id': new_id,
                'name': device_data['name'],
                'ip': device_data['ip'],
                'vendor': device_data['vendor'].lower(),
                'model': device_data.get('model', ''),
                'username': device_data.get('username', ''),
                'password': device_data.get('password', '')
            }
            
            devices.append(device_dict)
            
            # 백업 후 저장
            if self.backup_devices():
                if not self.file_handler.save_devices(devices):
                    raise ValueError("장비 데이터 저장 실패")
                logger.info(f"장비 추가 성공: {device_data['name']}")
                return device_dict
            else:
                raise ValueError("백업 실패로 인한 저장 중단")
                
        except Exception as e:
            logger.error(f"장비 추가 실패: {str(e)}")
            return {'error': str(e)}, 400

    def update_device_by_name(self, name, device_data):
        try:
            self.validate_device_data(device_data)
            self.validate_ip_address(device_data['ip'])
            
            devices = self.file_handler.load_devices()
            device_index = next((i for i, d in enumerate(devices) if d['name'] == name), -1)
            
            if device_index == -1:
                raise ValueError("장비를 찾을 수 없습니다")

            # IP 중복 체크 (자기 자신 제외)
            if self.check_duplicate_ip(device_data['ip'], name):
                raise ValueError("이미 등록된 IP 주소")

            current_device = devices[device_index]
            
            # 파일에 저장할 때는 정해진 필드 형식을 사용
            device_dict = {
                'id': current_device['id'],
                'name': device_data['name'],
                'ip': device_data['ip'],
                'vendor': device_data['vendor'].lower(),
                'model': device_data.get('model', ''),
                'username': device_data.get('username', ''),
                'password': device_data.get('password', '')
            }
            
            devices[device_index] = device_dict
            
            # 백업 후 저장
            if self.backup_devices():
                if not self.file_handler.save_devices(devices):
                    raise ValueError("장비 데이터 저장 실패")
                logger.info(f"장비 수정 성공: {name}")
                return device_dict
            else:
                raise ValueError("백업 실패로 인한 저장 중단")
                
        except Exception as e:
            logger.error(f"장비 수정 실패: {str(e)}")
            return {'error': str(e)}, 400

    def delete_device_by_name(self, name):
        try:
            devices = self.file_handler.load_devices()
            device_index = next((i for i, d in enumerate(devices) if d['name'] == name), -1)
            
            if device_index == -1:
                raise ValueError("장비를 찾을 수 없습니다")

            deleted_device = devices.pop(device_index)
            
            # 백업 후 저장
            if self.backup_devices():
                if not self.file_handler.save_devices(devices):
                    raise ValueError("장비 데이터 저장 실패")
                logger.info(f"장비 삭제 성공: {name}")
                return {'message': '장비가 삭제되었습니다'}
            else:
                raise ValueError("백업 실패로 인한 삭제 중단")
                
        except Exception as e:
            logger.error(f"장비 삭제 실패: {str(e)}")
            return {'error': str(e)}, 400
