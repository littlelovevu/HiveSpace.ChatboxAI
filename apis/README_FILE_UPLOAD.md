# 📁 HiveSpace Chatbox - Intelligent File Upload API

## 🚀 Tính năng mới: Xử lý file thông minh

API endpoint `/api/messages/with-file` đã được cập nhật để AI có thể xử lý file một cách thông minh dựa trên yêu cầu cụ thể của người dùng.

## 🔧 Cách sử dụng

### 1. Gửi file với message
```http
POST /api/messages/with-file
Content-Type: multipart/form-data

session_id: "session_123"
message: "preview file CV giúp tôi"
file: [file upload]
```

### 2. Các loại yêu cầu được hỗ trợ

#### 📋 CV/Resume Processing
- **Trigger keywords**: `cv`, `resume`, `sơ yếu lý lịch`
- **Capabilities**:
  - Phân tích nội dung CV
  - Đánh giá điểm mạnh/yếu
  - Gợi ý cải thiện
  - Tối ưu hóa cho vị trí cụ thể

**Example**: `"preview file CV giúp tôi"`

#### 🧾 Invoice Processing
- **Trigger keywords**: `hóa đơn`, `invoice`, `bill`
- **Capabilities**:
  - Trích xuất thông tin hóa đơn
  - Phân tích chi tiết giao dịch
  - Tính toán tổng tiền, thuế
  - Kiểm tra tính chính xác

**Example**: `"phân tích hóa đơn này"`

#### 📊 Report Processing
- **Trigger keywords**: `báo cáo`, `report`
- **Capabilities**:
  - Phân tích nội dung báo cáo
  - Trích xuất dữ liệu quan trọng
  - Tóm tắt điểm chính
  - Tạo biểu đồ và phân tích

**Example**: `"xem trước báo cáo"`

#### 📜 Contract Processing
- **Trigger keywords**: `hợp đồng`, `contract`
- **Capabilities**:
  - Phân tích điều khoản hợp đồng
  - Trích xuất thông tin quan trọng
  - Kiểm tra rủi ro pháp lý
  - Tóm tắt nghĩa vụ và quyền lợi

**Example**: `"kiểm tra hợp đồng"`

#### 👁️ Preview/Analysis
- **Trigger keywords**: `preview`, `xem trước`, `phân tích`
- **Capabilities**:
  - Xem trước nội dung file
  - Phân tích cấu trúc
  - Trích xuất thông tin cơ bản
  - Đưa ra gợi ý xử lý

**Example**: `"preview file này giúp tôi"`

## 📁 Loại file được hỗ trợ

| Loại file | MIME Type | Khả năng xử lý |
|-----------|-----------|----------------|
| **Images** | `image/*` | Phân tích nội dung, OCR, nhận diện đối tượng |
| **PDF** | `application/pdf` | Trích xuất văn bản, phân tích cấu trúc |
| **Word** | `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Phân tích nội dung, tóm tắt |
| **Text** | `text/plain` | Phân tích nội dung, tóm tắt |

## 💡 Ví dụ sử dụng

### Ví dụ 1: Preview CV
```
User: "preview file CV giúp tôi" + [file CV.pdf]
AI Response: 
📋 PHÂN TÍCH CV/Resume: CV.pdf

Tôi đã nhận được CV của bạn. Dựa trên yêu cầu "preview file CV giúp tôi", tôi sẽ phân tích:

📊 Thông tin cơ bản:
- Tên file: CV.pdf
- Kích thước: 245,760 bytes
- Loại file: PDF

🔍 Phân tích nội dung CV:
• Đây là file PDF, tôi có thể giúp bạn:
  - Xem trước nội dung chính
  - Kiểm tra thông tin liên hệ
  - Đánh giá cấu trúc CV
  - Gợi ý cải thiện

💡 Gợi ý: Bạn có muốn tôi phân tích chi tiết hơn về kinh nghiệm làm việc, kỹ năng, hoặc đưa ra lời khuyên cải thiện CV không?
```

### Ví dụ 2: Phân tích hóa đơn
```
User: "phân tích hóa đơn này" + [file invoice.pdf]
AI Response:
🧾 PHÂN TÍCH HÓA ĐƠN: invoice.pdf

Tôi đã nhận được file hóa đơn của bạn. Dựa trên yêu cầu "phân tích hóa đơn này":

📊 Thông tin file:
- Tên file: invoice.pdf
- Kích thước: 156,432 bytes
- Loại file: application/pdf

🔍 Tôi có thể giúp bạn:
• Trích xuất thông tin hóa đơn
• Phân tích chi tiết giao dịch
• Tính toán tổng tiền, thuế
• Kiểm tra tính chính xác
• Xuất dữ liệu sang Excel

💡 Gợi ý: Bạn muốn tôi phân tích chi tiết hóa đơn này không?
```

## 🔄 Luồng xử lý

1. **User gửi file + message** → API nhận request
2. **Phân tích yêu cầu** → AI xác định loại xử lý cần thiết
3. **Xử lý file thông minh** → Dựa trên loại file và yêu cầu
4. **Tạo phản hồi tùy chỉnh** → Phù hợp với context
5. **Trả về kết quả** → Kèm gợi ý tiếp theo

## 🚀 Khởi động API

```bash
cd apis
python main.py
```

API sẽ chạy tại: `http://localhost:8000`
Documentation: `http://localhost:8000/docs`

## 📝 Ghi chú

- AI sẽ tự động nhận diện loại file và yêu cầu của user
- Phản hồi được tùy chỉnh dựa trên context cụ thể
- Hỗ trợ đa ngôn ngữ (Tiếng Việt + Tiếng Anh)
- Có thể mở rộng thêm các loại file và xử lý khác

## 🔮 Tính năng tương lai

- [ ] OCR cho ảnh để trích xuất văn bản
- [ ] Phân tích sentiment của văn bản
- [ ] Tạo tóm tắt tự động
- [ ] So sánh file với mẫu chuẩn
- [ ] Xuất dữ liệu sang các định dạng khác
