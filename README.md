# Network Automation Tool

네트워크 장비 설정 자동화 도구입니다.

## 기능

- 네트워크 장비 관리 (추가/수정/삭제)
- 장비별 설정 스크립트 생성
- 벤더별 커맨드 템플릿 지원
  - Handreamnet
  - CoreEdge

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
python src/main.py
```

실행 후 자동으로 브라우저가 열리며 <http://localhost:5000> 에서 접속할 수 있습니다.

## 프로젝트 구조
