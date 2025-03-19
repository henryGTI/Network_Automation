import re
from typing import List, Dict, Optional
import logging

class CommandAnalyzer:
    def __init__(self, vendor: str):
        self.vendor = vendor
        self.patterns = VENDOR_PATTERNS.get(vendor, {})
        self.logger = logging.getLogger(__name__)

    def analyze_config(self, config_output: str, task_type: str) -> List[Dict]:
        """설정 출력을 분석하여 명령어 패턴 추출"""
        try:
            if task_type not in self.patterns:
                raise ValueError(f'지원하지 않는 작업 유형: {task_type}')

            task_patterns = self.patterns[task_type]['patterns']
            commands = []
            current_context = {}

            for line in config_output.splitlines():
                line = line.strip()
                if not line:
                    continue

                for pattern in task_patterns:
                    match = re.match(pattern, line)
                    if match:
                        if task_type == 'vlan_config' and 'vlan' in line:
                            current_context = {
                                'vlan_id': match.group(1)
                            }
                        elif 'name' in line and current_context:
                            current_context['vlan_name'] = match.group(1)
                            commands.append(current_context.copy())
                            current_context = {}

            return commands

        except Exception as e:
            self.logger.error(f'명령어 분석 중 오류: {str(e)}')
            raise

    def validate_command(self, command: str, task_type: str) -> bool:
        """명령어 유효성 검사"""
        try:
            if task_type not in self.patterns:
                return False

            return any(re.match(pattern, command) 
                      for pattern in self.patterns[task_type]['patterns'])

        except Exception as e:
            self.logger.error(f'명령어 검증 중 오류: {str(e)}')
            return False

    def generate_commands(self, task_type: str, params: Dict) -> List[str]:
        """템플릿 기반 명령어 생성"""
        try:
            if task_type not in self.patterns:
                raise ValueError(f'지원하지 않는 작업 유형: {task_type}')

            template = self.patterns[task_type]['template']
            return [cmd.format(**params) for cmd in template]

        except Exception as e:
            self.logger.error(f'명령어 생성 중 오류: {str(e)}')
            raise 