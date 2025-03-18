import os
from web_server import app, ensure_directories
import webbrowser
import logging
from flask import Flask, request, jsonify, render_template
import json
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )

def main():
    # 로깅 설정
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("네트워크 자동화 도구 시작")

    # 필요한 디렉토리 생성
    ensure_directories()
    
    # 웹 브라우저 실행
    webbrowser.open('http://127.0.0.1:5000')
    
    # 웹 서버 실행
    app.run(host='127.0.0.1', port=5000, debug=True)

app = Flask(__name__)

# 필요한 디렉토리 생성
required_dirs = ['tasks', 'logs', 'device_scripts']
for directory in required_dirs:
    if not os.path.exists(directory):
        os.makedirs(directory)

# 벤더별 템플릿 정의
vendor_templates = {
    'cisco': {
        'VLAN 설정': [
            "configure terminal",
            "vlan {vlan_id}",
            "name {vlan_name}",
            "exit",
            "end"
        ],
        'IP 설정': [
            "configure terminal",
            "interface {interface}",
            "ip address {ip_address} {subnet_mask}",
            "no shutdown",
            "exit",
            "end"
        ],
        '인터페이스 설정': [
            "configure terminal",
            "interface {interface}",
            "description {description}",
            "switchport mode access",
            "switchport access vlan {vlan_id}",
            "no shutdown",
            "exit",
            "end"
        ]
    },
    'juniper': {
        'VLAN 설정': [
            "configure",
            "set vlans {vlan_name} vlan-id {vlan_id}",
            "commit",
            "exit"
        ],
        'IP 설정': [
            "configure",
            "set interfaces {interface} unit 0 family inet address {ip_address}/{subnet_mask}",
            "commit",
            "exit"
        ],
        '인터페이스 설정': [
            "configure",
            "set interfaces {interface} description \"{description}\"",
            "set interfaces {interface} unit 0 family ethernet-switching vlan members {vlan_id}",
            "commit",
            "exit"
        ]
    },
    'hp': {
        # HP 템플릿 추가
    },
    'arista': {
        # Arista 템플릿 추가
    },
    'handreamnet': {
        # Handream Networks 템플릿 추가
    },
    'coreedge': {
        # CoreEdge Networks 템플릿 추가
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cli/learn', methods=['POST'])
def cli_learn():
    try:
        data = request.get_json()
        vendor = data.get('vendor')
        task_type = data.get('taskType')
        commands = data.get('commands', [])

        if not vendor or not task_type:
            return jsonify({'status': 'error', 'message': '벤더와 작업 유형은 필수입니다.'})

        # 벤더별 학습 파일 경로
        learned_file = os.path.join('tasks', f'{vendor}_learned_commands.json')
        
        # 기존 학습 데이터 로드 또는 새로 생성
        if os.path.exists(learned_file):
            with open(learned_file, 'r', encoding='utf-8') as f:
                learned_data = json.load(f)
        else:
            learned_data = {}

        # 새로운 명령어 저장
        learned_data[task_type] = commands

        # 학습 데이터 저장
        with open(learned_file, 'w', encoding='utf-8') as f:
            json.dump(learned_data, f, indent=2, ensure_ascii=False)

        return jsonify({'status': 'success', 'message': '명령어가 학습되었습니다.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/devices', methods=['GET'])
def get_devices():
    try:
        if not os.path.exists('device_scripts'):
            return jsonify({'status': 'success', 'data': []})
        
        devices = []
        for filename in os.listdir('device_scripts'):
            if filename.endswith('_script.json'):
                file_path = os.path.join('device_scripts', filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        script_data = json.load(f)
                        if 'device_info' in script_data:
                            devices.append(script_data['device_info'])
                except Exception as e:
                    print(f"파일 읽기 오류 ({filename}): {str(e)}")
                    continue
        
        return jsonify({'status': 'success', 'data': devices})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/device/scripts/<device_name>', methods=['GET'])
def get_device_script(device_name):
    try:
        script_file = os.path.join('device_scripts', f'{device_name}_script.json')
        if os.path.exists(script_file):
            with open(script_file, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            return jsonify({'status': 'success', 'data': script_data})
        else:
            return jsonify({'status': 'error', 'message': '스크립트 파일을 찾을 수 없습니다.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/device/<device_name>', methods=['DELETE'])
def delete_device(device_name):
    try:
        script_file = os.path.join('device_scripts', f'{device_name}_script.json')
        if os.path.exists(script_file):
            os.remove(script_file)
            return jsonify({'status': 'success', 'message': '장비가 삭제되었습니다.'})
        else:
            return jsonify({'status': 'error', 'message': '장비를 찾을 수 없습니다.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/script/execute/<device_name>', methods=['POST'])
def execute_script(device_name):
    try:
        script_file = os.path.join('device_scripts', f'{device_name}_script.json')
        if not os.path.exists(script_file):
            return jsonify({'status': 'error', 'message': '스크립트 파일을 찾을 수 없습니다.'})

        with open(script_file, 'r', encoding='utf-8') as f:
            script_data = json.load(f)

        # 여기에 실제 장비 연결 및 명령어 실행 로직 추가
        # 현재는 더미 응답 반환
        return jsonify({'status': 'success', 'message': '스크립트가 실행되었습니다.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    main()
