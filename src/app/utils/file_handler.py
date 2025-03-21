import json
from pathlib import Path

class FileHandler:
    def __init__(self, relative_path):
        self.file_path = Path(__file__).parent.parent.parent / 'data' / relative_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load_data(self):
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            return []

    def save_data(self, data):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"데이터 저장 오류: {e}")
            return False 