import os
from langchain.agents import create_agent
from langchain_classic import hub
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver  
from dotenv import load_dotenv
from langchain_google_genai  import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from pydantic import BaseModel, Field

from instructions.ui_instructions import ui_ux_instruction
from services.create_rag_chain import create_rag_chain



load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")


class UIUXTool(BaseModel):
    user_input: str = Field(description="The user input to analyze UI/UX")
    phase_id: str = Field(description="The phase ID to get the relevant context")




@tool("Analyze_UI_UX", description="useful for when you need to analyze UI/UX for a given functional requirements",
    args_schema=UIUXTool,
)
def ui_ux_tool(user_input: str, phase_id: str) -> str:
    print("=====TOOL: Phase ID:========"+phase_id)
    qa_system_prompt = (
        "Sử dụng các thông tin có sẵn để phân tích UI/UX cho các functional requirements"
        "\n\n"
        "{context}"
    )

    rag_chain = create_rag_chain(phase_id, qa_system_prompt, user_input)

    return rag_chain.invoke(
        {"input": user_input}
    )




tools = [
     ui_ux_tool,
]



uiux_agent = create_agent(
    llm,
    tools=tools,
    checkpointer=InMemorySaver(),  
    system_prompt=ui_ux_instruction,
)


class UIUXResponseTool(BaseModel):
    user_input: str = Field(description="The user input to analyze UI/UX")
    phase_id: str = Field(description="The phase ID to get the relevant context")
    


@tool("Get_UI_UX_Response", description="useful for when you need to analyze UI/UX for a given functional requirements", 
    args_schema=UIUXResponseTool,
)
def get_ui_ux_response(user_input: str, phase_id: str):

    response  = uiux_agent.invoke(
        {"messages": [{"role": "user", "content": "Phase ID: " + phase_id + "\nUser Input: " + user_input}]},
        
    )
    print("=====Response:========"+response["messages"][-1].content)
    return response["messages"][-1].content



