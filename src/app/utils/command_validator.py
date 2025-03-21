import re
from typing import Dict
import logging

class CommandValidator:
    def __init__(self, vendor: str):
        self.vendor = vendor
        self.analyzer = CommandAnalyzer(vendor)
        self.logger = logging.getLogger(__name__)

    def validate_learned_commands(self, learned_data: Dict) -> Dict:
        """학습된 명령어 검증"""
        validation_results = {
            'valid': [],
            'invalid': [],
            'warnings': []
        }

        try:
            for task_type, commands in learned_data.items():
                for command in commands:
                    if self.analyzer.validate_command(command, task_type):
                        validation_results['valid'].append({
                            'task_type': task_type,
                            'command': command
                        })
                    else:
                        validation_results['invalid'].append({
                            'task_type': task_type,
                            'command': command,
                            'reason': '패턴 불일치'
                        })

            # 필수 명령어 확인
            for task_type, task_info in VENDOR_PATTERNS[self.vendor].items():
                required_patterns = task_info['patterns']
                found_patterns = set()

                for command in learned_data.get(task_type, []):
                    for pattern in required_patterns:
                        if re.match(pattern, command):
                            found_patterns.add(pattern)

                missing_patterns = set(required_patterns) - found_patterns
                if missing_patterns:
                    validation_results['warnings'].append({
                        'task_type': task_type,
                        'missing_patterns': list(missing_patterns)
                    })

            return validation_results

        except Exception as e:
            self.logger.error(f'명령어 검증 중 오류: {str(e)}')
            raise 