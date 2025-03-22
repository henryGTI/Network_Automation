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
        """?꾩슂???붾젆?좊━ ?앹꽦"""
        for directory in [self.tasks_dir, self.logs_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"?붾젆?좊━ ?앹꽦?? {directory}")

    def save_config(self, config):
        """?ㅼ젙 ???""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"?ㅼ젙 ????ㅽ뙣: {str(e)}")

    def load_config(self):
        """?ㅼ젙 濡쒕뱶"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            raise Exception(f"?ㅼ젙 濡쒕뱶 ?ㅽ뙣: {str(e)}")

    def load_cli_data(self):
        """CLI ?숈뒿 ?곗씠??濡쒕뱶"""
        cli_file = "cli_learning.json"
        try:
            with open(cli_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 湲곕낯 CLI ?곗씠??援ъ“ 諛섑솚
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
            raise Exception(f"CLI ?곗씠??濡쒕뱶 ?ㅽ뙣: {str(e)}")

    def save_cli_data(self, cli_data):
        """CLI ?숈뒿 ?곗씠?????""
        try:
            with open(self.cli_data_file, "w", encoding="utf-8") as f:
                json.dump(cli_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"CLI ?곗씠??????ㅽ뙣: {str(e)}")

    def save_device_info(self, script_file, device_info):
        """?λ퉬 湲곕낯 ?뺣낫 ???""
        try:
            # 湲곗〈 ?ㅼ젙 濡쒕뱶 ?먮뒗 ?덈줈 ?앹꽦
            if os.path.exists(script_file):
                with open(script_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {'basic_info': {}, 'configurations': []}
            
            # 湲곕낯 ?뺣낫 ?낅뜲?댄듃
            config['basic_info'] = device_info
            
            # ?뚯씪 ???            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"?λ퉬 ?뺣낫 ????ㅽ뙣: {str(e)}")

    def add_device_config(self, device_name, config_type, config_data):
        """?λ퉬 ?ㅼ젙 異붽?"""
        script_file = f"tasks/{device_name}_config.json"
        
        try:
            # 湲곗〈 ?ㅼ젙 濡쒕뱶
            with open(script_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # ?덈줈???ㅼ젙 異붽?
            config['configurations'].append({
                'type': config_type,
                'data': config_data,
                'timestamp': datetime.now().isoformat()
            })
            
            # ?뚯씪 ???            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"?λ퉬 ?ㅼ젙 異붽? ?ㅽ뙣: {str(e)}")

    def load_device_config(self, device_name):
        """?λ퉬 ?ㅼ젙 濡쒕뱶"""
        script_file = f"tasks/{device_name}_config.json"
        
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValueError(f"?λ퉬 '{device_name}'???ㅼ젙??李얠쓣 ???놁뒿?덈떎.")
        except Exception as e:
            raise Exception(f"?ㅼ젙 濡쒕뱶 ?ㅽ뙣: {str(e)}")

    def save_device_config(self, config_data):
        """?λ퉬 ?ㅼ젙 ???""
        try:
            device_name = config_data['device_name']
            file_path = os.path.join(self.tasks_dir, f"{device_name}_config.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"?ㅼ젙 ????꾨즺: {file_path}")
            return True, "?ㅼ젙???깃났?곸쑝濡???λ릺?덉뒿?덈떎."
        except Exception as e:
            logger.error(f"?ㅼ젙 ???以??ㅻ쪟: {str(e)}")
            return False, str(e)

    def generate_cli_commands(self, config_data):
        """CLI 紐낅졊???앹꽦"""
        vendor = config_data.get('vendor', '').lower()
        commands = []

        if 'config_types' in config_data:
            if config_data['config_types'].get('vlan', False):
                commands.extend(self._generate_vlan_commands(vendor))
            if config_data['config_types'].get('interface', False):
                commands.extend(self._generate_interface_commands(vendor))
            # ?ㅻⅨ ?ㅼ젙 ??낆뿉 ???紐낅졊???앹꽦...

        return commands

    def _generate_vlan_commands(self, vendor):
        """VLAN ?ㅼ젙 紐낅졊???앹꽦"""
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
        # ?ㅻⅨ 踰ㅻ뜑 異붽?...
        return []

    def _generate_interface_commands(self, vendor):
        """?명꽣?섏씠???ㅼ젙 紐낅졊???앹꽦"""
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
        # ?ㅻⅨ 踰ㅻ뜑 異붽?...
        return []

