# Network Automation Tool

네트워크 자동화 도구는 네트워크 장비의 설정과 모니터링을 자동화하는 웹 기반 도구입니다.

## 주요 기능

- 네트워크 장비 관리
  - 장비 정보 등록 및 관리
  - 연결 상태 모니터링
  - 설정 백업 및 복원

- 설정 관리
  - VLAN 설정
  - 인터페이스 설정
  - 라우팅 설정
  - 보안 설정
  - QoS 설정
  - 모니터링 설정

- CLI 학습 기능
  - 벤더별 CLI 명령어 자동 학습
  - 명령어 데이터베이스 구축
  - 학습된 명령어 조회 및 활용

## 지원 벤더

- Cisco
- Juniper
- Arista
- HP
- 기타 벤더 추가 예정

## 설치 방법

1. 저장소 클론

```bash
git clone https://github.com/yourusername/network-automation.git
cd network-automation
```

1. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

1. 의존성 설치

```bash
pip install -r requirements.txt
```

1. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정을 입력
```

## 실행 방법

1. 서버 실행

```bash
python run.py
```

1. 웹 브라우저에서 접속

```text
http://localhost:5000
```

## 프로젝트 구조

```text
network-automation/
├── app/
│   ├── models/          # 데이터 모델
│   ├── services/        # 비즈니스 로직
│   ├── routes/          # API 라우트
│   └── utils/           # 유틸리티 함수
├── static/              # 정적 파일
├── templates/           # HTML 템플릿
├── config/             # 설정 파일
├── logs/               # 로그 파일
└── tests/              # 테스트 코드
```

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
