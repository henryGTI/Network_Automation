import os
from pathlib import Path

# 생성할 디렉토리 구조
directories = [
    'app',
    'app/routes',
    'app/models',
    'app/services',
    'app/utils',
    'static/css',
    'static/js',
    'static/vendor/bootstrap',
    'templates/device',
    'templates/script',
    'data/devices',
    'data/scripts/templates'
]

# 생성할 빈 파일들
files = [
    'app/__init__.py',
    'app/routes/__init__.py',
    'app/routes/device_routes.py',
    'app/routes/script_routes.py',
    'app/models/__init__.py',
    'app/models/device.py',
    'app/services/__init__.py',
    'app/services/device_service.py',
    'app/services/script_service.py',
    'app/utils/__init__.py',
    'app/utils/file_handler.py',
    'static/css/style.css',
    'static/js/device.js',
    'static/js/utils.js',
    'templates/base.html',
    'templates/device/index.html',
    'templates/device/form.html',
    'templates/script/index.html',
    'config.py',
    'run.py'
]

# 디렉토리 생성
for directory in directories:
    Path(directory).mkdir(parents=True, exist_ok=True)
    print(f'Created directory: {directory}')

# 빈 파일 생성
for file in files:
    Path(file).touch(exist_ok=True)
    print(f'Created file: {file}')

class Device:
    def __init__(self, name, vendor, ip, id=None):
        self.id = id
        self.name = name
        self.vendor = vendor
        self.ip = ip

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'vendor': self.vendor,
            'ip': self.ip
        }

from app.utils.file_handler import FileHandler
from app.models.device import Device

class DeviceService:
    def __init__(self):
        self.file_handler = FileHandler('devices/devices.json')

    def get_all_devices(self):
        devices = self.file_handler.load_data()
        return [device for device in devices if self._validate_device(device)]

    def add_device(self, device_data):
        if not self._validate_device(device_data):
            return {'status': 'error', 'message': '잘못된 장비 데이터'}, 400

        devices = self.file_handler.load_data()
        device = Device(**device_data)
        device.id = str(len(devices) + 1)
        devices.append(device.to_dict())

        if self.file_handler.save_data(devices):
            return {'status': 'success', 'device': device.to_dict()}, 201
        return {'status': 'error', 'message': '저장 실패'}, 500

    def update_device(self, device_id, device_data):
        devices = self.file_handler.load_data()
        device_index = next((i for i, d in enumerate(devices) 
                           if str(d.get('id')) == str(device_id)), None)

        if device_index is None:
            return {'status': 'error', 'message': '장비를 찾을 수 없음'}, 404

        if not self._validate_device(device_data):
            return {'status': 'error', 'message': '잘못된 장비 데이터'}, 400

        device_data['id'] = device_id
        devices[device_index] = device_data

        if self.file_handler.save_data(devices):
            return {'status': 'success', 'device': device_data}
        return {'status': 'error', 'message': '저장 실패'}, 500

    def delete_device(self, device_id):
        devices = self.file_handler.load_data()
        devices = [d for d in devices if str(d.get('id')) != str(device_id)]
        
        if self.file_handler.save_data(devices):
            return {'status': 'success'}
        return {'status': 'error', 'message': '삭제 실패'}, 500

    def _validate_device(self, device_data):
        required_fields = ['name', 'vendor', 'ip']
        return all(device_data.get(field) for field in required_fields)

import json
from pathlib import Path

class FileHandler:
    def __init__(self, relative_path):
        self.file_path = Path(__file__).parent.parent.parent / 'data' / relative_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load_data(self):
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            return []

    def save_data(self, data):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"데이터 저장 오류: {e}")
            return False

class Config:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / 'data'
    DEVICES_FILE = DATA_DIR / 'devices' / 'devices.json'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key'
    DEBUG = True 

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 