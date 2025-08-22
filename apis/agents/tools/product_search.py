"""
Viết thành một tool để về sau sử dụng gắn vào AI Agent
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class ProductSearchInput(BaseModel):
    input:str = Field(description="Nội dung cần tìm kiếm về thông tin sản phẩm trong cơ sở dữ liệu để cập nhật thêm thông tin trả lời.")

@tool("web_search", args_schema=ProductSearchInput, return_direct=True)
def web_search(input: str):
    """
    Tìm kiếm thông tin sản phẩm trong cơ sở dữ liệu  dựa vào nội dung người dùng cung cấp.
    """
    results = []
    return results


