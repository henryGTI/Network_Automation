from config_manager import ConfigManager
from script_generator import ScriptGenerator
from connection.ssh_connector import SSHConnector
from connection.serial_connector import SerialConnector
from netmiko import ConnectHandler
import serial
from logging_config import NetworkLogger
from exceptions import ExecutionError, ConnectionError
from validators import NetworkValidator
from datetime import datetime
import paramiko
import time
import json
import os

class NetworkExecutor:
    def __init__(self):
        self.ssh = None
        self.serial = None
        self.current_device = None
        self.log_file = None

    def execute_device_config(self, device_name, connection_type="SSH"):
        """장비 설정 실행"""
        try:
            # 스크립트 파일 로드
            script_file = f"tasks/{device_name}_config.json"
            if not os.path.exists(script_file):
                raise ValueError(f"장비 '{device_name}'의 스크립트를 찾을 수 없습니다.")

            with open(script_file, 'r', encoding='utf-8') as f:
                script_data = json.load(f)

            # 로그 파일 설정
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            self.log_file = f"{log_dir}/{device_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            # 기본 정보 가져오기
            basic_info = script_data['basic_info']
            self.current_device = basic_info

            # 연결 설정
            if connection_type == "SSH":
                self._connect_ssh(
                    basic_info['ip_address'],
                    basic_info['login_id'],
                    basic_info['login_pw']
                )
            else:  # Console
                self._connect_console()

            # 설정 실행 및 결과 저장
            results = []
            
            # 각 설정 순차 실행
            for config in script_data['configurations']:
                result = self._execute_commands(config['commands'])
                results.append({
                    'type': config['type'],
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                self._log_execution(f"설정 유형: {config['type']}, 결과: {result}")

            return results

        except Exception as e:
            error_msg = f"실행 오류: {str(e)}"
            self._log_execution(error_msg)
            raise Exception(error_msg)

        finally:
            self._disconnect()

    def _connect_ssh(self, ip, username, password):
        """SSH 연결"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(ip, username=username, password=password)
            self._log_execution(f"SSH 연결 성공: {ip}")
        except Exception as e:
            raise Exception(f"SSH 연결 실패: {str(e)}")

    def _connect_console(self, port="COM1", baudrate=9600):
        """콘솔 연결"""
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1
            )
            self._log_execution(f"콘솔 연결 성공: {port}")
        except Exception as e:
            raise Exception(f"콘솔 연결 실패: {str(e)}")

    def _execute_commands(self, commands):
        """명령어 실행"""
        try:
            results = []
            for cmd in commands:
                if self.ssh:
                    # SSH 실행
                    stdin, stdout, stderr = self.ssh.exec_command(cmd)
                    result = stdout.read().decode()
                    error = stderr.read().decode()
                    if error:
                        raise Exception(f"명령어 실행 오류: {error}")
                    results.append(result)
                    
                elif self.serial:
                    # 콘솔 실행
                    self.serial.write(f"{cmd}\n".encode())
                    time.sleep(1)  # 명령어 실행 대기
                    result = self.serial.read_all().decode()
                    results.append(result)

                self._log_execution(f"명령어 실행: {cmd}")
                self._log_execution(f"실행 결과: {results[-1]}")

            return "\n".join(results)

        except Exception as e:
            raise Exception(f"명령어 실행 실패: {str(e)}")

    def _disconnect(self):
        """연결 종료"""
        if self.ssh:
            self.ssh.close()
            self._log_execution("SSH 연결 종료")
        if self.serial:
            self.serial.close()
            self._log_execution("콘솔 연결 종료")

    def _log_execution(self, message):
        """실행 로그 기록"""
        if self.log_file:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")

class Executor:
    @staticmethod
    def run_script(vendor, task_type, method="ssh"):
        """저장된 스크립트를 불러와 콘솔 또는 SSH로 실행"""
        config = ConfigManager.load_config()
        if not config:
            print("[❌] 저장된 설정이 없습니다.")
            return

        commands = ScriptGenerator.generate_script(config)
        print(f"[✔] 실행할 명령어:\n{commands}")

        if method == "ssh":
            connector = SSHConnector(
                host=config["host"],
                username=config["username"],
                password=config["password"],
                secret=config["secret"]
            )
            result = connector.execute_commands(commands)
            print(result)
        else:
            connector = SerialConnector(
                port="/dev/ttyUSB0",
                baudrate=9600,
                username=config["username"],
                password=config["password"],
                secret=config["secret"]
            )
            connector.execute_commands(commands)

        print("[✔] 설정 적용 완료")
