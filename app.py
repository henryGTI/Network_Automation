import os
import json
from flask import jsonify, Flask, request, render_template, send_from_directory
from datetime import datetime
import logging
import shutil
from pathlib import Path
from flask_cors import CORS  # CORS 지원 추가

app = Flask(__name__)
CORS(app)  # CORS 활성화

# 로깅 설정
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# 데이터 저장 경로 설정
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
DEVICES_DIR = DATA_DIR / 'devices'
DEVICES_FILE = DEVICES_DIR / 'devices.json'
SCRIPTS_DIR = DATA_DIR / 'scripts'
LEARNING_DIR = DATA_DIR / 'learning'
VENDOR_COMMANDS_FILE = LEARNING_DIR / 'vendor_commands.json'

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

# 벤더별 명령어 패턴 정의
VENDOR_COMMANDS = {
    'cisco': {
        'vlan_config': {
            'name': 'VLAN 설정',
            'template': [
                'vlan {vlan_id}',
                'name {vlan_name}'
            ],
            'parameters': {
                'vlan_id': 'VLAN 번호 (1-4094)',
                'vlan_name': 'VLAN 이름'
            }
        },
        'interface_config': {
            'name': '인터페이스 설정',
            'patterns': [
                r'interface (.+)',
                r'switchport mode (access|trunk)',
                r'switchport access vlan (\d+)',
                r'switchport trunk allowed vlan (.+)',
                r'switchport trunk native vlan (\d+)',
                r'speed (auto|10|100|1000)',
                r'duplex (auto|full|half)'
            ],
            'show_commands': [
                'show interfaces',
                'show configuration interfaces'
            ],
            'template': 'interface {interface}\nswitchport mode {mode}\nswitchport {access_trunk} vlan {vlan_list}'
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
            'name': 'VLAN 생성/삭제',
            'patterns': [
                r'set vlans (\w+) vlan-id (\d+)',
                r'set vlans (\w+) description (.+)'
            ],
            'show_commands': [
                'show vlans',
                'show configuration vlans'
            ],
            'template': [
                'configure',
                'set vlans {vlan_name} vlan-id {vlan_id}',
                'set vlans {vlan_name} description {description}',
                'commit'
            ]
        },
        'interface_config': {
            'name': '인터페이스 설정',
            'patterns': [
                r'set interfaces (\S+) description (.+)',
                r'set interfaces (\S+) (disable|enable)'
            ],
            'show_commands': [
                'show interfaces',
                'show configuration interfaces'
            ],
            'template': [
                'configure',
                'set interfaces {interface_name} description {description}',
                'set interfaces {interface_name} {status}',
                'commit'
            ]
        },
        'vlan_interface': {
            'name': 'VLAN 인터페이스 설정',
            'patterns': [
                r'set interfaces (\S+) unit 0 family ethernet-switching port-mode (access|trunk)',
                r'set interfaces (\S+) unit 0 family ethernet-switching vlan members (\d+)'
            ],
            'show_commands': [
                'show ethernet-switching interfaces',
                'show configuration interfaces'
            ],
            'template': [
                'configure',
                'set interfaces {interface_name} unit 0 family ethernet-switching port-mode {mode}',
                'set interfaces {interface_name} unit 0 family ethernet-switching vlan members {vlan_id}',
                'commit'
            ]
        },
        'ip_config': {
            'name': 'IP 주소 설정',
            'patterns': [
                r'set interfaces (\S+) unit (\d+) family inet address (\d+\.\d+\.\d+\.\d+/\d+)'
            ],
            'show_commands': [
                'show interfaces terse',
                'show configuration interfaces'
            ],
            'template': [
                'configure',
                'set interfaces {interface_name} unit {unit} family inet address {ip_address}',
                'commit'
            ]
        },
        'routing_config': {
            'name': '라우팅 설정',
            'patterns': [
                r'set protocols (ospf|bgp) area (\d+) interface (\S+)',
                r'set protocols ospf area (\d+) interface (\S+) metric (\d+)'
            ],
            'show_commands': [
                'show route',
                'show configuration protocols'
            ],
            'template': [
                'configure',
                'set protocols {protocol} area {area} interface {interface}',
                'commit'
            ]
        },
        'acl_config': {
            'name': 'ACL 설정',
            'patterns': [
                r'set firewall family inet filter (\S+) term (\S+) then (accept|reject)',
                r'set firewall family inet filter (\S+) term (\S+) from destination-address (\S+)'
            ],
            'show_commands': [
                'show firewall',
                'show configuration firewall'
            ],
            'template': [
                'configure',
                'set firewall family inet filter {filter_name} term {term_name} then {action}',
                'commit'
            ]
        },
        'snmp_config': {
            'name': 'SNMP 설정',
            'patterns': [
                r'set snmp community (\S+) authorization (read-only|read-write)',
                r'set snmp trap-group (\S+) targets (\S+)'
            ],
            'show_commands': [
                'show snmp statistics',
                'show configuration snmp'
            ],
            'template': [
                'configure',
                'set snmp community {community_name} authorization {access_level}',
                'commit'
            ]
        },
        'ntp_config': {
            'name': 'NTP 설정',
            'patterns': [
                r'set system ntp server (\S+)',
                r'set system ntp boot-server (\S+)'
            ],
            'show_commands': [
                'show ntp associations',
                'show configuration system ntp'
            ],
            'template': [
                'configure',
                'set system ntp server {ntp_server}',
                'commit'
            ]
        }
    },
    'hp': {
        'vlan_config': {
            'name': 'VLAN 생성/삭제',
            'patterns': [
                r'vlan (\d+)',
                r'name (.+)'
            ],
            'show_commands': [
                'show vlan',
                'show running-config vlan'
            ],
            'template': [
                'config',
                'vlan {vlan_id}',
                'name {vlan_name}',
                'exit'
            ]
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
            'name': 'VLAN 생성/삭제',
            'patterns': [
                r'vlan (\d+)',
                r'name (.+)'
            ],
            'show_commands': [
                'show vlan',
                'show running-config | section vlan'
            ],
            'template': [
                'configure terminal',
                'vlan {vlan_id}',
                'name {vlan_name}',
                'exit'
            ]
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
            'name': 'VLAN 생성/삭제',
            'patterns': [
                r'vlan (\d+)',
                r'name (.+)'
            ],
            'show_commands': [
                'show vlan',
                'show running-config vlan'
            ],
            'template': [
                'configure terminal',
                'vlan {vlan_id}',
                'name {vlan_name}',
                'exit'
            ]
        }
    },
    'coreedge': {
        'vlan_config': {
            'name': 'VLAN 생성/삭제',
            'patterns': [
                r'create vlan (\w+) tag (\d+)',
                r'config vlan (\w+) name (.+)'
            ],
            'show_commands': [
                'show vlan',
                'show config current_config include vlan'
            ],
            'template': [
                'create vlan {vlan_name} tag {vlan_id}',
                'config vlan {vlan_name} name {description}'
            ]
        }
    }
}

