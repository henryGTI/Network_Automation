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
    """특정 작업 유형에 대한 하위 작업 목록을 반환합니다."""
    try:
        logger.info(f"subtasks API 호출(원본): {task_type} (타입: {type(task_type)})")
        
        # URL 인코딩 문제 처리
        if not task_type or task_type.strip() == '':
            logger.error("작업 유형이 비어 있습니다.")
            return jsonify({"error": "작업 유형이 지정되지 않았습니다."}), 400
        
        # 이전 작업 유형 이름을 새 이름으로 매핑
        task_type_mapping = {
            'VLAN 관리': 'VLAN 생성/삭제',
            '포트 설정': '인터페이스 설정',
            '인터페이스 구성': '인터페이스 설정',
            '보안 설정': 'ACL 설정',
            'STP 및 LACP': 'VLAN 인터페이스 설정',
            'QoS 및 트래픽 제어': '라우팅 설정',
            '라우팅 상태 모니터링': '라우팅 설정',
            '네트워크 상태 점검': 'IP 주소 설정',
            '로그 수집': 'SNMP 설정',
            '구성 백업 및 복원': 'NTP 설정',
            'SNMP 및 모니터링': 'SNMP 설정',
            '자동화 스크립트 확장': 'NTP 설정'
        }

        # 작업 유형 이름 매핑 적용
        mapped_task_type = task_type_mapping.get(task_type, task_type)
        logger.info(f"매핑된 작업 유형: {mapped_task_type}")
        
        # 기본 빈 배열로 초기화
        subtasks = []
        
        logger.info(f"작업 유형 매칭 시작: {mapped_task_type}")
        
        if mapped_task_type == 'VLAN 생성/삭제' or mapped_task_type == 'VLAN 관리':
            logger.info("VLAN 생성/삭제 작업에 대한 상세 작업 반환")
            subtasks = [
                {
                    'name': 'VLAN 생성',
                    'description': 'VLAN을 생성합니다',
                    'task_type': mapped_task_type,
                    'vendor': 'all',
                    'parameters': [
                        {'name': 'vlan_id', 'type': 'text', 'label': 'VLAN ID', 'required': True, 'placeholder': '예: 10'},
                        {'name': 'vlan_name', 'type': 'text', 'label': 'VLAN 이름', 'required': True, 'placeholder': '예: VLAN_10'}
                    ]
                },
                {
                    'name': 'VLAN 삭제',
                    'description': 'VLAN을 삭제합니다',
                    'task_type': mapped_task_type,
                    'vendor': 'all',
                    'parameters': [
                        {'name': 'vlan_id', 'type': 'text', 'label': 'VLAN ID', 'required': True, 'placeholder': '예: 10'}
                    ]
                },
                {
                    'name': 'VLAN 이름 설정',
                    'description': 'VLAN 이름을 설정합니다',
                    'task_type': mapped_task_type,
                    'vendor': 'all',
                    'parameters': [
                        {'name': 'vlan_id', 'type': 'text', 'label': 'VLAN ID', 'required': True, 'placeholder': '예: 10'},
                        {'name': 'vlan_name', 'type': 'text', 'label': 'VLAN 이름', 'required': True, 'placeholder': '예: VLAN_10'}
                    ]
                }
            ]
        elif mapped_task_type == '인터페이스 설정' or mapped_task_type == '포트 설정':
            logger.info("인터페이스 설정 작업의 상세 작업 반환")
            subtasks = [
                {
                    'name': '포트 IP추가',
                    'description': '포트에 IP를 추가합니다',
                    'task_type': mapped_task_type,
                    'vendor': 'all',
                    'parameters': [
                        {'name': 'interface_name', 'type': 'text', 'label': '인터페이스 이름', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                        {'name': 'ip_address', 'type': 'text', 'label': 'IP 주소', 'required': True, 'placeholder': '예: 192.168.1.1'},
                        {'name': 'subnet_mask', 'type': 'text', 'label': '서브넷 마스크', 'required': True, 'placeholder': '예: 255.255.255.0'}
                    ]
                },
                {
                    'name': '포트 활성화',
                    'description': '포트를 활성화합니다',
                    'task_type': mapped_task_type,
                    'vendor': 'all',
                    'parameters': [
                        {'name': 'interface_name', 'type': 'text', 'label': '인터페이스 이름', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'}
                    ]
                },
                {
                    'name': '포트 비활성화',
                    'description': '포트를 비활성화합니다',
                    'task_type': mapped_task_type,
                    'vendor': 'all',
                    'parameters': [
                        {'name': 'interface_name', 'type': 'text', 'label': '인터페이스 이름', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'}
                    ]
                },
                {
                    'name': '포트 속도 설정',
                    'description': '포트 속도와 듀플렉스 모드를 설정합니다',
                    'task_type': mapped_task_type,
                    'vendor': 'all',
                    'parameters': [
                        {'name': 'interface_name', 'type': 'text', 'label': '인터페이스 이름', 'required': True, 'placeholder': '예: GigabitEthernet1/0/1'},
                        {'name': 'speed', 'type': 'select', 'label': '속도', 'required': True, 'options': ['auto', '10', '100', '1000']},
                        {'name': 'duplex', 'type': 'select', 'label': '듀플렉스', 'required': True, 'options': ['auto', 'full', 'half']}
                    ]
                }
            ]
        elif mapped_task_type == 'VLAN 인터페이스 설정':
            logger.info("VLAN 인터페이스 설정 작업에 대한 상세 작업 반환")
            subtasks = [
                {'name': '액세스 모드 설정', 'description': '인터페이스를 액세스 모드로 설정합니다', 'task_type': mapped_task_type, 'vendor': 'all'},
                {'name': '트렁크 모드 설정', 'description': '인터페이스를 트렁크 모드로 설정합니다', 'task_type': mapped_task_type, 'vendor': 'all'},
                {'name': '액세스 VLAN 할당', 'description': '인터페이스에 액세스 VLAN을 할당합니다', 'task_type': mapped_task_type, 'vendor': 'all'},
                {'name': '허용 VLAN 설정', 'description': '트렁크 포트에 허용할 VLAN을 설정합니다', 'task_type': mapped_task_type, 'vendor': 'all'}
            ]
        elif mapped_task_type == 'IP 주소 설정':
            logger.info("IP 주소 설정 작업에 대한 상세 작업 반환")
            subtasks = [
                {'name': 'IPv4 주소 설정', 'description': '인터페이스에 IPv4 주소를 설정합니다', 'task_type': mapped_task_type, 'vendor': 'all'},
                {'name': '보조 IP 주소 설정', 'description': '인터페이스에 보조 IPv4 주소를 설정합니다', 'task_type': mapped_task_type, 'vendor': 'all'},
                {'name': '인터페이스 IPv6 주소 설정', 'description': '인터페이스에 IPv6 주소를 설정합니다', 'task_type': mapped_task_type, 'vendor': 'all'}
            ]
        elif mapped_task_type == '라우팅 설정':
            logger.info("라우팅 설정 작업에 대한 상세 작업 반환")
            subtasks = [
                {
                    'name': 'OSPF 설정',
                    'description': 'OSPF 라우팅 프로토콜을 설정합니다',
                    'task_type': mapped_task_type,
                    'vendor': 'all',
                    'parameters': [
                        {'name': 'process_id', 'type': 'text', 'label': '프로세스 ID', 'required': True, 'placeholder': '1-65535'},
                        {'name': 'network_address', 'type': 'text', 'label': '네트워크 주소', 'required': True, 'placeholder': '예: 192.168.1.0'},
                        {'name': 'wildcard_mask', 'type': 'text', 'label': '와일드카드 마스크', 'required': True, 'placeholder': '예: 0.0.0.255'},
                        {'name': 'area_id', 'type': 'text', 'label': '영역 ID', 'required': True, 'placeholder': '예: 0'}
                    ]
                },
                {
                    'name': '정적 라우팅 설정',
                    'description': '정적 라우팅을 설정합니다',
                    'task_type': mapped_task_type,
                    'vendor': 'all',
                    'parameters': [
                        {'name': 'network_address', 'type': 'text', 'label': '대상 네트워크', 'required': True, 'placeholder': '예: 192.168.1.0'},
                        {'name': 'subnet_mask', 'type': 'text', 'label': '서브넷 마스크', 'required': True, 'placeholder': '예: 255.255.255.0'},
                        {'name': 'next_hop', 'type': 'text', 'label': '다음 홉 주소', 'required': True, 'placeholder': '예: 10.0.0.1'}
                    ]
                }
            ]
        elif mapped_task_type == 'ACL 설정':
            logger.info("ACL 설정 작업에 대한 상세 작업 반환")
            subtasks = [
                {'name': '표준 ACL 설정', 'description': '표준 ACL을 구성합니다', 'task_type': mapped_task_type, 'vendor': 'all'},
                {'name': '확장 ACL 설정', 'description': '확장 ACL을 구성합니다', 'task_type': mapped_task_type, 'vendor': 'all'},
                {'name': '인터페이스 ACL 적용', 'description': '인터페이스에 ACL을 적용합니다', 'task_type': mapped_task_type, 'vendor': 'all'}
            ]
        elif mapped_task_type == 'SNMP 설정':
            logger.info("SNMP 설정 작업에 대한 상세 작업 반환")
            subtasks = [
                {'name': 'SNMP 커뮤니티 설정', 'description': 'SNMP 커뮤니티 문자열을 설정합니다', 'task_type': mapped_task_type, 'vendor': 'all'},
                {'name': 'SNMP 서버 설정', 'description': 'SNMP 서버 정보를 구성합니다', 'task_type': mapped_task_type, 'vendor': 'all'},
                {'name': 'SNMP 버전 설정', 'description': 'SNMP 버전을 설정합니다', 'task_type': mapped_task_type, 'vendor': 'all'}
            ]
        elif mapped_task_type == 'NTP 설정':
            logger.info("NTP 설정 작업에 대한 상세 작업 반환")
            subtasks = [
                {'name': 'NTP 서버 설정', 'description': 'NTP 서버를 구성합니다', 'task_type': mapped_task_type, 'vendor': 'all'},
                {'name': '시간대 설정', 'description': '장비의 시간대를 설정합니다', 'task_type': mapped_task_type, 'vendor': 'all'}
            ]
        elif mapped_task_type == 'VLAN':
            logger.info("VLAN 작업에 대한 상세 작업 반환")
            subtasks = [
                {
                    'name': 'vlan_id',
                    'type': 'text',
                    'label': 'VLAN ID',
                    'required': True,
                    'placeholder': '예: 10-15,20'
                },
                {
                    'name': 'interface',
                    'type': 'text',
                    'label': '인터페이스',
                    'required': True,
                    'placeholder': '예: gi 0/1'
                },
                {
                    'name': 'mode',
                    'type': 'select',
                    'label': '모드',
                    'required': True,
                    'options': [{'value': 'access', 'label': 'Access'}, {'value': 'trunk', 'label': 'Trunk'}]
                }
            ]
        elif mapped_task_type == 'Spanning-tree':
            if subtask == 'config':
                # 필수 파라미터 검증
                if not isinstance(parameters, dict):
                    logger.error(f"파라미터가 올바른 형식이 아닙니다. 받은 형식: {type(parameters)}")
                    return jsonify({'error': '파라미터가 올바른 형식이 아닙니다.'}), 400

                if config_mode == 'config(RSTP)':
                    if 'instance_id' not in parameters or 'priority' not in parameters:
                        missing_params = []
                        if 'instance_id' not in parameters: missing_params.append('instance_id')
                        if 'priority' not in parameters: missing_params.append('priority')
                        logger.error(f"필수 파라미터 누락: {', '.join(missing_params)}")
                        return jsonify({'error': f"다음 필수 파라미터가 누락되었습니다: {', '.join(missing_params)}"}), 400
                    
                    commands = [
                        'configure terminal',
                        'spanning-tree mode rstp',
                        'spanning-tree enable',
                        f'spanning-tree mst instance {parameters["instance_id"]} priority {parameters["priority"]}',
                        'spanning-tree mode rapid-vst',
                        'end'
                    ]
                elif config_mode == 'config(PVST+)':
                    if 'vlan_id' not in parameters or 'priority' not in parameters:
                        missing_params = []
                        if 'vlan_id' not in parameters: missing_params.append('vlan_id')
                        if 'priority' not in parameters: missing_params.append('priority')
                        logger.error(f"필수 파라미터 누락: {', '.join(missing_params)}")
                        return jsonify({'error': f"다음 필수 파라미터가 누락되었습니다: {', '.join(missing_params)}"}), 400
                    
                    commands = [
                        'configure terminal',
                        'spanning-tree mode rapid-vst',
                        'spanning-tree enable',
                        f'spanning-tree vlan {parameters["vlan_id"]} priority {parameters["priority"]}',
                        'end'
                    ]
                logger.info(f"생성된 명령어: {commands}")
            elif subtask == 'check':
                commands = [
                    'show spanning-tree',
                    'show spanning-tree detail',
                    'show spanning-tree bpdu statistics'
                ]
                logger.info(f"생성된 명령어: {commands}")
        
        if commands:
            result = {'output': '\n'.join(commands)}
            logger.info(f"반환할 결과: {result}")
            return jsonify(result)
        else:
            logger.warning("생성된 명령어가 없습니다.")
            return jsonify({'error': '지원되지 않는 작업입니다.'}), 400
    except Exception as e:
        logger.error(f"상세 작업 목록 조회 중 오류: {str(e)}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/parameters/<task_type>/<feature>/<subtask>/<config_mode>', methods=['GET'])
def get_parameters(task_type, feature, subtask, config_mode):
    """특정 작업에 대한 파라미터 목록을 반환합니다."""
    try:
        logger.info(f"파라미터 요청: task_type={task_type}, feature={feature}, subtask={subtask}, config_mode={config_mode}")
        
        # LAYER2 작업에 대한 파라미터 정의
        if task_type == 'LAYER2':
            if feature == 'Link-Aggregation (Manual)':
                if subtask == 'config':
                    return jsonify([
                        {'name': 'group_id', 'type': 'number', 'label': '그룹 ID', 'required': True, 'default': '1'},
                        {'name': 'interface_list', 'type': 'text', 'label': '인터페이스 목록', 'required': True, 'placeholder': '예: 0/1-0/2'}
                    ])
                elif subtask == 'check':
                    return jsonify([
                        {'name': 'group_id', 'type': 'number', 'label': '그룹 ID', 'required': False, 'default': '1'}
                    ])
            elif feature == 'Link-Aggregation (LACP)':
                if subtask == 'config':
                    return jsonify([
                        {'name': 'group_id', 'type': 'number', 'label': '그룹 ID', 'required': True, 'default': '1'},
                        {'name': 'interface_list', 'type': 'text', 'label': '인터페이스 목록', 'required': True, 'placeholder': '예: 0/1-0/2'}
                    ])
                elif subtask == 'check':
                    return jsonify([
                        {'name': 'group_id', 'type': 'number', 'label': '그룹 ID', 'required': False, 'default': '1'}
                    ])
            elif feature == 'VLAN':
                if subtask == 'config':
                    return jsonify([
                        {'name': 'vlan_id', 'type': 'text', 'label': 'VLAN ID', 'required': True, 'placeholder': '예: 10-15,20'},
                        {'name': 'interface', 'type': 'text', 'label': '인터페이스', 'required': True, 'placeholder': '예: gi 0/1'},
                        {'name': 'mode', 'type': 'select', 'label': '모드', 'required': True,
                         'options': [{'value': 'access', 'label': 'Access'}, {'value': 'trunk', 'label': 'Trunk'}]}
                    ])
                elif subtask == 'check':
                    return jsonify([
                        {'name': 'interface', 'type': 'text', 'label': '인터페이스', 'required': False, 'placeholder': '예: gi 0/1'}
                    ])
            elif feature == 'Spanning-tree':
                if subtask == 'config':
                    if config_mode == 'config(RSTP)':
                        return jsonify([
                            {'name': 'instance_id', 'type': 'number', 'label': 'MST 인스턴스 ID', 'required': True, 'default': '0'},
                            {'name': 'priority', 'type': 'number', 'label': '우선순위', 'required': True, 'default': '32768'}
                        ])
                    elif config_mode == 'config(PVST+)':
                        return jsonify([
                            {'name': 'vlan_id', 'type': 'number', 'label': 'VLAN ID', 'required': True},
                            {'name': 'priority', 'type': 'number', 'label': '우선순위', 'required': True, 'default': '32768'}
                        ])
                elif subtask == 'check':
                    return jsonify([])  # check 명령어는 파라미터가 필요 없음
        
        logger.warning(f"지원되지 않는 파라미터 요청: {task_type}/{feature}/{subtask}/{config_mode}")
        return jsonify([])
        
    except Exception as e:
        logger.error(f"파라미터 조회 실패: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/execute', methods=['POST'])
def execute_task():
    """작업을 실행하고 결과를 반환합니다."""
    try:
        data = request.get_json()
        logger.info("=== 실행 요청 데이터 ===")
        logger.info(f"Raw Data: {data}")
        
        if not data:
            logger.error("요청 데이터가 없습니다.")
            return jsonify({'error': '요청 데이터가 없습니다.'}), 400
            
        task_type = data.get('taskType')  # taskType으로 변경
        feature = data.get('feature')
        subtask = data.get('subtask')
        config_mode = data.get('configMode')  # configMode로 변경
        parameters = data.get('parameters', {})
        
        logger.info(f"Task Type: {task_type}")
        logger.info(f"Feature: {feature}")
        logger.info(f"Subtask: {subtask}")
        logger.info(f"Config Mode: {config_mode}")
        logger.info(f"Parameters: {parameters}")
        
        # 필수 필드 검증
        if not all([task_type, feature, subtask]):
            missing_fields = []
            if not task_type: missing_fields.append('taskType')
            if not feature: missing_fields.append('feature')
            if not subtask: missing_fields.append('subtask')
            logger.error(f"필수 필드 누락: {', '.join(missing_fields)}")
            return jsonify({'error': f"다음 필수 항목이 누락되었습니다: {', '.join(missing_fields)}"}), 400
        
        # LAYER2 작업 처리
        if task_type == 'LAYER2':
            commands = []
            
            if feature == 'Link-Aggregation (Manual)':
                if subtask == 'config':
                    # 필수 파라미터 검증
                    if not isinstance(parameters, dict):
                        logger.error(f"파라미터가 올바른 형식이 아닙니다. 받은 형식: {type(parameters)}")
                        return jsonify({'error': '파라미터가 올바른 형식이 아닙니다.'}), 400
                        
                    if 'group_id' not in parameters or 'interface_list' not in parameters:
                        missing_params = []
                        if 'group_id' not in parameters: missing_params.append('group_id')
                        if 'interface_list' not in parameters: missing_params.append('interface_list')
                        logger.error(f"필수 파라미터 누락: {', '.join(missing_params)}")
                        return jsonify({'error': f"다음 필수 파라미터가 누락되었습니다: {', '.join(missing_params)}"}), 400
                        
                    commands = [
                        'configure terminal',
                        f'link-aggregation {parameters["group_id"]} mode manual',
                        f'interface gi {parameters["interface_list"]}',
                        f'link-aggregation {parameters["group_id"]} manual',
                        'end'
                    ]
                    logger.info(f"생성된 명령어: {commands}")
                elif subtask == 'check':
                    commands = [
                        'show link-aggregation brief',
                        f'show link-aggregation group {parameters.get("group_id", "1")}'
                    ]
                    logger.info(f"생성된 명령어: {commands}")
            elif feature == 'Link-Aggregation (LACP)':
                if subtask == 'config':
                    # 필수 파라미터 검증
                    if not isinstance(parameters, dict):
                        logger.error(f"파라미터가 올바른 형식이 아닙니다. 받은 형식: {type(parameters)}")
                        return jsonify({'error': '파라미터가 올바른 형식이 아닙니다.'}), 400
                        
                    if 'group_id' not in parameters or 'interface_list' not in parameters:
                        missing_params = []
                        if 'group_id' not in parameters: missing_params.append('group_id')
                        if 'interface_list' not in parameters: missing_params.append('interface_list')
                        logger.error(f"필수 파라미터 누락: {', '.join(missing_params)}")
                        return jsonify({'error': f"다음 필수 파라미터가 누락되었습니다: {', '.join(missing_params)}"}), 400
                        
                    commands = [
                        'configure terminal',
                        f'link-aggregation {parameters["group_id"]} mode lacp',
                        f'interface gi {parameters["interface_list"]}',
                        f'link-aggregation {parameters["group_id"]} active',
                        'end'
                    ]
                    logger.info(f"생성된 명령어: {commands}")
                elif subtask == 'check':
                    commands = [
                        'show link-aggregation brief',
                        f'show link-aggregation group {parameters.get("group_id", "1")}'
                    ]
                    logger.info(f"생성된 명령어: {commands}")
            elif feature == 'VLAN':
                if subtask == 'config':
                    # 필수 파라미터 검증
                    if not isinstance(parameters, dict):
                        logger.error(f"파라미터가 올바른 형식이 아닙니다. 받은 형식: {type(parameters)}")
                        return jsonify({'error': '파라미터가 올바른 형식이 아닙니다.'}), 400
                        
                    if 'vlan_id' not in parameters or 'interface' not in parameters or 'mode' not in parameters:
                        missing_params = []
                        if 'vlan_id' not in parameters: missing_params.append('vlan_id')
                        if 'interface' not in parameters: missing_params.append('interface')
                        if 'mode' not in parameters: missing_params.append('mode')
                        logger.error(f"필수 파라미터 누락: {', '.join(missing_params)}")
                        return jsonify({'error': f"다음 필수 파라미터가 누락되었습니다: {', '.join(missing_params)}"}), 400
                    
                    commands = [
                        'configure terminal',
                        f'vlan {parameters["vlan_id"]}',
                        f'interface {parameters["interface"]}'
                    ]
                    
                    if parameters['mode'] == 'access':
                        commands.append(f'switchport access vlan {parameters["vlan_id"]}')
                    elif parameters['mode'] == 'trunk':
                        commands.extend([
                            'switchport mode trunk',
                            f'switchport trunk allowed vlan add {parameters["vlan_id"]}'
                        ])
                    
                    commands.append('end')
                    logger.info(f"생성된 명령어: {commands}")
                elif subtask == 'check':
                    commands = ['show vlan']
                    if parameters.get('interface'):
                        commands.append(f'show interface {parameters["interface"]} vlan status')
                    logger.info(f"생성된 명령어: {commands}")
            elif feature == 'Spanning-tree':
                if subtask == 'config':
                    # 필수 파라미터 검증
                    if not isinstance(parameters, dict):
                        logger.error(f"파라미터가 올바른 형식이 아닙니다. 받은 형식: {type(parameters)}")
                        return jsonify({'error': '파라미터가 올바른 형식이 아닙니다.'}), 400

                    if config_mode == 'config(RSTP)':
                        if 'instance_id' not in parameters or 'priority' not in parameters:
                            missing_params = []
                            if 'instance_id' not in parameters: missing_params.append('instance_id')
                            if 'priority' not in parameters: missing_params.append('priority')
                            logger.error(f"필수 파라미터 누락: {', '.join(missing_params)}")
                            return jsonify({'error': f"다음 필수 파라미터가 누락되었습니다: {', '.join(missing_params)}"}), 400
                        
                        commands = [
                            'configure terminal',
                            'spanning-tree mode rstp',
                            'spanning-tree enable',
                            f'spanning-tree mst instance {parameters["instance_id"]} priority {parameters["priority"]}',
                            'spanning-tree mode rapid-vst',
                            'end'
                        ]
                    elif config_mode == 'config(PVST+)':
                        if 'vlan_id' not in parameters or 'priority' not in parameters:
                            missing_params = []
                            if 'vlan_id' not in parameters: missing_params.append('vlan_id')
                            if 'priority' not in parameters: missing_params.append('priority')
                            logger.error(f"필수 파라미터 누락: {', '.join(missing_params)}")
                            return jsonify({'error': f"다음 필수 파라미터가 누락되었습니다: {', '.join(missing_params)}"}), 400
                        
                        commands = [
                            'configure terminal',
                            'spanning-tree mode rapid-vst',
                            'spanning-tree enable',
                            f'spanning-tree vlan {parameters["vlan_id"]} priority {parameters["priority"]}',
                            'end'
                        ]
                    logger.info(f"생성된 명령어: {commands}")
                elif subtask == 'check':
                    commands = [
                        'show spanning-tree',
                        'show spanning-tree detail',
                        'show spanning-tree bpdu statistics'
                    ]
                    logger.info(f"생성된 명령어: {commands}")
            
            if commands:
                result = {'output': '\n'.join(commands)}
                logger.info(f"반환할 결과: {result}")
                return jsonify(result)
            else:
                logger.warning("생성된 명령어가 없습니다.")
                return jsonify({'error': '지원되지 않는 작업입니다.'}), 400
        
        logger.warning(f"지원되지 않는 작업 유형: {task_type}")
        return jsonify({'error': '지원되지 않는 작업 유형입니다.'}), 400
        
    except Exception as e:
        logger.error(f"작업 실행 실패: {str(e)}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

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
            {"name": "VLAN 생성/삭제", "description": "VLAN 생성/삭제, 인터페이스 VLAN 할당, 트렁크 설정", "vendor": "all", "template_key": "vlan_config"},
            {"name": "인터페이스 설정", "description": "액세스/트렁크 모드 설정, 포트 속도/듀플렉스 조정, 인터페이스 활성화", "vendor": "all", "template_key": "interface_config"},
            {"name": "VLAN 인터페이스 설정", "description": "VLAN 인터페이스 구성, STP 설정, LACP/포트 채널 구성", "vendor": "all", "template_key": "vlan_interface"},
            {"name": "IP 주소 설정", "description": "인터페이스 IP 주소 설정, 서브넷 마스크 구성", "vendor": "all", "template_key": "ip_config"},
            {"name": "라우팅 설정", "description": "정적 라우팅, OSPF, EIGRP, BGP 설정 및 관리", "vendor": "all", "template_key": "routing_config"},
            {"name": "ACL 설정", "description": "ACL 구성, 포트 보안, SSH/Telnet 제한", "vendor": "all", "template_key": "acl_config"},
            {"name": "SNMP 설정", "description": "SNMP 커뮤니티 설정, 트랩 설정", "vendor": "all", "template_key": "snmp_config"},
            {"name": "NTP 설정", "description": "NTP 서버 설정, 타임존 구성", "vendor": "all", "template_key": "ntp_config"}
        ]
        
        for task_type_data in default_task_types:
            task_type = TaskType(
                name=task_type_data["name"],
                description=task_type_data["description"],
                vendor=task_type_data["vendor"],
                template_key=task_type_data.get("template_key")
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