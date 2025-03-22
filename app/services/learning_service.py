import os
import json
from exceptions import CLILearningError, ValidationError

CLI_LEARNING_FILE = "cli_learning.json"

def perform_cli_learning():
    """理쒖큹 ?ㅽ뻾 ??CLI ?숈뒿???섑뻾?섍퀬 寃곌낵瑜????""
    if os.path.exists(CLI_LEARNING_FILE):
        print("[?? CLI ?숈뒿???대? ?꾨즺?섏뿀?듬땲??")
        return

    print("[?뱼] CLI 紐낅졊???숈뒿???쒖옉?⑸땲??..")

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

        print("[?? CLI ?숈뒿 ?꾨즺! ?숈뒿??紐낅졊???곗씠?곌? ??λ릺?덉뒿?덈떎.")

    except Exception as e:
        raise CLILearningError(f"CLI ?숈뒿 以??ㅻ쪟 諛쒖깮: {str(e)}")

def get_cli_learning_status():
    """CLI ?숈뒿 ?꾨즺 ?щ? ?뺤씤"""
    return os.path.exists(CLI_LEARNING_FILE)

