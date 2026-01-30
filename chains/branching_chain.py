# Đây là nơi duy nhất bạn cần sửa sau này
CLASSIFICATION_TYPES = [
    "UI/UX", 
    "Functional and Non-functional Requirements", 
]

options_str = ", ".join(CLASSIFICATION_TYPES)


import os
from google.api_core.exceptions import ResourceExhausted
from langchain.agents import create_agent
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from langgraph.checkpoint.memory import InMemorySaver  
from dotenv import load_dotenv
from langchain_google_genai  import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from pydantic import BaseModel, Field

from chains.discovery_chain import discovery_tool, get_discovery_response
from chains.ui_ux_chain import get_ui_ux_response, ui_ux_tool
from instructions.branching_instruction import branching_instruction
from instructions.discovery_instruction import discovery_instruction
from key_manager.gemini_key_manager import key_manager
from mongodb.actions.agent_crud import get_agent_by_name
from services.create_rag_chain import create_rag_chain

from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)

from tools.create_tool_from_db import create_tool_from_db

load_dotenv()

_GLOBAL_BRANCHING_AGENT = None




branching_tools = [
    get_ui_ux_response,
    get_discovery_response
]


def create_new_agent_instance():
    """
    Hàm nội bộ: Chỉ chịu trách nhiệm TẠO MỚI agent.
    Đây là nơi logic nặng (load DB, init LLM) diễn ra.
    """
    print("--- INFO: Initializing/Re-building Branching Agent... ---")
    tools = create_tool_from_db() # Giả sử hàm này tốn tài nguyên
    
    
    agentObject = get_agent_by_name("Orchestration_Agent")
    llm = key_manager.get_llm(agentObject["model"])
    branching_instruction = agentObject["instructions"]

    agent = create_agent(
        llm,
        tools=tools,
        checkpointer=InMemorySaver(),  
        system_prompt=branching_instruction,
    )
    return agent

def refresh_agent():
    global _GLOBAL_BRANCHING_AGENT
    _GLOBAL_BRANCHING_AGENT = create_new_agent_instance()

def get_branching_agent():

    """
    Hàm Accessor: 
    - Nếu biến global chưa có -> Tạo mới & gán vào.
    - Nếu có rồi -> Trả về cái đang có (Cache).
    """
    global _GLOBAL_BRANCHING_AGENT
    
    if _GLOBAL_BRANCHING_AGENT is None:
        _GLOBAL_BRANCHING_AGENT = create_new_agent_instance()
        
    return _GLOBAL_BRANCHING_AGENT


def get_branching_response(user_input: str, phase_id: str,thread_id: str):

    
    attempt = 0
    max_retries = 9
    while attempt < max_retries:
        try:
            branching_agent = get_branching_agent()
            # Cố gắng chạy agent
            response = branching_agent.invoke(
                {"messages": [{"role": "user", "content": "Phase ID: " + phase_id + "\nUser Input: " + user_input}]},
                {"configurable": {"thread_id": thread_id}},  
            )
            
            print("========== START PRETTY PRINT MESSAGE HISTORY ==========")
            for msg in response["messages"]:
                msg.pretty_print()
            print("==========END PRETTY PRINT MESSAGE HISTORY ==========")    
            return response["messages"][-1].content
            
        except (ResourceExhausted, ChatGoogleGenerativeAIError):
            # Đây là lỗi 429 (Hết quota) của Google
            attempt += 1
            print(f"Lỗi Quota (Lần thử {attempt}/{max_retries}). Đang đổi API Key...")
            
            # 1. Xoay key sang cái tiếp theo
            key_manager.rotate_key()
            
            # 2. CẬP NHẬT LẠI LLM TRONG AGENT
            # Lưu ý: Bạn phải gán lại api_key mới cho model bên trong agent
            # Tùy vào cách bạn build agent, thường LLM nằm ở agent.llm hoặc agent.agent.llm_chain.llm
            # Đây là ví dụ chung, bạn cần trỏ đúng vào object LLM của bạn:
            

            refresh_agent()
            
            # Nếu dùng LangGraph hoặc cơ chế mới, cách đơn giản nhất là 
            # Re-build lại agent với LLM mới từ key_manager.get_llm()
            # (Xem phần lưu ý bên dưới)
            
        except Exception as e:
            # Nếu là lỗi khác (code sai, logic sai) thì throw luôn, không retry
            raise e
            
    raise Exception("Đã thử tất cả API Key nhưng vẫn đều hết Quota!") 



