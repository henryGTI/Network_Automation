from flask import Flask, Blueprint, jsonify, request
from app.database import db
from flask_cors import CORS
import logging
import os
from app.routes.device_routes import device_bp
from app.routes.learning_routes import learning_bp
from app.routes.main_routes import main_bp
from app.routes.config_routes import bp as config_bp

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

def create_app():
    app = Flask(__name__, template_folder='templates')
    CORS(app)
    
    # 설정
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///network_automation.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 데이터베이스 초기화
    db.init_app(app)
    
    # 블루프린트 등록
    app.register_blueprint(main_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(config_bp)  # config 블루프린트 등록
    app.register_blueprint(api_bp)  # 글로벌 API 라우트 등록
    
    # 데이터베이스 테이블 생성
    with app.app_context():
        db.create_all()
        logging.info('데이터베이스 테이블 생성 완료')
    
    # 서버 시작 로그
    app.logger.info("서버 시작 중...")
    
    return app
