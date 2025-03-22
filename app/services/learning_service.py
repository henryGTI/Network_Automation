import os
import json
from ..exceptions import CLILearningError, ValidationError
from datetime import datetime
from ..models.cli_command import CLICommand
from ..utils.file_handler import ensure_directory_exists

CLI_LEARNING_FILE = "cli_learning.json"

class LearningService:
    def __init__(self, base_dir='config/cli_learning'):
        self.base_dir = base_dir
        ensure_directory_exists(base_dir)
        self.commands = {}  # 벤더별 명령어 저장
        self.load_commands()  # 저장된 명령어 로드

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

