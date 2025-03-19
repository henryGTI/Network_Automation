import warnings
import logging
import os
import webbrowser
from threading import Timer
from app import app
from cryptography.utils import CryptographyDeprecationWarning

# paramiko 관련 경고 메시지 명시적으로 제거
warnings.filterwarnings(
    action='ignore',
    category=CryptographyDeprecationWarning
)

# 로깅 설정
logging.basicConfig(
    level=logging.ERROR,  # 전체 로깅 레벨을 ERROR로 설정
    format='%(message)s'
)

# Flask 관련 로거 설정
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

def create_directories():
    """필요한 디렉토리 생성"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dirs = {
        'data': ['devices', 'scripts', 'learning'],
        'static': ['js', 'css'],
        'templates': [],
        'logs': []
    }
    
    for main_dir, sub_dirs in dirs.items():
        dir_path = os.path.join(base_dir, main_dir)
        os.makedirs(dir_path, exist_ok=True)
        
        for sub_dir in sub_dirs:
            sub_path = os.path.join(dir_path, sub_dir)
            os.makedirs(sub_path, exist_ok=True)

def open_browser():
    """웹 브라우저 자동 실행"""
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # 디렉토리 생성
    create_directories()
    
    # 1.5초 후에 브라우저 자동 실행
    Timer(1.5, open_browser).start()
    
    # 서버 시작
    print('네트워크 자동화 도구 시작')
    app.run(
        host='127.0.0.1', 
        port=5000, 
        debug=False, 
        use_reloader=False
    )
