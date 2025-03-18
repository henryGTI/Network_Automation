import os
import json
from flask import jsonify, Flask, request, render_template
from datetime import datetime
import logging

app = Flask(__name__)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# 벤더별 명령어 패턴 정의
VENDOR_COMMANDS = {
    'cisco': {
        'vlan_config': {
            'show_commands': [
                'show vlan brief',
                'show vlan',
                'show running-config | section vlan'
            ],
            'patterns': {
                'vlan_id': r'vlan (\d+)',
                'vlan_name': r'name (.+)'
            }
        },
        'interface_config': {
            'show_commands': [
                'show interfaces status',
                'show interfaces description',
                'show running-config | section interface'
            ],
            'patterns': {
                'interface_name': r'interface (.+)',
                'description': r'description (.+)',
                'status': r'(shutdown|no shutdown)'
            }
        },
        'vlan_interface': {
            'show_commands': [
                'show interfaces switchport',
                'show vlan',
                'show interfaces trunk'
            ],
            'patterns': {
                'interface_name': r'interface (.+)',
                'mode': r'switchport mode (.+)',
                'vlan_id': r'switchport (access|trunk) vlan (\d+)'
            }
        },
        'ip_config': {
            'show_commands': [
                'show ip interface brief',
                'show running-config | section interface',
                'show ip route'
            ],
            'patterns': {
                'interface_name': r'interface (.+)',
                'ip_address': r'ip address (\d+\.\d+\.\d+\.\d+)',
                'subnet_mask': r'ip address \d+\.\d+\.\d+\.\d+ (\d+\.\d+\.\d+\.\d+)'
            }
        },
        'routing_config': {
            'show_commands': [
                'show ip protocols',
                'show ip route',
                'show running-config | section router'
            ],
            'patterns': {
                'protocol': r'router (\w+)',
                'network': r'network (\d+\.\d+\.\d+\.\d+)',
                'mask': r'mask (\d+\.\d+\.\d+\.\d+)'
            }
        },
        'acl_config': {
            'show_commands': [
                'show access-lists',
                'show running-config | section access-list',
                'show ip access-lists'
            ],
            'patterns': {
                'acl_name': r'ip access-list (\w+)',
                'rule': r'permit|deny'
            }
        },
        'qos_config': {
            'show_commands': [
                'show mls qos',
                'show class-map',
                'show policy-map',
                'show mls qos interface'
            ],
            'patterns': {
                'class_map': r'class-map (\w+)',
                'policy_map': r'policy-map (\w+)'
            }
        },
        'spanning_tree': {
            'show_commands': [
                'show spanning-tree',
                'show spanning-tree summary',
                'show spanning-tree detail'
            ],
            'patterns': {
                'mode': r'spanning-tree mode (\w+)',
                'priority': r'spanning-tree priority (\d+)'
            }
        },
        'port_channel': {
            'show_commands': [
                'show etherchannel summary',
                'show etherchannel port-channel',
                'show running-config | section channel-group'
            ],
            'patterns': {
                'group': r'channel-group (\d+)',
                'mode': r'mode (\w+)'
            }
        },
        'dhcp_config': {
            'show_commands': [
                'show ip dhcp pool',
                'show ip dhcp binding',
                'show running-config | section dhcp'
            ],
            'patterns': {
                'pool_name': r'ip dhcp pool (\w+)',
                'network': r'network (\d+\.\d+\.\d+\.\d+)'
            }
        }
    },
    'hp': {
        'vlan_config': {
            'show_commands': [
                'show vlans',
                'show running-config vlan',
                'display vlan all'
            ]
        },
        'interface_config': {
            'show_commands': [
                'show interfaces brief',
                'show interfaces all',
                'display interface'
            ]
        },
        'vlan_interface': {
            'show_commands': [
                'show interfaces',
                'show vlan ports',
                'display port vlan'
            ]
        },
        'ip_config': {
            'show_commands': [
                'show ip',
                'show ip interface',
                'display ip interface brief'
            ]
        },
        'routing_config': {
            'show_commands': [
                'show ip routing-protocol',
                'show ip route',
                'display ip routing-table'
            ]
        },
        'acl_config': {
            'show_commands': [
                'show access-list',
                'show running-config acl',
                'display acl all'
            ]
        },
        'qos_config': {
            'show_commands': [
                'show qos',
                'show qos interface',
                'display qos-interface'
            ]
        },
        'spanning_tree': {
            'show_commands': [
                'show spanning-tree',
                'show spanning-tree detail',
                'display stp'
            ]
        },
        'port_channel': {
            'show_commands': [
                'show trunk',
                'show lacp',
                'display link-aggregation summary'
            ]
        },
        'dhcp_config': {
            'show_commands': [
                'show ip dhcp',
                'show ip dhcp binding',
                'display dhcp server'
            ]
        }
    },
    'arista': {
        'vlan_config': {
            'show_commands': [
                'show vlan',
                'show running-config vlan',
                'show vlan internal usage'
            ]
        },
        'interface_config': {
            'show_commands': [
                'show interfaces status',
                'show interfaces description',
                'show running-config interfaces'
            ]
        },
        'vlan_interface': {
            'show_commands': [
                'show interfaces switchport',
                'show vlan',
                'show interfaces trunk'
            ]
        },
        'ip_config': {
            'show_commands': [
                'show ip interface',
                'show ip interface brief',
                'show running-config section ip interface'
            ]
        },
        'routing_config': {
            'show_commands': [
                'show ip route summary',
                'show ip protocols',
                'show running-config section router'
            ]
        },
        'acl_config': {
            'show_commands': [
                'show ip access-lists',
                'show running-config section ip access-list',
                'show access-list counters'
            ]
        },
        'qos_config': {
            'show_commands': [
                'show qos interfaces',
                'show qos maps',
                'show running-config section qos'
            ]
        },
        'spanning_tree': {
            'show_commands': [
                'show spanning-tree',
                'show spanning-tree blockedports',
                'show spanning-tree detail'
            ]
        },
        'port_channel': {
            'show_commands': [
                'show port-channel summary',
                'show port-channel load-balance',
                'show running-config section port-channel'
            ]
        },
        'dhcp_config': {
            'show_commands': [
                'show dhcp server',
                'show ip dhcp binding',
                'show running-config section dhcp'
            ]
        }
    },
    'juniper': {
        'vlan_config': {
            'show_commands': [
                'show vlans',
                'show configuration vlans',
                'show ethernet-switching domain'
            ]
        },
        'interface_config': {
            'show_commands': [
                'show interfaces',
                'show interfaces descriptions',
                'show configuration interfaces'
            ]
        },
        'vlan_interface': {
            'show_commands': [
                'show ethernet-switching interfaces',
                'show vlans interface',
                'show configuration interfaces'
            ]
        },
        'ip_config': {
            'show_commands': [
                'show interfaces terse',
                'show configuration interfaces | display set',
                'show route'
            ]
        },
        'routing_config': {
            'show_commands': [
                'show route summary',
                'show protocols',
                'show configuration protocols'
            ]
        },
        'acl_config': {
            'show_commands': [
                'show firewall',
                'show configuration firewall',
                'show firewall counter'
            ]
        },
        'qos_config': {
            'show_commands': [
                'show class-of-service',
                'show configuration class-of-service',
                'show interfaces queue'
            ]
        },
        'spanning_tree': {
            'show_commands': [
                'show spanning-tree bridge',
                'show spanning-tree interface',
                'show configuration protocols mstp'
            ]
        },
        'port_channel': {
            'show_commands': [
                'show lacp interfaces',
                'show interfaces ae0',
                'show configuration interfaces ae0'
            ]
        },
        'dhcp_config': {
            'show_commands': [
                'show dhcp server',
                'show dhcp binding',
                'show configuration system services dhcp'
            ]
        }
    },
    'coreedge': {
        'vlan_config': {
            'show_commands': [
                'show vlan all',
                'show running-config vlan',
                'show vlan summary'
            ]
        },
        'interface_config': {
            'show_commands': [
                'show interface status',
                'show interface description',
                'show running-config interface'
            ]
        },
        'vlan_interface': {
            'show_commands': [
                'show interface switchport',
                'show vlan interface',
                'show running-config interface'
            ]
        },
        'ip_config': {
            'show_commands': [
                'show ip interface brief',
                'show running-config interface',
                'show ip route'
            ]
        },
        'routing_config': {
            'show_commands': [
                'show ip protocols',
                'show ip route summary',
                'show running-config router'
            ]
        },
        'acl_config': {
            'show_commands': [
                'show access-lists',
                'show running-config access-list',
                'show ip access-list'
            ]
        },
        'qos_config': {
            'show_commands': [
                'show qos',
                'show class-map',
                'show policy-map'
            ]
        },
        'spanning_tree': {
            'show_commands': [
                'show spanning-tree',
                'show spanning-tree detail',
                'show running-config spanning-tree'
            ]
        },
        'port_channel': {
            'show_commands': [
                'show port-channel summary',
                'show port-channel detail',
                'show running-config port-channel'
            ]
        },
        'dhcp_config': {
            'show_commands': [
                'show ip dhcp binding',
                'show ip dhcp pool',
                'show running-config dhcp'
            ]
        }
    },
    'handream': {
        'vlan_config': {
            'show_commands': [
                'show vlan',
                'show running-config vlan',
                'show vlan brief'
            ]
        },
        'interface_config': {
            'show_commands': [
                'show interface brief',
                'show interface description',
                'show running-config interface'
            ]
        },
        'vlan_interface': {
            'show_commands': [
                'show interface switchport',
                'show vlan interface',
                'show running-config interface'
            ]
        },
        'ip_config': {
            'show_commands': [
                'show ip interface brief',
                'show running-config interface',
                'show ip route'
            ]
        },
        'routing_config': {
            'show_commands': [
                'show ip protocols',
                'show ip route summary',
                'show running-config router'
            ]
        },
        'acl_config': {
            'show_commands': [
                'show access-lists',
                'show running-config access-list',
                'show ip access-list'
            ]
        },
        'qos_config': {
            'show_commands': [
                'show qos',
                'show class-map',
                'show policy-map'
            ]
        },
        'spanning_tree': {
            'show_commands': [
                'show spanning-tree',
                'show spanning-tree detail',
                'show running-config spanning-tree'
            ]
        },
        'port_channel': {
            'show_commands': [
                'show port-channel summary',
                'show port-channel detail',
                'show running-config port-channel'
            ]
        },
        'dhcp_config': {
            'show_commands': [
                'show ip dhcp binding',
                'show ip dhcp pool',
                'show running-config dhcp'
            ]
        }
    }
}

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
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': '잘못된 요청 형식입니다.'
            }), 400

        data = request.get_json()
        vendor = data.get('vendor', '').lower()

        if not vendor:
            return jsonify({
                'status': 'error',
                'message': '벤더 정보가 필요합니다.'
            }), 400

        # 학습 데이터 수집
        learning_data = {
            'vendor': vendor,
            'timestamp': datetime.now().isoformat(),
            'tasks': {}
        }

        # 모든 작업 유형에 대한 명령어 수집
        for task_name, task_info in VENDOR_COMMANDS[vendor].items():
            learning_data['tasks'][task_name] = {
                'name': get_task_display_name(task_name),
                'show_commands': task_info['show_commands']
            }

        # 학습 데이터 저장
        try:
            # 기본 디렉토리 구조 생성
            base_dir = os.path.dirname(os.path.abspath(__file__))
            learning_dir = os.path.join(base_dir, 'data', 'learning')
            vendor_dir = os.path.join(learning_dir, vendor)
            
            # 디렉토리 생성
            os.makedirs(vendor_dir, exist_ok=True)

            # 파일명 생성 (타임스탬프 포함)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'learning_commands_{timestamp}.json'
            filepath = os.path.join(vendor_dir, filename)
            
            # 데이터 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(learning_data, f, indent=2, ensure_ascii=False)

            logger.info(f'학습 데이터 저장 완료: {filepath}')

            return jsonify({
                'status': 'success',
                'message': '자동학습 데이터가 생성되었습니다.',
                'saved_path': filepath,
                'tasks': learning_data['tasks']
            })

        except Exception as e:
            logger.error(f'학습 데이터 저장 중 오류: {str(e)}')
            return jsonify({
                'status': 'error',
                'message': f'학습 데이터 저장 중 오류가 발생했습니다: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f'자동학습 처리 중 오류: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'자동학습 처리 중 오류가 발생했습니다: {str(e)}'
        }), 500

def get_task_display_name(task_name):
    """작업 유형의 표시 이름을 반환합니다."""
    task_names = {
        'vlan_config': 'VLAN 설정',
        'interface_config': '인터페이스 설정',
        'vlan_interface': 'VLAN 인터페이스 설정',
        'ip_config': 'IP 설정',
        'routing_config': '라우팅 설정',
        'acl_config': 'ACL 설정',
        'qos_config': 'QoS 설정',
        'spanning_tree': '스패닝 트리 설정',
        'port_channel': '포트 채널 설정',
        'dhcp_config': 'DHCP 설정'
    }
    return task_names.get(task_name, task_name)

if __name__ == '__main__':
    app.run(debug=True) 