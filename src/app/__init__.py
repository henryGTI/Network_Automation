# -*- coding: utf-8 -*-
from flask import Flask
import os

# 프로젝트 루트 디렉토리 경로 설정
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Flask 앱 인스턴스 생성 및 템플릿 경로 설정
app = Flask(__name__,
           template_folder=os.path.join(project_root, 'templates'),
           static_folder=os.path.join(project_root, 'static'))

# 설정 로드
from src.app.config.config import Config
app.config.from_object(Config)

# routes import
from src.app.routes import routes
