from flask import Blueprint, jsonify, request, current_app, render_template
from ..services.config_service import ConfigService
from app.utils.logger import setup_logger
from app.models.task_type import TaskType
from app.database import db

bp = Blueprint('config', __name__, url_prefix='/config')
config_service = ConfigService()
logger = setup_logger(__name__)

@bp.route('/')
def index():
    """설정 페이지 렌더링"""
    logger.info("설정 페이지 요청")
    return render_template('config/index.html')

@bp.route('/api/task-types', methods=['GET'])
def get_task_types():
    """작업 유형 목록을 조회합니다."""
    try:
        logger.info("작업 유형 목록 조회 요청")
        
        # 강제 초기화 쿼리 파라미터 확인
        force_reset = request.args.get('reset', 'false').lower() == 'true'
        
        # 기존 작업 유형 테이블 초기화 옵션
        if force_reset:
            logger.warning("작업 유형 테이블 강제 초기화 요청")
            TaskType.query.delete()
            db.session.commit()
            logger.info("작업 유형 테이블 초기화 완료")
        
        task_types = TaskType.query.all()
        
        # 작업 유형이 없으면 기본 작업 유형 생성
        if not task_types:
            logger.info("작업 유형 테이블 빈 상태, 기본 작업 유형 생성")
            default_task_types = [
                {"name": "VLAN 관리", "description": "VLAN 생성/삭제, 인터페이스 VLAN 할당, 트렁크 설정", "vendor": "all"},
                {"name": "포트 설정", "description": "액세스/트렁크 모드 설정, 포트 속도/듀플렉스 조정, 인터페이스 활성화", "vendor": "all"},
                {"name": "라우팅 설정", "description": "정적 라우팅, OSPF, EIGRP, BGP 설정 및 관리", "vendor": "all"},
                {"name": "보안 설정", "description": "Port Security, SSH/Telnet 제한, AAA 인증, ACL 설정", "vendor": "all"},
                {"name": "STP 및 LACP", "description": "STP(RSTP/PVST) 설정, LACP/포트 채널 구성", "vendor": "all"},
                {"name": "QoS 및 트래픽 제어", "description": "QoS 정책 적용, 트래픽 제한, 서비스 정책 설정", "vendor": "all"},
                {"name": "라우팅 상태 모니터링", "description": "라우팅 테이블, OSPF 이웃, BGP 요약 정보 확인", "vendor": "all"},
                {"name": "네트워크 상태 점검", "description": "인터페이스 상태 확인, 트래픽 모니터링", "vendor": "all"},
                {"name": "로그 수집", "description": "로깅 명령 실행 후 파일 저장", "vendor": "all"},
                {"name": "구성 백업 및 복원", "description": "Running-config/Startup-config 백업 및 복원, TFTP 설정", "vendor": "all"},
                {"name": "SNMP 및 모니터링", "description": "SNMP 설정, CDP/LLDP 정보 수집", "vendor": "all"},
                {"name": "자동화 스크립트 확장", "description": "여러 장비에 설정 배포, 특정 조건 검증 후 자동 변경 적용", "vendor": "all"}
            ]
            
            for task_type_data in default_task_types:
                task_type = TaskType(
                    name=task_type_data["name"],
                    description=task_type_data["description"],
                    vendor=task_type_data["vendor"]
                )
                db.session.add(task_type)
            
            db.session.commit()
            logger.info("기본 작업 유형 생성 완료")
            task_types = TaskType.query.all()
        
        # 응답 데이터 형식 결정 (task_type 객체를 dict로 변환 또는 이름만 추출)
        format_type = request.args.get('format', 'full')
        if format_type == 'names_only':
            response_data = [task_type.name for task_type in task_types]
        else:
            response_data = [task_type.to_dict() for task_type in task_types]
            
        logger.info(f"작업 유형 목록 조회 완료: {len(response_data)}개 작업 유형 반환")
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"작업 유형 목록 조회 실패: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/api/task-types', methods=['POST'])
def add_task_type():
    """새 작업 유형을 추가합니다."""
    try:
        logger.info("작업 유형 추가 요청")
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['name', 'description', 'vendor']
        for field in required_fields:
            if field not in data:
                logger.warning(f"필수 필드 누락: {field}")
                return jsonify({'status': 'error', 'message': f'{field} 필드가 필요합니다.'}), 400
        
        # 중복 작업 유형 검사
        if TaskType.query.filter_by(name=data['name'], vendor=data['vendor']).first():
            logger.warning(f"중복된 작업 유형: {data['name']} ({data['vendor']})")
            return jsonify({'status': 'error', 'message': '이미 등록된 작업 유형입니다.'}), 400
        
        task_type = TaskType(
            name=data['name'],
            description=data['description'],
            vendor=data['vendor']
        )
        
        db.session.add(task_type)
        db.session.commit()
        
        logger.info(f"작업 유형 추가 성공: {task_type.name}")
        return jsonify({
            'status': 'success',
            'message': '작업 유형이 추가되었습니다.',
            'task_type': task_type.to_dict()
        })
    except Exception as e:
        logger.error(f"작업 유형 추가 실패: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/api/task-types/<int:task_type_id>', methods=['DELETE'])
def delete_task_type(task_type_id):
    """작업 유형을 삭제합니다."""
    try:
        logger.info(f"작업 유형 삭제 요청: {task_type_id}")
        task_type = TaskType.query.get_or_404(task_type_id)
        
        db.session.delete(task_type)
        db.session.commit()
        
        logger.info(f"작업 유형 삭제 성공: {task_type.name}")
        return jsonify({
            'status': 'success',
            'message': '작업 유형이 삭제되었습니다.'
        })
    except Exception as e:
        logger.error(f"작업 유형 삭제 실패: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/api/subtasks/<task_type>', methods=['GET'])
def get_subtasks(task_type):
    """특정 작업 유형에 해당하는 상세 작업 목록을 반환합니다."""
    try:
        subtasks = {
            'VLAN 관리': [
                'VLAN 생성',
                'VLAN 삭제',
                '인터페이스 VLAN 할당',
                '트렁크 설정'
            ],
            '포트 설정': [
                '액세스 모드 설정',
                '트렁크 모드 설정',
                '포트 속도 설정',
                '포트 듀플렉스 설정',
                '인터페이스 활성화'
            ],
            '라우팅 설정': [
                '정적 라우팅 설정',
                'OSPF 설정',
                'EIGRP 설정',
                'BGP 설정'
            ],
            '보안 설정': [
                'Port Security 설정',
                'SSH/Telnet 접근 제한',
                'AAA 인증 설정',
                'ACL 설정'
            ],
            'STP 및 LACP': [
                'STP 모드 설정',
                'STP 우선순위 설정',
                'LACP 채널 구성',
                '포트 채널 설정'
            ],
            'QoS 및 트래픽 제어': [
                'QoS 정책 적용',
                '트래픽 제한 설정',
                '서비스 정책 설정'
            ],
            '라우팅 상태 모니터링': [
                '라우팅 테이블 확인',
                'OSPF 이웃 정보 확인',
                'BGP 요약 정보 확인'
            ],
            '네트워크 상태 점검': [
                '인터페이스 상태 확인',
                '트래픽 모니터링'
            ],
            '로그 수집': [
                '시스템 로그 수집',
                '로그 파일 저장'
            ],
            '구성 백업 및 복원': [
                'Running-config 백업',
                'Startup-config 백업',
                '설정 복원',
                'TFTP 백업 설정'
            ],
            'SNMP 및 모니터링': [
                'SNMP 서버 설정',
                'SNMP 커뮤니티 설정',
                'CDP 정보 수집',
                'LLDP 정보 수집'
            ],
            '자동화 스크립트 확장': [
                '다중 장비 설정 배포',
                '조건별 설정 변경',
                '자동화 스크립트 실행'
            ]
        }
        
        logger.info(f"상세 작업 목록 조회 요청: {task_type}")
        
        if task_type not in subtasks:
            logger.warning(f"잘못된 작업 유형: {task_type}")
            return jsonify({'error': '잘못된 작업 유형입니다'}), 400
            
        return jsonify(subtasks[task_type])
    except Exception as e:
        logger.error(f'상세 작업 목록 조회 중 오류 발생: {str(e)}')
        return jsonify({'error': '상세 작업 목록을 불러오는데 실패했습니다'}), 500

@bp.route('/api/parameters/<task_type>/<subtask>', methods=['GET'])
def get_parameters(task_type, subtask):
    """특정 작업에 필요한 파라미터 목록을 반환합니다."""
    try:
        parameters = {
            'VLAN 관리': {
                'VLAN 생성': [
                    {'name': 'vlan_id', 'type': 'number', 'label': 'VLAN ID', 'required': True, 'min': 1, 'max': 4094},
                    {'name': 'vlan_name', 'type': 'text', 'label': 'VLAN 이름', 'required': True}
                ],
                'VLAN 삭제': [
                    {'name': 'vlan_id', 'type': 'number', 'label': 'VLAN ID', 'required': True, 'min': 1, 'max': 4094}
                ],
                '인터페이스 VLAN 할당': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                    {'name': 'vlan_id', 'type': 'number', 'label': 'VLAN ID', 'required': True, 'min': 1, 'max': 4094}
                ],
                '트렁크 설정': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                    {'name': 'allowed_vlans', 'type': 'text', 'label': '허용 VLAN', 'required': True, 'placeholder': '예: 1-10,20,30-40'}
                ]
            },
            '포트 설정': {
                '액세스 모드 설정': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                    {'name': 'vlan_id', 'type': 'number', 'label': 'VLAN ID', 'required': True, 'min': 1, 'max': 4094}
                ],
                '트렁크 모드 설정': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                    {'name': 'native_vlan', 'type': 'number', 'label': '네이티브 VLAN', 'required': True, 'min': 1, 'max': 4094}
                ],
                '포트 속도 설정': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                    {'name': 'speed', 'type': 'select', 'label': '속도', 'required': True, 'options': [
                        {'value': 'auto', 'label': '자동'},
                        {'value': '10', 'label': '10 Mbps'},
                        {'value': '100', 'label': '100 Mbps'},
                        {'value': '1000', 'label': '1 Gbps'}
                    ]}
                ],
                '포트 듀플렉스 설정': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                    {'name': 'duplex', 'type': 'select', 'label': '듀플렉스 모드', 'required': True, 'options': [
                        {'value': 'auto', 'label': '자동'},
                        {'value': 'full', 'label': '전이중(Full)'},
                        {'value': 'half', 'label': '반이중(Half)'}
                    ]}
                ],
                '인터페이스 활성화': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                    {'name': 'status', 'type': 'select', 'label': '상태', 'required': True, 'options': [
                        {'value': 'no shutdown', 'label': '활성화'},
                        {'value': 'shutdown', 'label': '비활성화'}
                    ]}
                ]
            },
            '라우팅 설정': {
                '정적 라우팅 설정': [
                    {'name': 'network_address', 'type': 'text', 'label': '대상 네트워크', 'required': True, 'placeholder': '예: 192.168.2.0'},
                    {'name': 'subnet_mask', 'type': 'text', 'label': '서브넷 마스크', 'required': True, 'placeholder': '예: 255.255.255.0'},
                    {'name': 'next_hop', 'type': 'text', 'label': '다음 홉 주소', 'required': True, 'placeholder': '예: 10.0.0.1'}
                ],
                'OSPF 설정': [
                    {'name': 'process_id', 'type': 'number', 'label': '프로세스 ID', 'required': True, 'min': 1, 'max': 65535},
                    {'name': 'network_address', 'type': 'text', 'label': '네트워크 주소', 'required': True, 'placeholder': '예: 192.168.1.0'},
                    {'name': 'wildcard_mask', 'type': 'text', 'label': '와일드카드 마스크', 'required': True, 'placeholder': '예: 0.0.0.255'},
                    {'name': 'area_id', 'type': 'number', 'label': '에리어 ID', 'required': True, 'min': 0}
                ],
                'EIGRP 설정': [
                    {'name': 'as_number', 'type': 'number', 'label': 'AS 번호', 'required': True, 'min': 1, 'max': 65535},
                    {'name': 'network_address', 'type': 'text', 'label': '네트워크 주소', 'required': True, 'placeholder': '예: 192.168.1.0'},
                    {'name': 'wildcard_mask', 'type': 'text', 'label': '와일드카드 마스크', 'required': True, 'placeholder': '예: 0.0.0.255'}
                ],
                'BGP 설정': [
                    {'name': 'as_number', 'type': 'number', 'label': 'AS 번호', 'required': True, 'min': 1, 'max': 65535},
                    {'name': 'neighbor_ip', 'type': 'text', 'label': '이웃 라우터 IP', 'required': True, 'placeholder': '예: 192.168.1.2'},
                    {'name': 'remote_as', 'type': 'number', 'label': '원격 AS 번호', 'required': True, 'min': 1, 'max': 65535}
                ]
            },
            '보안 설정': {
                'Port Security 설정': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                    {'name': 'max_mac', 'type': 'number', 'label': '최대 MAC 주소 수', 'required': True, 'min': 1, 'max': 8192},
                    {'name': 'violation', 'type': 'select', 'label': '위반 모드', 'required': True, 'options': [
                        {'value': 'protect', 'label': 'Protect'},
                        {'value': 'restrict', 'label': 'Restrict'},
                        {'value': 'shutdown', 'label': 'Shutdown'}
                    ]}
                ],
                'SSH/Telnet 접근 제한': [
                    {'name': 'access_type', 'type': 'select', 'label': '접근 유형', 'required': True, 'options': [
                        {'value': 'ssh', 'label': 'SSH'},
                        {'value': 'telnet', 'label': 'Telnet'},
                        {'value': 'both', 'label': 'SSH 및 Telnet'}
                    ]},
                    {'name': 'acl_number', 'type': 'number', 'label': 'ACL 번호', 'required': True, 'min': 1, 'max': 99}
                ],
                'AAA 인증 설정': [
                    {'name': 'auth_type', 'type': 'select', 'label': '인증 유형', 'required': True, 'options': [
                        {'value': 'local', 'label': '로컬 인증'},
                        {'value': 'tacacs', 'label': 'TACACS+'},
                        {'value': 'radius', 'label': 'RADIUS'}
                    ]},
                    {'name': 'server_ip', 'type': 'text', 'label': '서버 IP', 'required': False, 'placeholder': '예: 10.1.1.1'}
                ],
                'ACL 설정': [
                    {'name': 'acl_type', 'type': 'select', 'label': 'ACL 유형', 'required': True, 'options': [
                        {'value': 'standard', 'label': '표준(Standard)'},
                        {'value': 'extended', 'label': '확장(Extended)'}
                    ]},
                    {'name': 'acl_number', 'type': 'number', 'label': 'ACL 번호', 'required': True, 'min': 1, 'max': 199},
                    {'name': 'action', 'type': 'select', 'label': '작업', 'required': True, 'options': [
                        {'value': 'permit', 'label': '허용(permit)'},
                        {'value': 'deny', 'label': '거부(deny)'}
                    ]},
                    {'name': 'source_ip', 'type': 'text', 'label': '소스 IP', 'required': True, 'placeholder': '예: 192.168.1.0'},
                    {'name': 'source_wildcard', 'type': 'text', 'label': '소스 와일드카드', 'required': True, 'placeholder': '예: 0.0.0.255'}
                ]
            },
            'STP 및 LACP': {
                'STP 모드 설정': [
                    {'name': 'stp_mode', 'type': 'select', 'label': 'STP 모드', 'required': True, 'options': [
                        {'value': 'stp', 'label': 'STP'},
                        {'value': 'rapid-pvst', 'label': 'Rapid PVST+'},
                        {'value': 'mst', 'label': 'MST'}
                    ]}
                ],
                'STP 우선순위 설정': [
                    {'name': 'vlan_id', 'type': 'number', 'label': 'VLAN ID', 'required': True, 'min': 1, 'max': 4094},
                    {'name': 'priority', 'type': 'select', 'label': '우선순위', 'required': True, 'options': [
                        {'value': '0', 'label': '0 (최상위)'},
                        {'value': '4096', 'label': '4096'},
                        {'value': '8192', 'label': '8192'},
                        {'value': '16384', 'label': '16384 (기본값)'},
                        {'value': '32768', 'label': '32768'},
                        {'value': '49152', 'label': '49152'}
                    ]}
                ],
                'LACP 채널 구성': [
                    {'name': 'channel_group', 'type': 'number', 'label': '채널 그룹', 'required': True, 'min': 1, 'max': 128},
                    {'name': 'interfaces', 'type': 'text', 'label': '인터페이스 목록', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1,GigabitEthernet1/0/2'}
                ],
                '포트 채널 설정': [
                    {'name': 'channel_group', 'type': 'number', 'label': '채널 그룹', 'required': True, 'min': 1, 'max': 128},
                    {'name': 'mode', 'type': 'select', 'label': '모드', 'required': True, 'options': [
                        {'value': 'on', 'label': 'On (PAgP/LACP 없음)'},
                        {'value': 'active', 'label': 'Active (LACP)'},
                        {'value': 'passive', 'label': 'Passive (LACP)'},
                        {'value': 'auto', 'label': 'Auto (PAgP)'},
                        {'value': 'desirable', 'label': 'Desirable (PAgP)'}
                    ]}
                ]
            },
            'QoS 및 트래픽 제어': {
                'QoS 정책 적용': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                    {'name': 'policy_name', 'type': 'text', 'label': '정책 이름', 'required': True},
                    {'name': 'direction', 'type': 'select', 'label': '방향', 'required': True, 'options': [
                        {'value': 'input', 'label': '인바운드(input)'},
                        {'value': 'output', 'label': '아웃바운드(output)'}
                    ]}
                ],
                '트래픽 제한 설정': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                    {'name': 'rate_limit', 'type': 'number', 'label': '제한 속도(kbps)', 'required': True, 'min': 8, 'max': 1000000},
                    {'name': 'burst', 'type': 'number', 'label': '버스트 크기(bytes)', 'required': True, 'min': 1000, 'max': 512000000}
                ],
                '서비스 정책 설정': [
                    {'name': 'policy_name', 'type': 'text', 'label': '정책 이름', 'required': True},
                    {'name': 'class_name', 'type': 'text', 'label': '클래스 이름', 'required': True},
                    {'name': 'action', 'type': 'select', 'label': '작업', 'required': True, 'options': [
                        {'value': 'bandwidth', 'label': '대역폭 할당'},
                        {'value': 'priority', 'label': '우선순위 큐'},
                        {'value': 'shape', 'label': '트래픽 쉐이핑'},
                        {'value': 'police', 'label': '트래픽 폴리싱'}
                    ]},
                    {'name': 'value', 'type': 'number', 'label': '값(kbps)', 'required': True, 'min': 8, 'max': 1000000}
                ]
            },
            '라우팅 상태 모니터링': {
                '라우팅 테이블 확인': [],
                'OSPF 이웃 정보 확인': [
                    {'name': 'process_id', 'type': 'number', 'label': '프로세스 ID', 'required': False, 'min': 1, 'max': 65535}
                ],
                'BGP 요약 정보 확인': [
                    {'name': 'as_number', 'type': 'number', 'label': 'AS 번호', 'required': False, 'min': 1, 'max': 65535}
                ]
            },
            '네트워크 상태 점검': {
                '인터페이스 상태 확인': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': False, 'placeholder': '예: GigabitEthernet1/0/1'}
                ],
                '트래픽 모니터링': [
                    {'name': 'interface_name', 'type': 'text', 'label': '인터페이스', 'required': False, 'placeholder': '예: GigabitEthernet1/0/1'}
                ]
            },
            '로그 수집': {
                '시스템 로그 수집': [
                    {'name': 'severity', 'type': 'select', 'label': '심각도', 'required': False, 'options': [
                        {'value': 'all', 'label': '모든 로그'},
                        {'value': 'errors', 'label': '오류 로그만'},
                        {'value': 'warnings', 'label': '경고 이상 로그'}
                    ]}
                ],
                '로그 파일 저장': [
                    {'name': 'filename', 'type': 'text', 'label': '파일명', 'required': True, 'placeholder': '예: device_logs_20230323'},
                    {'name': 'format', 'type': 'select', 'label': '형식', 'required': True, 'options': [
                        {'value': 'txt', 'label': '텍스트 파일(TXT)'},
                        {'value': 'csv', 'label': 'CSV 파일'},
                        {'value': 'json', 'label': 'JSON 파일'}
                    ]}
                ]
            },
            '구성 백업 및 복원': {
                'Running-config 백업': [
                    {'name': 'backup_location', 'type': 'select', 'label': '백업 위치', 'required': True, 'options': [
                        {'value': 'local', 'label': '로컬 저장'},
                        {'value': 'tftp', 'label': 'TFTP 서버'}
                    ]},
                    {'name': 'filename', 'type': 'text', 'label': '파일명', 'required': True, 'placeholder': '예: running_config_backup'}
                ],
                'Startup-config 백업': [
                    {'name': 'backup_location', 'type': 'select', 'label': '백업 위치', 'required': True, 'options': [
                        {'value': 'local', 'label': '로컬 저장'},
                        {'value': 'tftp', 'label': 'TFTP 서버'}
                    ]},
                    {'name': 'filename', 'type': 'text', 'label': '파일명', 'required': True, 'placeholder': '예: startup_config_backup'}
                ],
                '설정 복원': [
                    {'name': 'restore_location', 'type': 'select', 'label': '복원 위치', 'required': True, 'options': [
                        {'value': 'local', 'label': '로컬 파일'},
                        {'value': 'tftp', 'label': 'TFTP 서버'}
                    ]},
                    {'name': 'filename', 'type': 'text', 'label': '파일명', 'required': True, 'placeholder': '예: config_backup.cfg'},
                    {'name': 'config_type', 'type': 'select', 'label': '복원할 설정 유형', 'required': True, 'options': [
                        {'value': 'running-config', 'label': 'Running-config'},
                        {'value': 'startup-config', 'label': 'Startup-config'}
                    ]}
                ],
                'TFTP 백업 설정': [
                    {'name': 'tftp_server', 'type': 'text', 'label': 'TFTP 서버 주소', 'required': True, 'placeholder': '예: 192.168.1.100'},
                    {'name': 'filename', 'type': 'text', 'label': '파일명', 'required': True, 'placeholder': '예: running-config'}
                ]
            },
            'SNMP 및 모니터링': {
                'SNMP 서버 설정': [
                    {'name': 'server_ip', 'type': 'text', 'label': 'SNMP 서버 IP', 'required': True, 'placeholder': '예: 192.168.1.100'},
                    {'name': 'version', 'type': 'select', 'label': 'SNMP 버전', 'required': True, 'options': [
                        {'value': '1', 'label': 'SNMPv1'},
                        {'value': '2c', 'label': 'SNMPv2c'},
                        {'value': '3', 'label': 'SNMPv3'}
                    ]}
                ],
                'SNMP 커뮤니티 설정': [
                    {'name': 'community_string', 'type': 'text', 'label': '커뮤니티 문자열', 'required': True},
                    {'name': 'access_type', 'type': 'select', 'label': '접근 권한', 'required': True, 'options': [
                        {'value': 'ro', 'label': '읽기 전용(RO)'},
                        {'value': 'rw', 'label': '읽기/쓰기(RW)'}
                    ]}
                ],
                'CDP 정보 수집': [
                    {'name': 'detail', 'type': 'select', 'label': '상세 정보', 'required': False, 'options': [
                        {'value': 'basic', 'label': '기본 정보'},
                        {'value': 'detail', 'label': '상세 정보'}
                    ]}
                ],
                'LLDP 정보 수집': [
                    {'name': 'detail', 'type': 'select', 'label': '상세 정보', 'required': False, 'options': [
                        {'value': 'basic', 'label': '기본 정보'},
                        {'value': 'detail', 'label': '상세 정보'}
                    ]}
                ]
            },
            '자동화 스크립트 확장': {
                '다중 장비 설정 배포': [
                    {'name': 'device_list', 'type': 'text', 'label': '장비 목록(쉼표로 구분)', 'required': True, 'placeholder': '예: 1,2,3'},
                    {'name': 'config_file', 'type': 'text', 'label': '설정 파일명', 'required': True}
                ],
                '조건별 설정 변경': [
                    {'name': 'condition_type', 'type': 'select', 'label': '조건 유형', 'required': True, 'options': [
                        {'value': 'interface_status', 'label': '인터페이스 상태'},
                        {'value': 'cpu_usage', 'label': 'CPU 사용률'},
                        {'value': 'memory_usage', 'label': '메모리 사용률'}
                    ]},
                    {'name': 'threshold', 'type': 'number', 'label': '임계값', 'required': True, 'min': 0, 'max': 100},
                    {'name': 'action_script', 'type': 'text', 'label': '실행 스크립트', 'required': True}
                ],
                '자동화 스크립트 실행': [
                    {'name': 'script_name', 'type': 'text', 'label': '스크립트 이름', 'required': True},
                    {'name': 'schedule', 'type': 'select', 'label': '실행 일정', 'required': True, 'options': [
                        {'value': 'now', 'label': '즉시 실행'},
                        {'value': 'hourly', 'label': '매시간'},
                        {'value': 'daily', 'label': '매일'},
                        {'value': 'weekly', 'label': '매주'}
                    ]}
                ]
            }
        }
        
        logger.info(f"파라미터 목록 조회 요청: {task_type}/{subtask}")
        
        if task_type not in parameters or subtask not in parameters[task_type]:
            logger.warning(f"잘못된 작업 유형 또는 상세 작업: {task_type}/{subtask}")
            return jsonify({'error': '잘못된 작업 유형 또는 상세 작업입니다'}), 400
            
        return jsonify(parameters[task_type][subtask])
    except Exception as e:
        logger.error(f'파라미터 목록 조회 중 오류 발생: {str(e)}')
        return jsonify({'error': '파라미터 목록을 불러오는데 실패했습니다'}), 500

