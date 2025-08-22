"""
HiveSpace Chatbox API
API backend cho hệ thống chatbox HiveSpace với quản lý phiên chat và lịch sử tin nhắn
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import json
from agents.agent import create_agent
from agents.tools.image_tool import build_general_image_markdown, build_invoice_html, invoice_html_to_image

# Khởi tạo FastAPI app
app = FastAPI(
    title="HiveSpace Chatbox API",
    description="API backend cho hệ thống chatbox HiveSpace",
    version="1.0.0"
)

# Cấu hình CORS
origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:3000",
    "localhost:3000",
    "*"  # Cho phép tất cả origins trong development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Message(BaseModel):
    id: str
    type: str  # "user" hoặc "ai"
    text: str
    timestamp: str
    sender_name: Optional[str] = None

class ChatSession(BaseModel):
    id: str
    title: str
    last_activity: str
    message_count: int
    created_at: str
    updated_at: str

class ChatSessionDetail(BaseModel):
    id: str
    title: str
    last_activity: str
    messages: List[Message]
    created_at: str
    updated_at: str

class NewMessageRequest(BaseModel):
    session_id: str
    message: str

class NewSessionRequest(BaseModel):
    title: str

# Fake data - Danh sách phiên chat (khởi tạo rỗng, không có dữ liệu mẫu)
chat_sessions = []

# Helper functions
def get_current_timestamp():
    """Lấy timestamp hiện tại"""
    return datetime.now().isoformat()

def format_time_ago(timestamp_str):
    """Format thời gian thành dạng "X time ago" """
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} min ago"
        else:
            return "Just now"
    except:
        return "Unknown time"

def update_session_activity(session_id: str):
    """Cập nhật thời gian hoạt động của phiên chat"""
    for session in chat_sessions:
        if session["id"] == session_id:
            session["updated_at"] = get_current_timestamp()
            session["last_activity"] = "Just now"
            break

# Image utilities
def is_image_request(text: str) -> bool:
    """Nhận diện yêu cầu tạo hình ảnh từ người dùng"""
    if not text:
        return False
    keywords = [
        "tạo hình", "tạo ảnh", "vẽ ảnh", "vẽ hình", "generate image", "create an image",
        "image of", "hình minh họa", "poster", "logo", "bìa", "banner"
    ]
    t = text.lower()
    return any(k in t for k in keywords)

def is_invoice_image_request(text: str) -> bool:
    """Nhận diện yêu cầu tạo hình ảnh hóa đơn cụ thể"""
    if not text:
        return False
    t = text.lower()
    
    # Từ khóa liên quan đến hóa đơn/đơn hàng
    invoice_keywords = [
        "hóa đơn", "hoá đơn", "bill", "invoice", "receipt", "đơn hàng", "order",
        "biên lai", "phiếu thu", "chứng từ"
    ]
    
    # Từ khóa tạo ảnh
    image_keywords = [
        "tạo hình", "tạo ảnh", "vẽ ảnh", "vẽ hình", "generate image", "create an image",
        "hình minh họa", "minh họa"
    ]
    
    # Phải có cả hai loại từ khóa
    has_invoice = any(k in t for k in invoice_keywords)
    has_image = any(k in t for k in image_keywords)
    
    return has_invoice and has_image

"""Image helpers moved to agents.tools.image_tool.
We import and reuse them here to avoid duplication and keep main.py slim.
"""

def generate_ai_response(user_message: str) -> str:
    """Tạo phản hồi AI sử dụng HiveSpace Agent"""
    try:
        # Tạo agent instance
        agent = create_agent()
        
        # Gọi agent để xử lý câu hỏi
        response = agent.ask_simple_question(user_message)
        
        return response
    
    except Exception as e:
        print(f"Error calling AI agent: {str(e)}")
        # Fallback response nếu có lỗi
        return f"Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau. (Lỗi: {str(e)})"

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HiveSpace Chatbox API",
        "version": "1.0.0",
        "description": "API backend cho hệ thống chatbox HiveSpace",
        "endpoints": {
            "sessions": "/api/sessions",
            "session_detail": "/api/sessions/{session_id}",
            "new_session": "/api/sessions/new",
            "send_message": "/api/messages/send",
            "clear_session": "/api/sessions/{session_id}/clear"
        }
    }

@app.get("/api/sessions", response_model=List[ChatSession])
async def get_chat_sessions():
    """Lấy danh sách tất cả phiên chat"""
    # Cập nhật last_activity cho tất cả sessions
    for session in chat_sessions:
        session["last_activity"] = format_time_ago(session["updated_at"])
        session["message_count"] = len(session["messages"])
    
    return chat_sessions

@app.get("/api/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_chat_session_detail(session_id: str):
    """Lấy chi tiết phiên chat và lịch sử tin nhắn"""
    for session in chat_sessions:
        if session["id"] == session_id:
            # Cập nhật last_activity
            session["last_activity"] = format_time_ago(session["updated_at"])
            return session
    
    raise HTTPException(status_code=404, detail="Phiên chat không tồn tại")

@app.post("/api/sessions/new", response_model=ChatSessionDetail)
async def create_new_chat_session(request: NewSessionRequest):
    """Tạo phiên chat mới"""
    new_session = {
        "id": f"session_{str(uuid.uuid4())[:8]}",
        "title": request.title,
        "last_activity": "Just now",
        "message_count": 1,
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp(),
        "messages": [
            {
                "id": f"msg_{str(uuid.uuid4())[:8]}",
                "type": "ai",
                "text": "Xin chào! Tôi là trợ lý AI HiveSpace. Tôi có thể giúp gì cho bạn hôm nay?",
                "timestamp": get_current_timestamp(),
                "sender_name": "HiveSpace AI"
            }
        ]
    }
    
    chat_sessions.append(new_session)
    return new_session

@app.post("/api/messages/send")
async def send_message(request: NewMessageRequest):
    """Gửi tin nhắn mới và nhận phản hồi AI"""
    # Tìm phiên chat
    session = None
    for s in chat_sessions:
        if s["id"] == request.session_id:
            session = s
            break
    
    if not session:
        raise HTTPException(status_code=404, detail="Phiên chat không tồn tại")
    
    # Thêm tin nhắn của user
    user_message = {
        "id": f"msg_{str(uuid.uuid4())[:8]}",
        "type": "user",
        "text": request.message,
        "timestamp": get_current_timestamp(),
        "sender_name": "User"
    }
    
    session["messages"].append(user_message)
    
    # Phân loại yêu cầu tạo ảnh: hóa đơn hoặc tổng quát
    if is_invoice_image_request(request.message):
        prompt = request.message
        order_id, html = build_invoice_html(prompt)
        ai_response = invoice_html_to_image(order_id, html)
    elif is_image_request(request.message):
        prompt = request.message
        ai_response = build_general_image_markdown(prompt)
    else:
        try:
            agent = create_agent()
            # Lấy tối đa 20 tin nhắn gần nhất để làm ngữ cảnh
            recent_messages = session["messages"][-20:] if len(session["messages"]) > 0 else []
            # Chuyển đổi định dạng tin nhắn sang format mà agent mong đợi
            history = []
                        # Thêm system prompt
            history.append({
                "role": "system",
                "content": """Bạn là AVA, trợ lý số của công ty cổ phần MISA. 

