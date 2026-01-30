import os
from langchain.agents import create_agent
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

from instructions.discovery_instruction import discovery_instruction
from services.create_rag_chain import create_rag_chain

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")


class DiscoveryTool(BaseModel):
    user_input: str = Field(description="The user input to discover functional requirements and non-functional requirements")
    phase_id: str = Field(description="The phase ID to get the relevant context")


@tool("Discovery_Requirements", description="Useful for when you need to discover functional requirements and non-functional requirements from the user input",
    args_schema=DiscoveryTool,
)
def discovery_tool(user_input: str, phase_id: str) -> str:
    print("=====TOOL: Phase ID:========"+phase_id)

    qa_system_prompt = (
            "Sử dụng các thông tin bên dưới để trả lời câu hỏi của người dùng"
            "Nếu có phần nội dung không liên quan đến câu hỏi của người dùng, đánh dấu là [Không liên quan]"
            "và hiển thị như vậy khi phản hồi lại cho người dùng"
            "\n\n"
            "{context}"
        )

    # Create a retrieval chain that combines the history-aware retriever and the question answering chain
    rag_chain = create_rag_chain(phase_id, qa_system_prompt, user_input)

    return rag_chain.invoke(
        {"input": user_input}
    )



discovery_tools = [
    discovery_tool,
]

# discovery_agent = create_agent(
#     llm,
#     tools=discovery_tools,
#     checkpointer=InMemorySaver(),  
#     system_prompt=discovery_instruction,
# )


def get_discovery_agent():
    return create_agent(
        llm,
        tools=discovery_tools,
        checkpointer=InMemorySaver(),  
        system_prompt=discovery_instruction,
    )


class DiscoveryResponseTool(BaseModel):
    user_input: str = Field(description="The user input to discover functional requirements and non-functional requirements")
    phase_id: str = Field(description="The phase ID to get the relevant context")


@tool("Get_Discovery_Response", description="useful for when you need to discover functional requirements and non-functional requirements from the user input",
    args_schema=DiscoveryResponseTool,
)
def get_discovery_response(user_input: str, phase_id: str):

    discovery_agent = get_discovery_agent()

    response  = discovery_agent.invoke(
        {"messages": [{"role": "user", "content": "Phase ID: " + phase_id + "\nUser Input: " + user_input}]},
    )
    print(response)
    return response["messages"][-1].content