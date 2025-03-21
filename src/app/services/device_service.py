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

    def _validate_device(self, device_data):
        required_fields = ['name', 'vendor', 'ip']
        return all(device_data.get(field) for field in required_fields) 