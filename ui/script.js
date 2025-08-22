// Chat sessions data
let chatSessions = [
    {
        id: 0,
        title: "General Support",
        icon: "fas fa-comments",
        lastActivity: "2 min ago",
        messages: [
            {
                type: "ai",
                text: "Hello! Welcome to HiveSpace. I'm your AI assistant, ready to help you with any questions about our products, orders, or general support. How can I assist you today?",
                time: "Just now"
            }
        ]
    },
    {
        id: 1,
        title: "Order Inquiry",
        icon: "fas fa-shopping-cart",
        lastActivity: "1 hour ago",
        messages: [
            {
                type: "ai",
                text: "Hi there! I can help you with your order. What would you like to know?",
                time: "1 hour ago"
            }
        ]
    },
    {
        id: 2,
        title: "Product Info",
        icon: "fas fa-box",
        lastActivity: "3 hours ago",
        messages: [
            {
                type: "ai",
                text: "Welcome! I'm here to provide detailed information about our products. What would you like to learn about?",
                time: "3 hours ago"
            }
        ]
    }
];

let currentSessionId = 0;

// Initialize the chat
document.addEventListener('DOMContentLoaded', function () {
    updateChatDisplay();
    autoResizeTextarea();
});

// Switch between chat sessions
function switchSession(sessionId) {
    // Remove active class from all sessions
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
    });

    // Add active class to selected session
    document.querySelectorAll('.session-item')[sessionId].classList.add('active');

    // Update current session
    currentSessionId = sessionId;

    // Update chat display
    updateChatDisplay();

    // Update chat title
    const session = chatSessions[sessionId];
    document.querySelector('.chat-title h3').textContent = session.title;
}

// Start a new chat session
function startNewChat() {
    const newSession = {
        id: chatSessions.length,
        title: `New Chat ${chatSessions.length + 1}`,
        icon: "fas fa-comments",
        lastActivity: "Just now",
        messages: [
            {
                type: "ai",
                text: "Hello! I'm your HiveSpace AI assistant. How can I help you today?",
                time: "Just now"
            }
        ]
    };

    chatSessions.push(newSession);

    // Add new session to sidebar
    addSessionToSidebar(newSession);

    // Switch to new session
    switchSession(newSession.id);
}

// Add new session to sidebar
function addSessionToSidebar(session) {
    const sessionsContainer = document.querySelector('.chat-sessions');
    const sessionElement = document.createElement('div');
    sessionElement.className = 'session-item';
    sessionElement.onclick = () => switchSession(session.id);

    sessionElement.innerHTML = `
        <i class="${session.icon}"></i>
        <span>${session.title}</span>
        <small>${session.lastActivity}</small>
    `;

    sessionsContainer.appendChild(sessionElement);
}

// Update chat display
function updateChatDisplay() {
    const chatMessages = document.getElementById('chatMessages');
    const session = chatSessions[currentSessionId];

    chatMessages.innerHTML = '';

    session.messages.forEach(message => {
        addMessageToChat(message.type, message.text, message.time);
    });

    scrollToBottom();
}

// Add message to chat
function addMessageToChat(type, text, time) {
    const chatMessages = document.getElementById('chatMessages');
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

// Send message
function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (message === '') return;

    // Add user message
    const userMessage = {
        type: "user",
        text: message,
        time: getCurrentTime()
    };

    chatSessions[currentSessionId].messages.push(userMessage);
    addMessageToChat("user", message, userMessage.time);

    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Update last activity
    chatSessions[currentSessionId].lastActivity = "Just now";
    updateSessionActivity();

    // Simulate AI response
    setTimeout(() => {
        const aiResponse = generateAIResponse(message);
        const aiMessage = {
            type: "ai",
            text: aiResponse,
            time: getCurrentTime()
        };

        chatSessions[currentSessionId].messages.push(aiMessage);
        addMessageToChat("ai", aiResponse, aiMessage.time);

        scrollToBottom();
    }, 1000);

    scrollToBottom();
}

// Generate AI response (simulated)
function generateAIResponse(userMessage) {
    const responses = [
        "Thank you for your message! I understand you're asking about that. Let me help you with more details.",
        "That's a great question! Based on what you've shared, I can provide you with the following information.",
        "I appreciate you reaching out about this. Here's what I can tell you based on your inquiry.",
        "Thanks for asking! This is something I can definitely help you with. Let me break it down for you.",
        "Excellent question! I have some helpful information that should address your concerns."
    ];

    // Simple keyword-based responses
    if (userMessage.toLowerCase().includes('order') || userMessage.toLowerCase().includes('purchase')) {
        return "I can help you with your order! Please provide your order number or email address so I can look up the details for you.";
    } else if (userMessage.toLowerCase().includes('product') || userMessage.toLowerCase().includes('item')) {
        return "I'd be happy to tell you more about our products! Which specific product are you interested in learning about?";
    } else if (userMessage.toLowerCase().includes('price') || userMessage.toLowerCase().includes('cost')) {
        return "I can help you with pricing information! Could you specify which product or service you're asking about?";
    } else if (userMessage.toLowerCase().includes('shipping') || userMessage.toLowerCase().includes('delivery')) {
        return "Great question about shipping! Our standard delivery takes 3-5 business days. Would you like to know about expedited options?";
    } else if (userMessage.toLowerCase().includes('return') || userMessage.toLowerCase().includes('refund')) {
        return "I understand you're asking about returns. We have a 30-day return policy for most items. What specific item are you looking to return?";
    }

    return responses[Math.floor(Math.random() * responses.length)];
}

// Get current time
function getCurrentTime() {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    return `${hours}:${minutes.toString().padStart(2, '0')}`;
}

// Update session activity in sidebar
function updateSessionActivity() {
    const sessionItems = document.querySelectorAll('.session-item');
    sessionItems[currentSessionId].querySelector('small').textContent = "Just now";
}

// Handle Enter key press
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Auto-resize textarea
function autoResizeTextarea() {
    const textarea = document.getElementById('messageInput');
    textarea.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

// Scroll to bottom of chat
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Clear chat
document.addEventListener('DOMContentLoaded', function () {
    const clearBtn = document.querySelector('.action-btn[title="Clear Chat"]');
    if (clearBtn) {
        clearBtn.addEventListener('click', function () {
            if (confirm('Are you sure you want to clear this chat?')) {
                chatSessions[currentSessionId].messages = [
                    {
                        type: "ai",
                        text: "Chat cleared. How can I help you today?",
                        time: getCurrentTime()
                    }
                ];
                updateChatDisplay();
            }
        });
    }
});

// Export chat (placeholder functionality)
document.addEventListener('DOMContentLoaded', function () {
    const exportBtn = document.querySelector('.action-btn[title="Export Chat"]');
    if (exportBtn) {
        exportBtn.addEventListener('click', function () {
            const session = chatSessions[currentSessionId];
            const chatText = session.messages.map(msg =>
                `${msg.type.toUpperCase()}: ${msg.text} (${msg.time})`
            ).join('\n\n');

            const blob = new Blob([chatText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `hivespace-chat-${session.title.replace(/\s+/g, '-')}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        });
    }
});
