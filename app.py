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

@app.route('/api/devices/<device_name>/script', methods=['GET'])
def get_device_script(device_name):
    try:
        script_file = os.path.join(DEVICE_SCRIPTS_DIR, f'{device_name}_script.txt')
        if not os.path.exists(script_file):
            return jsonify({
                'status': 'error',
                'message': '스크립트 파일을 찾을 수 없습니다.'
            }), 404

        with open(script_file, 'r', encoding='utf-8') as f:
            script_content = f.read()

        return jsonify({
            'status': 'success',
            'data': script_content
        })

    except Exception as e:
        app.logger.error(f'스크립트 조회 오류: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'스크립트 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/cli/learn', methods=['POST'])
def learn_cli():
    try:
        data = request.get_json()
        vendor = data.get('vendor')

        if not vendor:
            return jsonify({
                'status': 'error',
                'message': '벤더 정보가 필요합니다.'
            }), 400

        # 벤더별 기본 CLI 명령어 정의
        vendor_commands = {
            'cisco': {
                'vlan_config': {
                    'name': 'VLAN 설정',
                    'commands': [
                        'configure terminal',
                        'vlan {vlan_id}',
                        'name {vlan_name}',
                        'exit'
                    ],
                    'parameters': {
                        'vlan_id': 'VLAN 번호 (1-4094)',
                        'vlan_name': 'VLAN 이름'
                    }
                },
                'interface_config': {
                    'name': '인터페이스 설정',
                    'commands': [
                        'configure terminal',
                        'interface {interface_name}',
                        'switchport mode {mode}',
                        'switchport access vlan {vlan_id}',
                        'exit'
                    ],
                    'parameters': {
                        'interface_name': '인터페이스 이름 (예: GigabitEthernet1/0/1)',
                        'mode': '포트 모드 (access/trunk)',
                        'vlan_id': 'VLAN 번호'
                    }
                },
                'port_channel': {
                    'name': '포트 채널 설정',
                    'commands': [
                        'configure terminal',
                        'interface {interface_name}',
                        'channel-group {channel_id} mode {mode}',
                        'exit'
                    ],
                    'parameters': {
                        'interface_name': '인터페이스 이름',
                        'channel_id': '채널 그룹 번호',
                        'mode': '채널 모드 (active/passive/on)'
                    }
                },
                'port_security': {
                    'name': '포트 보안 설정',
                    'commands': [
                        'configure terminal',
                        'interface {interface_name}',
                        'switchport port-security',
                        'switchport port-security maximum {max_addresses}',
                        'switchport port-security violation {violation_mode}',
                        'exit'
                    ],
                    'parameters': {
                        'interface_name': '인터페이스 이름',
                        'max_addresses': '최대 MAC 주소 수',
                        'violation_mode': '위반 모드 (shutdown/restrict/protect)'
                    }
                },
                'storm_control': {
                    'name': '스톰 컨트롤 설정',
                    'commands': [
                        'configure terminal',
                        'interface {interface_name}',
                        'storm-control broadcast level {level}',
                        'storm-control multicast level {level}',
                        'storm-control unicast level {level}',
                        'exit'
                    ],
                    'parameters': {
                        'interface_name': '인터페이스 이름',
                        'level': '임계값 레벨 (백분율)'
                    }
                },
                'static_route': {
                    'name': '정적 라우팅 설정',
                    'commands': [
                        'configure terminal',
                        'ip route {network} {mask} {next_hop}',
                        'exit'
                    ],
                    'parameters': {
                        'network': '대상 네트워크',
                        'mask': '서브넷 마스크',
                        'next_hop': '다음 홉 주소'
                    }
                },
                'dynamic_route': {
                    'name': '동적 라우팅 설정',
                    'commands': [
                        'configure terminal',
                        'router {protocol}',
                        'network {network} {wildcard_mask} area {area_id}',
                        'exit'
                    ],
                    'parameters': {
                        'protocol': '라우팅 프로토콜 (예: ospf, eigrp)',
                        'network': '네트워크 주소',
                        'wildcard_mask': '와일드카드 마스크',
                        'area_id': '영역 ID'
                    }
                },
                'acl': {
                    'name': 'ACL 설정',
                    'commands': [
                        'configure terminal',
                        'ip access-list {acl_type} {acl_name}',
                        '{action} {protocol} {source} {destination}',
                        'exit'
                    ],
                    'parameters': {
                        'acl_type': 'ACL 타입 (standard/extended)',
                        'acl_name': 'ACL 이름',
                        'action': '허용/거부 (permit/deny)',
                        'protocol': '프로토콜',
                        'source': '출발지',
                        'destination': '목적지'
                    }
                },
                'aaa': {
                    'name': 'AAA 설정',
                    'commands': [
                        'configure terminal',
                        'aaa new-model',
                        'aaa authentication login {list_name} {method1} {method2}',
                        'aaa authorization network {list_name} {method1} {method2}',
                        'exit'
                    ],
                    'parameters': {
                        'list_name': '인증 목록 이름',
                        'method1': '첫 번째 인증 방법',
                        'method2': '두 번째 인증 방법'
                    }
                },
                'snmp': {
                    'name': 'SNMP 설정',
                    'commands': [
                        'configure terminal',
                        'snmp-server community {community_string} {access_type}',
                        'snmp-server host {host_ip} version {version} {community_string}',
                        'exit'
                    ],
                    'parameters': {
                        'community_string': '커뮤니티 문자열',
                        'access_type': '접근 타입 (ro/rw)',
                        'host_ip': 'SNMP 서버 IP',
                        'version': 'SNMP 버전'
                    }
                },
                'syslog': {
                    'name': 'Syslog 설정',
                    'commands': [
                        'configure terminal',
                        'logging {syslog_server}',
                        'logging trap {logging_level}',
                        'logging facility {facility_type}',
                        'exit'
                    ],
                    'parameters': {
                        'syslog_server': 'Syslog 서버 IP',
                        'logging_level': '로깅 레벨',
                        'facility_type': '시설 유형'
                    }
                },
                'ntp': {
                    'name': 'NTP 설정',
                    'commands': [
                        'configure terminal',
                        'ntp server {ntp_server}',
                        'ntp source {source_interface}',
                        'exit'
                    ],
                    'parameters': {
                        'ntp_server': 'NTP 서버 IP',
                        'source_interface': '소스 인터페이스'
                    }
                }
            },
            'juniper': {
                'vlan_config': {
                    'name': 'VLAN 설정',
                    'commands': [
                        'configure',
                        'set vlans {vlan_name} vlan-id {vlan_id}',
                        'commit'
                    ],
                    'parameters': {
                        'vlan_name': 'VLAN 이름',
                        'vlan_id': 'VLAN 번호 (1-4094)'
                    }
                },
                'interface_config': {
                    'name': '인터페이스 설정',
                    'commands': [
                        'configure',
                        'set interfaces {interface_name} unit 0 family ethernet-switching',
                        'set interfaces {interface_name} unit 0 family ethernet-switching port-mode {mode}',
                        'set interfaces {interface_name} unit 0 family ethernet-switching vlan members {vlan_id}',
                        'commit'
                    ],
                    'parameters': {
                        'interface_name': '인터페이스 이름 (예: ge-0/0/1)',
                        'mode': '포트 모드 (access/trunk)',
                        'vlan_id': 'VLAN 번호'
                    }
                },
                'port_channel': {
                    'name': '포트 채널 설정',
                    'commands': [
                        'configure',
                        'set chassis aggregated-devices ethernet device-count {ae_count}',
                        'set interfaces {interface_name} ether-options 802.3ad ae{ae_number}',
                        'set interfaces ae{ae_number} aggregated-ether-options lacp {lacp_mode}',
                        'commit'
                    ],
                    'parameters': {
                        'ae_count': '애그리게이트 인터페이스 수',
                        'interface_name': '물리 인터페이스 이름',
                        'ae_number': '애그리게이트 인터페이스 번호',
                        'lacp_mode': 'LACP 모드 (active/passive)'
                    }
                }
            },
            'hp': {
                'vlan_config': {
                    'name': 'VLAN 설정',
                    'commands': [
                        'configure',
                        'vlan {vlan_id}',
                        'name {vlan_name}',
                        'exit'
                    ],
                    'parameters': {
                        'vlan_id': 'VLAN 번호 (1-4094)',
                        'vlan_name': 'VLAN 이름'
                    }
                },
                'interface_config': {
                    'name': '인터페이스 설정',
                    'commands': [
                        'configure',
                        'interface {interface_name}',
                        'switchport mode {mode}',
                        'switchport access vlan {vlan_id}',
                        'exit'
                    ],
                    'parameters': {
                        'interface_name': '인터페이스 이름',
                        'mode': '포트 모드 (access/trunk)',
                        'vlan_id': 'VLAN 번호'
                    }
                }
            },
            'arista': {
                'vlan_config': {
                    'name': 'VLAN 설정',
                    'commands': [
                        'configure terminal',
                        'vlan {vlan_id}',
                        'name {vlan_name}',
                        'exit'
                    ],
                    'parameters': {
                        'vlan_id': 'VLAN 번호 (1-4094)',
                        'vlan_name': 'VLAN 이름'
                    }
                },
                'interface_config': {
                    'name': '인터페이스 설정',
                    'commands': [
                        'configure terminal',
                        'interface {interface_name}',
                        'switchport mode {mode}',
                        'switchport access vlan {vlan_id}',
                        'exit'
                    ],
                    'parameters': {
                        'interface_name': '인터페이스 이름',
                        'mode': '포트 모드 (access/trunk)',
                        'vlan_id': 'VLAN 번호'
                    }
                }
            },
            'handreamnet': {
                'vlan_config': {
                    'name': 'VLAN 설정',
                    'commands': [
                        'configure terminal',
                        'vlan {vlan_id}',
                        'name {vlan_name}',
                        'exit'
                    ],
                    'parameters': {
                        'vlan_id': 'VLAN 번호 (1-4094)',
                        'vlan_name': 'VLAN 이름'
                    }
                }
            },
            'coreedge': {
                'vlan_config': {
                    'name': 'VLAN 설정',
                    'commands': [
                        'configure terminal',
                        'vlan {vlan_id}',
                        'name {vlan_name}',
                        'exit'
                    ],
                    'parameters': {
                        'vlan_id': 'VLAN 번호 (1-4094)',
                        'vlan_name': 'VLAN 이름'
                    }
                }
            }
        }

        # 선택된 벤더의 CLI 명령어 가져오기
        if vendor not in vendor_commands:
            return jsonify({
                'status': 'error',
                'message': f'지원되지 않는 벤더입니다: {vendor}'
            }), 400

        cli_file = os.path.join(TASKS_DIR, f'{vendor}_cli_commands.json')
        
        # CLI 명령어 저장
        with open(cli_file, 'w', encoding='utf-8') as f:
            json.dump(vendor_commands[vendor], f, indent=4, ensure_ascii=False)

        return jsonify({
            'status': 'success',
            'message': f'{vendor}의 CLI 명령어 학습이 완료되었습니다.',
            'file_path': cli_file
        })

    except Exception as e:
        app.logger.error(f'CLI 명령어 학습 오류: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'CLI 명령어 학습 중 오류가 발생했습니다: {str(e)}'
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