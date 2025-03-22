# Network Automation Tool

네트워크 장비 설정 자동화 도구입니다.

## 주요 기능

1. 네트워크 장비 관리
   - 장비 추가/수정/삭제
   - 벤더/모델별 관리
   - IP 주소 기반 장비 식별

2. 장비 설정 관리
   - 장비별 설정 백업
   - 설정 이력 관리
   - 설정 비교 및 복원

3. CLI 학습 기능
   - 벤더별 CLI 명령어 학습
   - 매뉴얼 기반 자동 학습
   - 사용자 정의 명령어 추가

4. 지원 벤더
   - Cisco
   - Juniper
   - HP
   - Arista
   - Handreamnet
   - CoreEdge Networks

## 시작하기

### 요구사항

- Python 3.8 이상
- Flask
- 기타 필요한 패키지들은 requirements.txt 참고

### 설치

1. 저장소 클론

```bash
git clone https://github.com/henryGTI/Network_Automation.git
cd Network_Automation
```

1. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

1. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 실행

```bash
python run.py
```

웹 브라우저에서 http://localhost:5000 으로 접속하여 사용할 수 있습니다.

## 주요 기능 설명

### 1. 장비 관리
- 장비 목록 조회
- 장비 추가/수정/삭제
- 벤더/모델별 필터링
- IP 주소 중복 검사

### 2. 설정 관리
- 장비별 설정 백업
- 설정 이력 관리
- 설정 파일 비교
- 설정 복원

### 3. CLI 학습
- 벤더별 CLI 명령어 학습
- PDF 매뉴얼 기반 자동 학습
- 사용자 정의 명령어 추가/수정
- 학습된 명령어 검색

## 프로젝트 구조

```
network_automation/
├── app/
│   ├── models/          # 데이터 모델
│   ├── routes/          # 라우트 핸들러
│   ├── services/        # 비즈니스 로직
│   └── utils/          # 유틸리티 함수
├── static/
│   ├── css/            # 스타일시트
│   └── js/             # 자바스크립트
├── templates/          # HTML 템플릿
├── config/            # 설정 파일
├── tests/             # 테스트 코드
└── run.py            # 애플리케이션 시작점
```

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.
