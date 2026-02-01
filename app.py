# Shimplex - Personal AI Plex
# 외부 LLM 연결 + Pinehill Manager 통합
# 사용법: python app.py

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3
import json
import os
import httpx
from datetime import datetime
from typing import Optional, List, Dict
import asyncio

app = FastAPI(title="Shimplex", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 설정 파일 경로
CONFIG_FILE = "config.json"
DB_FILE = "pinehill.db"

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
                "provider": "openai",  # openai, anthropic, ollama, custom
                "api_key": "",
                "base_url": "",  # Ollama나 커스텀 서버용
                "model": "gpt-4o-mini",
                "temperature": 0.7
            },
            "pinehill": {
                "db_path": "pinehill.db"
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

# 데이터베이스 연결
def get_db():
    db_path = config.get('pinehill.db_path', DB_FILE)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# LLM 클라이언트
class LLMClient:
    def __init__(self):
        self.provider = config.get('llm.provider', 'openai')
        self.api_key = config.get('llm.api_key', '')
        self.base_url = config.get('llm.base_url', '')
        self.model = config.get('llm.model', 'gpt-4o-mini')
        self.temperature = config.get('llm.temperature', 0.7)
    
    async def chat(self, message: str, context: str = "") -> str:
        """LLM과 대화"""
        if not self.api_key and self.provider != 'ollama':
            return "❌ LLM API 키가 설정되지 않았습니다. 설정에서 API 키를 입력해주세요."
        
        try:
            if self.provider == 'openai':
                return await self._chat_openai(message, context)
            elif self.provider == 'anthropic':
                return await self._chat_anthropic(message, context)
            elif self.provider == 'ollama':
                return await self._chat_ollama(message, context)
            else:
                return await self._chat_custom(message, context)
        except Exception as e:
            return f"❌ LLM 오류: {str(e)}"
    
    async def _chat_openai(self, message: str, context: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = self._get_system_prompt()
        if context:
            system_prompt += f"\n\n[컨텍스트]\n{context}"
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
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
    
    async def _chat_anthropic(self, message: str, context: str) -> str:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        system_prompt = self._get_system_prompt()
        if context:
            system_prompt += f"\n\n[컨텍스트]\n{context}"
        
        data = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": message}],
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
    
    async def _chat_ollama(self, message: str, context: str) -> str:
        base_url = self.base_url or "http://localhost:11434"
        
        system_prompt = self._get_system_prompt()
        if context:
            system_prompt += f"\n\n[컨텍스트]\n{context}"
        
        data = {
            "model": self.model or "llama3.1:8b",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
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
    
    async def _chat_custom(self, message: str, context: str) -> str:
        # OpenAI 호환 API용
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = self._get_system_prompt()
        if context:
            system_prompt += f"\n\n[컨텍스트]\n{context}"
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
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
        return """당신은 Shimplex AI 어시스턴트입니다. 사용자의 개인 데이터를 분석하고 도움을 제공합니다.

능력:
1. pinehill-manager 데이터베이스 조회 (원룸 19세대 관리)
2. 월세/지출 현황 분석
3. 일반적인 질문 답변

응답은 간결하고 친절하게 한국어로 해주세요."""

llm_client = LLMClient()

# Pinehill 데이터 관리
class PinehillData:
    @staticmethod
    def get_units() -> List[Dict]:
        """모든 세대 조회"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM units ORDER BY unitId")
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except:
            return []
    
    @staticmethod
    def get_unit(unit_id: str) -> Optional[Dict]:
        """특정 세대 조회"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM units WHERE unitId = ?", (unit_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except:
            return None
    
    @staticmethod
    def get_payments(month: str) -> List[Dict]:
        """월별 납부 조회"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments WHERE month = ?", (month,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except:
            return []
    
    @staticmethod
    def get_summary(month: str) -> Dict:
        """월별 요약"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # 납부 통계
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'PAID' THEN 1 END) as paid,
                    COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending,
                    COUNT(CASE WHEN status = 'UNPAID' THEN 1 END) as unpaid,
                    SUM(amount) as total
                FROM payments WHERE month = ?
            """, (month,))
            payment_row = cursor.fetchone()
            
            # 지출 통계
            cursor.execute("SELECT SUM(amount) as total FROM expenses WHERE month = ?", (month,))
            expense_row = cursor.fetchone()
            
            conn.close()
            
            return {
                "month": month,
                "payments": {
                    "paid": payment_row[0] or 0,
                    "pending": payment_row[1] or 0,
                    "unpaid": payment_row[2] or 0,
                    "total_amount": payment_row[3] or 0
                },
                "expenses": {
                    "total": expense_row[0] or 0
                }
            }
        except Exception as e:
            return {"month": month, "error": str(e)}
    
    @staticmethod
    def get_context_for_llm() -> str:
        """LLM용 컨텍스트 생성"""
        try:
            units = PinehillData.get_units()
            current_month = datetime.now().strftime("%Y-%m")
            summary = PinehillData.get_summary(current_month)
            
            context = f"""[Pinehill Manager 현황]
- 총 세대: {len(units)}세대
- 이번 달({current_month}) 납부 현황:
  * 완납: {summary['payments']['paid']}세대
  * 미납: {summary['payments']['unpaid']}세대
  * 확인필요: {summary['payments']['pending']}세대
  * 총 입금액: {summary['payments']['total_amount']:,}원
- 이번 달 지출: {summary['expenses']['total']:,}원

세대 목록:
"""
            for u in units[:10]:  # 최대 10개만
                context += f"- {u['unitId']} ({u['roomNo']}호): {u['status']}\n"
            
            return context
        except:
            return ""

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
    return {"status": "ok"}

@app.get("/api/units")
async def api_units():
    """세대 목록 API"""
    return PinehillData.get_units()

@app.get("/api/units/{unit_id}")
async def api_unit(unit_id: str):
    """특정 세대 API"""
    unit = PinehillData.get_unit(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit

@app.get("/api/summary/{month}")
async def api_summary(month: str):
    """월별 요약 API"""
    return PinehillData.get_summary(month)

class ChatMessage(BaseModel):
    message: str
    use_context: bool = True

@app.post("/api/chat")
async def api_chat(chat: ChatMessage):
    """AI 채팅 API"""
    context = ""
    if chat.use_context:
        context = PinehillData.get_context_for_llm()
    
    response = await llm_client.chat(chat.message, context)
    return {
        "message": chat.message,
        "response": response,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """상태 확인"""
    return {
        "status": "ok",
        "llm_provider": config.get('llm.provider'),
        "llm_configured": bool(config.get('llm.api_key')),
        "db_exists": os.path.exists(config.get('pinehill.db_path', DB_FILE))
    }

# 데이터베이스 초기화
def init_database():
    """처음 실행 시 기본 테이블 생성"""
    if os.path.exists(DB_FILE):
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Units 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS units (
            unitId TEXT PRIMARY KEY,
            roomNo INTEGER,
            floor INTEGER,
            status TEXT DEFAULT 'RENTED',
            roomType TEXT,
            targetPrice TEXT,
            createdAt INTEGER,
            updatedAt INTEGER
        )
    """)
    
    # Payments 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            paymentId INTEGER PRIMARY KEY AUTOINCREMENT,
            tenantKey TEXT,
            unitId TEXT,
            month TEXT,
            paidAt INTEGER,
            amount INTEGER,
            senderName TEXT,
            source TEXT,
            status TEXT,
            createdAt INTEGER
        )
    """)
    
    # Expenses 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            expenseId INTEGER PRIMARY KEY AUTOINCREMENT,
            spentAt INTEGER,
            amount INTEGER,
            category TEXT,
            memo TEXT,
            unitId TEXT,
            month TEXT,
            source TEXT,
            createdAt INTEGER
        )
    """)
    
    # 초기 데이터 (19세대)
    units = [
        ("PINE-201", 201, 2, "RENTED", "1.5룸", "500-50", 1706744400, 1706744400),
        ("PINE-202", 202, 2, "RENTED", None, None, 1706744400, 1706744400),
        ("PINE-203", 203, 2, "RENTED", None, None, 1706744400, 1706744400),
        ("PINE-204", 204, 2, "LAWSUIT", None, None, 1706744400, 1706744400),
        ("PINE-205", 205, 2, "RENTED", "투룸", "500-60", 1706744400, 1706744400),
        ("PINE-206", 206, 2, "RENTED", "투룸", "500-60", 1706744400, 1706744400),
        ("PINE-207", 207, 2, "RENTED", None, None, 1706744400, 1706744400),
        ("PINE-301", 301, 3, "RENTED", "1.5룸", "500-50", 1706744400, 1706744400),
        ("PINE-302", 302, 3, "RENTED", None, None, 1706744400, 1706744400),
        ("PINE-303", 303, 3, "RENTED", None, None, 1706744400, 1706744400),
        ("PINE-304", 304, 3, "RENTED", None, None, 1706744400, 1706744400),
        ("PINE-305", 305, 3, "RENTED", "투룸", "500-60", 1706744400, 1706744400),
        ("PINE-306", 306, 3, "RENTED", "투룸", "500-60", 1706744400, 1706744400),
        ("PINE-307", 307, 3, "RENTED", None, None, 1706744400, 1706744400),
        ("PINE-401", 401, 4, "RENTED", "1.5룸", "500-50", 1706744400, 1706744400),
        ("PINE-402", 402, 4, "RENTED", None, None, 1706744400, 1706744400),
        ("PINE-403", 403, 4, "RENTED", None, None, 1706744400, 1706744400),
        ("PINE-404", 404, 4, "RENTED", None, None, 1706744400, 1706744400),
        ("PINE-405", 405, 4, "MAINTENANCE", None, None, 1706744400, 1706744400),
    ]
    
    cursor.executemany("""
        INSERT INTO units (unitId, roomNo, floor, status, roomType, targetPrice, createdAt, updatedAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, units)
    
    conn.commit()
    conn.close()
    print(f"✅ 데이터베이스 초기화 완료: {DB_FILE}")

if __name__ == "__main__":
    import uvicorn
    
    # 초기화
    init_database()
    
    # 설정 확인
    if not os.path.exists(CONFIG_FILE):
        config.save()
        print(f"✅ 기본 설정 생성: {CONFIG_FILE}")
    
    host = config.get('app.host', '0.0.0.0')
    port = config.get('app.port', 8080)
    
    print(f"""
🚀 Shimplex 시작!
🔗 http://{host}:{port}

⚙️ 설정 파일: {CONFIG_FILE}
🗄️ 데이터베이스: {DB_FILE}

💡 처음 사용하시나요?
   1. 브라우저에서 http://localhost:{port} 접속
   2. 설정 탭에서 LLM API 키 입력
   3. 채팅 시작!
""")
    
    uvicorn.run(app, host=host, port=port)
