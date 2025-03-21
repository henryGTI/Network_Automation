import serial
from netmiko import ConnectHandler
from exceptions import ConnectionError

class NetworkConnection:
    def __init__(self):
        self.ssh_connection = None
        self.console_connection = None
        
    def connect_ssh(self, device_info):
        """SSH 연결"""
        try:
            self.ssh_connection = ConnectHandler(**device_info)
            return True
        except Exception as e:
            raise ConnectionError(f"SSH 연결 실패: {str(e)}")
            
    def connect_console(self, port, baudrate=9600):
        """콘솔 연결"""
        try:
            self.console_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1
            )
            return True
        except Exception as e:
            raise ConnectionError(f"콘솔 연결 실패: {str(e)}")
            
    def send_command(self, command, connection_type="SSH"):
        """명령어 전송"""
        try:
            if connection_type == "SSH":
                return self.ssh_connection.send_command(command)
            else:
                self.console_connection.write(f"{command}\n".encode())
                return self.console_connection.readline().decode()
        except Exception as e:
            raise ConnectionError(f"명령어 전송 실패: {str(e)}") 