from flask import Flask, send_from_directory
from flask_cors import CORS
import logging
import os
import webbrowser
import threading
import time
import sys
from app import create_app, db
from app.models.task_type import TaskType
import platform

# 로그 디렉토리 생성
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(log_dir, 'app.log'), encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = create_app()
CORS(app)

browser_opened = False

def open_browser():
    """서버 시작 후 브라우저 자동 실행"""
    time.sleep(1)  # 서버가 시작될 때까지 잠시 대기
    url = 'http://localhost:5000'
    
    try:
        if platform.system() == 'Windows':
            os.system(f'start {url}')
        elif platform.system() == 'Darwin':  # macOS
            os.system(f'open {url}')
        else:  # Linux
            os.system(f'xdg-open {url}')
    except Exception as e:
        print(f"브라우저 자동 실행 실패: {e}")

def reset_task_types():
    """작업 유형 테이블 초기화 및 기본값 설정"""
    with app.app_context():
        print("작업 유형 테이블 초기화 중...")
        
        # 테이블 삭제 후 다시 생성
        try:
            # 기존 데이터 삭제
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
            print("작업 유형 테이블 초기화 완료")
            
        except Exception as e:
            db.session.rollback()
            print(f"작업 유형 테이블 초기화 실패: {e}")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    # 데이터베이스 초기화
    with app.app_context():
        db.create_all()
    
    # 작업 유형 테이블 초기화
    reset_task_types()
    
    # 서버 시작
    print('서버 시작 중...')
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
