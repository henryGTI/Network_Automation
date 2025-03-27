from flask import Flask, Blueprint, jsonify, request
from app.database import db
from flask_cors import CORS
import logging
import os
from app.routes.device_routes import device_bp
from app.routes.learning_routes import learning_bp
from app.routes.main_routes import main_bp
from app.routes.config_routes import bp as config_bp
from logging.handlers import RotatingFileHandler
from app.config import Config

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/app.log')
    ]
)

# 글로벌 API 라우트를 처리하는 Blueprint 생성
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 디바이스 API 경로 추가
@api_bp.route('/devices', methods=['GET'])
def get_devices_api():
    """디바이스 목록 API 라우트"""
    return jsonify([])  # 디바이스 라우트로 리다이렉션하지 않고 빈 배열 반환

@api_bp.route('/devices/<int:device_id>', methods=['GET'])
def get_device_api(device_id):
    """디바이스 상세 API 라우트"""
    return jsonify({})  # 디바이스 라우트로 리다이렉션하지 않고 빈 객체 반환

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates')
    CORS(app)
    
    # 설정
    app.config.from_object(config_class)
    
    # 데이터베이스 초기화
    db.init_app(app)
    
    # 보안 헤더 설정
    @app.after_request
    def add_security_headers(response):
        for header, value in app.config['SECURITY_HEADERS'].items():
            response.headers[header] = value
        return response
    
    # 로깅 설정
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=app.config['LOG_MAX_SIZE'],
        backupCount=app.config['LOG_BACKUP_COUNT']
    )
    file_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
    file_handler.setLevel(app.config['LOG_LEVEL'])
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(app.config['LOG_LEVEL'])
    app.logger.info('네트워크 자동화 애플리케이션 시작')
    
    # 블루프린트 등록
    app.register_blueprint(main_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(config_bp)  # config 블루프린트 등록
    app.register_blueprint(api_bp)  # 글로벌 API 라우트 등록
    
    with app.app_context():
        db.create_all()
    
    return app
