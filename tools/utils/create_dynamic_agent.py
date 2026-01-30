from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver

from key_manager.gemini_key_manager import key_manager  

def create_dynamic_agent(tool: dict, tools: list):

    new_key = key_manager.get_key()
    print("Dynamic Agent Key: "+new_key)
    print("Dynamic Agent Model: "+tool["model"])
    llm = ChatGoogleGenerativeAI(model=tool["model"], api_key=new_key)

    return create_agent(
        llm,
        tools=tools,
        checkpointer=InMemorySaver(),  
        system_prompt=tool["agentInstruction"],
    )