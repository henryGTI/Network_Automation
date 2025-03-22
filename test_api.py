import requests
import json

BASE_URL = 'http://localhost:5000/api'

def test_add_device():
    # 1. 정상적인 디바이스 추가 (한드림넷)
    device_data = {
        'name': 'test-switch2',
        'ip': '192.168.1.2',
        'vendor': 'handreamnet',
        'model': 'HOS'
    }
    response = requests.post(f'{BASE_URL}/devices', json=device_data)
    print('1. 정상적인 디바이스 추가 (한드림넷):', response.status_code, response.json())

    # 2. 잘못된 벤더로 디바이스 추가
    invalid_vendor_data = {
        'name': 'test-switch3',
        'ip': '192.168.1.3',
        'vendor': 'unknown',
        'model': 'HOS'
    }
    response = requests.post(f'{BASE_URL}/devices', json=invalid_vendor_data)
    print('2. 잘못된 벤더:', response.status_code, response.json())

    # 3. 잘못된 모델로 디바이스 추가
    invalid_model_data = {
        'name': 'test-switch4',
        'ip': '192.168.1.4',
        'vendor': 'cisco',
        'model': 'unknown'
    }
    response = requests.post(f'{BASE_URL}/devices', json=invalid_model_data)
    print('3. 잘못된 모델:', response.status_code, response.json())

    # 4. 정상적인 디바이스 추가 (Cisco)
    cisco_device_data = {
        'name': 'test-switch5',
        'ip': '192.168.1.5',
        'vendor': 'cisco',
        'model': 'IOS'
    }
    response = requests.post(f'{BASE_URL}/devices', json=cisco_device_data)
    print('4. 정상적인 디바이스 추가 (Cisco):', response.status_code, response.json())

    # 5. 중복 IP로 디바이스 추가
    duplicate_ip_data = {
        'name': 'test-switch6',
        'ip': '192.168.1.2',
        'vendor': 'juniper',
        'model': 'JunOS'
    }
    response = requests.post(f'{BASE_URL}/devices', json=duplicate_ip_data)
    print('5. 중복 IP 주소:', response.status_code, response.json())

    # 6. 잘못된 IP 주소
    invalid_ip_data = {
        'name': 'test-switch7',
        'ip': '256.256.256.256',
        'vendor': 'hp',
        'model': 'ProCurve'
    }
    response = requests.post(f'{BASE_URL}/devices', json=invalid_ip_data)
    print('6. 잘못된 IP 주소:', response.status_code, response.json())

    # 7. 디바이스 목록 조회
    response = requests.get(f'{BASE_URL}/devices')
    print('7. 디바이스 목록:', response.status_code, json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == '__main__':
    test_add_device() 