Bạn có khả năng:
1. Tìm kiếm thông tin trên web để cập nhật kiến thức mới nhất
2. Tìm kiếm thông tin sản phẩm trong cơ sở dữ liệu nội bộ
3. Tìm kiếm thông tin đơn hàng và trạng thái giao hàng
4. Tạo hình ảnh theo yêu cầu (hóa đơn hoặc tổng quát)

Khi người dùng hỏi về sản phẩm, hãy sử dụng product_search tool để tìm thông tin chi tiết.
Khi cần thông tin mới nhất, hãy sử dụng web_search tool để tìm kiếm trên internet.
Khi người dùng hỏi về đơn hàng, hãy sử dụng order_search tool để tìm thông tin đơn hàng.
Khi người dùng yêu cầu tạo hình ảnh hóa đơn/đơn hàng, tôi sẽ tạo hóa đơn đơn giản với background trắng, text đen, không trang trí, kích thước 400x600.
Khi người dùng yêu cầu tạo hình ảnh khác, tôi sẽ tạo hình ảnh tổng quát với kích thước 512x512."""
            })
            history.append({
                "role": "system",
                "content": f"Thông tin bổ sung:\n- Thời gian hiện tại: {datetime.now().strftime('%m-%Y')}"
            })

            # Đưa lịch sử cũ vào
            for m in recent_messages:
                role = "assistant" if m["type"] == "ai" else "user"
                history.append({"role": role, "content": m["text"]})

            # Thêm câu hỏi hiện tại
            history.append({"role": "user", "content": request.message})

            ai_response = agent.ask_react_agent(history)
        except Exception as e:
            ai_response = f"Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau. (Lỗi: {str(e)})"
    ai_message = {
        "id": f"msg_{str(uuid.uuid4())[:8]}",
        "type": "ai",
        "text": ai_response,
        "timestamp": get_current_timestamp(),
        "sender_name": "HiveSpace AI"
    }
    
    session["messages"].append(ai_message)
    
    # Cập nhật thời gian hoạt động
    update_session_activity(request.session_id)
    
    return {
        "success": True,
        "user_message": user_message,
        "ai_response": ai_message,
        "session_updated": True
    }

@app.post("/api/messages/send/stream")
async def send_message_stream(request: NewMessageRequest):
    """Gửi tin nhắn mới và nhận phản hồi AI streaming"""
    # Tìm phiên chat
    session = None
    for s in chat_sessions:
        if s["id"] == request.session_id:
            session = s
            break
    
    if not session:
        raise HTTPException(status_code=404, detail="Phiên chat không tồn tại")
    
    # Thêm tin nhắn của user
    user_message = {
        "id": f"msg_{str(uuid.uuid4())[:8]}",
        "type": "user",
        "text": request.message,
        "timestamp": get_current_timestamp(),
        "sender_name": "User"
    }
    
    session["messages"].append(user_message)
    
    # Cập nhật thời gian hoạt động
    update_session_activity(request.session_id)
    
    async def generate_stream():
        try:
            # Tạo agent instance
            agent = create_agent()
            
            # Phân loại yêu cầu tạo ảnh: hóa đơn hoặc tổng quát -> stream markdown ngay
            if is_invoice_image_request(request.message):
                order_id, html = build_invoice_html(request.message)
                md = invoice_html_to_image(order_id, html)
                yield f"data: {json.dumps({'type': 'chunk', 'content': md})}\n\n"
                ai_message = {
                    "id": f"msg_{str(uuid.uuid4())[:8]}",
                    "type": "ai",
                    "text": md,
                    "timestamp": get_current_timestamp(),
                    "sender_name": "HiveSpace AI"
                }
                session["messages"].append(ai_message)
                yield f"data: {json.dumps({'type': 'complete', 'ai_message': ai_message})}\n\n"
                return
            elif is_image_request(request.message):
                md = build_general_image_markdown(request.message)
                yield f"data: {json.dumps({'type': 'chunk', 'content': md})}\n\n"
                ai_message = {
                    "id": f"msg_{str(uuid.uuid4())[:8]}",
                    "type": "ai",
                    "text": md,
                    "timestamp": get_current_timestamp(),
                    "sender_name": "HiveSpace AI"
                }
                session["messages"].append(ai_message)
                yield f"data: {json.dumps({'type': 'complete', 'ai_message': ai_message})}\n\n"
                return

            # Chuẩn bị lịch sử hội thoại (tối đa 20 tin nhắn gần nhất)
            recent_messages = session["messages"][-20:] if len(session["messages"]) > 0 else []
            history = [
                                {
                    "role": "system",
                    "content": """Bạn là AVA, trợ lý số của công ty cổ phần MISA. 

