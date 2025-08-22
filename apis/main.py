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

# Fake data - Danh sách phiên chat
chat_sessions = [
    {
        "id": "session_001",
        "title": "Hỗ trợ khách hàng - Tư vấn sản phẩm và dịch vụ",
        "last_activity": "2 min ago",
        "message_count": 8,
        "created_at": "2024-01-15T10:00:00",
        "updated_at": "2024-01-15T14:30:00",
        "messages": [
            {
                "id": "msg_001",
                "type": "ai",
                "text": "Xin chào! Chào mừng bạn đến với HiveSpace. Tôi là trợ lý AI, sẵn sàng hỗ trợ bạn với mọi câu hỏi về sản phẩm, đơn hàng hoặc dịch vụ của chúng tôi. Bạn cần hỗ trợ gì hôm nay?",
                "timestamp": "2024-01-15T10:00:00",
                "sender_name": "HiveSpace AI"
            },
            {
                "id": "msg_002",
                "type": "user",
                "text": "Chào bạn! Tôi muốn tìm hiểu về sản phẩm smartphone mới nhất của HiveSpace",
                "timestamp": "2024-01-15T10:05:00",
                "sender_name": "Nguyễn Văn A"
            },
            {
                "id": "msg_003",
                "type": "ai",
                "text": "Tuyệt vời! HiveSpace vừa ra mắt smartphone HivePhone Pro 2024 với nhiều tính năng đột phá. Sản phẩm có màn hình 6.7 inch AMOLED, chip Snapdragon 8 Gen 3, camera 108MP chính và pin 5000mAh. Bạn có muốn biết thêm về giá cả hoặc thông số kỹ thuật không?",
                "timestamp": "2024-01-15T10:06:00",
                "sender_name": "HiveSpace AI"
            },
            {
                "id": "msg_004",
                "type": "user",
                "text": "Giá bao nhiêu vậy? Và có khuyến mãi gì không?",
                "timestamp": "2024-01-15T10:08:00",
                "sender_name": "Nguyễn Văn A"
            },
            {
                "id": "msg_005",
                "type": "ai",
                "text": "HivePhone Pro 2024 có giá niêm yết 25.990.000 VNĐ. Hiện tại chúng tôi đang có chương trình khuyến mãi đặc biệt: giảm giá 2.000.000 VNĐ, tặng kèm tai nghe không dây HiveBuds Pro trị giá 1.500.000 VNĐ và bảo hành 2 năm. Tổng giá trị quà tặng lên đến 3.500.000 VNĐ! Bạn có muốn đặt hàng ngay không?",
                "timestamp": "2024-01-15T10:09:00",
                "sender_name": "HiveSpace AI"
            },
            {
                "id": "msg_006",
                "type": "user",
                "text": "Tuyệt quá! Tôi muốn đặt hàng. Làm thế nào để đặt?",
                "timestamp": "2024-01-15T10:12:00",
                "sender_name": "Nguyễn Văn A"
            },
            {
                "id": "msg_007",
                "type": "ai",
                "text": "Rất đơn giản! Bạn có thể đặt hàng qua website chính thức của HiveSpace, qua ứng dụng mobile, hoặc gọi hotline 1900-xxxx. Tôi cũng có thể hỗ trợ bạn đặt hàng ngay tại đây. Bạn muốn đặt qua kênh nào?",
                "timestamp": "2024-01-15T10:13:00",
                "sender_name": "HiveSpace AI"
            },
            {
                "id": "msg_008",
                "type": "user",
                "text": "Tôi muốn đặt qua website. Cảm ơn bạn đã tư vấn rất chi tiết!",
                "timestamp": "2024-01-15T14:30:00",
                "sender_name": "Nguyễn Văn A"
            }
        ]
    },
    {
        "id": "session_002",
        "title": "Tư vấn đơn hàng - Theo dõi vận chuyển và thanh toán",
        "last_activity": "1 hour ago",
        "message_count": 6,
        "created_at": "2024-01-15T09:00:00",
        "updated_at": "2024-01-15T13:00:00",
        "messages": [
            {
                "id": "msg_009",
                "type": "ai",
                "text": "Xin chào! Tôi có thể giúp gì cho bạn về đơn hàng? Bạn cần tư vấn về vận chuyển, thanh toán hay có vấn đề gì khác?",
                "timestamp": "2024-01-15T09:00:00",
                "sender_name": "HiveSpace AI"
            },
            {
                "id": "msg_010",
                "type": "user",
                "text": "Chào bạn! Tôi đã đặt hàng laptop HiveBook Pro vào hôm qua, đơn hàng số #HSB2024001. Khi nào tôi nhận được hàng?",
                "timestamp": "2024-01-15T09:05:00",
                "sender_name": "Trần Thị B"
            },
            {
                "id": "msg_011",
                "type": "ai",
                "text": "Cảm ơn bạn đã đặt hàng! Tôi đã kiểm tra đơn hàng #HSB2024001 của bạn. Laptop HiveBook Pro đã được xác nhận và đang được chuẩn bị để giao hàng. Dự kiến bạn sẽ nhận được hàng trong 2-3 ngày làm việc tới.",
                "timestamp": "2024-01-15T09:06:00",
                "sender_name": "HiveSpace AI"
            },
            {
                "id": "msg_012",
                "type": "user",
                "text": "Tuyệt! Vậy phí vận chuyển là bao nhiêu? Và tôi có thể thanh toán bằng cách nào?",
                "timestamp": "2024-01-15T09:10:00",
                "sender_name": "Trần Thị B"
            },
            {
                "id": "msg_013",
                "type": "ai",
                "text": "Phí vận chuyển cho đơn hàng của bạn là 50.000 VNĐ (miễn phí cho đơn hàng trên 5 triệu VNĐ). Bạn có thể thanh toán bằng: thẻ tín dụng/ghi nợ, chuyển khoản ngân hàng, hoặc thanh toán khi nhận hàng (COD). Bạn muốn chọn phương thức thanh toán nào?",
                "timestamp": "2024-01-15T09:11:00",
                "sender_name": "HiveSpace AI"
            },
            {
                "id": "msg_014",
                "type": "user",
                "text": "Tôi sẽ thanh toán bằng thẻ tín dụng. Cảm ơn bạn đã tư vấn!",
                "timestamp": "2024-01-15T13:00:00",
                "sender_name": "Trần Thị B"
            }
        ]
    },
    {
        "id": "session_003",
        "title": "Thông tin sản phẩm - So sánh và đánh giá chi tiết",
        "last_activity": "3 hours ago",
        "message_count": 7,
        "created_at": "2024-01-15T08:00:00",
        "updated_at": "2024-01-15T11:00:00",
        "messages": [
            {
                "id": "msg_015",
                "type": "ai",
                "text": "Chào mừng bạn! Tôi ở đây để cung cấp thông tin chi tiết về các sản phẩm của HiveSpace. Bạn muốn tìm hiểu về sản phẩm nào? Tôi có thể giúp bạn so sánh, đánh giá và đưa ra lời khuyên phù hợp.",
                "timestamp": "2024-01-15T08:00:00",
                "sender_name": "HiveSpace AI"
            },
            {
                "id": "msg_016",
                "type": "user",
                "text": "Tôi đang phân vân giữa HivePhone Pro và HivePhone Max. Bạn có thể so sánh hai sản phẩm này không?",
                "timestamp": "2024-01-15T08:10:00",
                "sender_name": "Lê Văn C"
            },
            {
                "id": "msg_017",
                "type": "ai",
                "text": "Tuyệt vời! Hãy để tôi so sánh chi tiết hai sản phẩm này cho bạn:\n\nHivePhone Pro (25.990.000 VNĐ):\n- Màn hình 6.7 inch AMOLED\n- Chip Snapdragon 8 Gen 3\n- Camera 108MP + 12MP + 10MP\n- Pin 5000mAh, sạc 67W\n\nHivePhone Max (32.990.000 VNĐ):\n- Màn hình 6.9 inch AMOLED 2K\n- Chip Snapdragon 8 Gen 3 Plus\n- Camera 200MP + 50MP + 12MP + 10MP\n- Pin 6000mAh, sạc 100W\n\nBạn muốn biết thêm về điểm nào?",
                "timestamp": "2024-01-15T08:11:00",
                "sender_name": "HiveSpace AI"
            },
            {
                "id": "msg_018",
                "type": "user",
                "text": "Vậy hiệu năng và thời lượng pin thì sao? Cái nào tốt hơn?",
                "timestamp": "2024-01-15T08:15:00",
                "sender_name": "Lê Văn C"
            },
            {
                "id": "msg_019",
                "type": "ai",
                "text": "Về hiệu năng, cả hai đều rất mạnh mẽ nhưng HivePhone Max có chip Plus nên hiệu suất cao hơn khoảng 15-20%. Đặc biệt khi chơi game nặng hoặc xử lý video 4K.\n\nVề pin, HivePhone Max có ưu thế rõ rệt:\n- Pin lớn hơn (6000mAh vs 5000mAh)\n- Sạc nhanh hơn (100W vs 67W)\n- Thời gian sử dụng lâu hơn 2-3 giờ\n\nNếu bạn là người dùng nặng, tôi khuyên chọn Max. Còn nếu chỉ dùng cơ bản thì Pro đã đủ.",
                "timestamp": "2024-01-15T08:16:00",
                "sender_name": "HiveSpace AI"
            },
            {
                "id": "msg_020",
                "type": "user",
                "text": "Cảm ơn bạn đã phân tích rất chi tiết! Tôi sẽ cân nhắc và quyết định sau.",
                "timestamp": "2024-01-15T11:00:00",
                "sender_name": "Lê Văn C"
            }
        ]
    }
]

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
    
    # Tạo phản hồi AI
    ai_response = generate_ai_response(request.message)
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
            
            # Gọi agent để xử lý câu hỏi với streaming
            response_content = ""
            for event in agent.react_agent_graph.stream({
                "messages": [
                    {
                        "role": "system",
                        "content": """Bạn là AVA, trợ lý số của công ty cổ phần MISA. 

Bạn có khả năng:
1. Tìm kiếm thông tin trên web để cập nhật kiến thức mới nhất
2. Tìm kiếm thông tin sản phẩm trong cơ sở dữ liệu nội bộ
3. Tìm kiếm thông tin đơn hàng và trạng thái giao hàng

Khi người dùng hỏi về sản phẩm, hãy sử dụng product_search tool để tìm thông tin chi tiết.
Khi cần thông tin mới nhất, hãy sử dụng web_search tool để tìm kiếm trên internet.
Khi người dùng hỏi về đơn hàng, hãy sử dụng order_search tool để tìm thông tin đơn hàng."""
                    },
                    {
                        "role": "user",
                        "content": request.message
                    }
                ]
            }):
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
