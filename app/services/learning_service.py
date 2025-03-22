import os
import json
from ..exceptions import CLILearningError, ValidationError
from datetime import datetime
from ..models.cli_command import CLICommand
from ..models.device import Device
from ..utils.file_handler import ensure_directory_exists
from app.utils.logger import setup_logger
from flask_sqlalchemy import SQLAlchemy
from app import db
import logging
import requests
from bs4 import BeautifulSoup
import re

CLI_LEARNING_FILE = "cli_learning.json"

logger = setup_logger(__name__)
db = SQLAlchemy()

class LearningService:
    def __init__(self, base_dir='config/cli_learning'):
        self.base_dir = base_dir
        ensure_directory_exists(base_dir)
        self.commands = {}  # 벤더별 명령어 저장
        self.load_commands()  # 저장된 명령어 로드
        # 벤더별 명령어 템플릿
        self.vendor_templates = {
            'cisco': {
                'VLAN 관리': {
                    'VLAN 생성': {
                        'template': 'vlan {vlan_id}\n name {vlan_name}',
                        'parameters': ['vlan_id', 'vlan_name']
                    },
                    'VLAN 삭제': {
                        'template': 'no vlan {vlan_id}',
                        'parameters': ['vlan_id']
                    },
                    '인터페이스 VLAN 할당': {
                        'template': 'interface {interface}\n switchport mode access\n switchport access vlan {vlan_id}',
                        'parameters': ['interface', 'vlan_id']
                    }
                },
                '포트 설정': {
                    '포트 활성화': {
                        'template': 'interface {interface}\n no shutdown',
                        'parameters': ['interface']
                    },
                    '포트 속도 설정': {
                        'template': 'interface {interface}\n speed {speed}',
                        'parameters': ['interface', 'speed']
                    }
                }
            },
            'juniper': {
                'VLAN 관리': {
                    'VLAN 생성': {
                        'template': 'set vlans {vlan_name} vlan-id {vlan_id}',
                        'parameters': ['vlan_name', 'vlan_id']
                    },
                    'VLAN 삭제': {
                        'template': 'delete vlans {vlan_name}',
                        'parameters': ['vlan_name']
                    }
                },
                '포트 설정': {
                    '포트 활성화': {
                        'template': 'set interfaces {interface} enable',
                        'parameters': ['interface']
                    }
                }
            },
            'arista': {
                'VLAN 관리': {
                    'VLAN 생성': {
                        'template': 'vlan {vlan_id}\n name {vlan_name}',
                        'parameters': ['vlan_id', 'vlan_name']
                    },
                    'VLAN 삭제': {
                        'template': 'no vlan {vlan_id}',
                        'parameters': ['vlan_id']
                    }
                },
                '포트 설정': {
                    '포트 활성화': {
                        'template': 'interface {interface}\n no shutdown',
                        'parameters': ['interface']
                    }
                }
            }
        }
        # 벤더별 검색 키워드 정의
        self.vendor_search_queries = {
            'cisco': [
                'cisco ios command reference vlan configuration',
                'cisco ios interface configuration commands',
                'cisco switch port configuration guide'
            ],
            'juniper': [
                'juniper junos vlan configuration commands',
                'juniper ex series interface configuration',
                'juniper networks cli command reference'
            ],
            'arista': [
                'arista eos vlan configuration guide',
                'arista switch interface commands',
                'arista networks cli reference'
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
            commands = []
            search_queries = self.vendor_search_queries.get(vendor, [])
            
            for query in search_queries:
                try:
                    # 웹 검색 수행
                    search_results = self._perform_web_search(query)
                    
                    # 검색 결과에서 CLI 명령어 추출
                    for result in search_results:
                        # CLI 명령어 패턴 찾기
                        cli_commands = self._extract_cli_commands(result['snippet'], vendor)
                        
                        for cmd in cli_commands:
                            task_type = self._classify_command_type(cmd, vendor)
                            if task_type:
                                commands.append({
                                    'vendor': vendor,
                                    'task_type': task_type['category'],
                                    'subtask': task_type['subcategory'],
                                    'command': cmd,
                                    'parameters': self._extract_parameters(cmd)
                                })
                
                except Exception as e:
                    logger.error(f"검색 쿼리 '{query}' 처리 중 오류 발생: {str(e)}")
                    continue
            
            return commands
            
        except Exception as e:
            logger.error(f"명령어 검색 중 오류 발생: {str(e)}")
            raise

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
            if vendor not in self.vendor_search_queries:
                raise ValueError(f'지원하지 않는 벤더입니다: {vendor}')
            
            # 웹 검색을 통해 명령어 수집
            collected_commands = self.search_vendor_commands(vendor)
            
            # 수집된 명령어를 데이터베이스에 저장
            learned_commands = []
            for cmd_info in collected_commands:
                # 기존 명령어 조회
                command = CLICommand.query.filter_by(
                    vendor=cmd_info['vendor'],
                    task_type=cmd_info['task_type'],
                    subtask=cmd_info['subtask']
                ).first()
                
                # 명령어가 없으면 새로 생성
                if not command:
                    command = CLICommand(
                        vendor=cmd_info['vendor'],
                        task_type=cmd_info['task_type'],
                        subtask=cmd_info['subtask'],
                        command=cmd_info['command'],
                        parameters=cmd_info['parameters']
                    )
                    db.session.add(command)
                else:
                    # 기존 명령어 업데이트
                    command.command = cmd_info['command']
                    command.parameters = cmd_info['parameters']
                
                learned_commands.append(cmd_info)
            
            db.session.commit()
            
            return {
                'learned_commands': learned_commands
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
                'subtask_type': cmd.subtask,
                'template': cmd.command,
                'parameters': cmd.parameters,
                'last_learned': cmd.updated_at.isoformat()
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

