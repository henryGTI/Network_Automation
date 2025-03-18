import ipaddress
import re
from exceptions import ValidationError

class NetworkValidator:
    @staticmethod
    def validate_vlan_id(vlan_id):
        """VLAN ID 유효성 검사"""
        try:
            vlan_id = int(vlan_id)
            if not (1 <= vlan_id <= 4094):
                raise ValidationError("VLAN ID는 1-4094 범위여야 합니다.")
        except ValueError:
            raise ValidationError("VLAN ID는 숫자여야 합니다.")
            
    @staticmethod
    def validate_ip_address(ip):
        """IP 주소 유효성 검사"""
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise ValidationError("유효하지 않은 IP 주소입니다.")
            
    @staticmethod
    def validate_hostname(hostname):
        """호스트명 유효성 검사"""
        if not re.match(r'^[a-zA-Z0-9-]+$', hostname):
            raise ValidationError("호스트명은 영문자, 숫자, 하이픈만 포함할 수 있습니다.")
            
    @staticmethod
    def validate_port_number(port):
        """포트 번호 유효성 검사"""
        try:
            port = int(port)
            if not (1 <= port <= 65535):
                raise ValidationError("포트 번호는 1-65535 범위여야 합니다.")
        except ValueError:
            raise ValidationError("포트 번호는 숫자여야 합니다.")
            
    @staticmethod
    def validate_mac_address(mac):
        """MAC 주소 유효성 검사"""
        if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac):
            raise ValidationError("유효하지 않은 MAC 주소 형식입니다.")
            
    @staticmethod
    def validate_interface_name(interface):
        """인터페이스 이름 유효성 검사"""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9/]+$', interface):
            raise ValidationError("유효하지 않은 인터페이스 이름입니다.") 