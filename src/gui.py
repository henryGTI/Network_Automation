import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter.font import Font
from executor import Executor
from network_config_manager import NetworkConfigManager
from config_manager import ConfigManager
from script_generator import ScriptGenerator
from executor import NetworkExecutor
from log_manager import LogManager
import threading
import queue
import os
import json
from datetime import datetime

class NetworkAutomationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("네트워크 자동화 설정")
        self.root.geometry("1200x800")
        
        # 상태 변수 초기화
        self.status_var = tk.StringVar(value="대기 중...")
        self.progress_var = tk.DoubleVar(value=0)
        self.conn_type = tk.StringVar(value="SSH")
        
        # 관리자 객체 초기화
        self.config_manager = ConfigManager()
        self.script_generator = ScriptGenerator(self.config_manager.load_cli_data())
        self.executor = NetworkExecutor()
        self.log_manager = LogManager()
        
        # 스크립트 저장 경로
        self.script_path = "tasks"
        if not os.path.exists(self.script_path):
            os.makedirs(self.script_path)
            
        # 실시간 로그 큐 추가
        self.log_queue = queue.Queue()
        self.start_log_monitor()
        
        # 현재 단계 추적
        self.current_step = 1
        
        # 메인 프레임
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill='both', expand=True)
        
        # 노트북(탭) 생성
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # 기본 정보 탭 생성
        self.setup_basic_info_tab()
        self.setup_config_tab()
        self.setup_execution_tab()
        self.setup_log_tab()
        
        # 로그 업데이트 시작
        self.update_log_display()
        
    def setup_basic_info_tab(self):
        """기본 정보 입력 탭"""
        basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(basic_frame, text='기본 정보')

        # 단계별 프레임 생성
        step1_frame = ttk.LabelFrame(basic_frame, text="1단계: 벤더 선택", padding="10")
        step1_frame.pack(fill='x', padx=5, pady=5)
        
        # 1단계: 벤더 선택
        ttk.Label(step1_frame, text="벤더:").pack(side='left', padx=5)
        self.vendor_var = tk.StringVar()
        vendor_combo = ttk.Combobox(step1_frame, 
                                  textvariable=self.vendor_var,
                                  values=["Cisco", "Juniper", "HP", "Arista"])
        vendor_combo.pack(side='left', padx=5)
        ttk.Button(step1_frame, text="다음", 
                  command=lambda: self.show_step(2)).pack(side='left', padx=5)

        # 2단계: 장비명
        self.step2_frame = ttk.LabelFrame(basic_frame, text="2단계: 장비명 입력", padding="10")
        ttk.Label(self.step2_frame, text="장비명:").pack(side='left', padx=5)
        self.device_name = ttk.Entry(self.step2_frame)
        self.device_name.pack(side='left', padx=5)
        ttk.Button(self.step2_frame, text="다음",
                  command=lambda: self.show_step(3)).pack(side='left', padx=5)

        # 3단계: 로그인 정보
        self.step3_frame = ttk.LabelFrame(basic_frame, text="3단계: 로그인 정보 입력", padding="10")
        login_frame = ttk.Frame(self.step3_frame)
        login_frame.pack(fill='x')
        
        ttk.Label(login_frame, text="ID:").grid(row=0, column=0, padx=5, pady=2)
        self.login_id = ttk.Entry(login_frame)
        self.login_id.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=2)
        self.login_pw = ttk.Entry(login_frame, show="*")
        self.login_pw.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Button(self.step3_frame, text="다음",
                  command=lambda: self.show_step(4)).pack(pady=5)

        # 4단계: IP 주소
        self.step4_frame = ttk.LabelFrame(basic_frame, text="4단계: IP 주소 입력", padding="10")
        ttk.Label(self.step4_frame, text="IP 주소:").pack(side='left', padx=5)
        self.ip_address = ttk.Entry(self.step4_frame)
        self.ip_address.pack(side='left', padx=5)
        ttk.Button(self.step4_frame, text="저장",
                  command=self.save_basic_info).pack(side='left', padx=5)

        # 초기 상태 설정 (2,3,4단계 숨김)
        self.step2_frame.pack_forget()
        self.step3_frame.pack_forget()
        self.step4_frame.pack_forget()

    def show_step(self, step):
        """단계 전환"""
        try:
            # 현재 단계 검증
            if step == 2:
                if not self.vendor_var.get():
                    raise ValueError("벤더를 선택해주세요.")
                self.step2_frame.pack(fill='x', padx=5, pady=5)
                
            elif step == 3:
                if not self.device_name.get():
                    raise ValueError("장비명을 입력해주세요.")
                self.step3_frame.pack(fill='x', padx=5, pady=5)
                
            elif step == 4:
                if not self.login_id.get() or not self.login_pw.get():
                    raise ValueError("로그인 정보를 모두 입력해주세요.")
                self.step4_frame.pack(fill='x', padx=5, pady=5)
                
        except ValueError as e:
            messagebox.showerror("입력 오류", str(e))

    def save_basic_info(self):
        """기본 정보 저장"""
        try:
            # IP 주소 검증
            if not self.ip_address.get():
                raise ValueError("IP 주소를 입력해주세요.")

            # 모든 정보 수집
            device_info = {
                'vendor': self.vendor_var.get(),
                'device_name': self.device_name.get(),
                'login_id': self.login_id.get(),
                'login_pw': self.login_pw.get(),
                'ip_address': self.ip_address.get()
            }

            # 스크립트 파일 생성
            script_file = f"tasks/{device_info['device_name']}_config.json"
            
            # 디렉토리 생성
            os.makedirs('tasks', exist_ok=True)
            
            # 기본 스크립트 구조 생성
            script_data = {
                'basic_info': device_info,
                'configurations': [],
                'created_at': datetime.now().isoformat()
            }
            
            # 스크립트 저장
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("성공", "기본 정보가 저장되었습니다.")
            
            # 설정 탭으로 자동 전환
            self.notebook.select(1)
            
        except Exception as e:
            messagebox.showerror("오류", str(e))

    def setup_config_tab(self):
        """설정 작업 탭"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text='설정 작업')
        
        # 작업 유형 선택 프레임
        type_frame = ttk.LabelFrame(config_frame, text="설정 작업 유형 선택", padding="10")
        type_frame.pack(fill='x', padx=5, pady=5)
        
        # 작업 유형 라디오 버튼
        self.config_type = tk.StringVar()
        self.config_types = [
            ("VLAN 설정", "vlan"),
            ("인터페이스 설정", "interface"),
            ("IP 설정", "ip"),
            ("라우팅 설정", "routing"),
            ("ACL 설정", "acl"),
            ("보안 설정", "security"),
            ("백업/복원", "backup")
        ]
        
        # 라디오 버튼을 2열로 배치
        for i, (text, value) in enumerate(self.config_types):
            radio = ttk.Radiobutton(
                type_frame, 
                text=text, 
                value=value,
                variable=self.config_type,
                command=self.show_config_form
            )
            radio.grid(row=i//2, column=i%2, sticky='w', padx=10, pady=5)
        
        # 설정 입력 프레임
        self.config_input_frame = ttk.LabelFrame(config_frame, text="설정 입력", padding="10")
        self.config_input_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 초기 안내 메시지
        ttk.Label(self.config_input_frame, 
                 text="위에서 설정 작업 유형을 선택해주세요.").pack(pady=20)

    def show_config_form(self):
        """선택된 설정 유형에 따른 입력 폼 표시"""
        # 기존 위젯 제거
        for widget in self.config_input_frame.winfo_children():
            widget.destroy()
        
        config_type = self.config_type.get()
        
        if config_type == "vlan":
            self.setup_vlan_form()
        elif config_type == "interface":
            self.setup_interface_form()
        elif config_type == "ip":
            self.setup_ip_form()
        elif config_type == "routing":
            self.setup_routing_form()
        elif config_type == "acl":
            self.setup_acl_form()
        elif config_type == "security":
            self.setup_security_form()
        elif config_type == "backup":
            self.setup_backup_form()

    def setup_vlan_form(self):
        """VLAN 설정 폼"""
        # VLAN ID
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="VLAN ID:").pack(side='left', padx=5)
        self.vlan_id = ttk.Entry(frame, width=10)
        self.vlan_id.pack(side='left', padx=5)
        
        # VLAN 이름
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="VLAN 이름:").pack(side='left', padx=5)
        self.vlan_name = ttk.Entry(frame, width=20)
        self.vlan_name.pack(side='left', padx=5)
        
        # 저장 버튼
        ttk.Button(self.config_input_frame, text="VLAN 설정 저장",
                  command=self.save_vlan_config).pack(pady=20)

    def setup_interface_form(self):
        """인터페이스 설정 폼"""
        # 인터페이스 선택
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="인터페이스:").pack(side='left', padx=5)
        self.interface = ttk.Entry(frame, width=20)
        self.interface.pack(side='left', padx=5)
        
        # 모드 선택
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="모드:").pack(side='left', padx=5)
        self.interface_mode = ttk.Combobox(frame, values=["access", "trunk"], width=10)
        self.interface_mode.pack(side='left', padx=5)
        
        # VLAN 설정
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="VLAN:").pack(side='left', padx=5)
        self.interface_vlan = ttk.Entry(frame, width=10)
        self.interface_vlan.pack(side='left', padx=5)
        
        # 저장 버튼
        ttk.Button(self.config_input_frame, text="인터페이스 설정 저장",
                  command=self.save_interface_config).pack(pady=20)

    def setup_ip_form(self):
        """IP 설정 폼"""
        # 인터페이스 선택
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="인터페이스:").pack(side='left', padx=5)
        self.ip_interface = ttk.Entry(frame, width=20)
        self.ip_interface.pack(side='left', padx=5)
        
        # IP 주소
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="IP 주소:").pack(side='left', padx=5)
        self.ip_address_config = ttk.Entry(frame, width=15)
        self.ip_address_config.pack(side='left', padx=5)
        
        # 서브넷 마스크
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="서브넷 마스크:").pack(side='left', padx=5)
        self.subnet_mask = ttk.Entry(frame, width=15)
        self.subnet_mask.pack(side='left', padx=5)
        
        # 저장 버튼
        ttk.Button(self.config_input_frame, text="IP 설정 저장",
                  command=self.save_ip_config).pack(pady=20)

    def setup_routing_form(self):
        """라우팅 설정 폼"""
        # 라우팅 프로토콜 선택
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="프로토콜:").pack(side='left', padx=5)
        self.routing_protocol = ttk.Combobox(frame, 
                                           values=["OSPF", "EIGRP", "BGP", "Static"],
                                           width=10)
        self.routing_protocol.pack(side='left', padx=5)
        
        # 네트워크 주소
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="네트워크:").pack(side='left', padx=5)
        self.network_address = ttk.Entry(frame, width=15)
        self.network_address.pack(side='left', padx=5)
        
        # 저장 버튼
        ttk.Button(self.config_input_frame, text="라우팅 설정 저장",
                  command=self.save_routing_config).pack(pady=20)

    def setup_acl_form(self):
        """ACL 설정 폼"""
        # ACL 번호/이름
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="ACL 번호/이름:").pack(side='left', padx=5)
        self.acl_name = ttk.Entry(frame, width=20)
        self.acl_name.pack(side='left', padx=5)
        
        # 규칙 설정
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="규칙:").pack(side='left', padx=5)
        self.acl_rule = ttk.Entry(frame, width=40)
        self.acl_rule.pack(side='left', padx=5)
        
        # 저장 버튼
        ttk.Button(self.config_input_frame, text="ACL 설정 저장",
                  command=self.save_acl_config).pack(pady=20)

    def setup_security_form(self):
        """보안 설정 폼"""
        # 인터페이스 선택
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="인터페이스:").pack(side='left', padx=5)
        self.security_interface = ttk.Entry(frame, width=20)
        self.security_interface.pack(side='left', padx=5)
        
        # MAC 주소 제한
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="최대 MAC 주소 수:").pack(side='left', padx=5)
        self.max_mac = ttk.Entry(frame, width=5)
        self.max_mac.pack(side='left', padx=5)
        
        # 위반 모드
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="위반 모드:").pack(side='left', padx=5)
        self.violation_mode = ttk.Combobox(frame, 
                                         values=["shutdown", "restrict", "protect"],
                                         width=10)
        self.violation_mode.pack(side='left', padx=5)
        
        # 저장 버튼
        ttk.Button(self.config_input_frame, text="보안 설정 저장",
                  command=self.save_security_config).pack(pady=20)

    def setup_backup_form(self):
        """백업/복원 설정 폼"""
        # 작업 선택
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        self.backup_type = tk.StringVar(value="backup")
        ttk.Radiobutton(frame, text="백업", value="backup",
                       variable=self.backup_type).pack(side='left', padx=5)
        ttk.Radiobutton(frame, text="복원", value="restore",
                       variable=self.backup_type).pack(side='left', padx=5)
        
        # 파일명
        frame = ttk.Frame(self.config_input_frame)
        frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame, text="파일명:").pack(side='left', padx=5)
        self.backup_filename = ttk.Entry(frame, width=30)
        self.backup_filename.pack(side='left', padx=5)
        
        # 실행 버튼
        ttk.Button(self.config_input_frame, text="백업/복원 실행",
                  command=self.execute_backup_restore).pack(pady=20)

    def setup_execution_tab(self):
        """실행 탭"""
        execution_frame = ttk.Frame(self.notebook)
        self.notebook.add(execution_frame, text='실행')
        
        # 장비 선택
        device_frame = ttk.LabelFrame(execution_frame, text="장비 선택", padding="10")
        device_frame.pack(fill='x', padx=5, pady=5)
        
        self.device_list = ttk.Combobox(device_frame)
        self.device_list.pack(side='left', padx=5)
        
        ttk.Button(device_frame, text="장비 목록 새로고침",
                  command=self.refresh_device_list).pack(side='left', padx=5)
        
        # 연결 방식 선택
        conn_frame = ttk.LabelFrame(execution_frame, text="연결 방식", padding="10")
        conn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Radiobutton(conn_frame, text="SSH", variable=self.conn_type,
                       value="SSH").pack(side='left', padx=5)
        ttk.Radiobutton(conn_frame, text="Console", variable=self.conn_type,
                       value="CONSOLE").pack(side='left', padx=5)
        
        # 실행 버튼
        ttk.Button(execution_frame, text="설정 실행",
                  command=self.execute_config).pack(pady=20)
        
        # 실행 상태 및 결과
        result_frame = ttk.LabelFrame(execution_frame, text="실행 상태 및 결과", padding="10")
        result_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 상태 표시
        ttk.Label(result_frame, textvariable=self.status_var).pack(pady=5)
        
        # 진행 상태 바
        self.progress_bar = ttk.Progressbar(
            result_frame, 
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill='x', padx=5, pady=5)
        
        # 결과 표시
        self.result_text = tk.Text(result_frame, height=15)
        self.result_text.pack(fill='both', expand=True, padx=5, pady=5)

    def execute_config(self):
        """설정 실행"""
        try:
            device_name = self.device_list.get()
            if not device_name:
                raise ValueError("장비를 선택해주세요.")
            
            # 실행 스레드 시작
            self.status_var.set("실행 준비 중...")
            self.progress_var.set(0)
            self.result_text.delete('1.0', 'end')
            
            threading.Thread(
                target=self._execute_config_thread,
                args=(device_name,),
                daemon=True
            ).start()
            
        except Exception as e:
            messagebox.showerror("오류", str(e))

    def _execute_config_thread(self, device_name):
        """설정 실행 스레드"""
        try:
            self.status_var.set("설정 실행 중...")
            self.progress_var.set(10)
            
            # 설정 실행
            results = self.executor.execute_device_config(
                device_name,
                self.conn_type.get()
            )
            
            # 결과 표시
            self.progress_var.set(50)
            self.result_text.insert('end', "=== 실행 결과 ===\n\n")
            
            for i, result in enumerate(results, 1):
                self.result_text.insert('end',
                    f"[{i}] 설정 유형: {result['type']}\n"
                    f"실행 시간: {result['timestamp']}\n"
                    f"실행 결과:\n{result['result']}\n"
                    f"{'-'*50}\n\n"
                )
                self.progress_var.set(50 + (i/len(results))*50)
            
            self.status_var.set("실행 완료")
            self.progress_var.set(100)
            
        except Exception as e:
            self.status_var.set("실행 실패")
            self.result_text.insert('end', f"\n오류 발생: {str(e)}\n")
            messagebox.showerror("실행 오류", str(e))

    def refresh_device_list(self):
        """장비 목록 새로고침"""
        try:
            devices = [f.split('_')[0] for f in os.listdir('tasks') 
                      if f.endswith('_config.json')]
            self.device_list['values'] = devices
            if devices:
                self.device_list.set(devices[0])
        except Exception as e:
            messagebox.showerror("오류", f"장비 목록 새로고침 실패: {str(e)}")

    def refresh_log(self):
        """로그 새로고침"""
        try:
            self.log_text.delete('1.0', 'end')
            logs = self.log_manager.get_recent_logs()
            for log in logs:
                self.log_text.insert('end', f"{log}\n")
        except Exception as e:
            messagebox.showerror("오류", f"로그 새로고침 실패: {str(e)}")

    def start_log_monitor(self):
        """실시간 로그 모니터링 시작"""
        def update_log():
            try:
                while True:
                    log = self.log_queue.get_nowait()
                    self.log_text.insert('end', f"{log}\n")
                    self.log_text.see('end')
            except queue.Empty:
                pass
            finally:
                self.root.after(100, update_log)
        
        update_log()

    def save_vlan_config(self):
        """VLAN 설정 저장"""
        try:
            # 입력값 검증
            if not self.vlan_id.get() or not self.vlan_name.get():
                raise ValueError("모든 필드를 입력해주세요.")

            # 기본 정보 가져오기
            device_info = self._get_device_info()
            
            # 설정 데이터 구성
            config_data = {
                'vlan_id': self.vlan_id.get(),
                'vlan_name': self.vlan_name.get()
            }
            
            # 스크립트 생성
            success, message = self.script_generator.generate_script(
                device_info, 'vlan', config_data)
            
            if success:
                messagebox.showinfo("성공", message)
                self.log_manager.log_execution(
                    device_info['device_name'],
                    "VLAN 설정 스크립트 생성",
                    "성공"
                )
            else:
                raise ValueError(message)

        except Exception as e:
            messagebox.showerror("오류", str(e))
            self.log_manager.log_execution(
                "Unknown",
                "VLAN 설정 스크립트 생성",
                f"실패: {str(e)}"
            )

    def _get_device_info(self):
        """저장된 장비 기본 정보 가져오기"""
        device_name = self.device_name.get()
        if not device_name:
            raise ValueError("먼저 기본 정보를 저장해주세요.")
            
        script_file = f"tasks/{device_name}_config.json"
        if not os.path.exists(script_file):
            raise ValueError("장비 정보를 찾을 수 없습니다.")
            
        with open(script_file, 'r', encoding='utf-8') as f:
            script_data = json.load(f)
            
        return script_data['basic_info']

    # 다른 설정 저장 메서드들도 유사하게 구현...
    def save_interface_config(self):
        """인터페이스 설정 저장"""
        try:
            if not all([self.interface.get(), 
                       self.interface_mode.get(), 
                       self.interface_vlan.get()]):
                raise ValueError("모든 필드를 입력해주세요.")

            device_info = self._get_device_info()
            config_data = {
                'interface': self.interface.get(),
                'mode': self.interface_mode.get(),
                'vlan': self.interface_vlan.get()
            }
            
            success, message = self.script_generator.generate_script(
                device_info, 'interface', config_data)
            
            if success:
                messagebox.showinfo("성공", message)
                self.log_manager.log_execution(
                    device_info['device_name'],
                    "인터페이스 설정 스크립트 생성",
                    "성공"
                )
            else:
                raise ValueError(message)

        except Exception as e:
            messagebox.showerror("오류", str(e))
            self.log_manager.log_execution(
                "Unknown",
                "인터페이스 설정 스크립트 생성",
                f"실패: {str(e)}"
            )

def start_gui():
    """GUI 시작 함수"""
    root = tk.Tk()
    app = NetworkAutomationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    start_gui()
