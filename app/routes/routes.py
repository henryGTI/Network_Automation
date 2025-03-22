# -*- coding: utf-8 -*-
from flask import render_template, jsonify, request
from app.app import app
import json
import os
import re

# ?꾨줈?앺듃 猷⑦듃 ?붾젆?좊━ 寃쎈줈 ?ㅼ젙
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEVICES_FILE = os.path.join(project_root, 'config', 'devices.json')

def load_devices():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # ?곗씠?곌? 由ъ뒪?몄씤 寃쎌슦 ?뺤뀛?덈━濡?蹂??                if isinstance(data, list):
                    return {'devices': data}
                return data
            except json.JSONDecodeError:
                return {'devices': []}
    return {'devices': []}

def save_devices(devices):
    # devices媛 由ъ뒪?몄씤 寃쎌슦 ?뺤뀛?덈━濡?蹂??    if isinstance(devices, list):
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

        # ?좏슚??寃??        if not data.get('name') or not data.get('ip'):
            return jsonify({
                'status': 'error',
                'message': '?λ퉬 ?대쫫怨?IP 二쇱냼???꾩닔 ?낅젰 ??ぉ?낅땲??'
            }), 400

        # IP 二쇱냼 ?뺤떇 寃??        if not is_valid_ip(data['ip']):
            return jsonify({
                'status': 'error',
                'message': '?щ컮瑜?IP 二쇱냼 ?뺤떇???꾨떃?덈떎.'
            }), 400

        # 以묐났 寃??        if is_duplicate_device(data['name'], devices):
            return jsonify({
                'status': 'error',
                'message': '?대? 議댁옱?섎뒗 ?λ퉬 ?대쫫?낅땲??'
            }), 400

        if is_duplicate_ip(data['ip'], devices):
            return jsonify({
                'status': 'error',
                'message': '?대? ?ъ슜 以묒씤 IP 二쇱냼?낅땲??'
            }), 400

        # devices媛 ?뺤뀛?덈━媛 ?꾨땶 寃쎌슦 泥섎━
        if not isinstance(devices, dict):
            devices = {'devices': []}
        elif 'devices' not in devices:
            devices['devices'] = []

        devices['devices'].append(data)
        save_devices(devices)
        return jsonify({'status': 'success', 'message': '?λ퉬媛 異붽??섏뿀?듬땲??'})

    except Exception as e:
        print(f"Error in add_device: {str(e)}")  # ?쒕쾭 肄섏넄???먮윭 異쒕젰
        return jsonify({
            'status': 'error',
            'message': f'?λ퉬 異붽? 以??ㅻ쪟媛 諛쒖깮?덉뒿?덈떎: {str(e)}'
        }), 500

@app.route('/api/devices/<device_name>', methods=['DELETE'])
def delete_device(device_name):
    try:
        devices = load_devices()
        devices['devices'] = [d for d in devices['devices'] if d['name'] != device_name]
        save_devices(devices)
        return jsonify({'status': 'success', 'message': '?λ퉬媛 ??젣?섏뿀?듬땲??'})
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'?λ퉬 ??젣 以??ㅻ쪟媛 諛쒖깮?덉뒿?덈떎: {str(e)}'
        }), 500

@app.route('/api/devices/<device_name>', methods=['PUT'])
def update_device(device_name):
    try:
        data = request.json
        devices = load_devices()

        if not data.get('ip'):
            return jsonify({
                'status': 'error',
                'message': 'IP 二쇱냼???꾩닔 ?낅젰 ??ぉ?낅땲??'
            }), 400

        if not is_valid_ip(data['ip']):
            return jsonify({
                'status': 'error',
                'message': '?щ컮瑜?IP 二쇱냼 ?뺤떇???꾨떃?덈떎.'
            }), 400

        if is_duplicate_ip(data['ip'], devices, device_name):
            return jsonify({
                'status': 'error',
                'message': '?대? ?ъ슜 以묒씤 IP 二쇱냼?낅땲??'
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
                'message': '?λ퉬瑜?李얠쓣 ???놁뒿?덈떎.'
            }), 404

        save_devices(devices)
        return jsonify({'status': 'success', 'message': '?λ퉬媛 ?섏젙?섏뿀?듬땲??'})

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'?λ퉬 ?섏젙 以??ㅻ쪟媛 諛쒖깮?덉뒿?덈떎: {str(e)}'
        }), 500

@app.route('/api/generate-script', methods=['POST'])
def generate_script():
    try:
        data = request.json
        # TODO: ?ㅼ젣 ?ㅽ겕由쏀듃 ?앹꽦 濡쒖쭅 援ы쁽
        return jsonify({
            'status': 'success',
            'script': '# Generated Script\n# TODO: Implement script generation'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/learn-command', methods=['POST'])
def learn_command():
    try:
        data = request.json
        device_name = data.get('device')
        command = data.get('command')

        if not device_name or not command:
            return jsonify({
                'status': 'error',
                'message': '?λ퉬? 紐낅졊?대? 紐⑤몢 ?낅젰?댁＜?몄슂.'
            }), 400

        # ?λ퉬 ?뺣낫 議고쉶
        devices = load_devices()
        device = next((d for d in devices['devices'] if d['name'] == device_name), None)
        
        if not device:
            return jsonify({
                'status': 'error',
                'message': '?λ퉬瑜?李얠쓣 ???놁뒿?덈떎.'
            }), 404

        # TODO: ?ㅼ젣 ?λ퉬 ?곌껐 諛?紐낅졊???ㅽ뻾 濡쒖쭅 援ы쁽
        # ?꾩옱???뚯뒪?몄슜 ?묐떟 諛섑솚
        result = f"""?숈뒿 寃곌낵:
?λ퉬: {device_name} ({device['ip']})
?ㅽ뻾 紐낅졊?? {command}

===== 紐낅졊???ㅽ뻾 寃곌낵 =====
{command} 紐낅졊???ㅽ뻾 ?쒕??덉씠??========================"""

        return jsonify({
            'status': 'success',
            'result': result
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 
