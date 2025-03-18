import json
from cryptography.fernet import Fernet
import os

class SecurityManager:
    def __init__(self):
        self.security_dir = "security"
        self.key_file = f"{self.security_dir}/encryption.key"
        self.config_file = f"{self.security_dir}/security_config.json"
        self.setup_security()
        
    def setup_security(self):
        """보안 디렉토리 및 키 생성"""
        os.makedirs(self.security_dir, exist_ok=True)
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
                
    def save_security_config(self, config):
        """암호화된 보안 설정 저장"""
        with open(self.key_file, "rb") as f:
            key = f.read()
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(json.dumps(config, ensure_ascii=False).encode())
        with open(self.config_file, "wb") as f:
            f.write(encrypted_data)
            
    def load_security_config(self):
        """암호화된 보안 설정 로드"""
        try:
            with open(self.key_file, "rb") as f:
                key = f.read()
            with open(self.config_file, "rb") as f:
                encrypted_data = f.read()
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except FileNotFoundError:
            return None 