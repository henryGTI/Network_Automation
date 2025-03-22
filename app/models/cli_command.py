from datetime import datetime
from app import db

class CLICommand(db.Model):
    """CLI 명령어 모델"""
    __tablename__ = 'cli_commands'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor = db.Column(db.String(50), nullable=False)  # 벤더 (cisco, juniper, arista, hp)
    device_type = db.Column(db.String(50), nullable=False)  # 장비 유형 (switch, router, firewall)
    task_type = db.Column(db.String(50), nullable=False)  # 작업 유형 (vlan_config, interface_config 등)
    subtask = db.Column(db.String(50), nullable=False)  # 상세 작업
    command = db.Column(db.Text, nullable=False)  # CLI 명령어
    parameters = db.Column(db.JSON)  # 파라미터 정보
    description = db.Column(db.Text)  # 설명
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """객체를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'vendor': self.vendor,
            'device_type': self.device_type,
            'task_type': self.task_type,
            'subtask': self.subtask,
            'command': self.command,
            'parameters': self.parameters,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def get_by_task(cls, task_type, subtask=None):
        """작업 유형으로 명령어 조회"""
        query = cls.query.filter_by(task_type=task_type)
        if subtask:
            query = query.filter_by(subtask=subtask)
        return query.all()

    @classmethod
    def get_by_vendor(cls, vendor):
        """벤더별 명령어 조회"""
        return cls.query.filter_by(vendor=vendor).all()

    @classmethod
    def get_by_device_type(cls, device_type):
        """장비 유형별 명령어 조회"""
        return cls.query.filter_by(device_type=device_type).all()

    @classmethod
    def get_all(cls):
        return cls.query.all() 