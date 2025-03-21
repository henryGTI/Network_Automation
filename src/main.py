# -*- coding: utf-8 -*-

import os
import sys
import webbrowser
from threading import Timer

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.app import app

def open_browser():
    try:
        webbrowser.open('http://127.0.0.1:5000/')
    except Exception as e:
        print(f"브라우저 실행 중 오류 발생: {e}")

def main():
    print("네트워크 자동화 도구 시작")
    
    # 환경 변수를 확인하여 메인 프로세스인 경우에만 브라우저 실행
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        Timer(1.5, open_browser).start()
    
    # Flask 앱 실행
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
