"""
Viết thành một tool để về sau sử dụng gắn vào AI Agent
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class ProductSearchInput(BaseModel):
    input:str = Field(description="Nội dung cần tìm kiếm về thông tin sản phẩm trong cơ sở dữ liệu để cập nhật thêm thông tin trả lời.")

@tool("product_search", args_schema=ProductSearchInput, return_direct=True)
def product_search(input: str):
    """
    Tìm kiếm thông tin sản phẩm trong cơ sở dữ liệu  dựa vào nội dung người dùng cung cấp.
    """
    products = [
        {
            "id": 1,
            "name": "Laptop Dell XPS 13",
            "price": 1500,
            "category": "Electronics",
            "in_stock": True
        },
        {
            "id": 2,
            "name": "iPhone 15 Pro",
            "price": 1200,
            "category": "Electronics",
            "in_stock": False
        },
        {
            "id": 3,
            "name": "Bàn phím cơ Keychron K2",
            "price": 90,
            "category": "Accessories",
            "in_stock": True
        },
        {
            "id": 4,
            "name": "Ghế công thái học Sihoo",
            "price": 250,
            "category": "Furniture",
            "in_stock": True
        },
        {
            "id": 5,
            "name": "Tai nghe Sony WH-1000XM5",
            "price": 400,
            "category": "Audio",
            "in_stock": False
        }
    ]

    return products


