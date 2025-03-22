import json
import os
from datetime import datetime
import logging
from ..models.config_task import ConfigTask
from ..utils.file_handler import ensure_directory_exists

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, base_dir='config/tasks'):
        self.base_dir = base_dir
        ensure_directory_exists(base_dir)
        self.tasks = {}  # device_id별 작업 목록
        self.load_tasks()

    def load_tasks(self):
        """저장된 작업 로드"""
        for device_id in os.listdir(self.base_dir):
            device_path = os.path.join(self.base_dir, device_id)
            if os.path.isdir(device_path):
                self.tasks[device_id] = []
                tasks_file = os.path.join(device_path, 'tasks.json')
                if os.path.exists(tasks_file):
                    with open(tasks_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for task_data in data:
                            self.tasks[device_id].append(ConfigTask.from_dict(task_data))

    def save_tasks(self, device_id):
        """작업을 파일에 저장"""
        device_dir = os.path.join(self.base_dir, str(device_id))
        ensure_directory_exists(device_dir)
        tasks_file = os.path.join(device_dir, 'tasks.json')
        
        tasks_data = [task.to_dict() for task in self.tasks.get(str(device_id), [])]
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

    def add_task(self, device_id, task_type, subtask, parameters=None):
        """새로운 작업 추가"""
        device_id = str(device_id)
        if device_id not in self.tasks:
            self.tasks[device_id] = []
        
        task = ConfigTask(device_id, task_type, subtask, parameters)
        self.tasks[device_id].append(task)
        self.save_tasks(device_id)
        return task

    def get_tasks(self, device_id=None):
        """작업 조회"""
        if device_id:
            return self.tasks.get(str(device_id), [])
        return self.tasks

    def get_task_types(self):
        """작업 유형 목록 조회"""
        return ConfigTask.get_task_types()

    def get_subtasks(self, task_type):
        """작업 유형별 하위 작업 목록 조회"""
        return ConfigTask.get_subtasks(task_type)

    def update_task_status(self, device_id, task_index, status, result=None, error=None):
        """작업 상태 업데이트"""
        device_id = str(device_id)
        if device_id not in self.tasks:
            return False
        
        try:
            task = self.tasks[device_id][task_index]
            task.status = status
            task.result = result
            task.error = error
            self.save_tasks(device_id)
            return True
        except IndexError:
            return False

    def delete_task(self, device_id, task_index):
        """작업 삭제"""
        device_id = str(device_id)
        if device_id not in self.tasks:
            return False
        
        try:
            self.tasks[device_id].pop(task_index)
            self.save_tasks(device_id)
            return True
        except IndexError:
            return False

    def clear_tasks(self, device_id):
        """장비의 모든 작업 삭제"""
        device_id = str(device_id)
        if device_id in self.tasks:
            self.tasks[device_id] = []
            self.save_tasks(device_id)
            return True
        return False

    def get_task_parameters(self, task_type, subtask):
        """작업 유형별 필요한 파라미터 정보 반환"""
        parameters = {
            'vlan': {
                'create': ['vlan_id', 'vlan_name'],
                'delete': ['vlan_id'],
                'interface_assign': ['interface', 'vlan_id'],
                'trunk': ['interface', 'allowed_vlans']
            },
            'port': {
                'mode': ['interface', 'mode', 'vlan_id'],
                'speed': ['interface', 'speed', 'duplex'],
                'status': ['interface', 'status']
            },
            'routing': {
                'static': ['network', 'mask', 'next_hop'],
                'ospf': ['process_id', 'network', 'area'],
                'eigrp': ['as_number', 'network'],
                'bgp': ['as_number', 'neighbor', 'remote_as']
            },
            'security': {
                'port_security': ['interface', 'max_mac', 'violation'],
                'ssh': ['version', 'timeout', 'authentication'],
                'aaa': ['method', 'server_group', 'service'],
                'acl': ['name', 'type', 'entries']
            },
            'stp_lacp': {
                'stp': ['mode', 'priority'],
                'lacp': ['channel_group', 'interfaces', 'mode']
            },
            'qos': {
                'policy': ['policy_name', 'class_map', 'actions'],
                'rate_limit': ['interface', 'rate', 'burst'],
                'service_policy': ['interface', 'policy_name', 'direction']
            },
            'monitoring': {
                'route': [],
                'ospf': [],
                'bgp': []
            },
            'status': {
                'interface': ['interface'],
                'traffic': ['interface']
            },
            'logging': {
                'show': []
            },
            'backup': {
                'backup': ['filename'],
                'restore': ['filename'],
                'tftp': ['server', 'filename']
            },
            'snmp': {
                'setup': ['community', 'version', 'access'],
                'discovery': ['protocol']
            },
            'automation': {
                'deploy': ['config_file', 'devices'],
                'verify': ['condition', 'action']
            }
        }
        
        return parameters.get(task_type, {}).get(subtask, [])

class ConfigManager:
    def __init__(self):
        self.config_file = "config.json"
        self.cli_data_file = "cli_learning.json"
        self.tasks_dir = 'tasks'
        self.logs_dir = 'logs'
        self.setup_directories()

    def setup_directories(self):
        """디렉토리 구조 설정"""
        for directory in [self.tasks_dir, self.logs_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"디렉토리 생성됨: {directory}")

    def generate_script(self, device_id, task_types, parameters):
        """스크립트 생성"""
        try:
            # 장비 정보 조회
            device_info = self.get_device_info(device_id)
            if not device_info:
                raise ValueError(f"장비를 찾을 수 없습니다: {device_id}")

            vendor = device_info.get('vendor', '').lower()
            if not vendor:
                raise ValueError(f"장비의 벤더 정보가 없습니다: {device_id}")

            # CLI 데이터 로드
            cli_data = self.load_cli_data()
            if vendor not in cli_data:
                raise ValueError(f"지원하지 않는 벤더입니다: {vendor}")

            # 스크립트 생성
            script = []
            script.append(f"! 장비: {device_info['name']}")
            script.append(f"! IP: {device_info['ip']}")
            script.append(f"! 벤더: {vendor}")
            script.append("")

            # 작업 유형별 스크립트 생성
            for task_type in task_types:
                if task_type in cli_data[vendor]:
                    task_script = self._generate_task_script(
                        vendor, task_type, parameters.get(task_type, {})
                    )
                    script.extend(task_script)
                    script.append("")

            return "\n".join(script)

        except Exception as e:
            logger.error(f"스크립트 생성 중 오류: {str(e)}")
            raise Exception(f"스크립트 생성 실패: {str(e)}")

    def _generate_task_script(self, vendor, task_type, parameters):
        """작업 유형별 스크립트 생성"""
        try:
            cli_data = self.load_cli_data()
            if task_type not in cli_data[vendor]:
                return []

            script = []
            script.append(f"! {task_type} 설정")
            
            # 파라미터 적용하여 명령어 생성
            for cmd_type, cmd_template in cli_data[vendor][task_type].items():
                try:
                    cmd = cmd_template.format(**parameters)
                    script.append(cmd)
                except KeyError as e:
                    logger.warning(f"필수 파라미터 누락: {e}")
                    continue

            return script

        except Exception as e:
            logger.error(f"작업 스크립트 생성 중 오류: {str(e)}")
            return []

    def get_device_info(self, device_id):
        """장비 정보 조회"""
        try:
            config = self.load_config()
            devices = config.get('devices', [])
            for device in devices:
                if device.get('id') == device_id:
                    return device
            return None
        except Exception as e:
            logger.error(f"장비 정보 조회 중 오류: {str(e)}")
            return None

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
        try:
            with open(self.cli_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 기본 CLI 데이터 반환
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
            # 추가 설정 타입에 대한 명령어 생성...

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
        # 추가 벤더 지원...
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
        # 추가 벤더 지원...
        return []

