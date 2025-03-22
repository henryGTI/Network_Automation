import json
import os
import tempfile
import shutil

class FileHandler:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.devices_file = os.path.join(self.base_dir, 'data', 'devices', 'devices.json')
        os.makedirs(os.path.dirname(self.devices_file), exist_ok=True)

    def _safe_write(self, data, file_path):
        """안전한 파일 쓰기: 임시 파일을 사용하여 원자적 쓰기 수행"""
        temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file_path))
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            shutil.move(temp_path, file_path)
        except Exception as e:
            os.unlink(temp_path)
            raise e

    def load_devices(self):
        try:
            if not os.path.exists(self.devices_file):
                return []
            with open(self.devices_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return data
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return []
        except Exception as e:
            print(f"디바이스 데이터 로드 중 오류 발생: {str(e)}")
            return []

    def save_devices(self, devices):
        try:
            if not isinstance(devices, list):
                raise ValueError("devices는 리스트여야 합니다")
            self._safe_write(devices, self.devices_file)
            return True
        except Exception as e:
            print(f"디바이스 데이터 저장 중 오류 발생: {str(e)}")
            return False

def ensure_directory_exists(directory):
    """디렉토리가 존재하지 않으면 생성"""
    if not os.path.exists(directory):
        os.makedirs(directory)
