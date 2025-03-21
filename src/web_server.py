from flask import Flask, render_template, request, jsonify, send_from_directory, url_for, Response
import os
import json
import logging
from config_manager import ConfigManager
import hashlib
from datetime import datetime
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException, AuthenticationException
import time
import requests
from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="static")
config_manager = ConfigManager()

# 개발 중 캐시 비활성화
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# 정적 파일에 버전 추가
@app.after_request
def add_header(response):
    # 문자 인코딩 설정
    if 'text/html' in response.headers['Content-Type']:
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
    
    # 캐시 제어
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/favicon.ico')
def favicon():
    """브라우저에서 요청하는 favicon.ico 제공"""
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root():
    """프로젝트 루트 디렉토리 경로 반환"""
    return os.path.dirname(os.path.abspath(__file__))

def ensure_directories():
    """필요한 디렉토리 생성"""
    root_dir = get_project_root()
    directories = ['tasks', 'logs', 'static', 'templates']
    
    for directory in directories:
        dir_path = os.path.join(root_dir, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"디렉토리 생성됨: {dir_path}")
        else:
            logger.debug(f"디렉토리 이미 존재함: {dir_path}")

def get_tasks_dir():
    """tasks 디렉토리의 절대 경로를 반환"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tasks_dir = os.path.join(current_dir, 'tasks')
    if not os.path.exists(tasks_dir):
        os.makedirs(tasks_dir)
        logger.info(f"tasks 디렉토리 생성: {tasks_dir}")
    return tasks_dir

# 장비 정보 저장 경로
DEVICES_FILE = 'devices.json'

def load_devices():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_devices(devices):
    with open(DEVICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(devices, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/device/save', methods=['POST'])
def save_device():
    try:
        # 1. 데이터 받기
        data = request.json
        print("받은 데이터:", data)  # 디버깅용
        
        # 2. tasks 폴더 생성 (없는 경우)
        tasks_dir = os.path.join(os.getcwd(), 'tasks')
        if not os.path.exists(tasks_dir):
            os.makedirs(tasks_dir)
            print(f"tasks 폴더 생성됨: {tasks_dir}")
        
        # 3. 파일명 생성 (장비명.json)
        filename = f"{data['device_name']}_config.json"
        file_path = os.path.join(tasks_dir, filename)
        
        # 4. JSON 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"파일 저장됨: {file_path}")
        
        return jsonify({
            'success': True,
            'message': '설정이 저장되었습니다.',
            'file_path': file_path
        })
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'저장 중 오류 발생: {str(e)}'
        }), 500

@app.route('/api/devices', methods=['GET'])
def get_devices():
    try:
        if not os.path.exists('device_scripts'):
            return jsonify({'status': 'success', 'data': []})
        
        devices = []
        for filename in os.listdir('device_scripts'):
            if filename.endswith('_script.json'):
                file_path = os.path.join('device_scripts', filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        script_data = json.load(f)
                        if 'device_info' in script_data:
                            devices.append(script_data['device_info'])
                except Exception as e:
                    print(f"파일 읽기 오류 ({filename}): {str(e)}")
                    continue
        
        return jsonify({'status': 'success', 'data': devices})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/device/delete/<device_name>', methods=['DELETE'])
def delete_device(device_name):
    try:
        # tasks 디렉토리 경로
        tasks_dir = os.path.join(os.getcwd(), 'tasks')
        
        # 해당 장비의 설정 파일 찾기
        config_file = f"{device_name}_config.json"
        file_path = os.path.join(tasks_dir, config_file)
        
        # 파일이 존재하면 삭제
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({
                'success': True,
                'message': '장비 정보가 삭제되었습니다.'
            })
        else:
            return jsonify({
                'success': False,
                'message': '해당 장비 정보를 찾을 수 없습니다.'
            }), 404
            
    except Exception as e:
        print(f"삭제 중 오류 발생: {str(e)}")  # 디버깅용 로그
        return jsonify({
            'success': False,
            'message': f'삭제 중 오류가 발생했습니다: {str(e)}'
        }), 500

def get_file_hash(filepath):
    """파일의 해시값 생성"""
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    return ''

@app.context_processor
def utility_processor():
    """템플릿에서 사용할 유틸리티 함수"""
    def versioned_static(filename):
        filepath = os.path.join(app.static_folder, filename)
        file_hash = get_file_hash(filepath)
        return url_for('static', filename=filename, v=file_hash)
    return dict(versioned_static=versioned_static)

@app.route('/api/config/save', methods=['POST'])
def save_config():
    try:
        config = request.json
        
        # 필수 필드 검증
        required_fields = ['vendor', 'task_type', 'vlan_id', 'interface', 
                         'host', 'username', 'password', 'secret']
        for field in required_fields:
            if not config.get(field):
                return jsonify({'error': f'필수 필드 누락: {field}'}), 400
        
        # VLAN ID 유효성 검사
        vlan_id = int(config['vlan_id'])
        if not 1 <= vlan_id <= 4094:
            return jsonify({'error': 'VLAN ID는 1-4094 사이의 값이어야 합니다'}), 400
        
        # 설정 파일 저장
        device_name = config['host'].replace('.', '_')
        config_path = os.path.join('config', f'{device_name}_config.json')
        
        # 디렉토리가 없으면 생성
        os.makedirs('config', exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        return jsonify({'message': '설정이 성공적으로 저장되었습니다'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/device/execute/<device_name>', methods=['POST'])
def execute_device_config(device_name):
    try:
        # 장비 설정 파일 읽기
        config_file = os.path.join('tasks', f'{device_name}_config.json')
        if not os.path.exists(config_file):
            return jsonify({
                'success': False,
                'message': '장비 설정 파일을 찾을 수 없습니다.'
            }), 404

        with open(config_file, 'r', encoding='utf-8') as f:
            device_info = json.load(f)

        # SSH 클라이언트 설정
        # ssh = paramiko.SSHClient()
        # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # SSH 연결
            # ssh.connect(
            #     device_info['ip_address'],
            #     username=device_info['username'],
            #     password=device_info['password'],
            #     look_for_keys=False,
            #     allow_agent=False
            # )

            # 장비 벤더별 명령어 생성
            commands = generate_commands(device_info)
            
            # 명령어 실행
            for cmd in commands:
                # stdin, stdout, stderr = ssh.exec_command(cmd)
                print(f"실행 명령어: {cmd}")
                # print(f"출력: {stdout.read().decode()}")
                # print(f"에러: {stderr.read().decode()}")

            return jsonify({
                'success': True,
                'message': '설정이 성공적으로 실행되었습니다.'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'설정 실행 중 오류: {str(e)}'
            }), 500

        # finally:
        #     ssh.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}'
        }), 500

def generate_commands(device_info):
    """장비 벤더와 작업 유형에 따른 명령어 생성"""
    commands = []
    vendor = device_info['vendor'].lower()
    tasks = device_info['tasks']

    if vendor == 'cisco':
        commands.append('enable')
        commands.append('configure terminal')
        
        for task in tasks:
            if task == 'VLAN 설정':
                commands.extend([
                    'vlan 10',
                    'name TEST_VLAN',
                    'exit'
                ])
            elif task == '인터페이스 설정':
                commands.extend([
                    'interface GigabitEthernet1/0/1',
                    'switchport mode access',
                    'switchport access vlan 10',
                    'no shutdown',
                    'exit'
                ])
            elif task == 'IP 설정':
                commands.extend([
                    'interface Vlan10',
                    'ip address 192.168.10.1 255.255.255.0',
                    'no shutdown',
                    'exit'
                ])

        commands.append('end')
        commands.append('write memory')

    # 다른 벤더에 대한 명령어도 추가 가능

    return commands

# 서버 시작 시 디렉토리 생성
ensure_directories()

# CLI 관련 API 추가
@app.route('/api/cli/vendors', methods=['GET'])
def get_cli_vendors():
    vendors = ['Cisco', 'Juniper', 'HP', 'Arista', '코어앤지 네트웍스', '윈드리버']
    return jsonify({
        'success': True,
        'vendors': vendors
    })

@app.route('/cli/learn', methods=['POST'])
def cli_learn():
    try:
        data = request.get_json()
        vendor = data.get('vendor')
        task_type = data.get('taskType')
        commands = data.get('commands', [])

        if not vendor or not task_type:
            return jsonify({'status': 'error', 'message': '벤더와 작업 유형은 필수입니다.'})

        # 벤더별 학습 파일 경로
        learned_file = os.path.join('tasks', f'{vendor}_learned_commands.json')
        
        # 기존 학습 데이터 로드 또는 새로 생성
        if os.path.exists(learned_file):
            with open(learned_file, 'r', encoding='utf-8') as f:
                learned_data = json.load(f)
        else:
            learned_data = {}

        # 새로운 명령어 저장
        learned_data[task_type] = commands

        # 학습 데이터 저장
        with open(learned_file, 'w', encoding='utf-8') as f:
            json.dump(learned_data, f, indent=2, ensure_ascii=False)

        return jsonify({'status': 'success', 'message': '명령어가 학습되었습니다.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/cli/generate', methods=['POST'])
def generate_cli_script():
    try:
        # CLI 스크립트 자동 생성 로직
        # 여기에 실제 스크립트 생성 로직 구현
        return jsonify({
            'success': True,
            'script': '생성된 CLI 스크립트 내용'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/cli/auto-learn', methods=['POST'])
def auto_learn_cli():
    try:
        data = request.get_json()
        print("받은 데이터:", data)  # 디버깅용 로그
        
        vendor = data.get('vendor')
        task_type = data.get('task_type')
        
        if not vendor or not task_type:
            return jsonify({
                'success': False,
                'message': '벤더와 작업 유형을 지정해주세요.'
            }), 400

        # 벤더별 기본 명령어 템플릿
        vendor_templates = {
            'cisco': {
                'VLAN 설정': [
                    "configure terminal",
                    "vlan {vlan_id}",
                    "name {vlan_name}",
                    "exit",
                    "end"
                ],
                'IP 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "ip address {ip_address} {subnet_mask}",
                    "no shutdown",
                    "exit",
                    "end"
                ],
                '인터페이스 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "description {description}",
                    "switchport mode access",
                    "switchport access vlan {vlan_id}",
                    "no shutdown",
                    "exit",
                    "end"
                ],
                'OSPF 설정': [
                    "configure terminal",
                    "router ospf {process_id}",
                    "network {network} area {area}",
                    "exit",
                    "end"
                ],
                'BGP 설정': [
                    "configure terminal",
                    "router bgp {as_number}",
                    "neighbor {neighbor_ip} remote-as {remote_as}",
                    "network {network} mask {subnet_mask}",
                    "exit",
                    "end"
                ],
                'ACL 설정': [
                    "configure terminal",
                    "ip access-list {acl_type} {acl_number}",
                    "{action} {source} {destination}",
                    "exit",
                    "end"
                ],
                '포트 보안 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "switchport port-security",
                    "switchport port-security maximum {max_mac}",
                    "switchport port-security violation {violation_action}",
                    "exit",
                    "end"
                ],
                'SNMP 설정': [
                    "configure terminal",
                    "snmp-server community {community_string} {permission}",
                    "snmp-server location {location}",
                    "snmp-server contact {contact}",
                    "end"
                ],
                'Syslog 설정': [
                    "configure terminal",
                    "logging host {syslog_server}",
                    "logging trap {logging_level}",
                    "logging facility {facility_type}",
                    "end"
                ],
                'STP 설정': [
                    "configure terminal",
                    "spanning-tree mode {stp_mode}",
                    "spanning-tree vlan {vlan_id} priority {priority}",
                    "end"
                ],
                'HSRP 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "standby {group_number} ip {virtual_ip}",
                    "standby {group_number} priority {priority}",
                    "standby {group_number} preempt",
                    "exit",
                    "end"
                ]
            },
            'juniper': {
                'VLAN 설정': [
                    "configure",
                    "set vlans {vlan_name} vlan-id {vlan_id}",
                    "commit",
                    "exit"
                ],
                'IP 설정': [
                    "configure",
                    "set interfaces {interface} unit 0 family inet address {ip_address}/{subnet_mask}",
                    "commit",
                    "exit"
                ],
                '인터페이스 설정': [
                    "configure",
                    "set interfaces {interface} description \"{description}\"",
                    "set interfaces {interface} unit 0 family ethernet-switching vlan members {vlan_id}",
                    "commit",
                    "exit"
                ],
                'OSPF 설정': [
                    "configure",
                    "set protocols ospf area {area} interface {interface}",
                    "set protocols ospf area {area} interface {interface} metric {metric}",
                    "commit",
                    "exit"
                ],
                'BGP 설정': [
                    "configure",
                    "set protocols bgp group {group_name} type external",
                    "set protocols bgp group {group_name} peer-as {remote_as}",
                    "set protocols bgp group {group_name} neighbor {neighbor_ip}",
                    "commit",
                    "exit"
                ],
                'ACL 설정': [
                    "configure",
                    "set firewall family inet filter {acl_name} term {term_name}",
                    "set firewall family inet filter {acl_name} term {term_name} from {source}",
                    "set firewall family inet filter {acl_name} term {term_name} then {action}",
                    "commit",
                    "exit"
                ],
                'SNMP 설정': [
                    "configure",
                    "set snmp community {community_string} authorization {permission}",
                    "set snmp location {location}",
                    "set snmp contact {contact}",
                    "commit",
                    "exit"
                ],
                'Syslog 설정': [
                    "configure",
                    "set system syslog host {syslog_server} facility {facility_type} level {logging_level}",
                    "commit",
                    "exit"
                ],
                'STP 설정': [
                    "configure",
                    "set protocols {stp_mode}",
                    "set protocols {stp_mode} interface {interface} priority {priority}",
                    "commit",
                    "exit"
                ]
            },
            'hp': {
                'VLAN 설정': [
                    "configure terminal",
                    "vlan {vlan_id}",
                    "name {vlan_name}",
                    "exit",
                    "end"
                ],
                'IP 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "ip address {ip_address} {subnet_mask}",
                    "no shutdown",
                    "exit",
                    "end"
                ],
                '인터페이스 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "description {description}",
                    "switchport mode access",
                    "switchport access vlan {vlan_id}",
                    "no shutdown",
                    "exit",
                    "end"
                ],
                'OSPF 설정': [
                    "configure terminal",
                    "router ospf {process_id}",
                    "network {network} area {area}",
                    "exit",
                    "end"
                ],
                'BGP 설정': [
                    "configure terminal",
                    "router bgp {as_number}",
                    "neighbor {neighbor_ip} remote-as {remote_as}",
                    "network {network} mask {subnet_mask}",
                    "exit",
                    "end"
                ],
                'ACL 설정': [
                    "configure terminal",
                    "ip access-list {acl_type} {acl_number}",
                    "{action} {source} {destination}",
                    "exit",
                    "end"
                ],
                '포트 보안 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "switchport port-security",
                    "switchport port-security maximum {max_mac}",
                    "switchport port-security violation {violation_action}",
                    "exit",
                    "end"
                ],
                'SNMP 설정': [
                    "configure terminal",
                    "snmp-server community {community_string} {permission}",
                    "snmp-server location {location}",
                    "snmp-server contact {contact}",
                    "end"
                ],
                'Syslog 설정': [
                    "configure terminal",
                    "logging host {syslog_server}",
                    "logging trap {logging_level}",
                    "logging facility {facility_type}",
                    "end"
                ],
                'STP 설정': [
                    "configure terminal",
                    "spanning-tree mode {stp_mode}",
                    "spanning-tree vlan {vlan_id} priority {priority}",
                    "end"
                ],
                'HSRP 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "standby {group_number} ip {virtual_ip}",
                    "standby {group_number} priority {priority}",
                    "standby {group_number} preempt",
                    "exit",
                    "end"
                ]
            },
            'arista': {
                'VLAN 설정': [
                    "configure terminal",
                    "vlan {vlan_id}",
                    "name {vlan_name}",
                    "exit",
                    "end"
                ],
                'IP 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "ip address {ip_address} {subnet_mask}",
                    "no shutdown",
                    "exit",
                    "end"
                ],
                '인터페이스 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "description {description}",
                    "switchport mode access",
                    "switchport access vlan {vlan_id}",
                    "no shutdown",
                    "exit",
                    "end"
                ],
                'OSPF 설정': [
                    "configure terminal",
                    "router ospf {process_id}",
                    "network {network} area {area}",
                    "exit",
                    "end"
                ],
                'BGP 설정': [
                    "configure terminal",
                    "router bgp {as_number}",
                    "neighbor {neighbor_ip} remote-as {remote_as}",
                    "network {network} mask {subnet_mask}",
                    "exit",
                    "end"
                ],
                'ACL 설정': [
                    "configure terminal",
                    "ip access-list {acl_type} {acl_number}",
                    "{action} {source} {destination}",
                    "exit",
                    "end"
                ],
                '포트 보안 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "switchport port-security",
                    "switchport port-security maximum {max_mac}",
                    "switchport port-security violation {violation_action}",
                    "exit",
                    "end"
                ],
                'SNMP 설정': [
                    "configure terminal",
                    "snmp-server community {community_string} {permission}",
                    "snmp-server location {location}",
                    "snmp-server contact {contact}",
                    "end"
                ],
                'Syslog 설정': [
                    "configure terminal",
                    "logging host {syslog_server}",
                    "logging trap {logging_level}",
                    "logging facility {facility_type}",
                    "end"
                ],
                'STP 설정': [
                    "configure terminal",
                    "spanning-tree mode {stp_mode}",
                    "spanning-tree vlan {vlan_id} priority {priority}",
                    "end"
                ],
                'HSRP 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "standby {group_number} ip {virtual_ip}",
                    "standby {group_number} priority {priority}",
                    "standby {group_number} preempt",
                    "exit",
                    "end"
                ]
            },
            'handreamnet': {
                'VLAN 설정': [
                    "config terminal",
                    "vlan database",
                    "vlan {vlan_id} name {vlan_name}",
                    "exit",
                    "exit"
                ],
                'IP 설정': [
                    "config terminal",
                    "interface {interface}",
                    "ip address {ip_address} {subnet_mask}",
                    "no shutdown",
                    "exit",
                    "exit"
                ],
                '인터페이스 설정': [
                    "config terminal",
                    "interface {interface}",
                    "description {description}",
                    "switchport mode access",
                    "switchport access vlan {vlan_id}",
                    "no shutdown",
                    "exit",
                    "exit"
                ],
                'OSPF 설정': [
                    "config terminal",
                    "router ospf {process_id}",
                    "network {network} area {area}",
                    "exit",
                    "exit"
                ],
                'BGP 설정': [
                    "config terminal",
                    "router bgp {as_number}",
                    "neighbor {neighbor_ip} remote-as {remote_as}",
                    "network {network}",
                    "exit",
                    "exit"
                ],
                'ACL 설정': [
                    "config terminal",
                    "access-list {acl_number} {action} {source}",
                    "exit"
                ],
                '포트 보안 설정': [
                    "config terminal",
                    "interface {interface}",
                    "port security",
                    "port security maximum {max_mac}",
                    "port security violation {violation_action}",
                    "exit",
                    "exit"
                ],
                'SNMP 설정': [
                    "config terminal",
                    "snmp-server community {community_string} {permission}",
                    "snmp-server location {location}",
                    "snmp-server contact {contact}",
                    "exit"
                ],
                'Syslog 설정': [
                    "config terminal",
                    "logging {syslog_server}",
                    "logging level {logging_level}",
                    "logging facility {facility_type}",
                    "exit"
                ],
                'STP 설정': [
                    "config terminal",
                    "spanning-tree mode {stp_mode}",
                    "spanning-tree vlan {vlan_id} priority {priority}",
                    "exit"
                ],
                'HSRP 설정': [
                    "config terminal",
                    "interface {interface}",
                    "standby {group_number} ip {virtual_ip}",
                    "standby {group_number} priority {priority}",
                    "standby {group_number} preempt",
                    "exit",
                    "exit"
                ]
            },
            'coreedge': {
                'VLAN 설정': [
                    "configure terminal",
                    "vlan {vlan_id}",
                    "name {vlan_name}",
                    "exit",
                    "end"
                ],
                'IP 설정': [
                    "configure terminal",
                    'interface {interface}',
                    'ip address {ip_address} {subnet_mask}',
                    'no shutdown',
                    'exit',
                    'end'
                ],
                '인터페이스 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "description {description}",
                    "switchport mode access",
                    "switchport access vlan {vlan_id}",
                    "no shutdown",
                    "exit",
                    "end"
                ],
                'OSPF 설정': [
                    "configure terminal",
                    "router ospf {process_id}",
                    "network {network} area {area}",
                    "exit",
                    "end"
                ],
                'BGP 설정': [
                    "configure terminal",
                    "router bgp {as_number}",
                    "neighbor {neighbor_ip} remote-as {remote_as}",
                    "network {network} mask {subnet_mask}",
                    "exit",
                    "end"
                ],
                'ACL 설정': [
                    "configure terminal",
                    "ip access-list {acl_type} {acl_name}",
                    "{action} {source} {destination}",
                    "exit",
                    "end"
                ],
                '포트 보안 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "switchport port-security",
                    "switchport port-security maximum {max_mac}",
                    "switchport port-security violation {violation_action}",
                    "exit",
                    "end"
                ],
                'SNMP 설정': [
                    "configure terminal",
                    "snmp-server community {community_string} {permission}",
                    "snmp-server location {location}",
                    "snmp-server contact {contact}",
                    "end"
                ],
                'Syslog 설정': [
                    "configure terminal",
                    "logging host {syslog_server}",
                    "logging trap {logging_level}",
                    "logging facility {facility_type}",
                    "end"
                ],
                'STP 설정': [
                    "configure terminal",
                    "spanning-tree mode {stp_mode}",
                    "spanning-tree vlan {vlan_id} priority {priority}",
                    "end"
                ],
                'HSRP 설정': [
                    "configure terminal",
                    "interface {interface}",
                    "standby {group_number} ip {virtual_ip}",
                    "standby {group_number} priority {priority}",
                    "standby {group_number} preempt",
                    "exit",
                    "end"
                ]
            }
        }

        # tasks 디렉토리 확인 및 생성
        tasks_dir = os.path.join(os.getcwd(), 'tasks')
        if not os.path.exists(tasks_dir):
            os.makedirs(tasks_dir)
            print(f"tasks 디렉토리 생성됨: {tasks_dir}")  # 디버깅용 로그

        # 벤더별 파일 경로
        vendor_file = os.path.join(tasks_dir, f'{vendor.lower()}_learned_commands.json')
        print(f"저장할 파일 경로: {vendor_file}")  # 디버깅용 로그

        # 기존 데이터 로드 또는 새로 생성
        try:
            if os.path.exists(vendor_file):
                with open(vendor_file, 'r', encoding='utf-8') as f:
                    learned_data = json.load(f)
                    print("기존 데이터 로드됨")  # 디버깅용 로그
            else:
                learned_data = {'tasks': {}}
                print("새 데이터 구조 생성됨")  # 디버깅용 로그
        except Exception as e:
            print(f"파일 로드 중 오류: {str(e)}")  # 디버깅용 로그
            learned_data = {'tasks': {}}

        # 템플릿에서 해당 작업 유형의 명령어 가져오기
        if vendor.lower() in vendor_templates and task_type in vendor_templates[vendor.lower()]:
            commands = vendor_templates[vendor.lower()][task_type]
            
            # 학습 데이터 업데이트
            learned_data['tasks'][task_type] = {
                'commands': commands,
                'learned_at': datetime.now().isoformat()
            }

            # 파일 저장
            try:
                with open(vendor_file, 'w', encoding='utf-8') as f:
                    json.dump(learned_data, f, indent=2, ensure_ascii=False)
                print(f"데이터 저장됨: {vendor_file}")  # 디버깅용 로그
            except Exception as e:
                print(f"파일 저장 중 오류: {str(e)}")  # 디버깅용 로그
                raise

            return jsonify({
                'success': True,
                'message': '자동 학습이 완료되었습니다.',
                'results': commands
            })
        else:
            return jsonify({
                'success': False,
                'message': f'{vendor}의 {task_type}에 대한 템플릿이 없습니다.'
            }), 404

    except Exception as e:
        print(f"자동 학습 중 오류: {str(e)}")  # 디버깅용 로그
        return jsonify({
            'success': False,
            'message': f'자동 학습 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/cli/doc-learn', methods=['POST'])
def doc_learn_cli():
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '파일이 업로드되지 않았습니다.'
            }), 400

        file = request.files['file']
        vendor = request.form.get('vendor')
        task_type = request.form.get('task_type')

        if not file.filename or not vendor or not task_type:
            return jsonify({
                'success': False,
                'message': '필수 정보가 누락되었습니다.'
            }), 400

        # 문서 학습 로직 구현
        # TODO: 실제 문서 분석 및 학습 로직 구현 필요
        learned_commands = []  # 임시 결과

        return jsonify({
            'success': True,
            'message': '문서 학습이 완료되었습니다.',
            'results': learned_commands
        })

    except Exception as e:
        print(f"문서 학습 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'문서 학습 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/cli/learned', methods=['GET'])
def get_learned_commands():
    try:
        tasks_dir = os.path.join(os.getcwd(), 'tasks')
        learned_commands = {}

        if os.path.exists(tasks_dir):
            for filename in os.listdir(tasks_dir):
                if filename.endswith('_learned_commands.json'):
                    vendor = filename.replace('_learned_commands.json', '')
                    with open(os.path.join(tasks_dir, filename), 'r', encoding='utf-8') as f:
                        learned_commands[vendor] = json.load(f)

        return jsonify({
            'success': True,
            'learned_commands': learned_commands
        })

    except Exception as e:
        print(f"학습된 명령어 조회 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'학습된 명령어 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/cli/auto-learning', methods=['GET'])
def start_cli_auto_learning():
    def generate_learning_progress():
        # 벤더 목록 업데이트
        vendors = [
            'cisco',
            'juniper', 
            'hp', 
            'arista', 
            'coreedge', 
            'handreamnet'
        ]
        total_vendors = len(vendors)
        
        for idx, vendor in enumerate(vendors, 1):
            progress = (idx / total_vendors) * 100
            
            try:
                logger.info(f"수집 시작: {vendor}")
                # collect_vendor_manuals(vendor)
                
                data = {
                    'progress': progress,
                    'status': f'{vendor.upper()} CLI 명령어 수집 및 학습 중... ({idx}/{total_vendors})'
                }
                yield f"data: {json.dumps(data)}\n\n"
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"{vendor} 학습 중 오류: {str(e)}")
                data = {
                    'progress': progress,
                    'status': f'{vendor.upper()} 처리 중 오류 발생'
                }
                yield f"data: {json.dumps(data)}\n\n"

        yield f"data: {json.dumps({'progress': 100, 'status': '모든 벤더 학습 완료'})}\n\n"

    return Response(generate_learning_progress(), mimetype='text/event-stream')

def collect_vendor_manuals(vendor):
    """벤더별 매뉴얼 수집 및 학습 함수"""
    # 벤더별 매뉴얼 검색 URL 설정
    search_urls = {
        'cisco': 'https://www.cisco.com/c/en/us/support/all-products.html',
        'juniper': 'https://www.juniper.net/documentation/product/en_US/all-products',
        'hp': 'https://support.hpe.com/hpesc/public/home/documentHome',
        'arista': 'https://www.arista.com/en/support/product-documentation',
        # 다른 벤더 URL 추가
    }
    
    try:
        if vendor in search_urls:
            # 매뉴얼 페이지 요청
            response = requests.get(search_urls[vendor])
            response.raise_for_status()
            
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 매뉴얼 데이터 추출 및 저장
            save_manual_data(vendor, soup)
            
    except Exception as e:
        print(f"Error collecting manuals for {vendor}: {str(e)}")
        raise

def save_manual_data(vendor, soup):
    """수집된 매뉴얼 데이터 저장"""
    # 벤더별 데이터 저장 디렉토리 생성
    vendor_dir = os.path.join('cli_learning', vendor)
    os.makedirs(vendor_dir, exist_ok=True)
    
    # 매뉴얼 데이터 파일 저장
    with open(os.path.join(vendor_dir, 'manual_data.json'), 'w', encoding='utf-8') as f:
        json.dump({
            'vendor': vendor,
            'collected_at': datetime.now().isoformat(),
            'data': str(soup)
        }, f, ensure_ascii=False, indent=2)

@app.route('/api/cli/upload-docs', methods=['POST'])
def upload_cli_docs():
    try:
        vendor = request.form.get('vendor')
        if not vendor:
            return jsonify({
                'success': False,
                'message': '벤더 정보가 없습니다.'
            }), 400

        files = request.files.getlist('documents')
        if not files:
            return jsonify({
                'success': False,
                'message': '업로드된 파일이 없습니다.'
            }), 400

        # 벤더별 문서 저장 디렉토리
        upload_dir = os.path.join('cli_learning', vendor, 'user_uploads')
        os.makedirs(upload_dir, exist_ok=True)

        # 파일 저장 및 처리
        for file in files:
            if file.filename:
                file_path = os.path.join(upload_dir, secure_filename(file.filename))
                file.save(file_path)

        return jsonify({
            'success': True,
            'message': f'{len(files)}개의 문서가 업로드되어 학습되었습니다.'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 지원하는 벤더 목록
SUPPORTED_VENDORS = [
    'cisco',
    'juniper',
    'hp',
    'arista',
    'coreedge',
    'handreamnet'
]

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    return jsonify(SUPPORTED_VENDORS)

# 스크립트 저장 디렉토리
SCRIPTS_DIR = 'device_scripts'
os.makedirs(SCRIPTS_DIR, exist_ok=True)

def get_vendor_commands(vendor, tasks):
    """벤더별 명령어 템플릿을 가져오는 함수"""
    try:
        template_path = os.path.join(os.getcwd(), 'tasks', 'vendor_templates', f'{vendor.lower()}_template.json')
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            return templates
        return None
    except Exception as e:
        print(f"템플릿 로드 중 오류: {str(e)}")
        return None

def get_learned_commands(vendor, task_type):
    """CLI 학습 결과에서 벤더별 명령어를 가져오는 함수"""
    try:
        # tasks 폴더에서 해당 벤더의 학습된 명령어 파일 찾기
        vendor_files = [f for f in os.listdir('tasks') if f.startswith(vendor.lower()) and f.endswith('_config.json')]
        
        for file_name in vendor_files:
            with open(os.path.join('tasks', file_name), 'r', encoding='utf-8') as f:
                learned_data = json.load(f)
                # tasks 키가 있고, 요청된 task_type이 있는 경우
                if 'tasks' in learned_data and task_type in learned_data['tasks']:
                    return learned_data['tasks'][task_type]
        return None
    except Exception as e:
        print(f"학습된 명령어 로드 중 오류: {str(e)}")
        return None

def generate_cisco_commands(category, config_data):
    commands = []
    
    if category == 'basic':
        if config_data.get('sshEnable'):
            commands.extend([
                'ip ssh version 2',
                'crypto key generate rsa general-keys modulus 2048'
            ])
        if config_data.get('writeMemory'):
            commands.append('write memory')

    elif category == 'vlan':
        action = config_data.get('action')
        vlan_id = config_data.get('id')
        vlan_name = config_data.get('name')
        
        if action == 'create':
            commands.extend([
                f'vlan {vlan_id}',
                f'name {vlan_name}'
            ])
        elif action == 'delete':
            commands.append(f'no vlan {vlan_id}')
        elif action == 'modify':
            commands.extend([
                f'vlan {vlan_id}',
                f'name {vlan_name}'
            ])

    elif category == 'port':
        port_name = config_data.get('name')
        status = config_data.get('status')
        commands.extend([
            f'interface {port_name}',
            'no shutdown' if status == 'up' else 'shutdown'
        ])

    elif category == 'routing':
        if config_data.get('type') == 'static':
            network = config_data.get('network')
            mask = config_data.get('mask')
            next_hop = config_data.get('nextHop')
            commands.append(f'ip route {network} {mask} {next_hop}')
        elif config_data.get('type') == 'ospf':
            process_id = config_data.get('processId')
            network = config_data.get('network')
            wildcard = config_data.get('wildcard')
            area = config_data.get('area')
            commands.extend([
                f'router ospf {process_id}',
                f'network {network} {wildcard} area {area}'
            ])

    elif category == 'security':
        if config_data.get('portSecurity'):
            interface = config_data.get('interface')
            commands.extend([
                f'interface {interface}',
                'switchport port-security',
                f'switchport port-security maximum {config_data.get("maxMac", 1)}'
            ])
        if config_data.get('aaa'):
            commands.extend([
                'aaa new-model',
                'aaa authentication login default local'
            ])

    elif category == 'stp':
        if config_data.get('mode') == 'rapid-pvst':
            commands.append('spanning-tree mode rapid-pvst')
        if config_data.get('portfast'):
            interface = config_data.get('interface')
            commands.extend([
                f'interface {interface}',
                'spanning-tree portfast'
            ])

    elif category == 'qos':
        if config_data.get('type') == 'rate-limiting':
            interface = config_data.get('interface')
            rate = config_data.get('rate')
            commands.extend([
                f'interface {interface}',
                f'srr-queue bandwidth limit {rate}'
            ])
        
    elif category == 'monitor':
            commands.extend([
            'show ip route',
            'show ip ospf neighbor',
            'show ip bgp summary'
            ])

    elif category == 'interface':
            commands.extend([
            'show interface status',
            'show interface description'
        ])

    elif category == 'logging':
        commands.append('show logging')
        if config_data.get('setup'):
            server = config_data.get('server')
            commands.extend([
                f'logging {server}',
                'logging trap notifications'
            ])

    elif category == 'backup':
        if config_data.get('action') == 'backup':
            commands.append('show running-config')
        elif config_data.get('action') == 'restore':
            commands.extend(config_data.get('config', '').split('\n'))

    elif category == 'snmp':
        if config_data.get('setup'):
            community = config_data.get('community')
            commands.extend([
                f'snmp-server community {community} RO',
                'snmp-server enable traps'
            ])

    elif category == 'script':
        # 사용자 정의 스크립트 실행
        if config_data.get('commands'):
            commands.extend(config_data.get('commands').split('\n'))

    return commands

@app.route('/api/generate_script', methods=['POST'])
def generate_script():
    try:
        data = request.json
        basic_info = data['basicInfo']
        category = data['category']
        config_data = data['configData']
        
        # 벤더별 명령어 생성
        if basic_info['vendor'].lower() == 'cisco':
            commands = generate_cisco_commands(category, config_data)
        else:
            return jsonify({
                'status': 'error',
                'message': '지원하지 않는 벤더입니다.'
            }), 400

        # 스크립트 파일 생성
        script_content = '\n'.join(commands)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"device_scripts/{basic_info['deviceName']}_{category}_{timestamp}_script.txt"
        
        os.makedirs('device_scripts', exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # 장비 정보와 스크립트 정보를 JSON으로 저장
        device_info = {
            'device_name': basic_info['deviceName'],
            'vendor': basic_info['vendor'],
            'ip_address': basic_info['ip'],
            'username': basic_info['username'],
            'password': basic_info['password'],
            'category': category,
            'script_file': filename,
            'config_data': config_data,
            'timestamp': timestamp
        }

        info_filename = f"device_scripts/{basic_info['deviceName']}_script.json"
        with open(info_filename, 'w', encoding='utf-8') as f:
            json.dump(device_info, f, indent=4, ensure_ascii=False)

        return jsonify({
            'status': 'success',
            'script': script_content,
            'filename': filename,
            'message': '스크립트가 성공적으로 생성되었습니다.'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'스크립트 생성 중 오류 발생: {str(e)}'
        }), 500

@app.route('/api/execute_script', methods=['POST'])
def execute_script():
    try:
        data = request.json
        device_info = {
            'device_type': 'cisco_ios' if data['vendor'].lower() == 'cisco' else 'juniper_junos',
            'host': data['ip_address'],
            'username': data['username'],
            'password': data['password'],
        }

        try:
            net_connect = ConnectHandler(**device_info)
            commands = data['script'].split('\n')

            output = net_connect.send_config_set(commands)
            net_connect.save_config()
            net_connect.disconnect()

            # 실행 결과 로그 저장
            log_filename = f"logs/{data['deviceName']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_execution.log"
            os.makedirs('logs', exist_ok=True)
            with open(log_filename, 'w', encoding='utf-8') as f:
                f.write(output)

            return jsonify({
                'status': 'success',
                'message': '스크립트가 성공적으로 실행되었습니다.',
                'output': output
            })

        except NetMikoTimeoutException:
            return jsonify({
                'status': 'error',
                'message': '장비 연결 시간 초과'
            }), 400
        except AuthenticationException:
            return jsonify({
                'status': 'error',
                'message': '인증 실패'
            }), 401

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'스크립트 실행 중 오류 발생: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
