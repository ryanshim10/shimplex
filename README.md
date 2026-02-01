# Shimplex Lite 🧠

> **어떤 컴퓨터에서든** Python만 있으면 실행되는 Personal AI Client
> 
> 외부 LLM(OpenAI/Claude/Ollama) 연결 전용 - 간결한 버전

## ✨ 특징

- ✅ **간단 설치**: Python 3.8+만 필요
- ✅ **외부 LLM**: OpenAI, Claude, Ollama(로컬) 모두 지원
- ✅ **웹 UI**: 내장 웹 인터페이스
- ✅ **크로스플랫폼**: Windows, Mac, Linux 모두 지원
- ✅ **대화 기록**: 세션별 메모리 관리

## 🚀 설치 (3단계)

### 1. 다운로드
```bash
git clone https://github.com/ryanshim10/shimplex.git
cd shimplex
```

### 2. 설치
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
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 🔧 설정

### OpenAI 사용
```json
{
  "llm": {
    "provider": "openai",
    "api_key": "sk-...",
    "model": "gpt-4o-mini"
  }
}
```

### Claude 사용
```json
{
  "llm": {
    "provider": "anthropic",
    "api_key": "sk-ant-...",
    "model": "claude-3-haiku"
  }
}
```

### Ollama(로컬) 사용
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

## 🔒 보안

- API 키는 로컬 `config.json`에만 저장
- 외부 전송은 LLM API 호출뿐

## 📝 라이선스

MIT License
