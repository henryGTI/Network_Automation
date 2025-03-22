import os
import json
from ..exceptions import CLILearningError, ValidationError
from datetime import datetime
from ..models.cli_command import CLICommand
from ..models.device import Device
from ..utils.file_handler import ensure_directory_exists
from app.utils.logger import setup_logger
from app import db
import logging
import requests
from bs4 import BeautifulSoup
import re

CLI_LEARNING_FILE = "cli_learning.json"

logger = setup_logger(__name__)

class LearningService:
    def __init__(self, base_dir='config/cli_learning'):
        self.base_dir = base_dir
        ensure_directory_exists(base_dir)
        self.commands = {}  # 벤더별 명령어 저장
        self.load_commands()  # 저장된 명령어 로드
        # 벤더별 명령어 템플릿
        self.vendor_templates = {
            'cisco': {
                'vlan_config': {
                    'name': 'VLAN 생성/삭제',
                    'patterns': [
                        r'vlan (\d+)',
                        r'name (.+)'
                    ],
                    'show_commands': [
                        'show vlan brief',
                        'show running-config | include vlan'
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
                    'patterns': [
                        r'interface ([A-Za-z0-9/]+)',
                        r'description (.+)',
                        r'shutdown|no shutdown'
                    ],
                    'show_commands': [
                        'show interfaces status',
                        'show running-config interface'
                    ],
                    'template': [
                        'configure terminal',
                        'interface {interface_name}',
                        'description {interface_desc}',
                        '{interface_status}',
                        'exit'
                    ]
                },
                'vlan_interface': {
                    'name': 'VLAN 인터페이스 설정',
                    'patterns': [
                        r'interface ([A-Za-z0-9/]+)',
                        r'switchport mode (access|trunk)',
                        r'switchport (access|trunk allowed) vlan (\d+)'
                    ],
                    'show_commands': [
                        'show interfaces switchport',
                        'show running-config interface'
                    ],
                    'template': [
                        'configure terminal',
                        'interface {interface_name}',
                        'switchport mode {mode}',
                        'switchport {mode} vlan {vlan_id}',
                        'exit'
                    ]
                },
                'ip_config': {
                    'name': 'IP 주소 설정',
                    'patterns': [
                        r'interface ([A-Za-z0-9/]+)',
                        r'ip address (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+)'
                    ],
                    'show_commands': [
                        'show ip interface brief',
                        'show running-config interface'
                    ],
                    'template': [
                        'configure terminal',
                        'interface {interface_name}',
                        'ip address {ip_address} {subnet_mask}',
                        'no shutdown',
                        'exit'
                    ]
                },
                'routing_config': {
                    'name': '라우팅 설정',
                    'patterns': [
                        r'router (ospf|bgp) (\d+)',
                        r'network (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+) area (\d+)'
                    ],
                    'show_commands': [
                        'show ip route',
                        'show ip protocols'
                    ],
                    'template': [
                        'configure terminal',
                        'router {protocol} {process_id}',
                        'network {network_address} {wildcard_mask} area {area_id}',
                        'exit'
                    ]
                },
                'acl_config': {
                    'name': 'ACL 설정',
                    'patterns': [
                        r'access-list (\d+) (permit|deny) (.+)',
                        r'ip access-list (standard|extended) (.+)'
                    ],
                    'show_commands': [
                        'show access-lists',
                        'show running-config | include access-list'
                    ],
                    'template': [
                        'configure terminal',
                        'ip access-list {acl_type} {acl_number}',
                        '{action} {acl_rule}',
                        'exit'
                    ]
                },
                'snmp_config': {
                    'name': 'SNMP 설정',
                    'patterns': [
                        r'snmp-server community (.+) (RO|RW)',
                        r'snmp-server host (\d+\.\d+\.\d+\.\d+) version (\d+) (.+)'
                    ],
                    'show_commands': [
                        'show snmp',
                        'show running-config | include snmp'
                    ],
                    'template': [
                        'configure terminal',
                        'snmp-server community {snmp_community} {access_type}',
                        'snmp-server host {host} version {snmp_version} {community}',
                        'exit'
                    ]
                },
                'ntp_config': {
                    'name': 'NTP 설정',
                    'patterns': [
                        r'ntp server (\S+)',
                        r'ntp source (.+)'
                    ],
                    'show_commands': [
                        'show ntp status',
                        'show running-config | include ntp'
                    ],
                    'template': [
                        'configure terminal',
                        'ntp server {ntp_server}',
                        'exit'
                    ]
                }
            },
            'juniper': {
                'vlan_config': {
                    'name': 'VLAN 생성/삭제',
                    'patterns': [
                        r'set vlans (\S+) vlan-id (\d+)',
                        r'delete vlans (\S+)'
                    ],
                    'show_commands': [
                        'show vlans brief',
                        'show configuration vlans'
                    ],
                    'template': [
                        'set vlans {vlan_name} vlan-id {vlan_id}',
                        'set vlans {vlan_name} description "{description}"'
                    ]
                },
                'interface_config': {
                    'name': '인터페이스 설정',
                    'patterns': [
                        r'set interfaces (\S+) description (.+)',
                        r'set interfaces (\S+) disable|delete interfaces (\S+) disable'
                    ],
                    'show_commands': [
                        'show interfaces terse',
                        'show configuration interfaces'
                    ],
                    'template': [
                        'set interfaces {interface_name} description "{interface_desc}"',
                        '{interface_status}'
                    ]
                },
                'vlan_interface': {
                    'name': 'VLAN 인터페이스 설정',
                    'patterns': [
                        r'set interfaces (\S+) unit 0 family ethernet-switching port-mode (access|trunk)',
                        r'set interfaces (\S+) unit 0 family ethernet-switching vlan members (\S+)'
                    ],
                    'show_commands': [
                        'show ethernet-switching interfaces',
                        'show configuration interfaces'
                    ],
                    'template': [
                        'set interfaces {interface_name} unit 0 family ethernet-switching port-mode {mode}',
                        'set interfaces {interface_name} unit 0 family ethernet-switching vlan members {vlan_id}'
                    ]
                },
                'ip_config': {
                    'name': 'IP 주소 설정',
                    'patterns': [
                        r'set interfaces (\S+) unit (\d+) family inet address (\d+\.\d+\.\d+\.\d+)/(\d+)'
                    ],
                    'show_commands': [
                        'show interfaces terse',
                        'show configuration interfaces'
                    ],
                    'template': [
                        'set interfaces {interface_name} unit {unit_number} family inet address {ip_address}/{prefix_length}'
                    ]
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
                        'vlan {vlan_id}',
                        'name {vlan_name}'
                    ]
                },
                'interface_config': {
                    'name': '인터페이스 설정',
                    'patterns': [
                        r'interface ([A-Za-z0-9/]+)',
                        r'description (.+)',
                        r'shutdown|no shutdown'
                    ],
                    'show_commands': [
                        'show interfaces status',
                        'show running-config interfaces'
                    ],
                    'template': [
                        'interface {interface_name}',
                        'description {interface_desc}',
                        '{interface_status}'
                    ]
                },
                'vlan_interface': {
                    'name': 'VLAN 인터페이스 설정',
                    'patterns': [
                        r'interface ([A-Za-z0-9/]+)',
                        r'switchport mode (access|trunk)',
                        r'switchport (access|trunk allowed) vlan (\d+)'
                    ],
                    'show_commands': [
                        'show interfaces switchport',
                        'show running-config interfaces'
                    ],
                    'template': [
                        'interface {interface_name}',
                        'switchport mode {mode}',
                        'switchport {mode} vlan {vlan_id}'
                    ]
                }
            }
        }
        # 벤더별 검색 키워드 정의
        self.vendor_search_queries = {
            'cisco': [
                'cisco ios command reference vlan configuration',
                'cisco ios interface configuration commands',
                'cisco switch port configuration guide',
                'cisco ios routing commands ospf bgp',
                'cisco ios acl configuration commands',
                'cisco ios snmp configuration',
                'cisco ios ntp configuration',
                'cisco ios stp spanning-tree commands',
                'cisco ios port-channel lacp configuration',
                'cisco ios qos configuration commands',
                'cisco ios show ip route command',
                'cisco ios show interface status command',
                'cisco ios logging commands',
                'cisco ios backup configuration commands',
                'cisco ios monitor commands'
            ],
            'juniper': [
                'juniper junos vlan configuration commands',
                'juniper ex series interface configuration',
                'juniper networks cli command reference',
                'juniper junos routing configuration ospf bgp',
                'juniper junos firewall filter commands',
                'juniper junos snmp configuration',
                'juniper junos ntp configuration',
                'juniper junos spanning-tree protocol',
                'juniper junos link aggregation commands',
                'juniper junos class of service commands',
                'juniper junos show route command',
                'juniper junos show interfaces command',
                'juniper junos system logging commands',
                'juniper junos configuration backup commands',
                'juniper junos monitor commands'
            ],
            'arista': [
                'arista eos vlan configuration guide',
                'arista switch interface commands',
                'arista networks cli reference',
                'arista eos routing protocol commands',
                'arista eos access control list configuration',
                'arista eos snmp configuration commands',
                'arista eos ntp server configuration',
                'arista eos spanning-tree protocol commands',
                'arista eos port-channel configuration',
                'arista eos quality of service commands',
                'arista eos show ip route commands',
                'arista eos show interfaces commands',
                'arista eos logging configuration',
                'arista eos backup configuration commands',
                'arista eos monitoring commands'
            ]
        }

    def load_commands(self):
        """저장된 명령어 로드"""
        for vendor in os.listdir(self.base_dir):
            vendor_path = os.path.join(self.base_dir, vendor)
            if os.path.isdir(vendor_path):
                self.commands[vendor] = []
                data_file = os.path.join(vendor_path, 'commands.json')
                if os.path.exists(data_file):
                    with open(data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for cmd_data in data:
                            self.commands[vendor].append(CLICommand.from_dict(cmd_data))

    def save_commands(self, vendor):
        """명령어를 파일에 저장"""
        vendor = vendor.lower()
        vendor_dir = os.path.join(self.base_dir, vendor)
        ensure_directory_exists(vendor_dir)
        data_file = os.path.join(vendor_dir, 'commands.json')
        
        commands_data = [cmd.to_dict() for cmd in self.commands.get(vendor, [])]
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(commands_data, f, ensure_ascii=False, indent=2)

    def add_command(self, vendor, command, description, mode='', parameters=None, examples=None):
        """새로운 명령어 추가"""
        vendor = vendor.lower()
        if vendor not in self.commands:
            self.commands[vendor] = []
        
        # 중복 명령어 검사
        for cmd in self.commands[vendor]:
            if cmd.command == command:
                cmd.description = description
                cmd.mode = mode
                cmd.parameters = parameters or []
                cmd.examples = examples or []
                cmd.updated_at = datetime.now()
                self.save_commands(vendor)
                return cmd

        # 새 명령어 추가
        new_command = CLICommand(vendor, command, description, mode, parameters, examples)
        self.commands[vendor].append(new_command)
        self.save_commands(vendor)
        return new_command

    def get_commands(self, vendor=None):
        """명령어 조회"""
        if vendor:
            vendor = vendor.lower()
            return self.commands.get(vendor, [])
        return {v: cmds for v, cmds in self.commands.items()}

    def search_commands(self, query, vendor=None):
        """명령어 검색"""
        results = []
        vendors = [vendor.lower()] if vendor else self.commands.keys()
        
        for v in vendors:
            if v not in self.commands:
                continue
            
            for cmd in self.commands[v]:
                if (query.lower() in cmd.command.lower() or 
                    query.lower() in cmd.description.lower()):
                    results.append(cmd)
        
        return results

    def delete_command(self, vendor, command):
        """명령어 삭제"""
        vendor = vendor.lower()
        if vendor not in self.commands:
            return False
        
        self.commands[vendor] = [cmd for cmd in self.commands[vendor] 
                               if cmd.command != command]
        self.save_commands(vendor)
        return True

    def clear_commands(self, vendor):
        """벤더의 모든 명령어 삭제"""
        vendor = vendor.lower()
        if vendor in self.commands:
            self.commands[vendor] = []
            self.save_commands(vendor)
            return True
        return False

    def check_learning_status(self):
        """CLI 학습 완료 여부 확인"""
        return {
            'total_commands': len(self.get_all_commands()),
            'vendors': self.get_vendor_stats()
        }

    def get_vendor_stats(self):
        """벤더별 명령어 통계 반환"""
        stats = {}
        for vendor in self.get_vendors():
            commands = self.get_commands(vendor)
            stats[vendor] = len(commands)
        return stats

    def get_all_commands(self):
        """모든 명령어 목록 반환"""
        all_commands = []
        for vendor in self.get_vendors():
            all_commands.extend(self.get_commands(vendor))
        return all_commands

    def search_vendor_commands(self, vendor):
        """웹 검색을 통해 벤더별 CLI 명령어를 수집합니다."""
        try:
            logger.info(f"{vendor} 벤더의 CLI 명령어 검색 시작")
            
            # 실제 웹 검색 대신 미리 정의된 샘플 데이터 사용
            sample_commands = {
                'cisco': [
                    {
                        'vendor': 'cisco',
                        'device_type': '스위치',
                        'task_type': 'VLAN 관리',
                        'subtask': 'VLAN 생성',
                        'command': 'configure terminal\nvlan {vlan_id}\nname {vlan_name}\nexit',
                        'parameters': ['vlan_id', 'vlan_name'],
                        'description': 'VLAN을 생성하는 명령어'
                    },
                    {
                        'vendor': 'cisco',
                        'device_type': '스위치',
                        'task_type': 'VLAN 관리',
                        'subtask': 'VLAN 삭제',
                        'command': 'configure terminal\nno vlan {vlan_id}\nexit',
                        'parameters': ['vlan_id'],
                        'description': 'VLAN을 삭제하는 명령어'
                    },
                    {
                        'vendor': 'cisco',
                        'device_type': '스위치',
                        'task_type': '포트 설정',
                        'subtask': '인터페이스 활성화',
                        'command': 'configure terminal\ninterface {interface_name}\nno shutdown\nexit',
                        'parameters': ['interface_name'],
                        'description': '인터페이스를 활성화하는 명령어'
                    },
                    {
                        'vendor': 'cisco',
                        'device_type': '스위치',
                        'task_type': '포트 설정',
                        'subtask': '인터페이스 비활성화',
                        'command': 'configure terminal\ninterface {interface_name}\nshutdown\nexit',
                        'parameters': ['interface_name'],
                        'description': '인터페이스를 비활성화하는 명령어'
                    },
                    {
                        'vendor': 'cisco',
                        'device_type': '라우터',
                        'task_type': '라우팅 설정',
                        'subtask': '정적 라우팅 설정',
                        'command': 'configure terminal\nip route {network} {mask} {next_hop}\nexit',
                        'parameters': ['network', 'mask', 'next_hop'],
                        'description': '정적 라우팅을 설정하는 명령어'
                    },
                    {
                        'vendor': 'cisco',
                        'device_type': '라우터',
                        'task_type': '라우팅 설정',
                        'subtask': 'OSPF 설정',
                        'command': 'configure terminal\nrouter ospf {process_id}\nnetwork {network} {wildcard_mask} area {area_id}\nexit',
                        'parameters': ['process_id', 'network', 'wildcard_mask', 'area_id'],
                        'description': 'OSPF 라우팅을 설정하는 명령어'
                    },
                    {
                        'vendor': 'cisco',
                        'device_type': '라우터',
                        'task_type': '보안 설정',
                        'subtask': 'ACL 설정',
                        'command': 'configure terminal\nip access-list {acl_type} {acl_number}\n{action} {acl_rule}\nexit',
                        'parameters': ['acl_type', 'acl_number', 'action', 'acl_rule'],
                        'description': 'ACL을 설정하는 명령어'
                    },
                    {
                        'vendor': 'cisco',
                        'device_type': '스위치',
                        'task_type': 'VLAN 인터페이스 설정',
                        'subtask': '액세스 모드 설정',
                        'command': 'configure terminal\ninterface {interface_name}\nswitchport mode access\nswitchport access vlan {vlan_id}\nexit',
                        'parameters': ['interface_name', 'vlan_id'],
                        'description': '인터페이스를 액세스 모드로 설정하는 명령어'
                    },
                    {
                        'vendor': 'cisco',
                        'device_type': '스위치',
                        'task_type': 'VLAN 인터페이스 설정',
                        'subtask': '트렁크 모드 설정',
                        'command': 'configure terminal\ninterface {interface_name}\nswitchport mode trunk\nswitchport trunk allowed vlan {vlan_id}\nexit',
                        'parameters': ['interface_name', 'vlan_id'],
                        'description': '인터페이스를 트렁크 모드로 설정하는 명령어'
                    }
                ],
                'juniper': [
                    {
                        'vendor': 'juniper',
                        'device_type': '스위치',
                        'task_type': 'VLAN 관리',
                        'subtask': 'VLAN 생성',
                        'command': 'set vlans {vlan_name} vlan-id {vlan_id}\nset vlans {vlan_name} description "{description}"',
                        'parameters': ['vlan_name', 'vlan_id', 'description'],
                        'description': 'VLAN을 생성하는 명령어'
                    },
                    {
                        'vendor': 'juniper',
                        'device_type': '스위치',
                        'task_type': 'VLAN 관리',
                        'subtask': 'VLAN 삭제',
                        'command': 'delete vlans {vlan_name}',
                        'parameters': ['vlan_name'],
                        'description': 'VLAN을 삭제하는 명령어'
                    },
                    {
                        'vendor': 'juniper',
                        'device_type': '스위치',
                        'task_type': '포트 설정',
                        'subtask': '인터페이스 설정',
                        'command': 'set interfaces {interface_name} description "{interface_desc}"\n{interface_status}',
                        'parameters': ['interface_name', 'interface_desc', 'interface_status'],
                        'description': '인터페이스를 설정하는 명령어'
                    },
                    {
                        'vendor': 'juniper',
                        'device_type': '라우터',
                        'task_type': '라우팅 설정',
                        'subtask': '정적 라우팅 설정',
                        'command': 'set routing-options static route {network}/{prefix} next-hop {next_hop}',
                        'parameters': ['network', 'prefix', 'next_hop'],
                        'description': '정적 라우팅을 설정하는 명령어'
                    },
                    {
                        'vendor': 'juniper',
                        'device_type': '스위치',
                        'task_type': 'VLAN 인터페이스 설정',
                        'subtask': '액세스 모드 설정',
                        'command': 'set interfaces {interface_name} unit 0 family ethernet-switching port-mode access\nset interfaces {interface_name} unit 0 family ethernet-switching vlan members {vlan_id}',
                        'parameters': ['interface_name', 'vlan_id'],
                        'description': '인터페이스를 액세스 모드로 설정하는 명령어'
                    }
                ],
                'arista': [
                    {
                        'vendor': 'arista',
                        'device_type': '스위치',
                        'task_type': 'VLAN 관리',
                        'subtask': 'VLAN 생성',
                        'command': 'vlan {vlan_id}\nname {vlan_name}',
                        'parameters': ['vlan_id', 'vlan_name'],
                        'description': 'VLAN을 생성하는 명령어'
                    },
                    {
                        'vendor': 'arista',
                        'device_type': '스위치',
                        'task_type': 'VLAN 관리',
                        'subtask': 'VLAN 삭제',
                        'command': 'no vlan {vlan_id}',
                        'parameters': ['vlan_id'],
                        'description': 'VLAN을 삭제하는 명령어'
                    },
                    {
                        'vendor': 'arista',
                        'device_type': '스위치',
                        'task_type': '포트 설정',
                        'subtask': '인터페이스 설정',
                        'command': 'interface {interface_name}\ndescription {interface_desc}\n{interface_status}',
                        'parameters': ['interface_name', 'interface_desc', 'interface_status'],
                        'description': '인터페이스를 설정하는 명령어'
                    },
                    {
                        'vendor': 'arista',
                        'device_type': '라우터',
                        'task_type': '라우팅 설정',
                        'subtask': 'OSPF 설정',
                        'command': 'router ospf {process_id}\nnetwork {network} {wildcard_mask} area {area_id}',
                        'parameters': ['process_id', 'network', 'wildcard_mask', 'area_id'],
                        'description': 'OSPF 라우팅을 설정하는 명령어'
                    },
                    {
                        'vendor': 'arista',
                        'device_type': '스위치',
                        'task_type': 'VLAN 인터페이스 설정',
                        'subtask': '액세스 모드 설정',
                        'command': 'interface {interface_name}\nswitchport mode access\nswitchport access vlan {vlan_id}',
                        'parameters': ['interface_name', 'vlan_id'],
                        'description': '인터페이스를 액세스 모드로 설정하는 명령어'
                    }
                ]
            }
            
            # 요청된 벤더에 대한 샘플 명령어 반환
            commands = sample_commands.get(vendor.lower(), [])
            logger.info(f"{vendor} 벤더의 CLI 명령어 {len(commands)}개 검색 완료")
            return commands
            
        except Exception as e:
            logger.error(f"명령어 검색 중 오류 발생: {str(e)}")
            return []

    def _perform_web_search(self, query):
        """벤더 문서에서 CLI 명령어를 검색합니다."""
        try:
            vendor_docs = {
                'cisco': 'https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/fundamentals/command/cf_command_ref.html',
                'juniper': 'https://www.juniper.net/documentation/us/en/software/junos/cli-reference/',
                'arista': 'https://www.arista.com/en/um-eos/eos-section-1-overview'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(vendor_docs.get(query.split()[0].lower(), ''), headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            commands = []
            
            # 명령어가 포함된 요소 찾기
            code_elements = soup.find_all(['code', 'pre', 'div', 'span'], class_=['command', 'cli', 'code'])
            for element in code_elements:
                text = element.get_text().strip()
                if text and len(text) > 5:  # 최소 길이 체크
                    commands.append({
                        'snippet': text,
                        'url': response.url
                    })
            
            return commands
            
        except requests.RequestException as e:
            logger.error(f"웹 검색 중 오류 발생: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"예상치 못한 오류 발생: {str(e)}")
            return []

    def _extract_cli_commands(self, text, vendor):
        """텍스트에서 CLI 명령어를 추출합니다."""
        commands = []
        
        # 벤더별 명령어 패턴
        patterns = {
            'cisco': [
                r'(?m)^(config[^\n]*\#[^\n]+)',
                r'(?m)^(interface[^\n]+)',
                r'(?m)^(vlan[^\n]+)',
                r'(?m)^(ip[^\n]+)'
            ],
            'juniper': [
                r'(?m)^(set[^\n]+)',
                r'(?m)^(delete[^\n]+)',
                r'(?m)^(show[^\n]+)'
            ],
            'arista': [
                r'(?m)^(configure[^\n]+)',
                r'(?m)^(interface[^\n]+)',
                r'(?m)^(vlan[^\n]+)'
            ]
        }
        
        try:
            vendor_patterns = patterns.get(vendor.lower(), [])
            for pattern in vendor_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    command = match.group(1).strip()
                    if command and command not in commands:
                        commands.append(command)
            
            return commands
            
        except Exception as e:
            logger.error(f"명령어 추출 중 오류 발생: {str(e)}")
            return []

    def _classify_command_type(self, command, vendor):
        """명령어의 유형을 분류합니다."""
        command = command.lower()
        
        # 벤더별 명령어 분류 규칙
        classification_rules = {
            'cisco': {
                'VLAN 관리': {
                    'VLAN 생성': lambda cmd: 'vlan' in cmd and not 'no vlan' in cmd,
                    'VLAN 삭제': lambda cmd: 'no vlan' in cmd,
                    'VLAN 할당': lambda cmd: 'switchport' in cmd and 'vlan' in cmd
                },
                '포트 설정': {
                    '포트 활성화': lambda cmd: 'interface' in cmd and 'no shutdown' in cmd,
                    '포트 속도': lambda cmd: 'interface' in cmd and 'speed' in cmd
                }
            },
            'juniper': {
                'VLAN 관리': {
                    'VLAN 생성': lambda cmd: 'set vlans' in cmd,
                    'VLAN 삭제': lambda cmd: 'delete vlans' in cmd
                },
                '포트 설정': {
                    '포트 활성화': lambda cmd: 'set interfaces' in cmd and 'enable' in cmd
                }
            },
            'arista': {
                'VLAN 관리': {
                    'VLAN 생성': lambda cmd: 'vlan' in cmd and not 'no vlan' in cmd,
                    'VLAN 삭제': lambda cmd: 'no vlan' in cmd
                },
                '포트 설정': {
                    '포트 활성화': lambda cmd: 'interface' in cmd and 'no shutdown' in cmd
                }
            }
        }
        
        try:
            vendor_rules = classification_rules.get(vendor.lower(), {})
            for category, subtasks in vendor_rules.items():
                for subtask, rule in subtasks.items():
                    if rule(command):
                        return {
                            'category': category,
                            'subcategory': subtask
                        }
            return None
            
        except Exception as e:
            logger.error(f"명령어 분류 중 오류 발생: {str(e)}")
            return None

    def _extract_parameters(self, command):
        """명령어에서 매개변수를 추출합니다."""
        # 일반적인 매개변수 패턴
        param_patterns = [
            r'\{([^}]+)\}',  # {parameter} 형식
            r'<([^>]+)>',    # <parameter> 형식
            r'\[([^\]]+)\]'  # [parameter] 형식
        ]
        
        parameters = []
        for pattern in param_patterns:
            matches = re.finditer(pattern, command)
            parameters.extend(match.group(1) for match in matches)
        
        return list(set(parameters))  # 중복 제거

    def start_learning(self, vendor):
        """특정 벤더의 CLI 명령어를 학습합니다."""
        try:
            if not vendor:
                # 벤더가 지정되지 않은 경우 기본 벤더 사용
                vendor = 'cisco'
                
            if vendor not in self.vendor_search_queries:
                raise ValueError(f'지원하지 않는 벤더입니다: {vendor}')
            
            # 웹 검색을 통해 명령어 수집
            collected_commands = self.search_vendor_commands(vendor)
            
            # 해당 벤더의 기존 명령어 삭제 (새로 학습)
            CLICommand.query.filter_by(vendor=vendor).delete()
            db.session.commit()
            
            # 수집된 명령어를 데이터베이스에 저장
            learned_commands = []
            for cmd_info in collected_commands:
                try:
                    # 명령어 생성
                    command = CLICommand(
                        vendor=cmd_info['vendor'],
                        device_type=cmd_info.get('device_type', '스위치'),  # 기본값 제공
                        task_type=cmd_info['task_type'],
                        subtask=cmd_info['subtask'],
                        command=cmd_info['command'],
                        parameters=cmd_info['parameters'],
                        description=cmd_info.get('description', f"{cmd_info['subtask']} 명령어")
                    )
                    db.session.add(command)
                    learned_commands.append(cmd_info)
                    logger.info(f"명령어 추가: {cmd_info['vendor']} - {cmd_info['task_type']} - {cmd_info['subtask']}")
                except Exception as e:
                    logger.error(f"명령어 저장 중 오류: {str(e)}")
            
            # 명시적 커밋 
            db.session.commit()
            logger.info(f"{vendor} 벤더의 {len(learned_commands)}개 명령어 저장 완료")
            
            return {
                'learned_commands': learned_commands,
                'count': len(learned_commands)
            }
            
        except Exception as e:
            logger.error(f"학습 중 오류 발생: {str(e)}")
            db.session.rollback()
            raise

    def get_learned_commands(self, vendor=None):
        """학습된 명령어 목록을 반환합니다."""
        try:
            query = CLICommand.query
            
            if vendor:
                query = query.filter_by(vendor=vendor)
            
            commands = query.all()
            return [{
                'vendor': cmd.vendor,
                'task_type': cmd.task_type,
                'subtask': cmd.subtask,
                'command': cmd.command,
                'parameters': cmd.parameters,
                'updated_at': cmd.updated_at.isoformat()
            } for cmd in commands]
            
        except Exception as e:
            logger.error(f"명령어 목록 조회 중 오류 발생: {str(e)}")
            raise

    def get_vendor_templates(self, vendor):
        """특정 벤더의 명령어 템플릿 목록을 반환합니다."""
        try:
            if vendor not in self.vendor_templates:
                raise ValueError('지원하지 않는 벤더입니다.')
            
            return self.vendor_templates[vendor]
            
        except Exception as e:
            logger.error(f"템플릿 목록 조회 중 오류 발생: {str(e)}")
            raise

def perform_cli_learning():
    """CLI 학습을 수행하고 결과를 반환"""
    if os.path.exists(CLI_LEARNING_FILE):
        print("[정보] CLI 학습이 이미 시작되었습니다.")
        return

    print("[시작] CLI 명령어 학습을 시작합니다..")

    try:
        cli_knowledge = {
            "cisco": ["vlan 10", "interface GigabitEthernet1/0/1", "ip address 192.168.1.1 255.255.255.0"],
            "juniper": ["set vlans VLAN-10 vlan-id 10", "set interfaces ge-0/0/1 unit 0 family inet address 192.168.1.1/24"],
            "hp": ["vlan 10", "interface 1", "ip address 192.168.1.1/24"],
            "arista": ["vlan 10", "interface Ethernet1", "ip address 192.168.1.1/24"],
            "coreedge": ["create vlan 10 name VLAN_10", "interface 1 set vlan 10"],
            "handreamnet": ["vlan database", "vlan 10", "interface 1 switchport access vlan 10"]
        }

        with open(CLI_LEARNING_FILE, "w", encoding='utf-8') as f:
            json.dump(cli_knowledge, f, indent=4, ensure_ascii=False)

        print("[완료] CLI 학습 완료! 학습된 명령어들이 저장되었습니다.")

    except Exception as e:
        raise CLILearningError(f"CLI 학습 중 오류 발생: {str(e)}")

def get_cli_learning_status():
    """CLI 학습 완료 여부 확인"""
    return os.path.exists(CLI_LEARNING_FILE)

