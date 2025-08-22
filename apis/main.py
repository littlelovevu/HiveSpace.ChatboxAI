"""
HiveSpace Chatbox API
API backend cho hệ thống chatbox HiveSpace với quản lý phiên chat và lịch sử tin nhắn
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import json
import os
from agents.agent import create_agent
from agents.tools.image_tool import build_general_image_markdown, build_invoice_html, invoice_html_to_image
import json
import os

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

# Load AI system prompt from external document
AI_SYSTEM_PROMPT = ""

def load_ai_system_prompt():
    """Load system prompt cho AI từ file ai_system_prompt.md (nếu có)."""
    global AI_SYSTEM_PROMPT
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(base_dir, "ai_system_prompt.md")
        with open(prompt_path, "r", encoding="utf-8") as f:
            AI_SYSTEM_PROMPT = f.read().strip()
    except Exception:
        # Fallback nội dung mặc định nếu chưa có file
        AI_SYSTEM_PROMPT = (
            "Bạn là AVA, trợ lý số của công ty cổ phần MISA.\n\n"
            "Bạn có khả năng:\n"
            "1. Tìm kiếm thông tin trên web để cập nhật kiến thức mới nhất\n"
            "2. Tìm kiếm thông tin sản phẩm trong cơ sở dữ liệu nội bộ\n"
            "3. Tìm kiếm thông tin đơn hàng và trạng thái giao hàng\n"
            "4. Tạo hình ảnh theo yêu cầu (hóa đơn hoặc tổng quát)\n\n"
            "Khi người dùng hỏi về sản phẩm, hãy sử dụng product_search tool để tìm thông tin chi tiết.\n"
            "Khi cần thông tin mới nhất, hãy sử dụng web_search tool để tìm kiếm trên internet.\n"
            "Khi người dùng hỏi về đơn hàng, hãy sử dụng order_search tool để tìm thông tin đơn hàng.\n"
            "Khi người dùng yêu cầu tạo hình ảnh hóa đơn/đơn hàng, tôi sẽ tạo hóa đơn đơn giản với background trắng, text đen, không trang trí, kích thước 400x600.\n"
            "Khi người dùng yêu cầu tạo hình ảnh khác, tôi sẽ tạo hình ảnh tổng quát với kích thước 512x512."
        )

# Nạp prompt ngay khi khởi động
load_ai_system_prompt()

PRODUCTS_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "products.json")

def _ensure_products_db_dir():
    try:
        os.makedirs(os.path.dirname(PRODUCTS_DB_PATH), exist_ok=True)
    except Exception:
        pass

def load_imported_products():
    """Load products imported from txt into JSON store."""
    try:
        if not os.path.exists(PRODUCTS_DB_PATH):
            return []
        with open(PRODUCTS_DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_imported_products(products):
    """Persist imported products to JSON store (list of dicts)."""
    _ensure_products_db_dir()
    with open(PRODUCTS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

def import_products_from_txt(file_content: bytes):
    """Parse .txt content and append products into JSON store.

    Supported formats (UTF-8 text):
    - CSV header: name,price,category,brand,in_stock,rating
      Example line: SmartHome Hub Pro,199,Home & Garden,Acme,true,4.6
    - Pipe-delimited header: name|price|category|brand|in_stock|rating
    Booleans: true/false/1/0/yes/no. Missing rating defaults to 0.0.
    """
    try:
        text = file_content.decode("utf-8", errors="ignore").strip()
    except Exception:
        return {"success": False, "message": "Không đọc được nội dung file .txt"}

    if not text:
        return {"success": False, "message": "File .txt rỗng"}

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return {"success": False, "message": "File .txt không có dữ liệu"}

    header = lines[0].lower().replace(" ", "")
    delimiter = "," if "," in lines[0] else ("|" if "|" in lines[0] else None)
    expected_headers = ["name,price,category,brand,in_stock,rating", "name|price|category|brand|in_stock|rating"]
    if delimiter is None or header not in expected_headers:
        return {"success": False, "message": "Định dạng không hợp lệ. Cần header: name,price,category,brand,in_stock,rating"}

    def to_bool(v: str) -> bool:
        v = v.strip().lower()
        return v in ("true", "1", "yes", "y")

    imported = []
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(delimiter)]
        if len(parts) < 5:
            continue
        name = parts[0]
        try:
            price = float(parts[1])
        except Exception:
            continue
        category = parts[2] if len(parts) > 2 else "Others"
        brand = parts[3] if len(parts) > 3 else "Unknown"
        in_stock = to_bool(parts[4]) if len(parts) > 4 else True
        rating = 0.0
        if len(parts) > 5 and parts[5] != "":
            try:
                rating = float(parts[5])
            except Exception:
                rating = 0.0

        imported.append({
            "name": name,
            "price": price,
            "category": category,
            "brand": brand,
            "in_stock": in_stock,
            "rating": rating,
        })

    if not imported:
        return {"success": False, "message": "Không có dòng dữ liệu hợp lệ"}

    existing = load_imported_products()
    # Assign IDs after merge to avoid collision with built-in (1..100)
    current_max_id = max([p.get("id", 100) for p in existing] + [100])
    for item in imported:
        current_max_id += 1
        item["id"] = current_max_id
        existing.append(item)

    save_imported_products(existing)
    names = ", ".join([p["name"] for p in imported])
    return {"success": True, "count": len(imported), "names": names}

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
            # Thêm system prompt từ tài liệu bên ngoài
            history.append({"role": "system", "content": AI_SYSTEM_PROMPT})
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
                {"role": "system", "content": AI_SYSTEM_PROMPT},
                {"role": "system", "content": f"Thông tin bổ sung:\n- Thời gian hiện tại: {datetime.now().strftime('%m-%Y')}"}
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

@app.post("/api/messages/with-file")
async def send_message_with_file(
    session_id: str = Form(...),
    message: str = Form(""),
    file: UploadFile = File(...)
):
    """Gửi tin nhắn mới kèm file và nhận phản hồi AI thông minh"""
    # Tìm phiên chat
    session = None
    for s in chat_sessions:
        if s["id"] == session_id:
            session = s
            break
    
    if not session:
        raise HTTPException(status_code=404, detail="Phiên chat không tồn tại")
    
    # Kiểm tra file
    if not file:
        raise HTTPException(status_code=400, detail="Không có file được gửi")
    
    # Kiểm tra loại file được hỗ trợ
    allowed_types = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "application/msword", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Loại file {file.content_type} không được hỗ trợ. Chỉ chấp nhận: ảnh, PDF, Word, text"
        )
    
    # Thêm tin nhắn của user với file
    user_message_text = message if message else f"Đã gửi file: {file.filename}"
    user_message = {
        "id": f"msg_{str(uuid.uuid4())[:8]}",
        "type": "user",
        "text": user_message_text,
        "timestamp": get_current_timestamp(),
        "sender_name": "User"
    }
    
    session["messages"].append(user_message)
    
    # Xử lý file và tạo phản hồi AI thông minh
    try:
        # Đọc nội dung file
        file_content = await file.read()
        
        # Tạo prompt thông minh dựa trên yêu cầu của user
        user_request = message.lower() if message else ""
        file_info = f"File: {file.filename} ({len(file_content)} bytes, {file.content_type})"
        
        # Phân tích yêu cầu của user
        if "cv" in user_request or "resume" in user_request or "sơ yếu lý lịch" in user_request:
            # Xử lý CV/Resume
            ai_response = await process_cv_file(file, file_content, user_request)
        elif "hóa đơn" in user_request or "invoice" in user_request or "bill" in user_request:
            # Xử lý hóa đơn
            ai_response = await process_invoice_file(file, file_content, user_request)
        elif "báo cáo" in user_request or "report" in user_request:
            # Xử lý báo cáo
            ai_response = await process_report_file(file, file_content, user_request)
        elif "hợp đồng" in user_request or "contract" in user_request:
            # Xử lý hợp đồng
            ai_response = await process_contract_file(file, file_content, user_request)
        elif "preview" in user_request or "xem trước" in user_request or "phân tích" in user_request:
            # Xử lý preview/analysis
            ai_response = await process_preview_file(file, file_content, user_request)
        else:
            # Xử lý file thông thường với AI thông minh
            ai_response = await process_general_file(file, file_content, user_request)
        
    except Exception as e:
        ai_response = f"Xin lỗi, tôi gặp sự cố khi xử lý file **{file.filename}**. Vui lòng thử lại sau. (Lỗi: {str(e)})"
    
    # Tạo tin nhắn AI
    ai_message = {
        "id": f"msg_{str(uuid.uuid4())[:8]}",
        "type": "ai",
        "text": ai_response,
        "timestamp": get_current_timestamp(),
        "sender_name": "HiveSpace AI"
    }
    
    session["messages"].append(ai_message)
    
    # Cập nhật thời gian hoạt động
    update_session_activity(session_id)
    
    return {
        "success": True,
        "user_message": user_message,
        "ai_response": ai_message,
        "file_info": {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_content) if 'file_content' in locals() else 0
        },
        "session_updated": True
    }

async def process_cv_file(file: UploadFile, file_content: bytes, user_request: str) -> str:
    """Xử lý file CV/Resume một cách thông minh"""
    try:
        if file.content_type == "application/pdf":
            # Xử lý PDF CV
            ai_response = f"📋 **PHÂN TÍCH CV/Resume: {file.filename}**\n\n"
            ai_response += f"Tôi đã nhận được CV của bạn. Dựa trên yêu cầu \"{user_request}\", tôi sẽ phân tích:\n\n"
            ai_response += "**📊 Thông tin cơ bản:**\n"
            ai_response += f"- Tên file: {file.filename}\n"
            ai_response += f"- Kích thước: {len(file_content):,} bytes\n"
            ai_response += f"- Loại file: PDF\n\n"
            
            # Thêm phân tích thông minh
            if "preview" in user_request or "xem trước" in user_request:
                ai_response += "**🔍 Phân tích nội dung CV:**\n"
                ai_response += "• Đây là file PDF, tôi có thể giúp bạn:\n"
                ai_response += "  - Xem trước nội dung chính\n"
                ai_response += "  - Kiểm tra thông tin liên hệ\n"
                ai_response += "  - Đánh giá cấu trúc CV\n"
                ai_response += "  - Gợi ý cải thiện\n\n"
                ai_response += "**💡 Gợi ý:** Bạn có muốn tôi phân tích chi tiết hơn về kinh nghiệm làm việc, kỹ năng, hoặc đưa ra lời khuyên cải thiện CV không?"
            else:
                ai_response += "**💼 Tôi có thể giúp bạn:**\n"
                ai_response += "• Phân tích nội dung CV\n"
                ai_response += "• Đánh giá điểm mạnh/yếu\n"
                ai_response += "• Gợi ý cải thiện\n"
                ai_response += "• Tối ưu hóa cho vị trí cụ thể\n\n"
                ai_response += "Bạn muốn tôi tập trung vào khía cạnh nào của CV?"
            
        elif file.content_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            # Xử lý Word CV
            ai_response = f"📋 **PHÂN TÍCH CV/Resume: {file.filename}**\n\n"
            ai_response += f"Tôi đã nhận được CV Word của bạn. Dựa trên yêu cầu \"{user_request}\":\n\n"
            ai_response += "**📊 Thông tin cơ bản:**\n"
            ai_response += f"- Tên file: {file.filename}\n"
            ai_response += f"- Kích thước: {len(file_content):,} bytes\n"
            ai_response += f"- Loại file: Microsoft Word\n\n"
            
            ai_response += "**💼 Tôi có thể giúp bạn:**\n"
            ai_response += "• Phân tích nội dung CV\n"
            ai_response += "• Đánh giá cấu trúc và định dạng\n"
            ai_response += "• Gợi ý cải thiện\n"
            ai_response += "• Chuyển đổi sang PDF nếu cần\n\n"
            ai_response += "Bạn muốn tôi tập trung vào khía cạnh nào?"
            
        else:
            ai_response = f"📋 **PHÂN TÍCH CV/Resume: {file.filename}**\n\n"
            ai_response += f"Tôi đã nhận được file CV của bạn. Dựa trên yêu cầu \"{user_request}\":\n\n"
            ai_response += "**📊 Thông tin file:**\n"
            ai_response += f"- Tên file: {file.filename}\n"
            ai_response += f"- Kích thước: {len(file_content):,} bytes\n"
            ai_response += f"- Loại file: {file.content_type}\n\n"
            ai_response += "**💼 Tôi có thể giúp bạn:**\n"
            ai_response += "• Phân tích nội dung CV\n"
            ai_response += "• Đánh giá và gợi ý cải thiện\n"
            ai_response += "• Tối ưu hóa cho mục tiêu nghề nghiệp\n\n"
            ai_response += "Bạn muốn tôi tập trung vào khía cạnh nào?"
        
        return ai_response
        
    except Exception as e:
        return f"Xin lỗi, tôi gặp sự cố khi xử lý CV. Vui lòng thử lại sau. (Lỗi: {str(e)})"

async def process_invoice_file(file: UploadFile, file_content: bytes, user_request: str) -> str:
    """Xử lý file hóa đơn một cách thông minh"""
    try:
        ai_response = f"🧾 **PHÂN TÍCH HÓA ĐƠN: {file.filename}**\n\n"
        ai_response += f"Tôi đã nhận được file hóa đơn của bạn. Dựa trên yêu cầu \"{user_request}\":\n\n"
        ai_response += "**📊 Thông tin file:**\n"
        ai_response += f"- Tên file: {file.filename}\n"
        ai_response += f"- Kích thước: {len(file_content):,} bytes\n"
        ai_response += f"- Loại file: {file.content_type}\n\n"
        
        if file.content_type == "application/pdf":
            ai_response += "**🔍 Tôi có thể giúp bạn:**\n"
            ai_response += "• Trích xuất thông tin hóa đơn\n"
            ai_response += "• Phân tích chi tiết giao dịch\n"
            ai_response += "• Tính toán tổng tiền, thuế\n"
            ai_response += "• Kiểm tra tính chính xác\n"
            ai_response += "• Xuất dữ liệu sang Excel\n\n"
            ai_response += "**💡 Gợi ý:** Bạn muốn tôi phân tích chi tiết hóa đơn này không?"
        else:
            ai_response += "**💼 Tôi có thể giúp bạn:**\n"
            ai_response += "• Phân tích nội dung hóa đơn\n"
            ai_response += "• Kiểm tra tính chính xác\n"
            ai_response += "• Tổng hợp dữ liệu\n\n"
            ai_response += "Bạn muốn tôi tập trung vào khía cạnh nào?"
        
        return ai_response
        
    except Exception as e:
        return f"Xin lỗi, tôi gặp sự cố khi xử lý hóa đơn. Vui lòng thử lại sau. (Lỗi: {str(e)})"

async def process_report_file(file: UploadFile, file_content: bytes, user_request: str) -> str:
    """Xử lý file báo cáo một cách thông minh"""
    try:
        ai_response = f"📊 **PHÂN TÍCH BÁO CÁO: {file.filename}**\n\n"
        ai_response += f"Tôi đã nhận được file báo cáo của bạn. Dựa trên yêu cầu \"{user_request}\":\n\n"
        ai_response += "**📊 Thông tin file:**\n"
        ai_response += f"- Tên file: {file.filename}\n"
        ai_response += f"- Kích thước: {len(file_content):,} bytes\n"
        ai_response += f"- Loại file: {file.content_type}\n\n"
        
        ai_response += "**🔍 Tôi có thể giúp bạn:**\n"
        ai_response += "• Phân tích nội dung báo cáo\n"
        ai_response += "• Trích xuất dữ liệu quan trọng\n"
        ai_response += "• Tóm tắt điểm chính\n"
        ai_response += "• Tạo biểu đồ và phân tích\n"
        ai_response += "• So sánh với báo cáo trước\n\n"
        ai_response += "**💡 Gợi ý:** Bạn muốn tôi tập trung vào khía cạnh nào của báo cáo?"
        
        return ai_response
        
    except Exception as e:
        return f"Xin lỗi, tôi gặp sự cố khi xử lý báo cáo. Vui lòng thử lại sau. (Lỗi: {str(e)})"

async def process_contract_file(file: UploadFile, file_content: bytes, user_request: str) -> str:
    """Xử lý file hợp đồng một cách thông minh"""
    try:
        ai_response = f"📜 **PHÂN TÍCH HỢP ĐỒNG: {file.filename}**\n\n"
        ai_response += f"Tôi đã nhận được file hợp đồng của bạn. Dựa trên yêu cầu \"{user_request}\":\n\n"
        ai_response += "**📊 Thông tin file:**\n"
        ai_response += f"- Tên file: {file.filename}\n"
        ai_response += f"- Kích thước: {len(file_content):,} bytes\n"
        ai_response += f"- Loại file: {file.content_type}\n\n"
        
        ai_response += "**🔍 Tôi có thể giúp bạn:**\n"
        ai_response += "• Phân tích điều khoản hợp đồng\n"
        ai_response += "• Trích xuất thông tin quan trọng\n"
        ai_response += "• Kiểm tra rủi ro pháp lý\n"
        ai_response += "• Tóm tắt nghĩa vụ và quyền lợi\n"
        ai_response += "• So sánh với mẫu chuẩn\n\n"
        ai_response += "**💡 Gợi ý:** Bạn muốn tôi tập trung vào khía cạnh nào của hợp đồng?"
        
        return ai_response
        
    except Exception as e:
        return f"Xin lỗi, tôi gặp sự cố khi xử lý hợp đồng. Vui lòng thử lại sau. (Lỗi: {str(e)})"

async def process_preview_file(file: UploadFile, file_content: bytes, user_request: str) -> str:
    """Xử lý preview file một cách thông minh"""
    try:
        ai_response = f"👁️ **XEM TRƯỚC FILE: {file.filename}**\n\n"
        ai_response += f"Tôi đã nhận được yêu cầu xem trước file của bạn. Dựa trên yêu cầu \"{user_request}\":\n\n"
        ai_response += "**📊 Thông tin file:**\n"
        ai_response += f"- Tên file: {file.filename}\n"
        ai_response += f"- Kích thước: {len(file_content):,} bytes\n"
        ai_response += f"- Loại file: {file.content_type}\n\n"
        
        if file.content_type.startswith("image/"):
            ai_response += "**🖼️ Đây là file ảnh, tôi có thể:**\n"
            ai_response += "• Phân tích nội dung ảnh\n"
            ai_response += "• Nhận diện đối tượng\n"
            ai_response += "• Trích xuất văn bản (OCR)\n"
            ai_response += "• Phân tích màu sắc và bố cục\n\n"
            ai_response += "**💡 Gợi ý:** Bạn muốn tôi phân tích ảnh này như thế nào?"
            
        elif file.content_type == "application/pdf":
            ai_response += "**📄 Đây là file PDF, tôi có thể:**\n"
            ai_response += "• Trích xuất văn bản\n"
            ai_response += "• Phân tích cấu trúc\n"
            ai_response += "• Tóm tắt nội dung chính\n"
            ai_response += "• Trích xuất dữ liệu bảng\n\n"
            ai_response += "**💡 Gợi ý:** Bạn muốn tôi xem trước nội dung gì?"
            
        elif file.content_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            ai_response += "**📝 Đây là file Word, tôi có thể:**\n"
            ai_response += "• Phân tích nội dung\n"
            ai_response += "• Tóm tắt văn bản\n"
            ai_response += "• Trích xuất thông tin quan trọng\n"
            ai_response += "• Kiểm tra định dạng\n\n"
            ai_response += "**💡 Gợi ý:** Bạn muốn tôi xem trước phần nào?"
            
        elif file.content_type == "text/plain":
            try:
                text_content = file_content.decode('utf-8')
                ai_response += "**📃 Đây là file text, tôi có thể:**\n"
                ai_response += "• Phân tích nội dung\n"
                ai_response += "• Tóm tắt văn bản\n"
                ai_response += "• Trích xuất thông tin quan trọng\n\n"
                ai_response += "**📖 Nội dung file:**\n```\n{text_content[:300]}{'...' if len(text_content) > 300 else ''}\n```\n\n"
                ai_response += "**💡 Gợi ý:** Bạn muốn tôi phân tích chi tiết hơn không?"
            except UnicodeDecodeError:
                ai_response += "**⚠️ Lưu ý:** File text này có vấn đề về encoding. Tôi có thể giúp bạn:\n"
                ai_response += "• Chuyển đổi encoding\n"
                ai_response += "• Phân tích nội dung có thể đọc được\n\n"
                ai_response += "**💡 Gợi ý:** Bạn có muốn tôi thử đọc file với encoding khác không?"
        
        else:
            ai_response += "**📁 Đây là file đặc biệt, tôi có thể:**\n"
            ai_response += "• Phân tích thông tin cơ bản\n"
            ai_response += "• Kiểm tra tính toàn vẹn\n"
            ai_response += "• Đưa ra gợi ý xử lý\n\n"
            ai_response += "**💡 Gợi ý:** Bạn muốn tôi giúp gì với file này?"
        
        return ai_response
        
    except Exception as e:
        return f"Xin lỗi, tôi gặp sự cố khi xem trước file. Vui lòng thử lại sau. (Lỗi: {str(e)})"

async def process_general_file(file: UploadFile, file_content: bytes, user_request: str) -> str:
    """Xử lý file thông thường một cách thông minh"""
    try:
        ai_response = f"📁 **PHÂN TÍCH FILE: {file.filename}**\n\n"
        ai_response += f"Tôi đã nhận được file của bạn. Dựa trên yêu cầu \"{user_request}\":\n\n"
        ai_response += "**📊 Thông tin file:**\n"
        ai_response += f"- Tên file: {file.filename}\n"
        ai_response += f"- Kích thước: {len(file_content):,} bytes\n"
        ai_response += f"- Loại file: {file.content_type}\n\n"
        
        if file.content_type.startswith("image/"):
            ai_response += "**🖼️ Đây là file ảnh:**\n"
            ai_response += "• Tôi có thể phân tích nội dung ảnh\n"
            ai_response += "• Nhận diện đối tượng và văn bản\n"
            ai_response += "• Phân tích bố cục và màu sắc\n\n"
            ai_response += "**💡 Bạn muốn tôi làm gì với ảnh này?**"
            
        elif file.content_type == "application/pdf":
            ai_response += "**📄 Đây là file PDF:**\n"
            ai_response += "• Tôi có thể trích xuất văn bản\n"
            ai_response += "• Phân tích cấu trúc và nội dung\n"
            ai_response += "• Tóm tắt thông tin quan trọng\n\n"
            ai_response += "**💡 Bạn muốn tôi phân tích gì trong PDF này?**"
            
        elif file.content_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            ai_response += "**📝 Đây là file Word:**\n"
            ai_response += "• Tôi có thể phân tích nội dung\n"
            ai_response += "• Tóm tắt văn bản\n"
            ai_response += "• Trích xuất thông tin quan trọng\n\n"
            ai_response += "**💡 Bạn muốn tôi làm gì với file Word này?**"
            
        elif file.content_type == "text/plain":
            # Thử nhập sản phẩm từ file .txt nếu đúng định dạng
            result = import_products_from_txt(file_content)
            if result.get("success"):
                ai_response += "**🛒 ĐÃ THÊM SẢN PHẨM TỪ FILE .TXT**\n\n"
                ai_response += f"• Số lượng thêm mới: {result['count']}\n"
                ai_response += f"• Tên sản phẩm: {result['names']}\n\n"
                ai_response += "Bạn có thể dùng product_search để tìm các sản phẩm vừa thêm."
            else:
                try:
                    text_content = file_content.decode('utf-8')
                    ai_response += "**📃 Đây là file text:**\n"
                    ai_response += "• Tôi có thể phân tích nội dung\n"
                    ai_response += "• Tóm tắt văn bản\n"
                    ai_response += "• Trích xuất thông tin quan trọng\n\n"
                    ai_response += f"**ℹ️ Gợi ý:** Để thêm sản phẩm qua .txt, hãy dùng header: name,price,category,brand,in_stock,rating và mỗi dòng 1 sản phẩm.\n\n"
                    ai_response += f"**📖 Nội dung file (preview):**\n```\n{text_content[:200]}{'...' if len(text_content) > 200 else ''}\n```\n\n"
                    ai_response += "**💡 Bạn muốn tôi phân tích gì trong file text này?**"
                except UnicodeDecodeError:
                    ai_response += "**⚠️ Lưu ý:** File text này có vấn đề về encoding.\n"
                    ai_response += "• Tôi có thể giúp chuyển đổi encoding\n"
                    ai_response += "• Hoặc phân tích phần có thể đọc được\n\n"
                    ai_response += "**💡 Bạn muốn tôi làm gì với file này?**"
        
        else:
            ai_response += "**📁 Đây là file đặc biệt:**\n"
            ai_response += "• Tôi có thể phân tích thông tin cơ bản\n"
            ai_response += "• Kiểm tra tính toàn vẹn file\n"
            ai_response += "• Đưa ra gợi ý xử lý phù hợp\n\n"
            ai_response += "**💡 Bạn muốn tôi giúp gì với file này?**"
        
        return ai_response
        
    except Exception as e:
        return f"Xin lỗi, tôi gặp sự cố khi xử lý file. Vui lòng thử lại sau. (Lỗi: {str(e)})"

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
