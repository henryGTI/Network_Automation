import json
import os
from datetime import datetime
from typing import Dict, List

class ScriptGenerator:
    def __init__(self, cli_data=None):
        self.script_path = "tasks"
        if not os.path.exists(self.script_path):
            os.makedirs(self.script_path)
        self.cli_data = cli_data or {}

    def generate_script(self, device_info, config_type, config_data):
        """설정 스크립트 생성"""
        script_file = f"{self.script_path}/{device_info['device_name']}_config.json"
        
        try:
            # 기존 스크립트 파일이 있으면 로드, 없으면 새로 생성
            if os.path.exists(script_file):
                with open(script_file, 'r', encoding='utf-8') as f:
                    script_data = json.load(f)
            else:
                script_data = {
                    'basic_info': device_info,
                    'configurations': [],
                    'created_at': datetime.now().isoformat()
                }

            # 설정 명령어 생성
            commands = self._generate_commands(
                device_info['vendor'], 
                config_type, 
                config_data
            )
            
            # 설정 정보 추가
            script_data['configurations'].append({
                'type': config_type,
                'data': config_data,
                'commands': commands,
                'timestamp': datetime.now().isoformat()
            })

            # 스크립트 파일 저장
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=4, ensure_ascii=False)

            return True, "스크립트가 성공적으로 생성되었습니다."

        except Exception as e:
            return False, f"스크립트 생성 실패: {str(e)}"

    def _generate_commands(self, vendor, config_type, config_data):
        """벤더별 설정 명령어 생성"""
        commands = []

        if vendor.lower() == 'cisco':
            if config_type == 'vlan':
                commands.extend([
                    'configure terminal',
                    f"vlan {config_data['vlan_id']}",
                    f"name {config_data['vlan_name']}",
                    'exit'
                ])
            
            elif config_type == 'interface':
                commands.extend([
                    'configure terminal',
                    f"interface {config_data['interface']}",
                    f"switchport mode {config_data['mode']}"
                ])
                if config_data['mode'] == 'access':
                    commands.append(f"switchport access vlan {config_data['vlan']}")
                elif config_data['mode'] == 'trunk':
                    commands.append(f"switchport trunk allowed vlan {config_data['vlan']}")
                commands.append('exit')
            
            elif config_type == 'ip':
                commands.extend([
                    'configure terminal',
                    f"interface {config_data['interface']}",
                    f"ip address {config_data['ip_address']} {config_data['subnet_mask']}",
                    'no shutdown',
                    'exit'
                ])
            
            elif config_type == 'routing':
                if config_data['protocol'] == 'OSPF':
                    commands.extend([
                        'configure terminal',
                        f"router ospf 1",
                        f"network {config_data['network']} area 0",
                        'exit'
                    ])
                elif config_data['protocol'] == 'EIGRP':
                    commands.extend([
                        'configure terminal',
                        f"router eigrp 1",
                        f"network {config_data['network']}",
                        'exit'
                    ])
            
            elif config_type == 'acl':
                commands.extend([
                    'configure terminal',
                    f"ip access-list {config_data['acl_type']} {config_data['acl_name']}",
                    config_data['rule'],
                    'exit'
                ])
            
            elif config_type == 'security':
                commands.extend([
                    'configure terminal',
                    f"interface {config_data['interface']}",
                    'switchport port-security',
                    f"switchport port-security maximum {config_data['max_mac']}",
                    f"switchport port-security violation {config_data['violation_mode']}",
                    'exit'
                ])
            
            elif config_type == 'backup':
                if config_data['operation'] == 'backup':
                    commands.extend([
                        'copy running-config tftp:',
                        config_data['filename']
                    ])
                else:  # restore
                    commands.extend([
                        'copy tftp: running-config',
                        config_data['filename']
                    ])

        # 다른 벤더들의 명령어도 유사하게 구현...

        return commands

    def generate_routing_commands(self, vendor, routing_config):
        """라우팅 설정 명령어 생성"""
        commands = []
        vendor_cli = self.cli_data[vendor]
        
        if routing_config["protocol"] == "ospf":
            commands.append(vendor_cli["routing_ospf"].format(**routing_config))
        elif routing_config["protocol"] == "eigrp":
            commands.append(vendor_cli["routing_eigrp"].format(**routing_config))
        elif routing_config["protocol"] == "bgp":
            commands.append(vendor_cli["routing_bgp"].format(**routing_config))
            
        return commands
        
    def generate_acl_commands(self, vendor, acl_config):
        """ACL 설정 명령어 생성"""
        commands = []
        vendor_cli = self.cli_data[vendor]
        
        for rule in acl_config["rules"]:
            commands.append(vendor_cli["acl_rule"].format(**rule))
            
        return commands
        
    def generate_port_security_commands(self, vendor, security_config):
        """포트 보안 설정 명령어 생성"""
        commands = []
        vendor_cli = self.cli_data[vendor]
        
        if "port_security" in vendor_cli:
            commands.append(vendor_cli["port_security"].format(**security_config))
            
        return commands
        
    def save_script(self, vendor, script_name, commands):
        """생성된 스크립트 저장"""
        script_data = {
            "vendor": vendor,
            "created_at": datetime.now().isoformat(),
            "commands": commands
        }
        
        filename = f"tasks/{vendor}_{script_name}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(script_data, f, indent=4, ensure_ascii=False)
        return filename

    def generate_vlan_commands(self, vendor: str, config: Dict) -> List[str]:
        """VLAN 설정 명령어 생성"""
        commands = []
        vendor_cli = self.cli_data[vendor]
        
        # VLAN 생성
        commands.append(vendor_cli['vlan_create'].format(
            vlan_id=config['vlan_id']
        ))
        
        # VLAN 이름 설정
        if 'name' in config:
            commands.append(vendor_cli['vlan_name'].format(
                vlan_name=config['name']
            ))
            
        return commands

    def generate_interface_commands(self, vendor: str, config: Dict) -> List[str]:
        """인터페이스 설정 명령어 생성"""
        commands = []
        vendor_cli = self.cli_data[vendor]
        
        # 인터페이스 모드 설정
        if config['mode'] == 'access':
            commands.extend([
                f"interface {config['interface']}",
                vendor_cli['interface_access'].format(
                    vlan_id=config['vlan_id']
                )
            ])
        elif config['mode'] == 'trunk':
            commands.extend([
                f"interface {config['interface']}",
                vendor_cli['interface_trunk'].format(
                    vlan_list=config['allowed_vlans']
                )
            ])
            
        return commands

    def generate_ip_commands(self, vendor: str, config: Dict) -> List[str]:
        """IP 설정 명령어 생성"""
        commands = []
        vendor_cli = self.cli_data[vendor]
        
        commands.extend([
            f"interface {config['interface']}",
            vendor_cli['ip_config'].format(
                ip_address=config['ip_address'],
                subnet_mask=config['subnet_mask']
            )
        ])
        
        return commands

    def generate_routing_commands(self, vendor: str, config: Dict) -> List[str]:
        """라우팅 설정 명령어 생성"""
        commands = []
        vendor_cli = self.cli_data[vendor]
        
        if config['protocol'] == 'ospf':
            commands.extend([
                vendor_cli['routing_ospf'].format(
                    process_id=config['process_id'],
                    network=config['network'],
                    area=config['area']
                )
            ])
        elif config['protocol'] == 'eigrp':
            commands.extend([
                vendor_cli['routing_eigrp'].format(
                    as_number=config['as_number'],
                    network=config['network']
                )
            ])
        elif config['protocol'] == 'bgp':
            commands.extend([
                vendor_cli['routing_bgp'].format(
                    as_number=config['as_number'],
                    neighbor=config['neighbor'],
                    remote_as=config['remote_as']
                )
            ])
            
        return commands

    def generate_acl_commands(self, vendor: str, config: Dict) -> List[str]:
        """ACL 설정 명령어 생성"""
        commands = []
        vendor_cli = self.cli_data[vendor]
        
        for rule in config['rules']:
            commands.append(vendor_cli['acl_rule'].format(
                acl_id=config['acl_id'],
                action=rule['action'],
                source=rule['source'],
                destination=rule['destination']
            ))
            
        return commands

    def generate_port_security_commands(self, vendor: str, config: Dict) -> List[str]:
        """포트 보안 설정 명령어 생성"""
        commands = []
        vendor_cli = self.cli_data[vendor]
        
        commands.extend([
                    f"interface {config['interface']}",
            vendor_cli['port_security'].format(
                max_mac=config['max_mac_addresses'],
                violation=config['violation_action']
            )
        ])
        
        return commands

    def generate_backup_commands(self, vendor: str) -> str:
        """백업 명령어 생성"""
        return self.cli_data[vendor]['backup_config']

    def generate_restore_commands(self, vendor: str, config_file: str) -> List[str]:
        """복원 명령어 생성"""
        return [
            self.cli_data[vendor]['restore_config'].format(
                config_file=config_file
            )
        ]
