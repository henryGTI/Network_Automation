from app.database import db
from datetime import datetime

class TaskType(db.Model):
    """작업 유형 모델"""
    __tablename__ = 'task_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    vendor = db.Column(db.String(50))  # 특정 벤더에만 적용되는 작업 유형인 경우
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, description=None, vendor=None):
        self.name = name
        self.description = description
        self.vendor = vendor
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'vendor': self.vendor,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<TaskType {self.name}>' 