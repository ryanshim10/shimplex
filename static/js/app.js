// Shimplex Lite Frontend - Pinehill 의존성 제거

const API_BASE = '';

// 탭 전환
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabId = btn.dataset.tab;
        
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        
        if (tabId === 'settings') loadSettings();
    });
});

// 채팅 기능
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const clearBtn = document.getElementById('clear-btn');

// 대화 기록
let chatHistory = [];

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    addMessage(message, 'user');
    messageInput.value = '';
    
    const loadingId = addMessage('생각 중...', 'loading');
    
    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message,
                session_id: 'default'
            })
        });
        
        const data = await response.json();
        
        document.getElementById(loadingId).remove();
        addMessage(data.response, 'ai');
        
        // 대화 기록 저장
        chatHistory.push({role: 'user', content: message});
        chatHistory.push({role: 'ai', content: data.response});
        
    } catch (error) {
        document.getElementById(loadingId).remove();
        addMessage('❌ 오류가 발생했습니다: ' + error.message, 'ai');
    }
}

function addMessage(text, type) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    if (type === 'loading') {
        div.id = 'loading-' + Date.now();
    }
    div.innerHTML = text.replace(/\n/g, '<br>');
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return div.id || null;
}

sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// 대화 초기화
clearBtn.addEventListener('click', async () => {
    if (!confirm('대화를 모두 지우시겠습니까?')) return;
    
    try {
        await fetch(`${API_BASE}/api/history/default`, { method: 'DELETE' });
        chatMessages.innerHTML = `
            <div class="message system">
                👋 안녕하세요! Shimplex AI입니다.<br>
                외부 LLM(OpenAI/Claude/Ollama)에 연결하여 사용하세요.
            </div>
        `;
        chatHistory = [];
    } catch (error) {
        alert('❌ 초기화 실패: ' + error.message);
    }
});

// 설정
async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/api/config`);
        const config = await response.json();
        
        document.getElementById('llm-provider').value = config.llm.provider || 'openai';
        document.getElementById('llm-model').value = config.llm.model || '';
        document.getElementById('llm-base-url').value = config.llm.base_url || '';
        
        updateProviderFields(config.llm.provider);
        
        const healthRes = await fetch(`${API_BASE}/api/health`);
        const health = await healthRes.json();
        
        document.getElementById('health-status').innerHTML = `
            <p>✅ 서버 상태: ${health.status}</p>
            <p>🤖 LLM 제공자: ${health.llm_provider}</p>
            <p>🔑 API 설정: ${health.llm_configured ? '완료 ✅' : '미설정 ❌'}</p>
        `;
    } catch (error) {
        document.getElementById('health-status').innerHTML = '<p>❌ 서버 연결 실패</p>';
    }
}

function updateProviderFields(provider) {
    const ollamaFields = document.querySelectorAll('.ollama-only');
    const customFields = document.querySelectorAll('.custom-only');
    
    ollamaFields.forEach(el => el.style.display = provider === 'ollama' ? 'block' : 'none');
    customFields.forEach(el => el.style.display = provider === 'custom' ? 'block' : 'none');
}

document.getElementById('llm-provider').addEventListener('change', (e) => {
    updateProviderFields(e.target.value);
});

document.getElementById('settings-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        llm: {
            provider: document.getElementById('llm-provider').value,
            api_key: document.getElementById('llm-api-key').value,
            model: document.getElementById('llm-model').value,
            base_url: document.getElementById('llm-base-url').value || document.getElementById('llm-custom-url').value
        }
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert('✅ 설정이 저장되었습니다!');
            loadSettings();
        } else {
            alert('❌ 설정 저장 실패');
        }
    } catch (error) {
        alert('❌ 오류: ' + error.message);
    }
});

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
});
