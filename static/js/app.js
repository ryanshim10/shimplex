// Shimplex Frontend JavaScript

const API_BASE = '';

// 탭 전환
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabId = btn.dataset.tab;
        
        // 버튼 활성화
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // 콘텐츠 전환
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        
        // 탭별 초기화
        if (tabId === 'units') loadUnits();
        if (tabId === 'summary') loadSummary();
        if (tabId === 'settings') loadSettings();
    });
});

// 채팅 기능
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    // 사용자 메시지 추가
    addMessage(message, 'user');
    messageInput.value = '';
    
    // 로딩 표시
    const loadingId = addMessage('생각 중...', 'loading');
    
    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, use_context: true })
        });
        
        const data = await response.json();
        
        // 로딩 제거하고 응답 추가
        document.getElementById(loadingId).remove();
        addMessage(data.response, 'ai');
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

// 세대 목록
let currentFilter = 'all';

async function loadUnits() {
    const container = document.getElementById('units-list');
    container.innerHTML = '<div class="loading">로딩 중...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/units`);
        const units = await response.json();
        
        renderUnits(units);
    } catch (error) {
        container.innerHTML = '<div class="loading">❌ 데이터를 불러올 수 없습니다.</div>';
    }
}

function renderUnits(units) {
    const container = document.getElementById('units-list');
    const filtered = currentFilter === 'all' 
        ? units 
        : units.filter(u => u.status === currentFilter);
    
    if (filtered.length === 0) {
        container.innerHTML = '<div class="loading">해당하는 세대가 없습니다.</div>';
        return;
    }
    
    container.innerHTML = filtered.map(unit => `
        <div class="unit-card" onclick="showUnitDetail('${unit.unitId}')">
            <div class="room-no">${unit.roomNo}호</div>
            <div class="unit-id">${unit.unitId}</div>
            <span class="status status-${unit.status}">${getStatusText(unit.status)}</span>
            ${unit.targetPrice ? `<div style="margin-top:8px;font-size:0.85rem;color:#666">${unit.targetPrice}</div>` : ''}
        </div>
    `).join('');
}

function getStatusText(status) {
    const map = {
        'RENTED': '임대중',
        'VACANT': '공실',
        'MAINTENANCE': '정비중',
        'LAWSUIT': '소송',
        'OTHER': '기타'
    };
    return map[status] || status;
}

// 필터 버튼
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        loadUnits();
    });
});

function showUnitDetail(unitId) {
    alert(`세대 상세 정보: ${unitId}\n(상세 페이지는 추후 구현 예정)`);
}

// 요약
async function loadSummary() {
    const monthInput = document.getElementById('summary-month');
    if (!monthInput.value) {
        monthInput.value = new Date().toISOString().slice(0, 7);
    }
    
    const month = monthInput.value;
    const container = document.getElementById('summary-content');
    container.innerHTML = '<div class="loading">로딩 중...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/summary/${month}`);
        const data = await response.json();
        
        container.innerHTML = `
            <div class="summary-cards">
                <div class="summary-card">
                    <h3>✅ 완납</h3>
                    <div class="value">${data.payments.paid}</div>
                </div>
                <div class="summary-card">
                    <h3>⏳ 확인필요</h3>
                    <div class="value">${data.payments.pending}</div>
                </div>
                <div class="summary-card">
                    <h3>❌ 미납</h3>
                    <div class="value">${data.payments.unpaid}</div>
                </div>
                <div class="summary-card">
                    <h3>💰 총 입금</h3>
                    <div class="value">${data.payments.total_amount.toLocaleString()}원</div>
                </div>
                <div class="summary-card">
                    <h3>💸 총 지출</h3>
                    <div class="value">${data.expenses.total.toLocaleString()}원</div>
                </div>
            </div>
        `;
    } catch (error) {
        container.innerHTML = '<div class="loading">❌ 데이터를 불러올 수 없습니다.</div>';
    }
}

document.getElementById('summary-month').addEventListener('change', loadSummary);

// 설정
async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/api/config`);
        const config = await response.json();
        
        document.getElementById('llm-provider').value = config.llm.provider || 'openai';
        document.getElementById('llm-model').value = config.llm.model || '';
        document.getElementById('llm-base-url').value = config.llm.base_url || '';
        
        updateProviderFields(config.llm.provider);
        
        // 상태 확인
        const healthRes = await fetch(`${API_BASE}/api/health`);
        const health = await healthRes.json();
        
        document.getElementById('health-status').innerHTML = `
            <p>✅ 서버 상태: ${health.status}</p>
            <p>🤖 LLM 제공자: ${health.llm_provider}</p>
            <p>🔑 API 설정: ${health.llm_configured ? '완료' : '미설정'}</p>
            <p>🗄️ 데이터베이스: ${health.db_exists ? '연결됨' : '새로 생성됨'}</p>
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
    // 첫 번째 탭 데이터 로드
    loadSettings();
});
