# Shimplex - Personal AI Plex (Lite)
# 외부 LLM 연결 전용 - Pinehill 의존성 제거
# 사용법: python app.py

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import os
import httpx
from datetime import datetime
from typing import Optional, List, Dict
import asyncio

app = FastAPI(title="Shimplex Lite", version="1.1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 설정 파일 경로
CONFIG_FILE = "config.json"

class Config:
    """설정 관리"""
    def __init__(self):
        self.data = self.load()
    
    def load(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.default_config()
    
    def save(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def default_config(self) -> dict:
        return {
            "llm": {
                "provider": "openai",
                "api_key": "",
                "base_url": "",
                "model": "gpt-4o-mini",
                "temperature": 0.7
            },
            "app": {
                "host": "0.0.0.0",
                "port": 8080,
                "language": "ko"
            }
        }
    
    def get(self, key: str, default=None):
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value):
        keys = key.split('.')
        target = self.data
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        self.save()

config = Config()

# LLM 클라이언트
class LLMClient:
    def __init__(self):
        self.provider = config.get('llm.provider', 'openai')
        self.api_key = config.get('llm.api_key', '')
        self.base_url = config.get('llm.base_url', '')
        self.model = config.get('llm.model', 'gpt-4o-mini')
        self.temperature = config.get('llm.temperature', 0.7)
    
    async def chat(self, message: str, history: List[Dict] = None) -> str:
        """LLM과 대화"""
        if not self.api_key and self.provider != 'ollama':
            return "❌ LLM API 키가 설정되지 않았습니다. 설정에서 API 키를 입력해주세요."
        
        try:
            if self.provider == 'openai':
                return await self._chat_openai(message, history)
            elif self.provider == 'anthropic':
                return await self._chat_anthropic(message, history)
            elif self.provider == 'ollama':
                return await self._chat_ollama(message, history)
            else:
                return await self._chat_custom(message, history)
        except Exception as e:
            return f"❌ LLM 오류: {str(e)}"
    
    async def _chat_openai(self, message: str, history: List[Dict] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "system", "content": self._get_system_prompt()}]
        
        if history:
            for h in history[-10:]:  # 최근 10개만
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        
        messages.append({"role": "user", "content": message})
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
    
    async def _chat_anthropic(self, message: str, history: List[Dict] = None) -> str:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        system_prompt = self._get_system_prompt()
        
        # Anthropic은 history를 messages에 포함
        messages = []
        if history:
            for h in history[-10:]:
                role = "assistant" if h.get("role") == "ai" else "user"
                messages.append({"role": role, "content": h.get("content", "")})
        
        messages.append({"role": "user", "content": message})
        
        data = {
            "model": self.model or "claude-3-haiku-20240307",
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": messages,
            "temperature": self.temperature
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            return result['content'][0]['text']
    
    async def _chat_ollama(self, message: str, history: List[Dict] = None) -> str:
        base_url = self.base_url or "http://localhost:11434"
        
        messages = [{"role": "system", "content": self._get_system_prompt()}]
        
        if history:
            for h in history[-10:]:
                role = "assistant" if h.get("role") == "ai" else "user"
                messages.append({"role": role, "content": h.get("content", "")})
        
        messages.append({"role": "user", "content": message})
        
        data = {
            "model": self.model or "llama3.1:8b",
            "messages": messages,
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/chat",
                json=data,
                timeout=120.0
            )
            response.raise_for_status()
            result = response.json()
            return result['message']['content']
    
    async def _chat_custom(self, message: str, history: List[Dict] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "system", "content": self._get_system_prompt()}]
        
        if history:
            for h in history[-10:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        
        messages.append({"role": "user", "content": message})
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
    
    def _get_system_prompt(self) -> str:
        return """당신은 Shimplex AI 어시스턴트입니다. 사용자의 질문에 친절하고 정확하게 답변해주세요.

응답은 간결하고 명확하게 한국어로 해주세요."""

llm_client = LLMClient()

# 메모리 기반 대화 저장 (세션별)
chat_histories = {}

# API 엔드포인트
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """메인 페이지"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/config")
async def get_config():
    """설정 조회 (API 키는 제외)"""
    safe_config = {
        "llm": {
            "provider": config.get('llm.provider'),
            "model": config.get('llm.model'),
            "base_url": config.get('llm.base_url')
        },
        "app": config.get('app')
    }
    return safe_config

@app.post("/api/config")
async def update_config(data: dict):
    """설정 업데이트"""
    if 'llm' in data:
        for key, value in data['llm'].items():
            config.set(f'llm.{key}', value)
    
    # 설정 변경 후 클라이언트 재초기화
    global llm_client
    llm_client = LLMClient()
    
    return {"status": "ok"}

class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

@app.post("/api/chat")
async def api_chat(chat: ChatMessage):
    """AI 채팅 API"""
    session_id = chat.session_id or "default"
    
    # 대화 기록 가져오기
    if session_id not in chat_histories:
        chat_histories[session_id] = []
    
    history = chat_histories[session_id]
    
    response = await llm_client.chat(chat.message, history)
    
    # 대화 기록 저장
    history.append({"role": "user", "content": chat.message})
    history.append({"role": "ai", "content": response})
    
    # 최근 50개만 유지
    if len(history) > 50:
        chat_histories[session_id] = history[-50:]
    
    return {
        "message": chat.message,
        "response": response,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/history/{session_id}")
async def get_history(session_id: str = "default"):
    """대화 기록 조회"""
    return chat_histories.get(session_id, [])

@app.delete("/api/history/{session_id}")
async def clear_history(session_id: str = "default"):
    """대화 기록 삭제"""
    if session_id in chat_histories:
        chat_histories[session_id] = []
    return {"status": "ok"}

@app.get("/api/health")
async def health_check():
    """상태 확인"""
    return {
        "status": "ok",
        "llm_provider": config.get('llm.provider'),
        "llm_configured": bool(config.get('llm.api_key')),
        "version": "1.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    
    # 설정 확인
    if not os.path.exists(CONFIG_FILE):
        config.save()
        print(f"✅ 기본 설정 생성: {CONFIG_FILE}")
    
    host = config.get('app.host', '0.0.0.0')
    port = config.get('app.port', 8080)
    
    print(f"""
🚀 Shimplex Lite 시작!
🔗 http://{host}:{port}

⚙️ 설정 파일: {CONFIG_FILE}

💡 처음 사용하시나요?
   1. 브라우저에서 http://localhost:{port} 접속
   2. 설정 탭에서 LLM API 키 입력
   3. 채팅 시작!

📝 지원 LLM:
   - OpenAI (GPT-4, GPT-4o-mini 등)
   - Anthropic (Claude 3 등)
   - Ollama (로컬 AI)
   - Custom (OpenAI 호환 API)
""")
    
    uvicorn.run(app, host=host, port=port)
