# -*- coding: utf-8 -*-
from flask import render_template, jsonify, request
from src.app import app
import json
import os
import re

# 프로젝트 루트 디렉토리 경로 설정
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEVICES_FILE = os.path.join(project_root, 'config', 'devices.json')

def load_devices():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # 데이터가 리스트인 경우 딕셔너리로 변환
                if isinstance(data, list):
                    return {'devices': data}
                return data
            except json.JSONDecodeError:
                return {'devices': []}
    return {'devices': []}

def save_devices(devices):
    # devices가 리스트인 경우 딕셔너리로 변환
    if isinstance(devices, list):
        devices = {'devices': devices}
    
    os.makedirs(os.path.dirname(DEVICES_FILE), exist_ok=True)
    with open(DEVICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(devices, f, ensure_ascii=False, indent=2)

def is_valid_ip(ip):
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    octets = ip.split('.')
    return all(0 <= int(octet) <= 255 for octet in octets)

def is_duplicate_device(name, devices_data, exclude_name=None):
    devices_list = devices_data.get('devices', []) if isinstance(devices_data, dict) else devices_data
    return any(d['name'] == name and d['name'] != exclude_name for d in devices_list)

def is_duplicate_ip(ip, devices_data, exclude_name=None):
    devices_list = devices_data.get('devices', []) if isinstance(devices_data, dict) else devices_data
    return any(d['ip'] == ip and d['name'] != exclude_name for d in devices_list)

@app.route('/')
def index():
    return render_template('device/index.html')

@app.route('/api/devices', methods=['GET'])
def get_devices():
    devices = load_devices()
    return jsonify(devices)

@app.route('/api/devices', methods=['POST'])
def add_device():
    try:
        data = request.json
        devices = load_devices()

        # 유효성 검사
        if not data.get('name') or not data.get('ip'):
            return jsonify({
                'status': 'error',
                'message': '장비 이름과 IP 주소는 필수 입력 항목입니다.'
            }), 400

        # IP 주소 형식 검사
        if not is_valid_ip(data['ip']):
            return jsonify({
                'status': 'error',
                'message': '올바른 IP 주소 형식이 아닙니다.'
            }), 400

        # 중복 검사
        if is_duplicate_device(data['name'], devices):
            return jsonify({
                'status': 'error',
                'message': '이미 존재하는 장비 이름입니다.'
            }), 400

        if is_duplicate_ip(data['ip'], devices):
            return jsonify({
                'status': 'error',
                'message': '이미 사용 중인 IP 주소입니다.'
            }), 400

        # devices가 딕셔너리가 아닌 경우 처리
        if not isinstance(devices, dict):
            devices = {'devices': []}
        elif 'devices' not in devices:
            devices['devices'] = []

        devices['devices'].append(data)
        save_devices(devices)
        return jsonify({'status': 'success', 'message': '장비가 추가되었습니다.'})

    except Exception as e:
        print(f"Error in add_device: {str(e)}")  # 서버 콘솔에 에러 출력
        return jsonify({
            'status': 'error',
            'message': f'장비 추가 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/devices/<device_name>', methods=['DELETE'])
def delete_device(device_name):
    try:
        devices = load_devices()
        devices['devices'] = [d for d in devices['devices'] if d['name'] != device_name]
        save_devices(devices)
        return jsonify({'status': 'success', 'message': '장비가 삭제되었습니다.'})
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'장비 삭제 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/devices/<device_name>', methods=['PUT'])
def update_device(device_name):
    try:
        data = request.json
        devices = load_devices()

        if not data.get('ip'):
            return jsonify({
                'status': 'error',
                'message': 'IP 주소는 필수 입력 항목입니다.'
            }), 400

        if not is_valid_ip(data['ip']):
            return jsonify({
                'status': 'error',
                'message': '올바른 IP 주소 형식이 아닙니다.'
            }), 400

        if is_duplicate_ip(data['ip'], devices, device_name):
            return jsonify({
                'status': 'error',
                'message': '이미 사용 중인 IP 주소입니다.'
            }), 400

        device_found = False
        for device in devices['devices']:
            if device['name'] == device_name:
                device.update(data)
                device_found = True
                break

        if not device_found:
            return jsonify({
                'status': 'error',
                'message': '장비를 찾을 수 없습니다.'
            }), 404

        save_devices(devices)
        return jsonify({'status': 'success', 'message': '장비가 수정되었습니다.'})

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'장비 수정 중 오류가 발생했습니다: {str(e)}'
        }), 500 