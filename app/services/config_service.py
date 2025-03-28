﻿import json
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

    def get_task_parameters(self, task_type, subtask=None):
        """작업 유형과 상세 작업에 따른 파라미터 목록을 반환합니다."""
        try:
            parameters = {
                'LAYER2': {
                    'Link-Aggregation(Manual)': {
                        'config': {
                            'parameters': [
                                {'name': 'group_number', 'type': 'number', 'label': '그룹 번호', 'required': True, 'min': 1, 'max': 32},
                                {'name': 'interface_list', 'type': 'text', 'label': '인터페이스 목록', 'required': True, 'placeholder': '예: gi 0/1-0/2'},
                                {'name': 'mode', 'type': 'select', 'label': '모드', 'required': True, 'options': [
                                    {'value': 'manual', 'label': 'Manual'},
                                ]}
                            ],
                            'commands': [
                                'configure terminal',
                                'link-aggregation {group_number} mode manual',
                                'interface {interface_list}',
                                'link-aggregation {group_number} manual',
                                'end'
                            ]
                        },
                        'check': {
                            'parameters': [],
                            'commands': [
                                'show link-aggregation brief',
                                'show link-aggregation group {group_number}'
                            ]
                        }
                    },
                    'Link-Aggregation(LACP)': {
                        'config': {
                            'parameters': [
                                {'name': 'group_number', 'type': 'number', 'label': '그룹 번호', 'required': True, 'min': 1, 'max': 32},
                                {'name': 'interface_list', 'type': 'text', 'label': '인터페이스 목록', 'required': True, 'placeholder': '예: gi 0/1-0/2'},
                                {'name': 'mode', 'type': 'select', 'label': '모드', 'required': True, 'options': [
                                    {'value': 'active', 'label': 'Active'},
                                    {'value': 'passive', 'label': 'Passive'}
                                ]}
                            ],
                            'commands': [
                                'configure terminal',
                                'link-aggregation {group_number} mode lacp',
                                'interface {interface_list}',
                                'link-aggregation {group_number} active',
                                'end'
                            ]
                        },
                        'check': {
                            'parameters': [],
                            'commands': [
                                'show link-aggregation brief',
                                'show link-aggregation group {group_number}'
                            ]
                        }
                    },
                    'VLAN': {
                        'config': {
                            'parameters': [
                                {'name': 'vlan_id', 'type': 'number', 'label': 'VLAN ID', 'required': True, 'min': 2, 'max': 4094},
                                {'name': 'interface', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: gi 0/1'},
                                {'name': 'mode', 'type': 'select', 'label': '모드', 'required': True, 'options': [
                                    {'value': 'access', 'label': 'Access'},
                                    {'value': 'trunk', 'label': 'Trunk'}
                                ]},
                                {'name': 'allowed_vlans', 'type': 'text', 'label': '허용 VLAN', 'required': False, 'placeholder': '예: 10-15'}
                            ],
                            'commands': [
                                'configure terminal',
                                'vlan {vlan_id}',
                                'interface {interface}',
                                'switchport mode {mode}',
                                'switchport access vlan {vlan_id}',
                                'switchport trunk allowed vlan add {allowed_vlans}',
                                'end'
                            ]
                        },
                        'check': {
                            'parameters': [],
                            'commands': [
                                'show vlan',
                                'show interface {interface} vlan status'
                            ]
                        }
                    },
                    'Spanning-tree': {
                        'config(RSTP)': {
                            'parameters': [
                                {'name': 'mode', 'type': 'select', 'label': 'STP 모드', 'required': True, 'options': [
                                    {'value': 'rstp', 'label': 'RSTP'}
                                ]},
                                {'name': 'priority', 'type': 'number', 'label': '우선순위', 'required': True, 'min': 0, 'max': 32768}
                            ],
                            'commands': [
                                'configure terminal',
                                'spanning-tree mode rstp',
                                'spanning-tree enable',
                                'spanning-tree mst instance 0 priority {priority}',
                                'end'
                            ]
                        },
                        'config(PVST+)': {
                            'parameters': [
                                {'name': 'mode', 'type': 'select', 'label': 'STP 모드', 'required': True, 'options': [
                                    {'value': 'rapid-vst', 'label': 'Rapid-VST'}
                                ]},
                                {'name': 'vlan_id', 'type': 'number', 'label': 'VLAN ID', 'required': True, 'min': 1, 'max': 4094},
                                {'name': 'priority', 'type': 'number', 'label': '우선순위', 'required': True, 'min': 0, 'max': 32768}
                            ],
                            'commands': [
                                'configure terminal',
                                'spanning-tree mode rapid-vst',
                                'spanning-tree enable',
                                'spanning-tree vlan {vlan_id} priority {priority}',
                                'end'
                            ]
                        },
                        'check': {
                            'parameters': [],
                            'commands': [
                                'show spanning-tree',
                                'show spanning-tree detail',
                                'show spanning-tree bpdu statistics'
                            ]
                        }
                    }
                }
            }

            # 작업 유형과 하위 작업이 모두 존재하는지 확인
            if task_type not in parameters:
                logger.warning(f"지원하지 않는 작업 유형: {task_type}")
                return []
            
            if subtask not in parameters[task_type]:
                logger.warning(f"지원하지 않는 하위 작업: {task_type}/{subtask}")
                return []
            
            return parameters[task_type][subtask]
        except Exception as e:
            logger.error(f"파라미터 로드 중 오류 발생: {str(e)}")
            return []

    def get_task_types(self):
        """작업 유형 목록 조회"""
        return list(self.get_task_parameters("", "").keys())

    def get_subtasks(self, task_type):
        """작업 유형별 하위 작업 목록 조회"""
        task_parameters = self.get_task_parameters("", "")
        if task_type in task_parameters:
            return list(task_parameters[task_type].keys())
        return []

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

    def generate_script(self, device_id, task_types, subtask_type, vendor, parameters):
        """스크립트 생성 메소드
        
        Args:
            device_id (str): 장비 ID
            task_types (list): 작업 유형 목록
            subtask_type (dict): 작업 유형별 상세 작업 딕셔너리
            vendor (str): 장비 벤더
            parameters (dict): 작업 유형별 파라미터 딕셔너리
            
        Returns:
            str: 생성된 스크립트
        """
        try:
            logger.info(f"스크립트 생성 시작: 장비={device_id}, 벤더={vendor}, 작업={task_types}")
            
            # 라우팅 설정 파라미터 검증
            if '라우팅 설정' in task_types:
                current_subtask = subtask_type.get('라우팅 설정')
                if current_subtask == 'OSPF 설정':
                    required_params = ['process_id', 'network_address', 'wildcard_mask', 'area_id']
                    template_key = 'ospf'
                elif current_subtask == '정적 라우팅 설정':
                    required_params = ['network_address', 'subnet_mask', 'next_hop']
                    template_key = 'static'
                else:
                    raise ValueError(f"지원하지 않는 라우팅 설정 유형입니다: {current_subtask}")

                task_params = parameters.get('라우팅 설정', {})
                for param in required_params:
                    if param not in task_params:
                        raise ValueError(f"라우팅 설정에 필요한 파라미터가 누락되었습니다: {param}")
                
                if current_subtask == 'OSPF 설정':
                    # process_id 검증
                    try:
                        process_id = int(task_params['process_id'])
                        if not (1 <= process_id <= 65535):
                            raise ValueError
                    except ValueError:
                        raise ValueError("프로세스 ID는 1-65535 사이의 숫자여야 합니다.")
                    
                    # area_id 검증
                    try:
                        area_id = int(task_params['area_id'])
                        if not (0 <= area_id <= 4294967295):
                            raise ValueError
                    except ValueError:
                        raise ValueError("OSPF Area ID는 0-4294967295 사이의 숫자여야 합니다.")

            # 벤더별 명령어 템플릿 정의
            templates = {
                'cisco': {
                    'vlan_config': {
                        'name': 'VLAN 관리',
                        'template': [
                            'configure terminal',
                            'vlan {vlan_id}',
                            'name {vlan_name}',
                            'exit'
                        ]
                    },
                    'interface_config': {
                        'name': '인터페이스 설정',
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
                        'template': {
                            'ospf': [
                                'configure terminal',
                                'router ospf {process_id}',
                                'network {network_address} {wildcard_mask} area {area_id}',
                                'exit'
                            ],
                            'static': [
                                'configure terminal',
                                'ip route {network_address} {subnet_mask} {next_hop}',
                                'exit'
                            ]
                        }
                    },
                    'acl_config': {
                        'name': 'ACL 설정',
                        'template': [
                            'configure terminal',
                            'ip access-list {acl_type} {acl_number}',
                            '{action} {acl_rule}',
                            'exit'
                        ]
                    },
                    'snmp_config': {
                        'name': 'SNMP 설정',
                        'template': [
                            'configure terminal',
                            'snmp-server community {snmp_community} {access_type}',
                            'snmp-server host {host} version {snmp_version} {community}',
                            'exit'
                        ]
                    },
                    'ntp_config': {
                        'name': 'NTP 설정',
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
                        'template': [
                            'configure',
                            'set vlans {vlan_name} vlan-id {vlan_id}',
                            'commit'
                        ]
                    },
                    'interface_config': {
                        'name': '인터페이스 설정',
                        'template': [
                            'configure',
                            'set interfaces {interface_name} description "{interface_desc}"',
                            'commit'
                        ]
                    }
                },
                'huawei': {
                    'vlan_config': {
                        'name': 'VLAN 생성/삭제',
                        'template': [
                            'system-view',
                            'vlan {vlan_id}',
                            'name {vlan_name}',
                            'quit'
                        ]
                    }
                }
            }
            
            # 작업 유형과 템플릿 키 간의 매핑
            task_type_to_template = {
                'VLAN 관리': 'vlan_config',
                '포트 설정': 'interface_config',
                'VLAN 인터페이스 설정': 'vlan_interface',
                'IP 주소 설정': 'ip_config',
                '라우팅 설정': 'routing_config',
                'ACL 설정': 'acl_config',
                'SNMP 설정': 'snmp_config',
                'NTP 설정': 'ntp_config'
            }
            
            # 상세 작업과 템플릿 키 간의 매핑
            subtask_to_template = {
                'VLAN 관리': {
                    'VLAN 생성': 'vlan_config',
                    'VLAN 삭제': 'vlan_config',
                    'VLAN 이름 설정': 'vlan_config'
                },
                '포트 설정': {
                    '포트 IP추가': 'ip_config',
                    '포트 활성화': 'interface_config',
                    '포트 비활성화': 'interface_config',
                    '포트 속도 설정': 'interface_config',
                    '액세스 모드 설정': 'vlan_interface',
                    '트렁크 모드 설정': 'vlan_interface'
                },
                '라우팅 설정': {
                    'OSPF 설정': 'routing_config',
                    '정적 라우팅 설정': 'routing_config'
                }
            }

            # 작업 유형별 필수 파라미터 정의
            required_parameters = {
                'VLAN 관리': {
                    'VLAN 생성': ['vlan_id', 'vlan_name'],
                    'VLAN 삭제': ['vlan_id'],
                    'VLAN 이름 설정': ['vlan_id', 'vlan_name']
                },
                '포트 설정': {
                    '포트 IP추가': ['interface_name', 'ip_address', 'subnet_mask'],
                    '포트 활성화': ['interface_name'],
                    '포트 비활성화': ['interface_name'],
                    '포트 속도 설정': ['interface_name', 'speed', 'duplex'],
                    '액세스 모드 설정': ['interface_name', 'vlan_id'],
                    '트렁크 모드 설정': ['interface_name', 'allowed_vlans']
                },
                '라우팅 설정': {
                    'OSPF 설정': ['process_id', 'network_address', 'wildcard_mask', 'area_id'],
                    '정적 라우팅 설정': ['network_address', 'subnet_mask', 'next_hop']
                }
            }
            
            # 지원하는 벤더인지 확인
            if vendor.lower() not in templates:
                raise ValueError(f"지원하지 않는 벤더입니다: {vendor}")
            
            # 스크립트 생성
            script_lines = []
            script_lines.append(f"! 설정 스크립트 - 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            script_lines.append(f"! 장비 ID: {device_id}")
            script_lines.append(f"! 벤더: {vendor}")
            script_lines.append("!")
            
            vendor_templates = templates[vendor.lower()]
            
            # 각 작업 유형별로 스크립트 생성
            for task_type in task_types:
                current_subtask = subtask_type.get(task_type)
                task_params = parameters.get(task_type, {})
                
                # 필수 파라미터 검증
                if task_type in required_parameters and current_subtask in required_parameters[task_type]:
                    required_params = required_parameters[task_type][current_subtask]
                    for param in required_params:
                        if param not in task_params:
                            raise ValueError(f"{task_type} - {current_subtask}에 필요한 파라미터가 누락되었습니다: {param}")
                
                # 작업 유형에 해당하는 템플릿 키 찾기
                template_key = None
                
                # 상세 작업이 특별한 템플릿을 사용하는지 확인
                if task_type in subtask_to_template and current_subtask in subtask_to_template[task_type]:
                    template_key = subtask_to_template[task_type][current_subtask]
                else:
                    template_key = task_type_to_template.get(task_type)
                
                if not template_key:
                    logger.warning(f"템플릿을 찾을 수 없습니다: {task_type}/{current_subtask}")
                    continue

                # 벤더별 템플릿 확인
                template_data = vendor_templates.get(template_key)
                
                if not template_data:
                    logger.warning(f"벤더 {vendor}에 대한 템플릿을 찾을 수 없습니다: {template_key}")
                    continue

                script_lines.append(f"! {task_type} - {current_subtask}")
                
                # 라우팅 설정의 경우 템플릿 선택
                if task_type == '라우팅 설정':
                    if current_subtask == 'OSPF 설정':
                        template = template_data['template']['ospf']
                    elif current_subtask == '정적 라우팅 설정':
                        template = template_data['template']['static']
                    else:
                        continue
                else:
                    template = template_data['template']
                
                # 템플릿에 파라미터 적용
                for cmd_template in template:
                    try:
                        cmd = cmd_template.format(**task_params)
                        script_lines.append(cmd)
                    except KeyError as e:
                        script_lines.append(f"! 주의: '{e.args[0]}' 파라미터가 필요합니다")
                
                script_lines.append("!")
            
            script_content = "\n".join(script_lines)
            logger.info("스크립트 생성 완료")
            
            return script_content
            
        except Exception as e:
            logger.error(f"스크립트 생성 실패: {str(e)}")
            raise ValueError(f"스크립트 생성 실패: {str(e)}")
    
    def execute_script(self, device_id, script):
        """스크립트 실행 메소드
        
        Args:
            device_id (str): 장비 ID
            script (str): 실행할 스크립트
            
        Returns:
            str: 실행 결과
        """
        try:
            logger.info(f"스크립트 실행 시작: 장비={device_id}, 스크립트 길이={len(script)}")
            
            # 실행 결과를 저장할 디렉토리
            result_dir = os.path.join(self.base_dir, str(device_id), "results")
            ensure_directory_exists(result_dir)
            
            # 실행할 스크립트 저장
            script_filename = f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            script_path = os.path.join(result_dir, script_filename)
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            
            # TODO: 실제 장비 연결 및 명령 실행 로직
            # 여기서는 시뮬레이션만 수행
            
            # 실행 결과 생성
            result_lines = []
            result_lines.append(f"=== 스크립트 실행 결과 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
            result_lines.append(f"장비 ID: {device_id}")
            result_lines.append("")
            
            # 각 명령어 실행 결과 시뮬레이션
            for line in script.splitlines():
                if line.startswith('!') or not line.strip():
                    continue
                    
                result_lines.append(f"> {line}")
                # 명령어에 따른 결과 시뮬레이션
                if "show" in line:
                    result_lines.append("시뮬레이션된 출력 결과")
                    result_lines.append("")
                else:
                    # 설정 명령어는 성공 응답만 표시
                    result_lines.append("명령 성공적으로 실행됨")
                    result_lines.append("")
            
            # 실행 결과 저장
            result_filename = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            result_path = os.path.join(result_dir, result_filename)
            result_content = "\n".join(result_lines)
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write(result_content)
            
            logger.info(f"스크립트 실행 완료, 결과 저장: {result_path}")
            
            return result_content
            
        except Exception as e:
            logger.error(f"스크립트 실행 중 오류: {str(e)}")
            raise ValueError(f"스크립트 실행 실패: {str(e)}")

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

