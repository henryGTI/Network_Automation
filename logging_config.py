import logging
from datetime import datetime
import os

class NetworkLogger:
    def __init__(self):
        self.logs_dir = "logs"
        self.setup_log_directory()
        
    def setup_log_directory(self):
        """로그 디렉토리 구조 생성"""
        directories = [
            f"{self.logs_dir}/device_logs",
            f"{self.logs_dir}/system_logs",
            f"{self.logs_dir}/security_logs"
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
    def get_device_logger(self, device_name):
        """장비별 로거 생성"""
        logger = logging.getLogger(f"device_{device_name}")
        if not logger.handlers:
            date_str = datetime.now().strftime("%Y%m%d")
            handler = logging.FileHandler(
                f"{self.logs_dir}/device_logs/{device_name}_{date_str}.log",
                encoding='utf-8'
            )
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def get_system_logger(self):
        """시스템 로거 생성"""
        logger = logging.getLogger("system")
        if not logger.handlers:
            date_str = datetime.now().strftime("%Y%m%d")
            handler = logging.FileHandler(
                f"{self.logs_dir}/system_logs/system_{date_str}.log",
                encoding='utf-8'
            )
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger 