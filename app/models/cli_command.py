from datetime import datetime

class CLICommand:
    def __init__(self, vendor, command, description, mode='', parameters=None, examples=None):
        self.vendor = vendor.lower()  # 벤더 이름 (소문자로 저장)
        self.command = command  # CLI 명령어
        self.description = description  # 명령어 설명
        self.mode = mode  # 명령어 실행 모드 (예: config, exec 등)
        self.parameters = parameters or []  # 명령어 파라미터 목록
        self.examples = examples or []  # 명령어 사용 예제
        self.created_at = datetime.now()  # 생성 시간
        self.updated_at = datetime.now()  # 수정 시간

    def to_dict(self):
        """객체를 딕셔너리로 변환"""
        return {
            'vendor': self.vendor,
            'command': self.command,
            'description': self.description,
            'mode': self.mode,
            'parameters': self.parameters,
            'examples': self.examples,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        """딕셔너리에서 객체 생성"""
        cmd = cls(
            vendor=data['vendor'],
            command=data['command'],
            description=data['description'],
            mode=data.get('mode', ''),
            parameters=data.get('parameters', []),
            examples=data.get('examples', [])
        )
        cmd.created_at = datetime.fromisoformat(data['created_at'])
        cmd.updated_at = datetime.fromisoformat(data['updated_at'])
        return cmd 