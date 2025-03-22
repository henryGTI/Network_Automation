from app.database import db
from datetime import datetime

class TaskType(db.Model):
    """작업 유형 모델"""
    __tablename__ = 'task_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    vendor = db.Column(db.String(50))  # 특정 벤더에만 적용되는 작업 유형인 경우
    template_key = db.Column(db.String(100))  # 벤더 명령어 템플릿의 키 값
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, description=None, vendor=None, template_key=None):
        self.name = name
        self.description = description
        self.vendor = vendor
        self.template_key = template_key
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'vendor': self.vendor,
            'template_key': self.template_key,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<TaskType {self.name}>' 