# 스크립트 저장 경로 추가
SCRIPTS_DIR = DATA_DIR / 'scripts'

# 학습 데이터 경로 설정
DATA_DIR = Path(__file__).parent / 'data'
LEARNING_DIR = DATA_DIR / 'learning'
VENDOR_COMMANDS_FILE = LEARNING_DIR / 'vendor_commands.json'

# 벤더 매핑 확장
VENDOR_MAPPING = {
    'cisco': 'cisco',
    'cisco systems': 'cisco',
    'cisco_ios': 'cisco',
    'juniper': 'juniper',
    'juniper networks': 'juniper',
    'huawei': 'huawei',
    'arista': 'arista',
    'hp': 'hp',
    'hewlett packard': 'hp',
    'hp enterprise': 'hp',
    'handreamnet': 'handreamnet',
    '한드림넷': 'handreamnet',
    'coreedge': 'coreedge',
    'coreedgenetworks': 'coreedge',
    '코어엣지네트웍스': 'coreedge',
    '코어엣지': 'coreedge'
}

# 기본 벤더 명령어 템플릿 확장
DEFAULT_VENDOR_COMMANDS = {
    "cisco": {
        # 기존 Cisco 템플릿 유지
    },
    "handreamnet": {
        "vlan": {
            "create": "vlan database\nvlan {vlan_id}",
            "name": "vlan name {vlan_id} {vlan_name}",
            "delete": "vlan database\nno vlan {vlan_id}",
            "interface": "interface {interface}",
            "access": "switchport mode access",
            "assign": "switchport access vlan {vlan_id}",
            "trunk": "switchport mode trunk",
            "allow": "switchport trunk allowed vlan add {vlan_id}"
        },
        "port": {
            "interface": "interface {interface}",
            "mode_access": "switchport mode access",
            "mode_trunk": "switchport mode trunk",
            "speed": "speed {speed}",
            "duplex": "duplex {duplex}",
            "shutdown": "shutdown",
            "no_shutdown": "no shutdown"
        },
        "routing": {
            "static": "ip route {network} {mask} {next_hop}",
            "ospf_network": "network {network} {wildcard} area {area}",
            "eigrp_network": "network {network} {wildcard}",
            "bgp_neighbor": "neighbor {neighbor_ip} remote-as {remote_as}"
        },
        "security": {
            "port_security": "port-security",
            "max_mac": "port-security maximum {max_addresses}",
            "violation": "port-security violation {violation_mode}",
            "access_list": "access-list {acl_number} {action} {protocol} {source} {destination}"
        }
    },
    "coreedge": {
        "vlan": {
            "create": "vlan {vlan_id}",
            "name": "name {vlan_name}",
            "delete": "no vlan {vlan_id}",
            "interface": "interface {interface}",
            "access": "switchport mode access",
            "assign": "switchport access vlan {vlan_id}",
            "trunk": "switchport mode trunk",
            "allow": "switchport trunk allowed vlan add {vlan_id}"
        },
        "port": {
            "interface": "interface {interface}",
            "mode_access": "switchport mode access",
            "mode_trunk": "switchport mode trunk",
            "speed": "speed-duplex {speed}-{duplex}",
            "shutdown": "shutdown",
            "no_shutdown": "no shutdown"
        },
        "routing": {
            "static": "ip route {network} {mask} {next_hop}",
            "ospf_network": "router ospf {process_id}\nnetwork {network} {wildcard} area {area}",
            "eigrp_network": "router eigrp {as_number}\nnetwork {network} {wildcard}",
            "bgp_neighbor": "router bgp {as_number}\nneighbor {neighbor_ip} remote-as {remote_as}"
        },
        "security": {
            "port_security": "port-security",
            "max_mac": "port-security maximum {max_addresses}",
            "violation": "port-security violation {violation_mode}",
            "access_list": "access-list {acl_number} {action} {protocol} {source} {destination}"
        }
    }
}

