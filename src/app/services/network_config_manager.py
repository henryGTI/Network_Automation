from typing import Dict, List
import ipaddress
from exceptions import ValidationError

class NetworkConfigManager:
    def __init__(self, script_generator, executor):
        self.script_generator = script_generator
        self.executor = executor

    def validate_vlan_id(self, vlan_id: int) -> bool:
        """VLAN ID 유효성 검사"""
        if not isinstance(vlan_id, int):
            raise ValidationError("VLAN ID는 정수여야 합니다.")
        if not 1 <= vlan_id <= 4094:
            raise ValidationError("VLAN ID는 1-4094 범위여야 합니다.")
        return True

    def validate_ip_address(self, ip: str) -> bool:
        """IP 주소 유효성 검사"""
        try:
            ipaddress.ip_interface(ip)
            return True
        except ValueError:
            raise ValidationError("유효하지 않은 IP 주소입니다.")

    def configure_vlan(self, vendor: str, config: Dict) -> str:
        """VLAN 설정"""
        self.validate_vlan_id(int(config['vlan_id']))
        commands = self.script_generator.generate_vlan_commands(vendor, config)
        return self.executor.execute_config(commands)

    def configure_interface(self, vendor: str, config: Dict) -> str:
        """인터페이스 설정"""
        commands = self.script_generator.generate_interface_commands(vendor, config)
        return self.executor.execute_config(commands)

    def configure_ip(self, vendor: str, config: Dict) -> str:
        """IP 설정"""
        self.validate_ip_address(config['ip_address'])
        commands = self.script_generator.generate_ip_commands(vendor, config)
        return self.executor.execute_config(commands)

    def configure_routing(self, vendor: str, config: Dict) -> str:
        """라우팅 설정"""
        commands = self.script_generator.generate_routing_commands(vendor, config)
        return self.executor.execute_config(commands)

    def configure_acl(self, vendor: str, config: Dict) -> str:
        """ACL 설정"""
        commands = self.script_generator.generate_acl_commands(vendor, config)
        return self.executor.execute_config(commands)

    def configure_port_security(self, vendor: str, config: Dict) -> str:
        """포트 보안 설정"""
        commands = self.script_generator.generate_port_security_commands(vendor, config)
        return self.executor.execute_config(commands)

    def backup_config(self, vendor: str, device_info: Dict) -> str:
        """설정 백업"""
        command = self.script_generator.generate_backup_commands(vendor)
        return self.executor.execute_config(command)

    def restore_config(self, vendor: str, device_info: Dict, config_file: str) -> str:
        """설정 복원"""
        commands = self.script_generator.generate_restore_commands(vendor, config_file)
        return self.executor.execute_config(commands) 