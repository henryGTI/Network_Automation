# 벤더별 명령어 패턴 정의
from typing import Dict, Any

VENDOR_PATTERNS: Dict[str, Dict[str, Any]] = {
    'cisco': {
        'vlan_config': {
            'patterns': [
                r'vlan (\d+)',
                r'name (.+)',
                r'interface .+\.\d+',
                r'encapsulation dot1q \d+'
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
            'patterns': [
                r'interface ([A-Za-z0-9/]+)',
                r'switchport mode (access|trunk)',
                r'switchport (access|trunk allowed) vlan (\d+)'
            ],
            'show_commands': [
                'show interfaces status',
                'show running-config interface'
            ],
            'template': [
                'configure terminal',
                'interface {interface_name}',
                'switchport mode {mode}',
                'switchport {mode} vlan {vlan_id}',
                'exit'
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
                'show vlans',
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
                r'name (.+)',
                r'disable|enable'
            ],
            'show_commands': [
                'show interfaces brief',
                'show running-config interface'
            ],
            'template': [
                'configure terminal',
                'interface {interface_name}',
                'name {interface_desc}',
                '{interface_status}',
                'exit'
            ]
        },
        'vlan_interface': {
            'name': 'VLAN 인터페이스 설정',
            'patterns': [
                r'interface ([A-Za-z0-9/]+)',
                r'(tagged|untagged) vlan (\d+)'
            ],
            'show_commands': [
                'show interfaces',
                'show running-config interface'
            ],
            'template': [
                'configure terminal',
                'interface {interface_name}',
                '{mode} vlan {vlan_id}',
                'exit'
            ]
        },
        'ip_config': {
            'name': 'IP 주소 설정',
            'patterns': [
                r'interface ([A-Za-z0-9/]+)',
                r'ip address (\d+\.\d+\.\d+\.\d+)/(\d+)'
            ],
            'show_commands': [
                'show ip interface',
                'show running-config interface'
            ],
            'template': [
                'configure terminal',
                'interface {interface_name}',
                'ip address {ip_address}/{prefix_length}',
                'exit'
            ]
        },
        'routing_config': {
            'name': '라우팅 설정',
            'patterns': [
                r'router (ospf|bgp) (\d+)',
                r'area (\d+)',
                r'network (\d+\.\d+\.\d+\.\d+)/(\d+)'
            ],
            'show_commands': [
                'show ip route',
                'show ip ospf',
                'show ip bgp'
            ],
            'template': [
                'configure terminal',
                'router {protocol} {process_id}',
                'area {area_id}',
                'network {network_address}/{prefix_length}',
                'exit'
            ]
        },
        'acl_config': {
            'name': 'ACL 설정',
            'patterns': [
                r'ip access-list (standard|extended) (.+)',
                r'(permit|deny) (.+)'
            ],
            'show_commands': [
                'show access-list',
                'show running-config | include ip access-list'
            ],
            'template': [
                'configure terminal',
                'ip access-list {acl_type} {acl_name}',
                '{action} {acl_rule}',
                'exit'
            ]
        },
        'snmp_config': {
            'name': 'SNMP 설정',
            'patterns': [
                r'snmp-server community (.+) (operator|manager)',
                r'snmp-server host (\d+\.\d+\.\d+\.\d+) (.+)'
            ],
            'show_commands': [
                'show snmp-server',
                'show running-config | include snmp-server'
            ],
            'template': [
                'configure terminal',
                'snmp-server community {snmp_community} {access_level}',
                'snmp-server host {host} {community}',
                'exit'
            ]
        },
        'ntp_config': {
            'name': 'NTP 설정',
            'patterns': [
                r'ntp server (\S+)',
                r'ntp enable'
            ],
            'show_commands': [
                'show ntp',
                'show running-config | include ntp'
            ],
            'template': [
                'configure terminal',
                'ntp server {ntp_server}',
                'ntp enable',
                'exit'
            ]
        }
    },
    'arista': {
        'vlan_config': {
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
        }
    },
    'coreedgenetworks': {
        'vlan_config': {
            'name': 'VLAN 생성/삭제',
            'patterns': [
                r'vlan (\d+)',
                r'name (.+)'
            ],
            'show_commands': [
                'show vlan',
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
                'show interface status',
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
                'show interface switchport',
                'show running-config interface'
            ],
            'template': [
                'configure terminal',
                'interface {interface_name}',
                'switchport mode {mode}',
                'switchport {mode} vlan {vlan_id}',
                'exit'
            ]
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
                'show interface status',
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
                'show interface switchport',
                'show running-config interface'
            ],
            'template': [
                'configure terminal',
                'interface {interface_name}',
                'switchport mode {mode}',
                'switchport {mode} vlan {vlan_id}',
                'exit'
            ]
        }
    }
}

# app.py에서 import
from vendor_patterns import VENDOR_PATTERNS 