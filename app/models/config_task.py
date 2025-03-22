from datetime import datetime

class ConfigTask:
    TASK_TYPES = {
        'vlan': {
            'name': 'VLAN 관리',
            'subtasks': {
                'create': 'VLAN 생성',
                'delete': 'VLAN 삭제',
                'interface_assign': 'VLAN 인터페이스 할당',
                'trunk': '트렁크 설정'
            }
        },
        'port': {
            'name': '포트 설정',
            'subtasks': {
                'mode': '액세스/트렁크 모드 설정',
                'speed': '포트 속도/듀플렉스 조정',
                'status': '인터페이스 활성화'
            }
        },
        'routing': {
            'name': '라우팅 설정',
            'subtasks': {
                'static': '정적 라우팅',
                'ospf': 'OSPF 설정',
                'eigrp': 'EIGRP 설정',
                'bgp': 'BGP 설정'
            }
        },
        'security': {
            'name': '보안 설정',
            'subtasks': {
                'port_security': 'Port Security',
                'ssh': 'SSH/Telnet 제한',
                'aaa': 'AAA 인증',
                'acl': 'ACL 설정'
            }
        },
        'stp_lacp': {
            'name': 'STP 및 LACP',
            'subtasks': {
                'stp': 'STP 설정',
                'lacp': 'LACP/포트 채널 구성'
            }
        },
        'qos': {
            'name': 'QoS 및 트래픽 제어',
            'subtasks': {
                'policy': 'QoS 정책 적용',
                'rate_limit': '트래픽 제한',
                'service_policy': '서비스 정책 설정'
            }
        },
        'monitoring': {
            'name': '라우팅 상태 모니터링',
            'subtasks': {
                'route': 'show ip route',
                'ospf': 'show ip ospf neighbor',
                'bgp': 'show ip bgp summary'
            }
        },
        'status': {
            'name': '네트워크 상태 점검',
            'subtasks': {
                'interface': '인터페이스 상태 확인',
                'traffic': '트래픽 모니터링'
            }
        },
        'logging': {
            'name': '로그 수집',
            'subtasks': {
                'show': 'show logging'
            }
        },
        'backup': {
            'name': '구성 백업 및 복원',
            'subtasks': {
                'backup': '설정 백업',
                'restore': '설정 복원',
                'tftp': 'TFTP 복원'
            }
        },
        'snmp': {
            'name': 'SNMP 및 모니터링',
            'subtasks': {
                'setup': 'SNMP 설정',
                'discovery': 'CDP/LLDP 정보 수집'
            }
        },
        'automation': {
            'name': '자동화 스크립트 확장',
            'subtasks': {
                'deploy': '설정 배포',
                'verify': '조건 검증 및 변경'
            }
        }
    }

    def __init__(self, device_id, task_type, subtask, parameters=None):
        self.device_id = device_id
        self.task_type = task_type
        self.subtask = subtask
        self.parameters = parameters or {}
        self.status = 'pending'
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self):
        """객체를 딕셔너리로 변환"""
        return {
            'device_id': self.device_id,
            'task_type': self.task_type,
            'subtask': self.subtask,
            'parameters': self.parameters,
            'status': self.status,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        """딕셔너리에서 객체 생성"""
        task = cls(
            device_id=data['device_id'],
            task_type=data['task_type'],
            subtask=data['subtask'],
            parameters=data.get('parameters')
        )
        task.status = data.get('status', 'pending')
        task.result = data.get('result')
        task.error = data.get('error')
        task.created_at = datetime.fromisoformat(data['created_at'])
        task.updated_at = datetime.fromisoformat(data['updated_at'])
        return task

    @staticmethod
    def get_task_types():
        """작업 유형 목록 반환"""
        return [
            'vlan',
            'port',
            'routing',
            'security',
            'stp_lacp',
            'qos',
            'monitoring',
            'status',
            'logging',
            'backup',
            'snmp',
            'automation'
        ]

    @staticmethod
    def get_subtasks(task_type):
        """작업 유형별 하위 작업 목록 반환"""
        subtasks = {
            'vlan': ['create', 'delete', 'interface_assign', 'trunk'],
            'port': ['mode', 'speed', 'status'],
            'routing': ['static', 'ospf', 'eigrp', 'bgp'],
            'security': ['port_security', 'ssh', 'aaa', 'acl'],
            'stp_lacp': ['stp', 'lacp'],
            'qos': ['policy', 'rate_limit', 'service_policy'],
            'monitoring': ['route', 'ospf', 'bgp'],
            'status': ['interface', 'traffic'],
            'logging': ['show'],
            'backup': ['backup', 'restore', 'tftp'],
            'snmp': ['setup', 'discovery'],
            'automation': ['deploy', 'verify']
        }
        return subtasks.get(task_type, []) 