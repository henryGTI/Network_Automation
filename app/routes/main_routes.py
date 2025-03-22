from flask import Blueprint, render_template, redirect, url_for
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """메인 페이지 요청을 처리합니다."""
    logger.info("메인 페이지 요청")
    return redirect(url_for('device.index'))  # 장비 관리 페이지로 리다이렉트

@main_bp.route('/config')
def config():
    """설정 페이지"""
    logger.info("설정 페이지 요청")
    return render_template('config/index.html')

@main_bp.route('/learning')
def learning():
    """학습 페이지"""
    logger.info("학습 페이지 요청")
    return render_template('learning/index.html')

@main_bp.errorhandler(404)
def not_found_error(error):
    """404 에러 처리"""
    logger.warning("404 에러 발생")
    return render_template('error/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """500 에러 처리"""
    logger.error("500 에러 발생")
    return render_template('error/500.html'), 500 