@bp.route('/api/tasks', methods=['GET'])
def get_tasks():
    """작업 목록 조회"""
    device_id = request.args.get('device_id')
    tasks = config_service.get_tasks(device_id)
    
    if device_id:
        return jsonify({
            'status': 'success',
            'data': [task.to_dict() for task in tasks]
        })
    
    return jsonify({
        'status': 'success',
        'data': {
            device_id: [task.to_dict() for task in device_tasks]
            for device_id, device_tasks in tasks.items()
        }
    })

@bp.route('/api/tasks', methods=['POST'])
def add_task():
    """새로운 작업 추가"""
    data = request.get_json()
    
    required_fields = ['device_id', 'task_type', 'subtask']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'status': 'error',
                'message': f'필수 필드가 누락되었습니다: {field}'
            }), 400
    
    task = config_service.add_task(
        device_id=data['device_id'],
        task_type=data['task_type'],
        subtask=data['subtask'],
        parameters=data.get('parameters')
    )
    
    return jsonify({
        'status': 'success',
        'message': '작업이 추가되었습니다.',
        'data': task.to_dict()
    }), 201

@bp.route('/api/tasks/<device_id>/<int:task_index>', methods=['PUT'])
def update_task_status(device_id, task_index):
    """작업 상태 업데이트"""
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({
            'status': 'error',
            'message': '상태 정보가 누락되었습니다.'
        }), 400
    
    success = config_service.update_task_status(
        device_id=device_id,
        task_index=task_index,
        status=data['status'],
        result=data.get('result'),
        error=data.get('error')
    )
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': '작업을 찾을 수 없습니다.'
        }), 404
    
    return jsonify({
        'status': 'success',
        'message': '작업 상태가 업데이트되었습니다.'
    })

