# Shimplex 🧠

> **어떤 컴퓨터에서든** Python만 있으면 실행되는 Personal AI Plex
> 
> 외부 LLM(OpenAI/Claude/Ollama) 연결 + Pinehill Manager 통합

## ✨ 특징

- ✅ **간단 설치**: Docker 없이 Python만으로 실행
- ✅ **외부 LLM**: OpenAI, Claude, Ollama(로컬) 모두 지원
- ✅ **웹 UI**: 별도 서버 없이 내장 웹 인터페이스
- ✅ **Pinehill 연동**: 19세대 원룸 관리 데이터 분석
- ✅ **크로스플랫폼**: Windows, Mac, Linux 모두 지원

## 🚀 설치 (3단계)

### 1. 클론
```bash
git clone https://github.com/ryanshim10/shimplex.git
cd shimplex
```

### 2. 설치 스크립트 실행
```bash
./install.sh
```

### 3. 실행
```bash
source venv/bin/activate
python app.py
```

**브라우저에서 http://localhost:8080 접속**

## 📋 수동 설치

```bash
# 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 실행
python app.py
```

## 🔧 설정

### 1. OpenAI 사용
```json
{
  "llm": {
    "provider": "openai",
    "api_key": "sk-...",
    "model": "gpt-4o-mini"
  }
}
```

### 2. Claude 사용
```json
{
  "llm": {
    "provider": "anthropic",
    "api_key": "sk-ant-...",
    "model": "claude-3-haiku"
  }
}
```

### 3. Ollama(로컬) 사용
```json
{
  "llm": {
    "provider": "ollama",
    "base_url": "http://localhost:11434",
    "model": "llama3.1:8b"
  }
}
```

## 🧪 테스트

```bash
./test.sh
```

## 💬 사용 예시

### 채팅에서 물어보기
- "이번 달 미납 세대 알려줘"
- "PINE-201 현황 보여줘"
- "1월 입금 총액이 얼마야?"

### API 직접 호출
```bash
# 세대 목록
curl http://localhost:8080/api/units

# 월별 요약
curl http://localhost:8080/api/summary/2026-01

# AI 채팅
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'
```

## 🏗️ 아키텍처

```
Shimplex
├── app.py              # 메인 애플리케이션 (FastAPI)
├── requirements.txt    # Python 패키지
├── config.json         # 사용자 설정 (자동 생성)
├── pinehill.db         # SQLite 데이터베이스 (자동 생성)
├── templates/
│   └── index.html      # 웹 UI
├── static/
│   ├── css/style.css   # 스타일
│   └── js/app.js       # 프론트엔드
├── install.sh          # 설치 스크립트
└── test.sh             # 테스트 스크립트
```

## 🔒 보안

- API 키는 로컬 `config.json`에만 저장
- 외부로 전송되는 데이터는 LLM API 호출뿐
- pinehill.db는 로컬 SQLite 파일

## 📝 라이선스

MIT License

## 🙏 감사

- [FastAPI](https://fastapi.tiangolo.com)
- [OpenAI](https://openai.com)
- [Anthropic](https://anthropic.com)
- [Ollama](https://ollama.com)
