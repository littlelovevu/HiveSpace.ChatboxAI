// HiveSpace Chatbox - API Integration
// Biến global để lưu trạng thái
let currentSessionId = null;
let chatSessions = [];
let isLoading = false;

// API Base URL
const API_BASE_URL = 'http://localhost:8000';

// Khởi tạo ứng dụng
document.addEventListener('DOMContentLoaded', function () {
    loadChatSessions();
    setupEventListeners();
    autoResizeTextarea();
});

// Thiết lập event listeners
function setupEventListeners() {
    // Close modal khi click bên ngoài
    window.onclick = function (event) {
        const modal = document.getElementById('newChatModal');
        if (event.target === modal) {
            closeNewChatModal();
        }
    }
}

// API Functions
async function loadChatSessions() {
    try {
        isLoading = true;
        showLoadingState();

        const response = await fetch(`${API_BASE_URL}/api/sessions`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        chatSessions = await response.json();
        // Sắp xếp theo thời gian mới nhất lên đầu
        chatSessions.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
        renderChatSessions();

        // Tự động chọn session đầu tiên nếu có
        if (chatSessions.length > 0 && !currentSessionId) {
            switchSession(chatSessions[0].id);
        }

    } catch (error) {
        console.error('Error loading chat sessions:', error);
        showErrorMessage('Failed to load chat sessions');
    } finally {
        isLoading = false;
        hideLoadingState();
    }
}

async function loadChatSessionDetail(sessionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const session = await response.json();
        renderChatMessages(session.messages);
        updateChatHeader(session.title);
        enableChatInput();

    } catch (error) {
        console.error('Error loading chat session:', error);
        showErrorMessage('Failed to load chat session');
    }
}

async function createNewChatSession(title) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/sessions/new`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const newSession = await response.json();

        // Thêm session mới vào danh sách và sắp xếp lại
        chatSessions.unshift(newSession);
        chatSessions.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
        renderChatSessions();

        // Chuyển đến session mới
        switchSession(newSession.id);

        // Đóng modal
        closeNewChatModal();

        return newSession;

    } catch (error) {
        console.error('Error creating new chat session:', error);
        showErrorMessage('Failed to create new chat session');
        return null;
    }
}

async function sendMessageToAPI(message) {
    if (!currentSessionId) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/messages/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            // Cập nhật UI với tin nhắn mới
            addMessageToChat('user', message, formatTime(new Date()));
            addMessageToChat('ai', result.ai_response.text, formatTime(new Date()));

            // Cập nhật danh sách sessions
            await loadChatSessions();

            // Scroll xuống cuối
            scrollToBottom();
        }

    } catch (error) {
        console.error('Error sending message:', error);
        showErrorMessage('Failed to send message');
    }
}

async function clearChatSession(sessionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/clear`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Reload session detail
        await loadChatSessionDetail(sessionId);

        // Cập nhật danh sách sessions
        await loadChatSessions();

        showSuccessMessage('Chat cleared successfully');

    } catch (error) {
        console.error('Error clearing chat session:', error);
        showErrorMessage('Failed to clear chat session');
    }
}

async function exportChatSession(sessionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/export`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            // Tạo và download file
            const blob = new Blob([result.content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = result.filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showSuccessMessage('Chat exported successfully');
        }

    } catch (error) {
        console.error('Error exporting chat session:', error);
        showErrorMessage('Failed to export chat session');
    }
}

// UI Functions
function renderChatSessions() {
    const sessionsContainer = document.getElementById('chatSessions');
    sessionsContainer.innerHTML = '';

    if (chatSessions.length === 0) {
        sessionsContainer.innerHTML = `
            <div class="no-sessions">
                <p>No chat sessions yet</p>
                <small>Start a new conversation to begin</small>
            </div>
        `;
        return;
    }

    chatSessions.forEach(session => {
        const sessionElement = document.createElement('div');
        sessionElement.className = `session-item ${session.id === currentSessionId ? 'active' : ''}`;
        sessionElement.setAttribute('data-session-id', session.id);
        sessionElement.onclick = () => switchSession(session.id);

        sessionElement.innerHTML = `
            <span>${session.title}</span>
            <small>${session.last_activity}</small>
        `;

        sessionsContainer.appendChild(sessionElement);
    });
}

function renderChatMessages(messages) {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';

    if (!messages || messages.length === 0) {
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">
                    <i class="fas fa-hive"></i>
                </div>
                <h3>Start a conversation</h3>
                <p>Type your first message to begin chatting with our AI assistant.</p>
            </div>
        `;
        return;
    }

    messages.forEach(message => {
        addMessageToChat(message.type, message.text, formatTime(new Date(message.timestamp)));
    });
}

