from app import db
from datetime import datetime

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)
    feature = db.Column(db.String(100), nullable=False)
    subtask = db.Column(db.String(100))
    config_mode = db.Column(db.String(50))
    parameters = db.Column(db.JSON)
    commands = db.Column(db.JSON)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    device = db.relationship('Device', backref=db.backref('tasks', lazy=True))

    def __repr__(self):
        return f'<Task {self.id} - {self.task_type}>' 