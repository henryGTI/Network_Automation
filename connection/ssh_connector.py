from netmiko import ConnectHandler

class SSHConnector:
    """SSH 연결을 위한 클래스"""

    def __init__(self, host, username, password, secret):
        self.device = {
            "device_type": "cisco_ios",
            "host": host,
            "username": username,
            "password": password,
            "secret": secret
        }

    def execute_commands(self, commands):
        """SSH를 통해 명령 실행"""
        connection = ConnectHandler(**self.device)
        connection.enable()
        output = connection.send_config_set(commands)
        connection.disconnect()
        return output
