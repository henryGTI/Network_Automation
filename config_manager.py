import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self):
        self.config_file = "config.json"
        self.cli_data_file = "cli_learning.json"
        self.tasks_dir = 'tasks'
        self.logs_dir = 'logs'
        self.setup_directories()

    def setup_directories(self):
        """필요한 디렉토리 생성"""
        for directory in [self.tasks_dir, self.logs_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"디렉토리 생성됨: {directory}")

    def save_config(self, config):
        """설정 저장"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"설정 저장 실패: {str(e)}")

    def load_config(self):
        """설정 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            raise Exception(f"설정 로드 실패: {str(e)}")

    def load_cli_data(self):
        """CLI 학습 데이터 로드"""
        cli_file = "cli_learning.json"
        try:
            with open(cli_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 기본 CLI 데이터 구조 반환
            return {
                "cisco": {
                    "vlan": {"create": "vlan {vlan_id}", "name": "name {vlan_name}"},
                    "interface": {"access": "switchport mode access", "trunk": "switchport mode trunk"}
                },
                "juniper": {
                    "vlan": {"create": "set vlans {vlan_name} vlan-id {vlan_id}"},
                    "interface": {"access": "set interface {interface} unit 0 family ethernet-switching port-mode access"}
                }
            }
        except Exception as e:
            raise Exception(f"CLI 데이터 로드 실패: {str(e)}")

    def save_cli_data(self, cli_data):
        """CLI 학습 데이터 저장"""
        try:
            with open(self.cli_data_file, "w", encoding="utf-8") as f:
                json.dump(cli_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"CLI 데이터 저장 실패: {str(e)}")

    def save_device_info(self, script_file, device_info):
        """장비 기본 정보 저장"""
        try:
            # 기존 설정 로드 또는 새로 생성
            if os.path.exists(script_file):
                with open(script_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {'basic_info': {}, 'configurations': []}
            
            # 기본 정보 업데이트
            config['basic_info'] = device_info
            
            # 파일 저장
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"장비 정보 저장 실패: {str(e)}")

    def add_device_config(self, device_name, config_type, config_data):
        """장비 설정 추가"""
        script_file = f"tasks/{device_name}_config.json"
        
        try:
            # 기존 설정 로드
            with open(script_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 새로운 설정 추가
            config['configurations'].append({
                'type': config_type,
                'data': config_data,
                'timestamp': datetime.now().isoformat()
            })
            
            # 파일 저장
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"장비 설정 추가 실패: {str(e)}")

    def load_device_config(self, device_name):
        """장비 설정 로드"""
        script_file = f"tasks/{device_name}_config.json"
        
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValueError(f"장비 '{device_name}'의 설정을 찾을 수 없습니다.")
        except Exception as e:
            raise Exception(f"설정 로드 실패: {str(e)}")

    def save_device_config(self, config_data):
        """장비 설정 저장"""
        try:
            device_name = config_data['device_name']
            file_path = os.path.join(self.tasks_dir, f"{device_name}_config.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"설정 저장 완료: {file_path}")
            return True, "설정이 성공적으로 저장되었습니다."
        except Exception as e:
            logger.error(f"설정 저장 중 오류: {str(e)}")
            return False, str(e)

    def generate_cli_commands(self, config_data):
        """CLI 명령어 생성"""
        vendor = config_data.get('vendor', '').lower()
        commands = []

        if 'config_types' in config_data:
            if config_data['config_types'].get('vlan', False):
                commands.extend(self._generate_vlan_commands(vendor))
            if config_data['config_types'].get('interface', False):
                commands.extend(self._generate_interface_commands(vendor))
            # 다른 설정 타입에 대한 명령어 생성...

        return commands

    def _generate_vlan_commands(self, vendor):
        """VLAN 설정 명령어 생성"""
        if vendor == 'cisco':
            return [
                "conf t",
                "vlan 10",
                "name VLAN_10",
                "exit"
            ]
        elif vendor == 'juniper':
            return [
                "configure",
                "set vlans VLAN_10 vlan-id 10",
                "commit"
            ]
        # 다른 벤더 추가...
        return []

    def _generate_interface_commands(self, vendor):
        """인터페이스 설정 명령어 생성"""
        if vendor == 'cisco':
            return [
                "conf t",
                "interface GigabitEthernet1/0/1",
                "switchport mode access",
                "switchport access vlan 10",
                "exit"
            ]
        elif vendor == 'juniper':
            return [
                "configure",
                "set interfaces ge-0/0/1 unit 0 family ethernet-switching vlan members 10",
                "commit"
            ]
        # 다른 벤더 추가...
        return []
