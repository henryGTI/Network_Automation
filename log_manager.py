import logging
from datetime import datetime
import os
import queue

class LogManager:
    def __init__(self):
        self.setup_logger()
        self.log_queue = queue.Queue()
        
    def setup_logger(self):
        """로거 설정"""
        self.logger = logging.getLogger('NetworkAutomation')
        self.logger.setLevel(logging.INFO)
        
        # 로그 파일 핸들러
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = f"{log_dir}/execution_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 포맷 설정
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)

    def log_execution(self, device_name, action, result):
        """실행 결과 로깅"""
        message = f"[{device_name}] {action}: {result}"
        self.logger.info(message)
        self.log_queue.put(message)

    def get_recent_logs(self, count=100):
        """최근 로그 조회"""
        try:
            log_file = f"logs/execution_{datetime.now().strftime('%Y%m%d')}.log"
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()
            return logs[-count:]
        except FileNotFoundError:
            return [] 
        self.logger.info(f"장비: {device_name} - 작업: {action} - 결과: {result}") 