Bạn có khả năng:
1. Tìm kiếm thông tin trên web để cập nhật kiến thức mới nhất
2. Tìm kiếm thông tin sản phẩm trong cơ sở dữ liệu nội bộ
3. Tìm kiếm thông tin đơn hàng và trạng thái giao hàng
4. Tạo hình ảnh theo yêu cầu (hóa đơn hoặc tổng quát)

Khi người dùng hỏi về sản phẩm, hãy sử dụng product_search tool để tìm thông tin chi tiết.
Khi cần thông tin mới nhất, hãy sử dụng web_search tool để tìm kiếm trên internet.
Khi người dùng hỏi về đơn hàng, hãy sử dụng order_search tool để tìm thông tin đơn hàng.
Khi người dùng yêu cầu tạo hình ảnh hóa đơn/đơn hàng, tôi sẽ tạo hóa đơn đơn giản với background trắng, text đen, không trang trí, kích thước 400x600.
Khi người dùng yêu cầu tạo hình ảnh khác, tôi sẽ tạo hình ảnh tổng quát với kích thước 512x512."""
                },
                {
                    "role": "system",
                    "content": f"Thông tin bổ sung:\n- Thời gian hiện tại: {datetime.now().strftime('%m-%Y')}"
                }
            ]

            for m in recent_messages:
                role = "assistant" if m["type"] == "ai" else "user"
                history.append({"role": role, "content": m["text"]})

            history.append({"role": "user", "content": request.message})

            # Gọi agent để xử lý câu hỏi với streaming kèm lịch sử
            response_content = ""
            for event in agent.react_agent_graph.stream({"messages": history}):
                for key, value in event.items():
                    if key != "llm" or value["messages"][-1].content == "":
                        continue
                    
                    current_content = value["messages"][-1].content
                    if current_content != response_content:
                        # Gửi phần mới
                        new_part = current_content[len(response_content):]
                        if new_part:
                            yield f"data: {json.dumps({'type': 'chunk', 'content': new_part})}\n\n"
                        response_content = current_content
            
            # Lưu tin nhắn AI hoàn chỉnh
            ai_message = {
                "id": f"msg_{str(uuid.uuid4())[:8]}",
                "type": "ai",
                "text": response_content,
                "timestamp": get_current_timestamp(),
                "sender_name": "HiveSpace AI"
            }
            
            session["messages"].append(ai_message)
            
            # Gửi signal hoàn thành
            yield f"data: {json.dumps({'type': 'complete', 'ai_message': ai_message})}\n\n"
            
        except Exception as e:
            error_msg = f"Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau. (Lỗi: {str(e)})"
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.delete("/api/sessions/{session_id}/clear")
async def clear_chat_session(session_id: str):
    """Xóa tất cả tin nhắn trong phiên chat"""
    for session in chat_sessions:
        if session["id"] == session_id:
            # Giữ lại tin nhắn chào mừng
            session["messages"] = [
                {
                    "id": f"msg_{str(uuid.uuid4())[:8]}",
                    "type": "ai",
                    "text": "Chat cleared. How can I help you today?",
                    "timestamp": get_current_timestamp(),
                    "sender_name": "HiveSpace AI"
                }
            ]
            session["message_count"] = 1
            update_session_activity(session_id)
            return {"success": True, "message": "Đã xóa tất cả tin nhắn"}
    
    raise HTTPException(status_code=404, detail="Phiên chat không tồn tại")

@app.get("/api/sessions/{session_id}/export")
async def export_chat_session(session_id: str):
    """Xuất phiên chat thành text"""
    for session in chat_sessions:
        if session["id"] == session_id:
            chat_text = f"HiveSpace Chat Export - {session['title']}\n"
            chat_text += f"Created: {session['created_at']}\n"
            chat_text += f"Last Updated: {session['updated_at']}\n"
            chat_text += "=" * 50 + "\n\n"
            
            for msg in session["messages"]:
                sender = msg["sender_name"] if msg["sender_name"] else msg["type"].upper()
                chat_text += f"[{msg['timestamp']}] {sender}: {msg['text']}\n\n"
            
            return {
                "success": True,
                "filename": f"hivespace-chat-{session['title'].replace(' ', '-')}.txt",
                "content": chat_text
            }
    
    raise HTTPException(status_code=404, detail="Phiên chat không tồn tại")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Khởi động HiveSpace Chatbox API...")
    print("📱 API sẽ chạy tại: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