@bp.route('/api/tasks/<device_id>/<int:task_index>', methods=['DELETE'])
def delete_task(device_id, task_index):
    """작업 삭제"""
    success = config_service.delete_task(device_id, task_index)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': '작업을 찾을 수 없습니다.'
        }), 404
    
    return jsonify({
        'status': 'success',
        'message': '작업이 삭제되었습니다.'
    })

@bp.route('/api/tasks/<device_id>', methods=['DELETE'])
def clear_tasks(device_id):
    """장비의 모든 작업 삭제"""
    success = config_service.clear_tasks(device_id)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': '장비를 찾을 수 없습니다.'
        }), 404
    
    return jsonify({
        'status': 'success',
        'message': '모든 작업이 삭제되었습니다.'
    })

@bp.route('/api/generate-script', methods=['POST'])
def generate_script():
    """스크립트 생성"""
    try:
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['device_id', 'task_types', 'subtask_type', 'vendor', 'parameters']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'필수 필드가 누락되었습니다: {field}'
                }), 400
        
        # 스크립트 생성
        script = config_service.generate_script(
            device_id=data['device_id'],
            task_types=data['task_types'],
            subtask_type=data['subtask_type'],
            vendor=data['vendor'],
            parameters=data['parameters']
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'script': script
            }
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"스크립트 생성 중 오류: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"스크립트 생성 실패: {str(e)}"
        }), 500

