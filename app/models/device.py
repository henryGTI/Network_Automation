from app.database import db
from datetime import datetime

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(15), nullable=False)
    vendor = db.Column(db.String(50), nullable=False)
    device_type = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='offline')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ip_address': self.ip_address,
            'vendor': self.vendor,
            'device_type': self.device_type,
            'username': self.username,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
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
