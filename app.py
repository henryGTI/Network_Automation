import os
import json
from flask import jsonify, Flask, request, render_template
from datetime import datetime

app = Flask(__name__)

# 디렉토리 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(BASE_DIR, 'tasks')
DEVICE_SCRIPTS_DIR = os.path.join(BASE_DIR, 'device_scripts')

# 디렉토리 생성
for directory in [TASKS_DIR, DEVICE_SCRIPTS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# 전역 변수
devices = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/devices', methods=['GET'])
def get_devices():
    try:
        device_list = []
        if not os.path.exists(TASKS_DIR):
            app.logger.warning('tasks 디렉토리가 존재하지 않습니다.')
            return jsonify({
                'status': 'success',
                'data': []
            })

        for filename in os.listdir(TASKS_DIR):
            if filename.endswith('_config.json'):
                file_path = os.path.join(TASKS_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # device_info 대신 전체 데이터를 사용
                        device_info = {
                            'device_name': data.get('device_name'),
                            'device_type': data.get('device_type'),
                            'vendor': data.get('vendor')
                        }
                        
                        if not device_info['device_name']:
                            app.logger.warning(f'장비 이름이 없는 데이터: {file_path}')
                            continue
                            
                        device_list.append(device_info)
                except json.JSONDecodeError as je:
                    app.logger.error(f'JSON 파싱 오류 ({file_path}): {str(je)}')
                    continue
                except Exception as e:
                    app.logger.error(f'파일 읽기 오류 ({file_path}): {str(e)}')
                    continue
        
        app.logger.info(f'조회된 장비 수: {len(device_list)}')
        return jsonify({
            'status': 'success',
            'data': device_list
        })
    except Exception as e:
        app.logger.error(f'장비 목록 조회 오류: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'장비 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/devices/script', methods=['POST'])
def create_device_script():
    try:
        data = request.get_json()
        device_name = data.get('device_name')
        
        if not device_name:
            return jsonify({
                'status': 'error',
                'message': '장비 이름이 필요합니다.'
            }), 400

        # 설정 파일 저장
        config_file = os.path.join(TASKS_DIR, f'{device_name}_config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # 스크립트 생성
        script_content = generate_device_script(data)
        script_file = os.path.join(DEVICE_SCRIPTS_DIR, f'{device_name}_script.txt')
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)

        return jsonify({
            'status': 'success',
            'message': '스크립트가 생성되었습니다.',
            'config_path': config_file,
            'script_path': script_file
        })

    except Exception as e:
        app.logger.error(f'스크립트 생성 오류: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/devices/<device_name>/execute', methods=['POST'])
def execute_device_script(device_name):
    try:
        script_file = os.path.join(DEVICE_SCRIPTS_DIR, f'{device_name}_script.txt')
        if not os.path.exists(script_file):
            return jsonify({
                'status': 'error',
                'message': '스크립트 파일을 찾을 수 없습니다.'
            }), 404

        # 여기에 실제 스크립트 실행 로직 추가
        return jsonify({
            'status': 'success',
            'message': f'{device_name} 스크립트 실행 완료'
        })

    except Exception as e:
        app.logger.error(f'스크립트 실행 오류: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/devices/<device_name>', methods=['DELETE'])
def delete_device(device_name):
    try:
        config_file = os.path.join(TASKS_DIR, f'{device_name}_config.json')
        script_file = os.path.join(DEVICE_SCRIPTS_DIR, f'{device_name}_script.txt')

        # 파일 삭제
        for file in [config_file, script_file]:
            if os.path.exists(file):
                os.remove(file)

        return jsonify({
            'status': 'success',
            'message': f'{device_name} 삭제 완료'
        })

    except Exception as e:
        app.logger.error(f'장비 삭제 오류: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def generate_device_script(data):
    """장비 스크립트 생성"""
    commands = []
    tasks = data.get('tasks', {})
    
    if tasks.get('VLAN 생성/삭제'):
        commands.extend([
            'configure terminal',
            'vlan 10',
            'name TEST_VLAN',
            'exit'
        ])
    
    return '\n'.join(commands)

if __name__ == '__main__':
    app.run(debug=True) 