@bp.route('/api/execute-script', methods=['POST'])
def execute_script():
    """스크립트 실행"""
    try:
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['device_id', 'script']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'필수 필드가 누락되었습니다: {field}'
                }), 400
        
        # 스크립트 실행
        result = config_service.execute_script(
            device_id=data['device_id'],
            script=data['script']
        )
        
        return jsonify({
            'status': 'success',
            'result': result
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"스크립트 실행 중 오류: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"스크립트 실행 실패: {str(e)}"
        }), 500

@bp.route('/api/reset-task-types', methods=['GET'])
def reset_task_types():
    """작업 유형 테이블을 초기화합니다."""
    try:
        logger.warning("작업 유형 테이블 강제 초기화 요청")
        
        # 기존 작업 유형 삭제
        TaskType.query.delete()
        db.session.commit()
        
        # 기본 작업 유형 생성
        default_task_types = [
            {"name": "VLAN 관리", "description": "VLAN 생성/삭제, 인터페이스 VLAN 할당, 트렁크 설정", "vendor": "all"},
            {"name": "포트 설정", "description": "액세스/트렁크 모드 설정, 포트 속도/듀플렉스 조정, 인터페이스 활성화", "vendor": "all"},
            {"name": "라우팅 설정", "description": "정적 라우팅, OSPF, EIGRP, BGP 설정 및 관리", "vendor": "all"},
            {"name": "보안 설정", "description": "Port Security, SSH/Telnet 제한, AAA 인증, ACL 설정", "vendor": "all"},
            {"name": "STP 및 LACP", "description": "STP(RSTP/PVST) 설정, LACP/포트 채널 구성", "vendor": "all"},
            {"name": "QoS 및 트래픽 제어", "description": "QoS 정책 적용, 트래픽 제한, 서비스 정책 설정", "vendor": "all"},
            {"name": "라우팅 상태 모니터링", "description": "라우팅 테이블, OSPF 이웃, BGP 요약 정보 확인", "vendor": "all"},
            {"name": "네트워크 상태 점검", "description": "인터페이스 상태 확인, 트래픽 모니터링", "vendor": "all"},
            {"name": "로그 수집", "description": "로깅 명령 실행 후 파일 저장", "vendor": "all"},
            {"name": "구성 백업 및 복원", "description": "Running-config/Startup-config 백업 및 복원, TFTP 설정", "vendor": "all"},
            {"name": "SNMP 및 모니터링", "description": "SNMP 설정, CDP/LLDP 정보 수집", "vendor": "all"},
            {"name": "자동화 스크립트 확장", "description": "여러 장비에 설정 배포, 특정 조건 검증 후 자동 변경 적용", "vendor": "all"}
        ]
        
        for task_type_data in default_task_types:
            task_type = TaskType(
                name=task_type_data["name"],
                description=task_type_data["description"],
                vendor=task_type_data["vendor"]
            )
            db.session.add(task_type)
        
        db.session.commit()
        logger.info("작업 유형 테이블 초기화 완료")
        
        return jsonify({
            'status': 'success',
            'message': '작업 유형 테이블이 초기화되었습니다.',
            'count': len(default_task_types)
        })
    except Exception as e:
        logger.error(f"작업 유형 테이블 초기화 실패: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 