function addMessageToChat(type, text, time) {
    const chatMessages = document.getElementById('chatMessages');

    // Xóa welcome message nếu có
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const avatarIcon = type === 'ai' ? 'fas fa-robot' : 'fas fa-user';

    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="${avatarIcon}"></i>
        </div>
        <div class="message-content">
            <div class="message-text">${text}</div>
            <div class="message-time">${time}</div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
}

function updateChatHeader(title) {
    document.getElementById('chatTitle').textContent = title;
}

function enableChatInput() {
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.querySelector('.send-btn');

    messageInput.disabled = false;
    messageInput.placeholder = "Type your message here...";
    sendBtn.disabled = false;
}

function disableChatInput() {
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.querySelector('.send-btn');

    messageInput.disabled = true;
    messageInput.placeholder = "Select a chat session to start messaging...";
    sendBtn.disabled = true;
}

// Event Handlers
function switchSession(sessionId) {
    // Cập nhật active state
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
    });

    // Tìm session item theo sessionId
    const activeItem = document.querySelector(`[data-session-id="${sessionId}"]`);
    if (activeItem) {
        activeItem.classList.add('active');
    }

    // Cập nhật current session
    currentSessionId = sessionId;

    // Load session detail
    loadChatSessionDetail(sessionId);
}

function startNewChat() {
    document.getElementById('newChatModal').style.display = 'block';
    document.getElementById('newChatTitle').focus();
}

function closeNewChatModal() {
    document.getElementById('newChatModal').style.display = 'none';
    document.getElementById('newChatTitle').value = 'Chat mới';
}

function createNewChat() {
    const title = document.getElementById('newChatTitle').value.trim();

    if (!title) {
        showErrorMessage('Vui lòng nhập tiêu đề chat');
        return;
    }

    createNewChatSession(title);
}

function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message || !currentSessionId) return;

    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Send message via API
    sendMessageToAPI(message);
}

function clearCurrentChat() {
    if (!currentSessionId) {
        showErrorMessage('No active chat session');
        return;
    }

    if (confirm('Are you sure you want to clear this chat?')) {
        clearChatSession(currentSessionId);
    }
}

function exportCurrentChat() {
    if (!currentSessionId) {
        showErrorMessage('No active chat session');
        return;
    }

    exportChatSession(currentSessionId);
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Utility Functions
function formatTime(date) {
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) { // Less than 1 minute
        return 'Just now';
    } else if (diff < 3600000) { // Less than 1 hour
        const minutes = Math.floor(diff / 60000);
        return `${minutes} min ago`;
    } else if (diff < 86400000) { // Less than 1 day
        const hours = Math.floor(diff / 3600000);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
        return date.toLocaleDateString();
    }
}

function autoResizeTextarea() {
    const textarea = document.getElementById('messageInput');
    textarea.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Loading and Error States
function showLoadingState() {
    // Có thể thêm loading spinner
}

function hideLoadingState() {
    // Ẩn loading spinner
}

function showErrorMessage(message) {
    // Hiển thị error message
    alert(`Error: ${message}`);
}

function showSuccessMessage(message) {
    // Hiển thị success message
    alert(`Success: ${message}`);
}

// Auto-refresh sessions every 30 seconds
setInterval(() => {
    if (chatSessions.length > 0) {
        loadChatSessions();
    }
}, 30000);
