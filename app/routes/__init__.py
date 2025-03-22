from flask import Blueprint
from app.routes.device_routes import device_bp
from app.routes.learning_routes import learning_bp

# 블루프린트 등록
def register_blueprints(app):
    app.register_blueprint(device_bp)
    app.register_blueprint(learning_bp)
