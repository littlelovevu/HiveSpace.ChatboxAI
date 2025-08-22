"""
Viết thành một tool để về sau sử dụng gắn vào AI Agent
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from duckduckgo_search import DDGS


class WebSearchInput(BaseModel):
    input:str = Field(description="Nội dung cần tìm kiếm trên internet để cập nhật thêm thông tin trả lời.")

@tool("web_search", args_schema=WebSearchInput, return_direct=True)
def web_search(input: str):
    """
    Tìm kiếm thông tin trên internet dựa vào nội dung người dùng cung cấp.
    """
    results = DDGS().text(input, max_results=5, region="vn-vi")
    return results

print(web_search("MISA cam kết 2500 tỷ làm gì?")) # Kiểm tra thử

