"""
HiveSpace AI Agent - Tích hợp với Gemini và LangGraph
Agent thông minh có khả năng tìm kiếm web và xử lý ngôn ngữ tự nhiên
"""

from openai import OpenAI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from .tools.web_search import web_search
from .tools.product_tool import product_search
from .tools.order_tool import order_search
from .tools.image_tool import generate_image
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import json
from langchain_core.messages import ToolMessage, SystemMessage
from langchain_core.runnables import RunnableConfig


class State(TypedDict):
    """Trạng thái của workflow graph"""
    # Messages có kiểu "list". Hàm `add_messages` trong annotation
    # định nghĩa cách cập nhật state key này (trong trường hợp này,
    # nó append messages vào list thay vì ghi đè)
    messages: Annotated[list, add_messages]


class HiveSpaceAgent:
    """AI Agent chính của HiveSpace với khả năng tìm kiếm web"""
    
    def __init__(self):
        """Khởi tạo agent với các cấu hình cần thiết"""
        # Load biến từ .env vào môi trường
        load_dotenv()
        
        # Lấy API key
        self.api_key = os.getenv("api_key")
        
        if not self.api_key:
            raise ValueError("API key không được tìm thấy trong file .env")
        
        # Khởi tạo Basic Agent
        self.basic_agent = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",    # Model ngôn ngữ lớn
            temperature=1.0,              # Mức độ sáng tạo của model, từ 0 tới 1
            max_tokens=None,              # Giới hạn token của Input, Output. Thường nên để tối đa 32K
            timeout=None,
            max_retries=2,
            google_api_key=self.api_key   # API key đã lấy ở trên
        )
        
        # Tạo LLM class với tools
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",    # replace with "gemini-2.0-flash"
            temperature=1.0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            google_api_key=self.api_key
        )
        
        # Bind tools to the model
        self.react_agent = self.llm.bind_tools([web_search, product_search, order_search, generate_image])
        
        # Khởi tạo workflow graph
        self._setup_workflow()
    
    def _setup_workflow(self):
        """Thiết lập workflow graph cho agent"""
        # Khởi tạo graph builder
        graph_builder = StateGraph(State)
        
        # Định nghĩa tools
        tools = [web_search, product_search, order_search, generate_image]
        tools_by_name = {tool.name: tool for tool in tools}
        
        # Định nghĩa tool node
        def call_tool(state: State):
            outputs = []
            # Iterate over the tool calls in the last message
            for tool_call in state["messages"][-1].tool_calls:
                # Get the tool by name
                tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
                outputs.append(
                    ToolMessage(
                        content=tool_result,
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )
            return {"messages": outputs}
        
        def call_model(state: State, config: RunnableConfig):
            # Invoke the model with the system prompt and the messages
            response = self.react_agent.invoke(state["messages"], config)
            # We return a list, because this will get added to the existing messages state using the add_messages reducer
            return {"messages": [response]}
        
        # Định nghĩa conditional edge để xác định có tiếp tục hay không
        def should_continue(state: State):
            messages = state["messages"]
            # If the last message is not a tool call, then we finish
            if not messages[-1].tool_calls:
                return "end"
            # default to continue
            return "continue"
        
        # Định nghĩa graph mới với state
        workflow = StateGraph(State)
        
        # 1. Add our nodes
        workflow.add_node("llm", call_model)
        workflow.add_node("tools", call_tool)
        
        # 2. Set the entrypoint as `agent`, this is the first node called
        workflow.set_entry_point("llm")
        
        # 3. Add a conditional edge after the `llm` node is called
        workflow.add_conditional_edges(
            # Edge is used after the `llm` node is called
            "llm",
            # The function that will determine which node is called next
            should_continue,
            # Mapping for where to go next, keys are strings from the function return, and the values are other nodes
            # END is a special node marking that the graph is finish
            {
                # If `tools`, then we call the tool node
                "continue": "tools",
                # Otherwise we finish
                "end": END,
            },
        )
        
        # 4. Add a normal edge after `tools` is called, `llm` node is called next
        workflow.add_edge("tools", "llm")
        
        # Compile graph
        self.react_agent_graph = workflow.compile()
    
    def ask_react_agent(self, messages: list):
        """
        Gọi react agent với danh sách messages
        
        Args:
            messages (list): Danh sách messages với format:
                [
                    {"role": "system", "content": "system prompt"},
                    {"role": "user", "content": "user message"}
                ]
        
        Returns:
            str: Phản hồi từ AI agent
        """
        
        response_content = ""
        for event in self.react_agent_graph.stream({"messages": messages}):
            for key, value in event.items():
                if key != "llm" or value["messages"][-1].content == "":
                    continue
                response_content = value["messages"][-1].content
        
        return response_content
    
    def ask_simple_question(self, question: str, system_prompt: str = None):
        """
        Hỏi câu hỏi đơn giản với system prompt mặc định
        
        Args:
            question (str): Câu hỏi của user
            system_prompt (str, optional): System prompt tùy chỉnh
        
        Returns:
            str: Phản hồi từ AI agent
        """
        if system_prompt is None:
            system_prompt = """Bạn là AVA, trợ lý số của công ty cổ phần MISA. 

Bạn có khả năng:
1. Tìm kiếm thông tin trên web để cập nhật kiến thức mới nhất
2. Tìm kiếm thông tin sản phẩm trong cơ sở dữ liệu nội bộ
3. Tìm kiếm thông tin đơn hàng và trạng thái giao hàng

Khi người dùng hỏi về sản phẩm, hãy sử dụng product_search tool để tìm thông tin chi tiết.
Khi cần thông tin mới nhất, hãy sử dụng web_search tool để tìm kiếm trên internet.
Khi người dùng hỏi về đơn hàng, hãy sử dụng order_search tool để tìm thông tin đơn hàng."""
        
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "system",
                "content": f"Thông tin bổ sung:\n- Thời gian hiện tại: 08-2025",
            },
            {
                "role": "user",
                "content": question,
            }
        ]
        
        return self.ask_react_agent(messages)
    
    def get_basic_response(self, question: str):
        """
        Lấy phản hồi cơ bản từ basic agent (không có tools)
        
        Args:
            question (str): Câu hỏi của user
        
        Returns:
            str: Phản hồi từ basic agent
        """
        try:
            response = self.basic_agent.invoke(question)
            return response.content
        except Exception as e:
            return f"Lỗi khi xử lý câu hỏi: {str(e)}"


# Hàm tiện ích để sử dụng nhanh
def create_agent():
    """Tạo instance của HiveSpaceAgent"""
    return HiveSpaceAgent()


def ask_question(question: str, use_web_search: bool = True):
    """
    Hỏi câu hỏi với agent
    
    Args:
        question (str): Câu hỏi cần hỏi
        use_web_search (bool): Có sử dụng web search hay không
    
    Returns:
        str: Phản hồi từ agent
    """
    try:
        agent = create_agent()
        
        if use_web_search:
            return agent.ask_simple_question(question)
        else:
            return agent.get_basic_response(question)
    
    except Exception as e:
        return f"Lỗi khi khởi tạo agent: {str(e)}"


# Ví dụ sử dụng
if __name__ == "__main__":
    # Tạo agent
    agent = create_agent()
    
    # Hỏi câu hỏi với web search
    response = agent.ask_simple_question("MISA cam kết 2500 tỷ làm gì?")
    
    # Hỏi câu hỏi đơn giản
    simple_response = agent.get_basic_response("Xin chào, bạn là ai?")
