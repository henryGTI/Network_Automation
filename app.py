import os
import json
from flask import jsonify, Flask, request, render_template
from datetime import datetime
import logging
import shutil

app = Flask(__name__)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 기본 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DEVICES_DIR = os.path.join(DATA_DIR, 'devices')
SCRIPTS_DIR = os.path.join(DATA_DIR, 'scripts')
LEARNING_DIR = os.path.join(DATA_DIR, 'learning')

# VENDOR_PATTERNS를 app.py 상단에 정의
VENDOR_PATTERNS = {
    'cisco': {
        'vlan': {
            'patterns': [
                r'vlan (\d+)',
                r'name (.+)',
                r'state (active|suspend)'
            ],
            'template': 'vlan {vlan_id}\nname {vlan_name}\nstate {state}'
        },
        'interface': {
            'patterns': [
                r'interface (.+)',
                r'switchport mode (access|trunk)',
                r'switchport access vlan (\d+)',
                r'switchport trunk allowed vlan (.+)',
                r'switchport trunk native vlan (\d+)',
                r'speed (auto|10|100|1000)',
                r'duplex (auto|full|half)'
            ],
            'template': 'interface {interface}\nswitchport mode {mode}\nswitchport {access_trunk} vlan {vlan_list}'
        },
        'ip': {
            'patterns': [
                r'ip address (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+)',
                r'ip default-gateway (\d+\.\d+\.\d+\.\d+)',
                r'ip helper-address (\d+\.\d+\.\d+\.\d+)'
            ],
            'template': 'ip address {ip_address} {subnet_mask}'
        },
        'routing': {
            'patterns': [
                r'ip routing',
                r'ip route (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+)',
                r'router ospf (\d+)',
                r'network (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+) area (\d+)',
                r'router bgp (\d+)',
                r'neighbor (\d+\.\d+\.\d+\.\d+) remote-as (\d+)'
            ],
            'template': '...'
        },
        'acl': {
            'patterns': [
                r'access-list (\d+) (permit|deny) (.+)',
                r'ip access-list (standard|extended) (.+)',
                r'permit ip (\S+) (\S+)',
                r'deny ip (\S+) (\S+)'
            ],
            'template': '...'
        },
        'qos': {
            'patterns': [
                r'mls qos',
                r'class-map (.+)',
                r'match (access-group|protocol|dscp) (.+)',
                r'policy-map (.+)',
                r'service-policy (input|output) (.+)'
            ],
            'template': '...'
        },
        'spanning_tree': {
            'patterns': [
                r'spanning-tree mode (pvst|rapid-pvst|mst)',
                r'spanning-tree vlan (\d+) priority (\d+)',
                r'spanning-tree portfast',
                r'spanning-tree guard root'
            ],
            'template': '...'
        },
        'port_channel': {
            'patterns': [
                r'interface port-channel(\d+)',
                r'channel-group (\d+) mode (active|passive|on)',
                r'lacp port-priority (\d+)'
            ],
            'template': '...'
        },
        'dhcp': {
            'patterns': [
                r'ip dhcp pool (.+)',
                r'network (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+)',
                r'default-router (\d+\.\d+\.\d+\.\d+)',
                r'dns-server (\d+\.\d+\.\d+\.\d+)'
            ],
            'template': '...'
        },
        'ntp': {
            'patterns': [
                r'ntp server (\d+\.\d+\.\d+\.\d+)',
                r'ntp source (.+)',
                r'ntp authenticate'
            ],
            'template': '...'
        },
        'snmp': {
            'patterns': [
                r'snmp-server community (.+) (RO|RW)',
                r'snmp-server host (\d+\.\d+\.\d+\.\d+) (.+)',
                r'snmp-server enable traps'
            ],
            'template': '...'
        },
        'syslog': {
            'patterns': [
                r'logging host (\d+\.\d+\.\d+\.\d+)',
                r'logging facility (.+)',
                r'logging level (.+)',
                r'logging source-interface (.+)'
            ],
            'template': '...'
        },
        'radius': {
            'patterns': [
                r'radius-server host (\d+\.\d+\.\d+\.\d+)',
                r'radius-server key (.+)',
                r'aaa new-model'
            ],
            'template': '...'
        },
        'tacacs': {
            'patterns': [
                r'tacacs-server host (\d+\.\d+\.\d+\.\d+)',
                r'tacacs-server key (.+)'
            ],
            'template': '...'
        },
        'ssh': {
            'patterns': [
                r'ip ssh version (\d+)',
                r'crypto key generate rsa',
                r'line vty (\d+) (\d+)',
                r'transport input ssh'
            ],
            'template': '...'
        }
    },
    'arista': {
        # 아리스타의 모든 기능 패턴
    },
    'juniper': {
        # 주니퍼의 모든 기능 패턴
    },
    'hp': {
        # HP의 모든 기능 패턴
    },
    'coreedge': {
        # 코어엣지네트웍스의 모든 기능 패턴
    },
    'handreamnet': {
        # 한드림넷의 모든 기능 패턴
    }
}

