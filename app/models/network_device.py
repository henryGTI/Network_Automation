import paramiko
import time
from typing import List, Dict
import logging

class NetworkDevice:
    def __init__(self, host: str, username: str, password: str, device_type: str = 'cisco'):
        self.host = host
        self.username = username
        self.password = password
        self.device_type = device_type
        self.ssh = None
        self.channel = None
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                self.host,
                username=self.username,
                password=self.password,
                look_for_keys=False,
                allow_agent=False
            )
            self.channel = self.ssh.invoke_shell()
            self.logger.info(f'SSH ?곌껐 ?깃났: {self.host}')
            return True
        except Exception as e:
            self.logger.error(f'SSH ?곌껐 ?ㅽ뙣: {str(e)}')
            return False

    def disconnect(self):
        if self.ssh:
            self.ssh.close()
            self.logger.info(f'SSH ?곌껐 醫낅즺: {self.host}')

    def send_command(self, command: str, wait_time: float = 1) -> str:
        try:
            if not self.channel:
                raise Exception('SSH 梨꾨꼸???곌껐?섏? ?딆븯?듬땲??')

            self.channel.send(command + '\n')
            time.sleep(wait_time)
            output = self.channel.recv(65535).decode('utf-8')
            self.logger.debug(f'紐낅졊???ㅽ뻾: {command}')
            self.logger.debug(f'?ㅽ뻾 寃곌낵: {output}')
            return output
        except Exception as e:
            self.logger.error(f'紐낅졊???ㅽ뻾 ?ㅽ뙣: {str(e)}')
            raise

    def execute_script(self, commands: List[str]) -> Dict[str, str]:
        results = {}
        try:
            if not self.connect():
                raise Exception('?λ퉬 ?곌껐 ?ㅽ뙣')

            for command in commands:
                output = self.send_command(command)
                results[command] = output

            return {
                'status': 'success',
                'results': results
            }
        except Exception as e:
            self.logger.error(f'?ㅽ겕由쏀듃 ?ㅽ뻾 ?ㅽ뙣: {str(e)}')
            return {
                'status': 'error',
                'message': str(e),
                'results': results
            }
        finally:
            self.disconnect() 
