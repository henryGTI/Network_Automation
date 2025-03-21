from datetime import datetime
import os
import json
import tkinter as tk
from tkinter import ttk

class BackupManager:
    def __init__(self):
        self.backup_dir = "backups"
        self.setup_backup_directory()
        
    def setup_backup_directory(self):
        """백업 디렉토리 구조 생성"""
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def create_backup(self, device_name, config_data):
        """설정 변경 전 자동 백업 수행"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{self.backup_dir}/{device_name}_{timestamp}.json"
        
        # 설정 데이터 백업
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        return backup_file
            
    def restore_backup(self, backup_file):
        """백업 복원"""
        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
            
    def list_backups(self, device_name=None):
        """백업 목록 조회"""
        backups = []
        for file in os.listdir(self.backup_dir):
            if device_name is None or file.startswith(device_name):
                backups.append(file)
        return sorted(backups, reverse=True)

    def setup_ui(self):
        # ... 기존 코드 ...
        
        # 벤더 선택 옵션 업데이트
        self.vendor_var = tk.StringVar(value="Cisco")
        self.vendor_combo = ttk.Combobox(main_frame, textvariable=self.vendor_var, 
                                       values=["Cisco", "Juniper", "HP", "Arista", 
                                             "CoreEdge", "HandreamNet"], 
                                       state="readonly")
        self.vendor_combo.grid(row=1, column=1, sticky=(tk.W, tk.E)) 