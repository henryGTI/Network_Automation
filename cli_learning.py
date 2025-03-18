import os
import json
from exceptions import CLILearningError, ValidationError

CLI_LEARNING_FILE = "cli_learning.json"

def perform_cli_learning():
    """최초 실행 시 CLI 학습을 수행하고 결과를 저장"""
    if os.path.exists(CLI_LEARNING_FILE):
        print("[✔] CLI 학습이 이미 완료되었습니다.")
        return

    print("[📢] CLI 명령어 학습을 시작합니다...")

    try:
        cli_knowledge = {
            "cisco": ["vlan 10", "interface GigabitEthernet1/0/1", "ip address 192.168.1.1 255.255.255.0"],
            "juniper": ["set vlans VLAN-10 vlan-id 10", "set interfaces ge-0/0/1 unit 0 family inet address 192.168.1.1/24"],
            "hp": ["vlan 10", "interface 1", "ip address 192.168.1.1/24"],
            "arista": ["vlan 10", "interface Ethernet1", "ip address 192.168.1.1/24"],
            "coreedge": ["create vlan 10 name VLAN_10", "interface 1 set vlan 10"],
            "handreamnet": ["vlan database", "vlan 10", "interface 1 switchport access vlan 10"]
        }

        with open(CLI_LEARNING_FILE, "w") as f:
            json.dump(cli_knowledge, f, indent=4)

        print("[✔] CLI 학습 완료! 학습된 명령어 데이터가 저장되었습니다.")

    except Exception as e:
        raise CLILearningError(f"CLI 학습 중 오류 발생: {str(e)}")

def get_cli_learning_status():
    """CLI 학습 완료 여부 확인"""
    return os.path.exists(CLI_LEARNING_FILE)
