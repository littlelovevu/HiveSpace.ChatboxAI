"""
Order Tool - Quản lý đơn hàng và tìm kiếm thông tin đơn hàng
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import random


class OrderSearchInput(BaseModel):
    input: str = Field(description="Nội dung cần tìm kiếm về đơn hàng (mã đơn hàng, email, tên khách hàng, trạng thái)")


@tool("order_search", args_schema=OrderSearchInput, return_direct=True)
def order_search(input: str):
    """
    Tìm kiếm thông tin đơn hàng trong cơ sở dữ liệu dựa vào nội dung người dùng cung cấp.
    """
    # Dữ liệu đơn hàng mẫu
    orders = [
        {
            "order_id": "ORD-2024-001",
            "customer_name": "Nguyễn Văn An",
            "customer_email": "nguyenvanan@email.com",
            "customer_phone": "0901234567",
            "order_date": "2024-01-15",
            "status": "Đã giao hàng",
            "total_amount": 2500000,
            "payment_method": "Chuyển khoản",
            "shipping_address": "123 Đường ABC, Quận 1, TP.HCM",
            "items": [
                {"product_id": 1, "name": "Laptop Dell XPS 13", "quantity": 1, "price": 1500000},
                {"product_id": 31, "name": "AirPods Pro 2", "quantity": 1, "price": 1000000}
            ]
        },
        {
            "order_id": "ORD-2024-002",
            "customer_name": "Trần Thị Bình",
            "customer_email": "tranthibinh@email.com",
            "customer_phone": "0912345678",
            "order_date": "2024-01-16",
            "status": "Đang xử lý",
            "total_amount": 1800000,
            "payment_method": "Tiền mặt",
            "shipping_address": "456 Đường XYZ, Quận 3, TP.HCM",
            "items": [
                {"product_id": 2, "name": "iPhone 15 Pro", "quantity": 1, "price": 1200000},
                {"product_id": 71, "name": "KitchenAid Stand Mixer", "quantity": 1, "price": 600000}
            ]
        },
        {
            "order_id": "ORD-2024-003",
            "customer_name": "Lê Văn Cường",
            "customer_email": "levancuong@email.com",
            "customer_phone": "0923456789",
            "order_date": "2024-01-17",
            "status": "Đang giao hàng",
            "total_amount": 3200000,
            "payment_method": "Thẻ tín dụng",
            "shipping_address": "789 Đường DEF, Quận 5, TP.HCM",
            "items": [
                {"product_id": 11, "name": "Gaming PC RTX 4080", "quantity": 1, "price": 2500000},
                {"product_id": 44, "name": "Logitech G Pro X", "quantity": 1, "price": 130000},
                {"product_id": 45, "name": "Razer DeathAdder V3", "quantity": 1, "price": 70000}
            ]
        },
        {
            "order_id": "ORD-2024-004",
            "customer_name": "Phạm Thị Dung",
            "customer_email": "phamthidung@email.com",
            "customer_phone": "0934567890",
            "order_date": "2024-01-18",
            "status": "Chờ xác nhận",
            "total_amount": 950000,
            "payment_method": "Chuyển khoản",
            "shipping_address": "321 Đường GHI, Quận 7, TP.HCM",
            "items": [
                {"product_id": 81, "name": "Herman Miller Aeron", "quantity": 1, "price": 1500000}
            ]
        },
        {
            "order_id": "ORD-2024-005",
            "customer_name": "Hoàng Văn Em",
            "customer_email": "hoangvanem@email.com",
            "customer_phone": "0945678901",
            "order_date": "2024-01-19",
            "status": "Đã hủy",
            "total_amount": 800000,
            "payment_method": "Chuyển khoản",
            "shipping_address": "654 Đường JKL, Quận 9, TP.HCM",
            "items": [
                {"product_id": 51, "name": "Canon EOS R5", "quantity": 1, "price": 3900000}
            ]
        },
        {
            "order_id": "ORD-2024-006",
            "customer_name": "Vũ Thị Phương",
            "customer_email": "vuthiphuong@email.com",
            "customer_phone": "0956789012",
            "order_date": "2024-01-20",
            "status": "Đã giao hàng",
            "total_amount": 450000,
            "payment_method": "Tiền mặt",
            "shipping_address": "987 Đường MNO, Quận 2, TP.HCM",
            "items": [
                {"product_id": 91, "name": "Nike Air Max 270", "quantity": 1, "price": 150000},
                {"product_id": 92, "name": "Adidas Ultraboost 22", "quantity": 1, "price": 180000},
                {"product_id": 99, "name": "Casio G-Shock", "quantity": 1, "price": 100000}
            ]
        },
        {
            "order_id": "ORD-2024-007",
            "customer_name": "Đặng Văn Giang",
            "customer_email": "dangvangiang@email.com",
            "customer_phone": "0967890123",
            "order_date": "2024-01-21",
            "status": "Đang xử lý",
            "total_amount": 1200000,
            "payment_method": "Thẻ tín dụng",
            "shipping_address": "147 Đường PQR, Quận 4, TP.HCM",
            "items": [
                {"product_id": 21, "name": "Google Pixel 8", "quantity": 1, "price": 700000},
                {"product_id": 31, "name": "AirPods Pro 2", "quantity": 1, "price": 1000000}
            ]
        },
        {
            "order_id": "ORD-2024-008",
            "customer_name": "Bùi Thị Hoa",
            "customer_email": "buithihoa@email.com",
            "customer_phone": "0978901234",
            "order_date": "2024-01-22",
            "status": "Đã giao hàng",
            "total_amount": 2800000,
            "payment_method": "Chuyển khoản",
            "shipping_address": "258 Đường STU, Quận 6, TP.HCM",
            "items": [
                {"product_id": 13, "name": "Lenovo ThinkPad X1", "quantity": 1, "price": 1600000},
                {"product_id": 81, "name": "Herman Miller Aeron", "quantity": 1, "price": 1500000}
            ]
        },
        {
            "order_id": "ORD-2024-009",
            "customer_name": "Ngô Văn Inh",
            "customer_email": "ngovaninh@email.com",
            "customer_phone": "0989012345",
            "order_date": "2024-01-23",
            "status": "Đang giao hàng",
            "total_amount": 600000,
            "payment_method": "Tiền mặt",
            "shipping_address": "369 Đường VWX, Quận 8, TP.HCM",
            "items": [
                {"product_id": 71, "name": "KitchenAid Stand Mixer", "quantity": 1, "price": 400000},
                {"product_id": 75, "name": "Ninja Foodi 9-in-1", "quantity": 1, "price": 200000}
            ]
        },
        {
            "order_id": "ORD-2024-010",
            "customer_name": "Lý Thị Kim",
            "customer_email": "lythikim@email.com",
            "customer_phone": "0990123456",
            "order_date": "2024-01-24",
            "status": "Chờ xác nhận",
            "total_amount": 1500000,
            "payment_method": "Chuyển khoản",
            "shipping_address": "741 Đường YZA, Quận 10, TP.HCM",
            "items": [
                {"product_id": 41, "name": "Xbox Series X", "quantity": 1, "price": 500000},
                {"product_id": 44, "name": "Logitech G Pro X", "quantity": 1, "price": 130000},
                {"product_id": 45, "name": "Razer DeathAdder V3", "quantity": 1, "price": 70000}
            ]
        }
    ]
    
    # Tìm kiếm đơn hàng dựa trên input
    input_lower = input.lower()
    matched_orders = []
    
    # Kiểm tra xem có phải tìm kiếm mã đơn hàng cụ thể không
    is_order_id_search = input_lower.startswith("ord-") and len(input_lower) >= 8
    
    for order in orders:
        # Nếu tìm kiếm mã đơn hàng cụ thể, ưu tiên tìm kiếm chính xác
        if is_order_id_search:
            if input_lower == order["order_id"].lower():
                # Tìm thấy chính xác, trả về ngay
                return {
                    "message": f"Tìm thấy đơn hàng chính xác: {order['order_id']}",
                    "orders": [order],
                    "total": 1,
                    "search_query": input,
                    "exact_match": True
                }
            elif input_lower in order["order_id"].lower():
                # Tìm thấy một phần, thêm vào danh sách
                matched_orders.append(order)
        else:
            # Tìm kiếm theo mã đơn hàng, tên khách hàng, email, trạng thái
            if (input_lower in order["order_id"].lower() or 
                input_lower in order["customer_name"].lower() or 
                input_lower in order["customer_email"].lower() or 
                input_lower in order["status"].lower()):
                matched_orders.append(order)
    
    # Nếu không tìm thấy, trả về tất cả đơn hàng
    if not matched_orders:
        return {
            "message": f"Không tìm thấy đơn hàng phù hợp với '{input}'. Dưới đây là tất cả đơn hàng:",
            "orders": orders,
            "total": len(orders),
            "status_summary": {
                "Đã giao hàng": len([o for o in orders if o["status"] == "Đã giao hàng"]),
                "Đang xử lý": len([o for o in orders if o["status"] == "Đang xử lý"]),
                "Đang giao hàng": len([o for o in orders if o["status"] == "Đang giao hàng"]),
                "Chờ xác nhận": len([o for o in orders if o["status"] == "Chờ xác nhận"]),
                "Đã hủy": len([o for o in orders if o["status"] == "Đã hủy"])
            }
        }
    
    return {
        "message": f"Tìm thấy {len(matched_orders)} đơn hàng phù hợp với '{input}':",
        "orders": matched_orders,
        "total": len(matched_orders),
        "search_query": input
    }
