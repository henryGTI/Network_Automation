from flask import Flask, render_template, jsonify
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import os
import webbrowser
import threading
import time
import sys

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

app = Flask(__name__)
CORS(app)

browser_opened = False

def open_browser():
    global browser_opened
    if not browser_opened:
        time.sleep(1.5)  # 서버 시작 대기
        webbrowser.open('http://127.0.0.1:5000', new=1)
        browser_opened = True

@app.route('/')
def index():
    logger.info('메인 페이지 요청됨')
    return render_template('device/index.html', active_tab='device')

@app.route('/config')
def config():
    logger.info('설정 페이지 요청됨')
    return render_template('config/index.html', active_tab='config')

@app.route('/learning')
def learning():
    logger.info('학습 페이지 요청됨')
    return render_template('learning/index.html', active_tab='learning')

# API 에러 핸들러
@app.errorhandler(404)
def not_found_error(error):
    logger.error(f'404 에러 발생: {error}')
    return jsonify({'status': 'error', 'message': '요청한 리소스를 찾을 수 없습니다.'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'500 에러 발생: {error}')
    return jsonify({'status': 'error', 'message': '서버 내부 오류가 발생했습니다.'}), 500

# device_routes 블루프린트 등록
from app.routes.device_routes import bp as device_bp
app.register_blueprint(device_bp)

if __name__ == '__main__':
    logger.info('서버 시작 중...')
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=5000)
