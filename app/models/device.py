class Device:
    def __init__(self, name, vendor, ip, model, id=None):
        self.id = id
        self.name = name
        self.validate_vendor_and_model(vendor, model)
        self.vendor = vendor
        self.ip = ip
        self.model = model

    def validate_vendor_and_model(self, vendor, model):
        vendor_lower = vendor.lower()
        if vendor_lower not in VENDOR_LIST:
            valid_vendors = ', '.join(VENDOR_LIST.keys())
            raise ValueError(f"지원하지 않는 벤더입니다. 지원되는 벤더: {valid_vendors}")
        
        vendor_info = VENDOR_LIST[vendor_lower]
        if model not in vendor_info['models']:
            valid_models = ', '.join(vendor_info['models'])
            raise ValueError(f"지원하지 않는 모델입니다. {vendor}의 지원 모델: {valid_models}")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'vendor': self.vendor,
            'ip': self.ip,
            'model': self.model
        } 

VENDOR_TEMPLATES = {
    'cisco': {
        'vlan_config': {
            'name': 'VLAN 생성/삭제',
            'patterns': [
                r'vlan (\d+)',
                r'name (.+)'
            ],
            'show_commands': [
                'show vlan brief',
                'show running-config | include vlan'
            ],
            'template': [
                'configure terminal',
                'vlan {vlan_id}',
                'name {vlan_name}',
                'exit'
            ]
        },
        # ... 다른 Cisco 설정들
    },
    
    'juniper': {
        'vlan_config': {
            'name': 'VLAN 생성/삭제',
            'patterns': [
                r'set vlans (\w+) vlan-id (\d+)',
                r'set vlans (\w+) description (.+)'
            ],
            'show_commands': [
                'show vlans',
                'show configuration vlans'
            ],
            'template': [
                'edit',
                'set vlans {vlan_name} vlan-id {vlan_id}',
                'set vlans {vlan_name} description {description}',
                'commit'
            ]
        },
        # ... 다른 Juniper 설정들
    },

    'hp': {
        'vlan_config': {
            'name': 'VLAN 생성/삭제',
            'patterns': [
                r'vlan (\d+)',
                r'name (.+)'
            ],
            'show_commands': [
                'show vlan',
                'show running-config vlan'
            ],
            'template': [
                'configure',
                'vlan {vlan_id}',
                'name {vlan_name}',
                'exit'
            ]
        },
        # ... 다른 HP 설정들
    },

    'arista': {
        'vlan_config': {
            'name': 'VLAN 생성/삭제',
            'patterns': [
                r'vlan (\d+)',
                r'name (.+)'
            ],
            'show_commands': [
                'show vlan',
                'show running-config section vlan'
            ],
            'template': [
                'configure',
                'vlan {vlan_id}',
                'name {vlan_name}',
                'exit'
            ]
        },
        # ... 다른 Arista 설정들
    },

    'handreamnet': {
        'vlan_config': {
            'name': 'VLAN 생성/삭제',
            'patterns': [
                r'vlan (\d+)',
                r'name (.+)'
            ],
            'show_commands': [
                'show vlan',
                'show running-config | include vlan'
            ],
            'template': [
                'configure terminal',
                'vlan {vlan_id}',
                'name {vlan_name}',
                'exit'
            ]
        },
        # ... 다른 Handreamnet 설정들
    },

    'coreedgenetworks': {
        'vlan_config': {
            'name': 'VLAN 생성/삭제',
            'patterns': [
                r'vlan (\d+)',
                r'name (.+)'
            ],
            'show_commands': [
                'show vlan',
                'show running-config | include vlan'
            ],
            'template': [
                'configure terminal',
                'vlan {vlan_id}',
                'name {vlan_name}',
                'exit'
            ]
        },
        # ... 다른 CoreEdge Networks 설정들
    }
}

# 벤더 리스트 정규화
VENDOR_LIST = {
    'cisco': {
        'name': 'Cisco',
        'models': ['IOS', 'IOS-XE', 'NX-OS'],
        'default_protocol': 'ssh'
    },
    'juniper': {
        'name': 'Juniper',
        'models': ['JunOS'],
        'default_protocol': 'ssh'
    },
    'hp': {
        'name': 'HP',
        'models': ['ProCurve', 'Aruba'],
        'default_protocol': 'ssh'
    },
    'arista': {
        'name': 'Arista',
        'models': ['EOS'],
        'default_protocol': 'ssh'
    },
    'handreamnet': {
        'name': 'Handream Networks',
        'models': ['HOS'],
        'default_protocol': 'ssh'
    },
    'coreedgenetworks': {
        'name': 'CoreEdge Networks',
        'models': ['CEN-OS'],
        'default_protocol': 'ssh'
    }
} 
