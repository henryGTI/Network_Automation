class NetworkAutomationError(Exception):
    """기본 네트워크 자동화 예외 클래스"""
    pass

class CLILearningError(NetworkAutomationError):
    """CLI 학습 관련 예외"""
    def __init__(self, message="CLI 학습 과정에서 오류가 발생했습니다."):
        self.message = message
        super().__init__(self.message)

class ScriptGenerationError(NetworkAutomationError):
    """스크립트 생성 관련 예외"""
    def __init__(self, message="스크립트 생성 중 오류가 발생했습니다."):
        self.message = message
        super().__init__(self.message)

class ExecutionError(NetworkAutomationError):
    """명령어 실행 관련 예외"""
    pass

class ConnectionError(NetworkAutomationError):
    """네트워크 연결 관련 예외"""
    pass

class ConfigurationError(NetworkAutomationError):
    """설정 관련 예외"""
    pass

class ValidationError(NetworkAutomationError):
    """입력값 검증 관련 예외"""
    def __init__(self, message="입력 데이터가 유효하지 않습니다."):
        self.message = message
        super().__init__(self.message)