def create_directories():
    """필요한 디렉토리 생성"""
    try:
        # 기본 디렉토리 생성
        for dir_path in [DEVICES_DIR, SCRIPTS_DIR, LEARNING_DIR]:
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f'디렉토리 생성/확인: {dir_path}')
    except Exception as e:
        logger.error(f'디렉토리 생성 중 오류: {str(e)}')
        raise

def update_device_info(device_name, vendor, script_filename):
    """장비 정보 업데이트 및 스크립트 정보 추가"""
    try:
        devices_file = os.path.join(DEVICES_DIR, 'devices.json')
        devices = []
        
        # devices.json 파일 읽기 또는 생성
        if os.path.exists(devices_file):
            with open(devices_file, 'r', encoding='utf-8') as f:
                devices = json.load(f)
        
        # 현재 시간
        timestamp = datetime.now().isoformat()
        
        # 장비별 스크립트 디렉토리 생성
        device_script_dir = os.path.join(SCRIPTS_DIR, device_name)
        os.makedirs(device_script_dir, exist_ok=True)
        
        # 기존 장비 정보 업데이트 또는 새로운 장비 추가
        device_found = False
        for device in devices:
            if device['device_name'] == device_name:
                device_found = True
                device.update({
                    'vendor': vendor,
                    'updated_at': timestamp,
                    'script': {
                        'filename': script_filename,
                        'updated_at': timestamp
                    }
                })
                break
        
        if not device_found:
            devices.append({
                'device_name': device_name,
                'vendor': vendor,
                'created_at': timestamp,
                'updated_at': timestamp,
                'script': {
                    'filename': script_filename,
                    'updated_at': timestamp
                }
            })
        
        # devices.json 파일 저장
        with open(devices_file, 'w', encoding='utf-8') as f:
            json.dump(devices, f, indent=2, ensure_ascii=False)
            
        logger.info(f'장비 정보 업데이트 완료: {device_name}')
        
    except Exception as e:
        logger.error(f'장비 정보 업데이트 중 오류: {str(e)}')
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/devices', methods=['GET'])
def get_devices():
    try:
        device_list = []
        if not os.path.exists(DEVICES_DIR):
            app.logger.warning('devices 디렉토리가 존재하지 않습니다.')
            return jsonify({
                'status': 'success',
                'data': []
            })

        for filename in os.listdir(DEVICES_DIR):
            if filename.endswith('_config.json'):
                file_path = os.path.join(DEVICES_DIR, filename)
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
        vendor = data.get('vendor')
        tasks = data.get('tasks', [])

        if not device_name or not vendor:
            return jsonify({'error': '장비 이름과 벤더는 필수입니다.'}), 400

        # 장비별 스크립트 디렉토리 경로
        device_script_dir = os.path.join(SCRIPTS_DIR, device_name)
        
        # 스크립트 파일명 (장비명으로 고정)
        script_filename = f'{device_name}.txt'
        script_path = os.path.join(device_script_dir, script_filename)

        # 스크립트 생성
        try:
            os.makedirs(device_script_dir, exist_ok=True)
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(f'! Device: {device_name}\n')
                f.write(f'! Vendor: {vendor}\n')
                f.write(f'! Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
                
                for task in tasks:
                    task_type = task.get('type')
                    if task_type == 'vlan_config':
                        f.write(f'vlan {task.get("vlan_id")}\n')
                        f.write(f' name {task.get("vlan_name")}\n')
                    elif task_type == 'interface_config':
                        f.write(f'interface {task.get("interface")}\n')
                        f.write(' switchport mode access\n')

            # 장비 정보 업데이트
            update_device_info(device_name, vendor, script_filename)
            
            logger.info(f'스크립트 생성 완료: {script_filename}')
            return jsonify({
                'status': 'success',
                'message': '스크립트가 생성되었습니다.',
                'script_path': script_filename
            })

        except Exception as e:
            logger.error(f'스크립트 생성 중 오류: {str(e)}')
            return jsonify({
                'status': 'error',
                'message': f'스크립트 생성 중 오류가 발생했습니다: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f'요청 처리 중 오류: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'요청 처리 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/devices/<device_name>/execute', methods=['POST'])
def execute_device_script(device_name):
    """스크립트 실행"""
    try:
        script_path = os.path.join(SCRIPTS_DIR, device_name, f'{device_name}.txt')
        if not os.path.exists(script_path):
            return jsonify({'error': '스크립트를 찾을 수 없습니다.'}), 404
            
        # 여기에 실제 스크립트 실행 로직 구현
        # (네트워크 장비 연결 및 명령어 실행)
        
        return jsonify({
            'status': 'success',
            'message': f'{device_name} 스크립트가 실행되었습니다.'
        })
    except Exception as e:
        logger.error(f'스크립트 실행 중 오류: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_name>', methods=['DELETE'])
def delete_device(device_name):
    """장비 및 관련 스크립트 삭제"""
    try:
        # 장비 스크립트 디렉토리 삭제
        device_script_dir = os.path.join(SCRIPTS_DIR, device_name)
        if os.path.exists(device_script_dir):
            shutil.rmtree(device_script_dir)
            
        # devices.json에서 장비 정보 삭제
        devices_file = os.path.join(DEVICES_DIR, 'devices.json')
        if os.path.exists(devices_file):
            with open(devices_file, 'r', encoding='utf-8') as f:
                devices = json.load(f)
                
            devices = [d for d in devices if d['device_name'] != device_name]
            
            with open(devices_file, 'w', encoding='utf-8') as f:
                json.dump(devices, f, indent=2, ensure_ascii=False)
                
        logger.info(f'장비 삭제 완료: {device_name}')
        return jsonify({
            'status': 'success',
            'message': f'{device_name} 장비가 삭제되었습니다.'
        })
    except Exception as e:
        logger.error(f'장비 삭제 중 오류: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<device_name>/script', methods=['GET'])
def get_device_script(device_name):
    """장비 스크립트 조회"""
    try:
        script_path = os.path.join(SCRIPTS_DIR, device_name, f'{device_name}.txt')
        if not os.path.exists(script_path):
            return jsonify({'error': '스크립트를 찾을 수 없습니다.'}), 404
            
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return content
    except Exception as e:
        logger.error(f'스크립트 조회 중 오류: {str(e)}')
        return jsonify({'error': str(e)}), 500

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

        cli_file = os.path.join(DEVICES_DIR, f'{vendor}_cli_commands.json')
        
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

@app.route('/api/validate', methods=['POST'])
def validate_data():
    try:
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': '잘못된 요청 형식입니다. JSON 형식이어야 합니다.'
            }), 400

        data = request.get_json()
        logger.info(f'데이터 검증 요청: {json.dumps(data, indent=2, ensure_ascii=False)}')

        # 필수 필드 검증
        required_fields = {
            'device_name': '장비 이름',
            'vendor': '벤더'
        }

        missing_fields = []
        for field, name in required_fields.items():
            if not data.get(field):
                missing_fields.append(name)

        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'다음 필드가 필요합니다: {", ".join(missing_fields)}'
            }), 400

        # 벤더 검증
        valid_vendors = ['cisco', 'hp', 'arista']
        if data['vendor'].lower() not in valid_vendors:
            return jsonify({
                'status': 'error',
                'message': f'지원하지 않는 벤더입니다. 지원 벤더: {", ".join(valid_vendors)}'
            }), 400

        # 작업 검증
        tasks = data.get('tasks', {})
        if not tasks:
            return jsonify({
                'status': 'error',
                'message': '최소한 하나의 작업을 선택해주세요.'
            }), 400

        # 각 작업별 필수 파라미터 검증
        task_requirements = {
            'vlan_config': ['vlan_id'],
            'interface_config': ['interface_name'],
            'vlan_interface': ['interface_name', 'mode', 'vlan_id'],
            'ip_config': ['interface_name', 'ip_address', 'subnet_mask']
        }

        validation_errors = []
        for task_name, task_info in tasks.items():
            if task_info.get('enabled'):
                if task_name not in task_requirements:
                    validation_errors.append(f'알 수 없는 작업 유형: {task_name}')
                    continue
                
                missing_params = []
                for param in task_requirements[task_name]:
                    if not task_info.get(param):
                        missing_params.append(param)
                
                if missing_params:
                    validation_errors.append(f'{task_name}: 다음 파라미터가 필요합니다: {", ".join(missing_params)}')

        if validation_errors:
            return jsonify({
                'status': 'error',
                'message': '검증 오류가 발생했습니다.',
                'errors': validation_errors
            }), 400

        return jsonify({
            'status': 'success',
            'message': '데이터가 유효합니다.',
            'validated_data': data
        })

    except Exception as e:
        logger.error(f'데이터 검증 중 오류: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'데이터 검증 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/auto-learning', methods=['POST'])
def auto_learning():
    try:
        data = request.get_json()
        if not data or 'vendor' not in data:
            return jsonify({'error': '벤더 정보가 필요합니다.'}), 400
            
        vendor = data['vendor']
        if vendor not in VENDOR_PATTERNS:
            return jsonify({'error': f'지원하지 않는 벤더입니다: {vendor}'}), 400
            
        # 성공 응답
        return jsonify({
            'status': 'success',
            'message': f'{vendor} 벤더의 자동학습이 완료되었습니다.',
            'data': {
                'vendor': vendor,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        app.logger.error(f'자동학습 오류: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-learning/<vendor>', methods=['GET'])
def get_learned_commands(vendor):
    """학습된 명령어 조회 API"""
    try:
        learning_file = os.path.join(LEARNING_DIR, vendor, f'{vendor}_commands.json')
        
        if not os.path.exists(learning_file):
            return jsonify({
                'status': 'warning',
                'message': f'{vendor}의 학습된 명령어가 없습니다.',
                'commands': {}
            })
            
        with open(learning_file, 'r', encoding='utf-8') as f:
            learning_data = json.load(f)
            
        return jsonify({
            'status': 'success',
            'data': learning_data
        })
        
    except Exception as e:
        logger.error(f'학습된 명령어 조회 중 오류: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'학습된 명령어 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 