def init_learning_data():
    """학습 데이터 디렉토리 및 파일 초기화"""
    try:
        # 디렉토리 생성
        LEARNING_DIR.mkdir(parents=True, exist_ok=True)
        
        # 현재 저장된 벤더 명령어 로드
        current_commands = {}
        if VENDOR_COMMANDS_FILE.exists():
            with open(VENDOR_COMMANDS_FILE, 'r', encoding='utf-8') as f:
                current_commands = json.load(f)
        
        # 새로운 벤더 명령어 추가 또는 업데이트
        updated = False
        for vendor, commands in DEFAULT_VENDOR_COMMANDS.items():
            if vendor not in current_commands:
                current_commands[vendor] = commands
                updated = True
                logger.info(f"새로운 벤더 추가됨: {vendor}")
        
        # 변경사항이 있을 경우에만 파일 저장
        if updated or not VENDOR_COMMANDS_FILE.exists():
            with open(VENDOR_COMMANDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(current_commands, f, ensure_ascii=False, indent=2)
                logger.info(f"벤더 명령어 파일 업데이트됨: {VENDOR_COMMANDS_FILE}")
        
        return True
    except Exception as e:
        logger.error(f"학습 데이터 초기화 오류: {str(e)}")
        return False

def load_vendor_commands():
    """벤더별 학습된 CLI 명령어 로드"""
    try:
        # 파일이 없으면 초기화
        if not VENDOR_COMMANDS_FILE.exists():
            init_learning_data()
        
        with open(VENDOR_COMMANDS_FILE, 'r', encoding='utf-8') as f:
            commands = json.load(f)
            logger.debug(f"벤더 명령어 로드됨: {len(commands)} 벤더")
            return commands
    except Exception as e:
        logger.error(f"벤더 명령어 로드 오류: {str(e)}")
        return DEFAULT_VENDOR_COMMANDS

def save_vendor_commands(commands):
    """벤더별 CLI 명령어 저장"""
    try:
        LEARNING_DIR.mkdir(parents=True, exist_ok=True)
        with open(VENDOR_COMMANDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(commands, f, ensure_ascii=False, indent=2)
        logger.info("벤더 명령어 저장 완료")
        return True
    except Exception as e:
        logger.error(f"벤더 명령어 저장 오류: {str(e)}")
        return False

def init_data_directories():
    """데이터 디렉토리 및 파일 초기화"""
    try:
        # 디렉토리 생성
        directories = [
            DATA_DIR,
            DEVICES_DIR,
            DATA_DIR / 'scripts',
            DATA_DIR / 'learning'
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"디렉토리 확인: {directory}")

        # devices.json 파일 초기화
        if not DEVICES_FILE.exists():
            with open(DEVICES_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            logger.info(f"devices.json 파일 생성됨: {DEVICES_FILE}")
        else:
            # 파일이 존재하지만 비어있거나 손상된 경우 처리
            try:
                with open(DEVICES_FILE, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError:
                logger.warning("손상된 devices.json 파일을 재생성합니다.")
                with open(DEVICES_FILE, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        logger.error(f"초기화 중 오류 발생: {str(e)}")
        return False

def load_devices():
    """장비 목록 로드"""
    try:
        devices_file = DATA_DIR / 'devices' / 'devices.json'
        if devices_file.exists():
            with open(devices_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"장비 목록 로드 오류: {str(e)}")
        return []

def save_devices(devices):
    """장비 목록 저장"""
    try:
        devices_dir = DATA_DIR / 'devices'
        devices_dir.mkdir(parents=True, exist_ok=True)
        
        devices_file = devices_dir / 'devices.json'
        with open(devices_file, 'w', encoding='utf-8') as f:
            json.dump(devices, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"장비 목록 저장 오류: {str(e)}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/devices', methods=['GET', 'POST'])  # POST 메소드 명시적 허용
def handle_devices():
    if request.method == 'GET':
        devices = load_devices()
        return jsonify({
            'status': 'success',
            'data': devices
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': '잘못된 요청 데이터'
                }), 400

            # 필수 필드 검증
            required_fields = ['name', 'vendor', 'ip']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({
                        'status': 'error',
                        'message': f'{field} 필드가 필요합니다.'
                    }), 400

            devices = load_devices()
            
            # 중복 검사
            for device in devices:
                if device['name'] == data['name']:
                    return jsonify({
                        'status': 'error',
                        'message': '이미 존재하는 장비 이름입니다.'
                    }), 400
                if device['ip'] == data['ip']:
                    return jsonify({
                        'status': 'error',
                        'message': '이미 존재하는 IP 주소입니다.'
                    }), 400

            # 새 장비 추가
            new_device = {
                'name': data['name'].strip(),
                'vendor': data['vendor'].strip(),
                'ip': data['ip'].strip()
            }
            
            devices.append(new_device)
            
            if save_devices(devices):
                return jsonify({
                    'status': 'success',
                    'data': new_device
                }), 201
            else:
                return jsonify({
                    'status': 'error',
                    'message': '장비 저장 중 오류가 발생했습니다.'
                }), 500

        except Exception as e:
            print(f"장비 추가 오류: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': '장비 추가 중 오류가 발생했습니다.'
            }), 500

@app.route('/api/devices/<name>', methods=['DELETE'])
def delete_device(name):
    """장비 및 관련 스크립트 삭제"""
    try:
        # 1. 장비 목록에서 삭제
        devices = load_devices()
        device = next((d for d in devices if d['name'] == name), None)
        
        if not device:
            return jsonify({
                'status': 'error',
                'message': f'장비를 찾을 수 없습니다: {name}'
            }), 404

        devices = [d for d in devices if d['name'] != name]
        
        # 2. 장비 관련 스크립트 디렉토리 삭제
        device_script_dir = SCRIPTS_DIR / name
        if device_script_dir.exists():
            try:
                shutil.rmtree(device_script_dir)
                logger.info(f"장비 스크립트 디렉토리 삭제됨: {device_script_dir}")
            except Exception as e:
                logger.error(f"스크립트 디렉토리 삭제 실패: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': '스크립트 삭제 중 오류가 발생했습니다.'
                }), 500

        # 3. 장비 목록 파일 업데이트
        if save_devices(devices):
            return jsonify({
                'status': 'success',
                'message': f'장비 {name}와 관련 스크립트가 삭제되었습니다.'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': '장비 목록 저장 중 오류가 발생했습니다.'
            }), 500

    except Exception as e:
        logger.error(f"장비 삭제 오류: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '장비 삭제 중 오류가 발생했습니다.'
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
                        'set vlans {vlan_name} vlan-id {vlan_id}',
                        'set vlans {vlan_name} description {description}'
                    ],
                    'show_commands': [
                        'show vlans',
                        'show configuration vlans'
                    ],
                    'template': [
                        'edit',
                        'set vlans {vlan_name} vlan-id {vlan_id}',
                        'set vlans {vlan_name} description {description}',
                        'commit'
                    ]
                },
                'interface_config': {
                    'name': '인터페이스 설정',
                    'patterns': [
                        r'set interfaces (\S+) description (.+)',
                        r'set interfaces (\S+) (disable|enable)'
                    ],
                    'show_commands': [
                        'show interfaces',
                        'show configuration interfaces'
                    ],
                    'template': [
                        'configure',
                        'set interfaces {interface_name} description {description}',
                        'set interfaces {interface_name} {status}',
                        'commit'
                    ]
                },
                'vlan_interface': {
                    'name': 'VLAN 인터페이스 설정',
                    'patterns': [
                        r'set interfaces (\S+) unit 0 family ethernet-switching port-mode (access|trunk)',
                        r'set interfaces (\S+) unit 0 family ethernet-switching vlan members (\d+)'
                    ],
                    'show_commands': [
                        'show ethernet-switching interfaces',
                        'show configuration interfaces'
                    ],
                    'template': [
                        'configure',
                        'set interfaces {interface_name} unit 0 family ethernet-switching port-mode {mode}',
                        'set interfaces {interface_name} unit 0 family ethernet-switching vlan members {vlan_id}',
                        'commit'
                    ]
                },
                'ip_config': {
                    'name': 'IP 주소 설정',
                    'patterns': [
                        r'set interfaces (\S+) unit (\d+) family inet address (\d+\.\d+\.\d+\.\d+/\d+)'
                    ],
                    'show_commands': [
                        'show interfaces terse',
                        'show configuration interfaces'
                    ],
                    'template': [
                        'configure',
                        'set interfaces {interface_name} unit {unit} family inet address {ip_address}',
                        'commit'
                    ]
                },
                'routing_config': {
                    'name': '라우팅 설정',
                    'patterns': [
                        r'set protocols (ospf|bgp) area (\d+) interface (\S+)',
                        r'set protocols ospf area (\d+) interface (\S+) metric (\d+)'
                    ],
                    'show_commands': [
                        'show route',
                        'show configuration protocols'
                    ],
                    'template': [
                        'configure',
                        'set protocols {protocol} area {area} interface {interface}',
                        'commit'
                    ]
                },
                'acl_config': {
                    'name': 'ACL 설정',
                    'patterns': [
                        r'set firewall family inet filter (\S+) term (\S+) then (accept|reject)',
                        r'set firewall family inet filter (\S+) term (\S+) from destination-address (\S+)'
                    ],
                    'show_commands': [
                        'show firewall',
                        'show configuration firewall'
                    ],
                    'template': [
                        'configure',
                        'set firewall family inet filter {filter_name} term {term_name} then {action}',
                        'commit'
                    ]
                },
                'snmp_config': {
                    'name': 'SNMP 설정',
                    'patterns': [
                        r'set snmp community (\S+) authorization (read-only|read-write)',
                        r'set snmp trap-group (\S+) targets (\S+)'
                    ],
                    'show_commands': [
                        'show snmp statistics',
                        'show configuration snmp'
                    ],
                    'template': [
                        'configure',
                        'set snmp community {community_name} authorization {access_level}',
                        'commit'
                    ]
                },
                'ntp_config': {
                    'name': 'NTP 설정',
                    'patterns': [
                        r'set system ntp server (\S+)',
                        r'set system ntp boot-server (\S+)'
                    ],
                    'show_commands': [
                        'show ntp associations',
                        'show configuration system ntp'
                    ],
                    'template': [
                        'configure',
                        'set system ntp server {ntp_server}',
                        'commit'
                    ]
                }
            },
            'hp': {
                'vlan_config': {
                    'name': 'VLAN 설정',
                    'patterns': [
                        r'vlan (\d+)',
                        r'name (.+)'
                    ],
                    'show_commands': [
                        'show vlan',
                        'show running-config vlan'
                    ],
                    'template': [
                        'config',
                        'vlan {vlan_id}',
                        'name {vlan_name}',
                        'exit'
                    ]
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
                    'patterns': [
                        r'vlan (\d+)',
                        r'name (.+)'
                    ],
                    'show_commands': [
                        'show vlan',
                        'show running-config | section vlan'
                    ],
                    'template': [
                        'configure terminal',
                        'vlan {vlan_id}',
                        'name {vlan_name}',
                        'exit'
                    ]
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
                    'patterns': [
                        r'vlan (\d+)',
                        r'name (.+)'
                    ],
                    'show_commands': [
                        'show vlan',
                        'show running-config vlan'
                    ],
                    'template': [
                        'configure terminal',
                        'vlan {vlan_id}',
                        'name {vlan_name}',
                        'exit'
                    ]
                }
            },
            'coreedge': {
                'vlan_config': {
                    'name': 'VLAN 설정',
                    'patterns': [
                        r'create vlan (\w+) tag (\d+)',
                        r'config vlan (\w+) name (.+)'
                    ],
                    'show_commands': [
                        'show vlan',
                        'show config current_config include vlan'
                    ],
                    'template': [
                        'create vlan {vlan_name} tag {vlan_id}',
                        'config vlan {vlan_name} name {description}'
                    ]
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
    """자동 학습 API 엔드포인트"""
    try:
        data = request.get_json()
        if not data or 'vendor' not in data:
            raise ValueError('벤더 정보가 필요합니다.')

        vendor = data['vendor']
        if vendor not in VENDOR_COMMANDS:
            raise ValueError(f'지원하지 않는 벤더입니다: {vendor}')

        logger.info(f'자동학습 시작: {vendor}')

        # 벤더별 디렉토리 생성
        vendor_dir = os.path.join(LEARNING_DIR, vendor)
        os.makedirs(vendor_dir, exist_ok=True)

        # 학습 데이터 구조화
        learning_data = {
            'vendor': vendor,
            'updated_at': datetime.now().isoformat(),
            'commands': VENDOR_COMMANDS[vendor],
            'metadata': {
                'source': 'auto-learning',
                'version': '1.0',
                'command_types': list(VENDOR_COMMANDS[vendor].keys())
            }
        }

        # 학습 데이터 저장
        filename = f'{vendor}_commands.json'
        filepath = os.path.join(vendor_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(learning_data, f, indent=2, ensure_ascii=False)

        logger.info(f'{vendor} 벤더 자동학습 완료: {filepath}')

        return jsonify({
            'status': 'success',
            'message': f'{vendor} 벤더의 명령어가 학습되었습니다.',
            'data': {
                'vendor': vendor,
                'command_types': list(VENDOR_COMMANDS[vendor].keys()),
                'file_path': filepath,
                'commands_count': len(VENDOR_COMMANDS[vendor])
            }
        })

    except Exception as e:
        logger.error(f'자동학습 오류: {str(e)}', exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico', 
        mimetype='image/vnd.microsoft.icon'
    )

@app.route('/api/backups', methods=['GET'])
def get_backups():
    """백업 목록 조회"""
    try:
        backup_dir = DATA_DIR / 'backups' / 'devices'
        if not backup_dir.exists():
            return jsonify({
                'status': 'success',
                'data': []
            })

        backups = []
        for backup in backup_dir.iterdir():
            if backup.is_dir():
                # 디렉토리 이름에서 장비명과 날짜 추출
                name_parts = backup.name.split('_')
                if len(name_parts) >= 2:
                    device_name = name_parts[0]
                    date_str = '_'.join(name_parts[1:])
                    try:
                        date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                        backups.append({
                            'id': backup.name,
                            'device_name': device_name,
                            'backup_date': date.strftime('%Y-%m-%d %H:%M:%S'),
                            'path': str(backup)
                        })
                    except ValueError:
                        continue

        return jsonify({
            'status': 'success',
            'data': sorted(backups, key=lambda x: x['backup_date'], reverse=True)
        })

    except Exception as e:
        logger.error(f"백업 목록 조회 오류: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '백업 목록 조회 중 오류가 발생했습니다.'
        }), 500

@app.route('/api/backups/<backup_id>/restore', methods=['POST'])
def restore_backup(backup_id):
    """백업 데이터 복원"""
    try:
        backup_dir = DATA_DIR / 'backups' / 'devices' / backup_id
        if not backup_dir.exists():
            return jsonify({
                'status': 'error',
                'message': '백업을 찾을 수 없습니다.'
            }), 404

        # 장비명 추출
        device_name = backup_id.split('_')[0]
        
        # 현재 장비 목록 로드
        devices = load_devices()
        
        # 복원할 장비가 이미 존재하는지 확인
        if any(d['name'] == device_name for d in devices):
            return jsonify({
                'status': 'error',
                'message': f'이미 존재하는 장비입니다: {device_name}'
            }), 400

        # 스크립트 디렉토리 복원
        target_dir = SCRIPTS_DIR / device_name
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(backup_dir, target_dir)

        # devices.json 백업 파일이 있다면 해당 장비 정보도 복원
        backup_devices_file = backup_dir / 'device_info.json'
        if backup_devices_file.exists():
            with open(backup_devices_file, 'r', encoding='utf-8') as f:
                device_info = json.load(f)
                devices.append(device_info)
                save_devices(devices)

        return jsonify({
            'status': 'success',
            'message': f'장비 {device_name}의 백업이 성공적으로 복원되었습니다.',
            'device': device_info if 'device_info' in locals() else None
        })

    except Exception as e:
        logger.error(f"백업 복원 오류: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '백업 복원 중 오류가 발생했습니다.'
        }), 500

@app.route('/api/backups/<backup_id>', methods=['DELETE'])
def delete_backup(backup_id):
    """백업 삭제"""
    try:
        backup_dir = DATA_DIR / 'backups' / 'devices' / backup_id
        if not backup_dir.exists():
            return jsonify({
                'status': 'error',
                'message': '백업을 찾을 수 없습니다.'
            }), 404

        shutil.rmtree(backup_dir)
        return jsonify({
            'status': 'success',
            'message': '백업이 삭제되었습니다.'
        })

    except Exception as e:
        logger.error(f"백업 삭제 오류: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '백업 삭제 중 오류가 발생했습니다.'
        }), 500

@app.route('/api/generate-script', methods=['POST'])
def generate_script():
    """설정 스크립트 생성"""
    try:
        logger.debug("스크립트 생성 요청 받음")
        data = request.get_json()
        logger.debug(f"받은 데이터: {data}")

        device_name = data.get('device')
        task_type = data.get('taskType')
        params = data.get('params', {})

        if not device_name or not task_type:
            return jsonify({
                'status': 'error',
                'message': '장비와 작업 유형은 필수입니다.'
            }), 400

        # 장비의 벤더 정보 조회
        vendor = get_device_vendor(device_name)
        if not vendor:
            return jsonify({
                'status': 'error',
                'message': f'장비 {device_name}의 벤더 정보를 찾을 수 없습니다.'
            }), 404

        # 벤더별 명령어 로드
        vendor_commands = load_vendor_commands()
        vendor_templates = vendor_commands.get(vendor.lower(), {})
        
        if not vendor_templates:
            return jsonify({
                'status': 'error',
                'message': f'{vendor} 벤더의 명령어 템플릿이 없습니다.'
            }), 404

        # 스크립트 생성
        script = generate_config_script(task_type, params, vendor_templates)
        
        return jsonify({
            'status': 'success',
            'script': script,
            'vendor': vendor
        })

    except Exception as e:
        logger.exception("스크립트 생성 중 오류 발생")
        return jsonify({
            'status': 'error',
            'message': f'스크립트 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500

def generate_config_script(task_type, params, vendor_templates):
    """작업 유형별 설정 스크립트 생성"""
    logger.debug(f"스크립트 생성 시작 - 작업유형: {task_type}, 파라미터: {params}")
    
    # 작업 유형별 템플릿 매핑
    task_templates = vendor_templates.get(task_type, {})
    if not task_templates:
        raise ValueError(f'해당 작업 유형의 템플릿이 없습니다: {task_type}')

    script_lines = ['configure terminal']

    try:
        if task_type == 'vlan':
            script_lines.extend(generate_vlan_commands(params, task_templates))
        elif task_type == 'port':
            script_lines.extend(generate_port_commands(params, task_templates))
        elif task_type == 'routing':
            script_lines.extend(generate_routing_commands(params, task_templates))
        elif task_type == 'security':
            script_lines.extend(generate_security_commands(params, task_templates))
        # 다른 작업 유형들에 대한 처리...

        script_lines.append('end')
        return '\n'.join(filter(None, script_lines))

    except Exception as e:
        logger.exception(f"{task_type} 스크립트 생성 중 오류")
        raise ValueError(f'스크립트 생성 오류: {str(e)}')

def generate_vlan_commands(params, templates):
    """VLAN 설정 명령어 생성"""
    logger.debug(f"VLAN 명령어 생성 시작 - 파라미터: {params}")
    
    # 필수 파라미터 검증
    action = params.get('vlanAction')
    if not action:
        raise ValueError('VLAN 작업 유형을 선택해주세요.')

    vlan_id = params.get('vlanId')
    if not vlan_id:
        raise ValueError('VLAN ID를 입력해주세요.')

    try:
        vlan_id = int(vlan_id)
        if not (1 <= vlan_id <= 4094):
            raise ValueError('VLAN ID는 1-4094 범위여야 합니다.')
    except (TypeError, ValueError):
        raise ValueError('올바른 VLAN ID를 입력해주세요.')

    commands = []
    
    try:
        # 템플릿이 patterns/template 구조인 경우
        if 'template' in templates:
            template_lines = templates['template']
            if isinstance(template_lines, list):
                for line in template_lines:
                    commands.append(line.format(
                        vlan_id=vlan_id,
                        vlan_name=params.get('vlanName', f'VLAN{vlan_id}')
                    ))
            else:
                commands.append(template_lines.format(
                    vlan_id=vlan_id,
                    vlan_name=params.get('vlanName', f'VLAN{vlan_id}')
                ))
            return commands

        # 템플릿이 개별 명령어 구조인 경우
        if action == 'create':
            commands.append(f'vlan {vlan_id}')
            if params.get('vlanName'):
                commands.append(f'name {params["vlanName"]}')
                
        elif action == 'delete':
            commands.append(f'no vlan {vlan_id}')
            
        elif action in ['assign', 'trunk']:
            interface = params.get('interface')
            if not interface:
                raise ValueError('인터페이스를 지정해주세요.')
            
            commands.append(f'interface {interface}')
            
            if action == 'assign':
                commands.extend([
                    'switchport mode access',
                    f'switchport access vlan {vlan_id}'
                ])
            else:
                commands.extend([
                    'switchport mode trunk',
                    f'switchport trunk allowed vlan add {vlan_id}'
                ])
        else:
            raise ValueError(f'지원하지 않는 VLAN 작업 유형입니다: {action}')

        logger.debug(f"생성된 VLAN 명령어: {commands}")
        return commands

    except Exception as e:
        logger.error(f"VLAN 명령어 생성 오류: {str(e)}")
        raise ValueError(f'VLAN 명령어 생성 중 오류가 발생했습니다: {str(e)}')

def generate_port_commands(params, templates):
    """포트 설정 명령어 생성"""
    logger.debug(f"포트 명령어 생성 시작 - 파라미터: {params}")
    
    # 필수 파라미터 검증
    action = params.get('portAction')
    if not action:
        raise ValueError('포트 작업 유형을 선택해주세요.')

    interface = params.get('interface')
    if not interface:
        raise ValueError('인터페이스를 지정해주세요.')

    commands = []
    
    try:
        # 인터페이스 진입
        interface_template = templates.get('interface', 'interface {interface}')
        commands.append(interface_template.format(interface=interface))

        if action == 'mode':
            # 포트 모드 설정
            port_mode = params.get('portMode')
            if not port_mode:
                raise ValueError('포트 모드를 선택해주세요.')
                
            mode_template = templates.get(f'mode_{port_mode}', 'switchport mode {port_mode}')
            commands.append(mode_template)

        elif action == 'speed':
            # 속도 및 듀플렉스 설정
            speed = params.get('portSpeed')
            duplex = params.get('portDuplex')
            
            if speed and speed != 'auto':
                speed_template = templates.get('speed', 'speed {speed}')
                commands.append(speed_template.format(speed=speed))
            
            if duplex and duplex != 'auto':
                duplex_template = templates.get('duplex', 'duplex {duplex}')
                commands.append(duplex_template.format(duplex=duplex))

        elif action == 'status':
            # 포트 상태 설정
            status = params.get('portStatus')
            if not status:
                raise ValueError('포트 상태를 선택해주세요.')
                
            if status == 'up':
                commands.append(templates.get('no_shutdown', 'no shutdown'))
            else:
                commands.append(templates.get('shutdown', 'shutdown'))

        logger.debug(f"생성된 포트 명령어: {commands}")
        return commands

    except KeyError as e:
        logger.error(f"템플릿 키 오류: {str(e)}")
        raise ValueError(f'필요한 명령어 템플릿이 없습니다: {str(e)}')
    except Exception as e:
        logger.error(f"포트 명령어 생성 오류: {str(e)}")
        raise ValueError(f'포트 명령어 생성 중 오류가 발생했습니다: {str(e)}')

def generate_routing_commands(params, templates):
    """라우팅 설정 명령어 생성"""
    logger.debug(f"라우팅 명령어 생성 시작 - 파라미터: {params}")
    
    protocol = params.get('routingProtocol')
    if not protocol:
        raise ValueError('라우팅 프로토콜을 선택해주세요.')

    commands = []
    
    try:
        if protocol == 'static':
            # 정적 라우팅 설정
            network = params.get('network')
            mask = params.get('mask')
            next_hop = params.get('next_hop')
            
            if not all([network, mask, next_hop]):
                raise ValueError('네트워크, 마스크, 넥스트홉 정보가 필요합니다.')
                
            static_template = templates.get('static', 'ip route {network} {mask} {next_hop}')
            commands.append(static_template.format(
                network=network,
                mask=mask,
                next_hop=next_hop
            ))

        elif protocol in ['ospf', 'eigrp', 'bgp']:
            # 동적 라우팅 프로토콜 설정
            if protocol == 'ospf':
                process_id = params.get('process_id', '1')
                network = params.get('network')
                wildcard = params.get('wildcard')
                area = params.get('area', '0')
                
                if not all([network, wildcard]):
                    raise ValueError('네트워크와 와일드카드 마스크가 필요합니다.')
                    
                ospf_template = templates.get('ospf_network')
                commands.append(ospf_template.format(
                    process_id=process_id,
                    network=network,
                    wildcard=wildcard,
                    area=area
                ))

        logger.debug(f"생성된 라우팅 명령어: {commands}")
        return commands

    except KeyError as e:
        logger.error(f"템플릿 키 오류: {str(e)}")
        raise ValueError(f'필요한 명령어 템플릿이 없습니다: {str(e)}')
    except Exception as e:
        logger.error(f"라우팅 명령어 생성 오류: {str(e)}")
        raise ValueError(f'라우팅 명령어 생성 중 오류가 발생했습니다: {str(e)}')

def generate_security_commands(params, templates):
    """보안 설정 명령어 생성"""
    logger.debug(f"보안 명령어 생성 시작 - 파라미터: {params}")
    
    security_type = params.get('securityType')
    if not security_type:
        raise ValueError('보안 설정 유형을 선택해주세요.')

    commands = []
    
    try:
        if security_type == 'port-security':
            interface = params.get('interface')
            if not interface:
                raise ValueError('인터페이스를 지정해주세요.')
                
            # 인터페이스 설정 진입
            commands.append(f'interface {interface}')
            
            # 포트 보안 기본 설정
            commands.append(templates.get('port_security', 'switchport port-security'))
            
            # 최대 MAC 주소 수 설정
            max_addr = params.get('max_addresses')
            if max_addr:
                max_template = templates.get('max_mac')
                commands.append(max_template.format(max_addresses=max_addr))
            
            # 위반 모드 설정
            violation = params.get('violation_mode')
            if violation:
                violation_template = templates.get('violation')
                commands.append(violation_template.format(violation_mode=violation))

        elif security_type == 'acl':
            # ACL 설정
            acl_number = params.get('acl_number')
            action = params.get('action')
            protocol = params.get('protocol')
            source = params.get('source')
            destination = params.get('destination')
            
            if not all([acl_number, action, protocol, source, destination]):
                raise ValueError('ACL 설정에 필요한 모든 정보를 입력해주세요.')
                
            acl_template = templates.get('access_list')
            commands.append(acl_template.format(
                acl_number=acl_number,
                action=action,
                protocol=protocol,
                source=source,
                destination=destination
            ))

        logger.debug(f"생성된 보안 명령어: {commands}")
        return commands

    except KeyError as e:
        logger.error(f"템플릿 키 오류: {str(e)}")
        raise ValueError(f'필요한 명령어 템플릿이 없습니다: {str(e)}')
    except Exception as e:
        logger.error(f"보안 명령어 생성 오류: {str(e)}")
        raise ValueError(f'보안 명령어 생성 중 오류가 발생했습니다: {str(e)}')

# before_first_request 대신 with app.app_context() 사용
def initialize_app():
    """앱 초기화"""
    with app.app_context():
        if init_data_directories():
            logger.info("앱 초기화 완료")
        else:
            logger.error("앱 초기화 실패")

# 서버 시작 시 초기화 실행
init_learning_data()  # 직접 호출

def get_device_vendor(device_name):
    """장비의 벤더 정보 조회"""
    try:
        devices_file = DATA_DIR / 'devices' / 'devices.json'
        if devices_file.exists():
            with open(devices_file, 'r', encoding='utf-8') as f:
                devices = json.load(f)
                device = next((d for d in devices if d['name'] == device_name), None)
                return device['vendor'] if device else None
        return None
    except Exception as e:
        logger.error(f"장비 벤더 조회 오류: {str(e)}")
        return None

@app.route('/api/vendor-commands', methods=['GET'])
def get_vendor_commands():
    """벤더별 명령어 조회"""
    commands = load_vendor_commands()
    return jsonify({
        'status': 'success',
        'data': commands
    })

@app.route('/api/vendor-commands/<vendor>', methods=['POST'])
def update_vendor_commands(vendor):
    """벤더별 명령어 업데이트"""
    try:
        data = request.get_json()
        commands = load_vendor_commands()
        
        # 벤더 명령어 업데이트
        commands[vendor.lower()] = data
        
        if save_vendor_commands(commands):
            return jsonify({
                'status': 'success',
                'message': f'{vendor} 벤더의 명령어가 업데이트되었습니다.'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '명령어 저장 중 오류가 발생했습니다.'
            }), 500

    except Exception as e:
        logger.exception("벤더 명령어 업데이트 중 오류 발생")
        return jsonify({
            'status': 'error',
            'message': f'명령어 업데이트 중 오류가 발생했습니다: {str(e)}'
        }), 500

def update_device_info(device_name, vendor, script_filename):
    """장비 정보 업데이트"""
    try:
        # 장비 정보 로드
        devices = load_devices()
        device = next((d for d in devices if d['name'] == device_name), None)
        
        if not device:
            logger.error(f"장비를 찾을 수 없음: {device_name}")
            return False
            
        # 장비 정보 업데이트
        device['last_script'] = script_filename
        device['last_updated'] = datetime.now().isoformat()
        
        # 장비 정보 저장
        if save_devices(devices):
            logger.info(f"장비 정보 업데이트 완료: {device_name}")
            
            # 장비별 정보 백업
            backup_dir = DATA_DIR / 'backups' / 'devices' / f"{device_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 장비 정보 백업
            with open(backup_dir / 'device_info.json', 'w', encoding='utf-8') as f:
                json.dump(device, f, ensure_ascii=False, indent=2)
                
            return True
        else:
            logger.error(f"장비 정보 저장 실패: {device_name}")
            return False
            
    except Exception as e:
        logger.error(f"장비 정보 업데이트 오류: {str(e)}")
        return False

if __name__ == '__main__':
    app.run(debug=True) 