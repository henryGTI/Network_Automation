import os
import json
import shutil
from datetime import datetime

class FileManager:
    def __init__(self):
        # 디렉토리 구조 생성
        self.directories = {
            'cli_learning': '.',
            'config': '.',
            'tasks': 'tasks',
            'uploads': 'uploads',
            'logs': 'logs'
        }
        self.setup_directories()
        
    def setup_directories(self):
        """디렉토리 구조 생성"""
        for directory in self.directories.values():
            os.makedirs(directory, exist_ok=True)
            
    def save_cli_learning(self, data):
        """CLI 학습 데이터 저장"""
        with open('cli_learning.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
    def save_config(self, config):
        """사용자 설정 저장"""
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
    def save_task(self, vendor, task_name, commands):
        """CLI 스크립트 저장"""
        filename = f"tasks/{vendor}_{task_name}.json"
        data = {
            "vendor": vendor,
            "created_at": datetime.now().isoformat(),
            "commands": commands
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
    def save_upload(self, file_path):
        """업로드 파일 저장"""
        filename = os.path.basename(file_path)
        dest_path = f"uploads/{filename}"
        shutil.copy2(file_path, dest_path)
        return dest_path
        
    def log_execution(self, message):
        """실행 로그 저장"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = f"logs/execution_{datetime.now().strftime('%Y%m%d')}.log"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
