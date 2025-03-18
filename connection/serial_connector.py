import serial
import time

class SerialConnector:
    """콘솔(Serial) 연결을 위한 클래스"""

    def __init__(self, port="/dev/ttyUSB0", baudrate=9600, username="admin", password="password", secret="enable"):
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=1)
        self.username = username
        self.password = password
        self.secret = secret

    def send_command(self, cmd, wait=0.5):
        """명령어 전송 및 응답 받기"""
        self.ser.write(cmd.encode() + b"\n")
        time.sleep(wait)
        response = self.ser.read(self.ser.inWaiting()).decode()
        return response

    def login(self):
        """로그인 프롬프트 감지 후 사용자 인증"""
        time.sleep(1)
        self.ser.write(b"\r\n")  # 초기 엔터 입력

        response = self.ser.read(self.ser.inWaiting()).decode()
        if "Username:" in response:
            self.send_command(self.username)
        if "Password:" in response:
            self.send_command(self.password)

        self.send_command("enable")
        self.send_command(self.secret)

    def execute_commands(self, commands):
        """저장된 명령어 실행"""
        self.login()
        for cmd in commands:
            print(self.send_command(cmd))
        self.send_command("write memory")
        self.send_command("exit")
        self.ser.close()
