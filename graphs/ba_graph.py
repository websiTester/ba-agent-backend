from typing import Literal
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict
from langgraph.graph import MessagesState, END,StateGraph, START
from langgraph.types import Command   # use to pass from one Agent to Another Agent
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain_google_genai  import ChatGoogleGenerativeAI
from graph_nodes.create_node_from_db import create_new_graph_from_db
from instructions.instruction import discovery_instruction,uiux_instruction
from models.state import State


_GLOBAL_BA_GRAPH = None

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash") 
memory = MemorySaver()


members=["discover","ui_ux"]
member_descriptions = """
1. discover: Chuyên gia nghiên cứu, tìm kiếm thông tin, phân tích thị trường và dữ liệu. Sử dụng khi người dùng cần tìm hiểu, tra cứu cái gì đó.
2. ui_ux: Chuyên gia thiết kế giao diện, trải nghiệm người dùng. Sử dụng khi người dùng muốn vẽ wireframe, thiết kế nút, bố cục website.
"""

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal['discover', 'ui_ux', 'FINISH']



system_prompt=f"""
You are a supervisor, tasked with managing a conversation between the following workers: {members}. 
Here are the job descriptions for each worker:
{member_descriptions}

Given the following user request, respond with the worker to act next. 
Each worker will perform a task and respond with their results and status. 
When finished, respond with FINISH.
"""


def supervisor_node(state: State) -> Command[Literal["discover", "ui_ux", "__end__"]]:
    
    messages = [{"role": "system", "content": system_prompt},] + state["messages"]
    
    response = llm.with_structured_output(Router).invoke(messages)
    
    goto = response["next"]
    
    print("below my goto**********************************")
    
    print(goto)
    
    if goto == "FINISH":
        goto = END
        
    return Command(goto=goto, update={"next": goto})


def discover_node(state: State) -> Command[Literal["supervisor"]]:
    
    discover_agent = create_agent(llm, system_prompt=discovery_instruction)
    
    #print(f"DISCOVER NODE STATE: {state['messages']}\n\n")
    result = discover_agent.invoke(state)
    
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="discover")
            ]
        },
        goto="supervisor",
    )


def uiux_node(state: State) -> Command[Literal["supervisor"]]:
    
 
    uiux_agent = create_agent(llm, system_prompt=uiux_instruction)
    
    #print(f"UI/UX NODE STATE: {state['messages']}\n\n")
    result = uiux_agent.invoke(state)
    
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="ui_ux")
            ]
        },
        goto="supervisor",
    )


graph = StateGraph(State)
graph.add_node("supervisor",supervisor_node)
graph.add_node("discover", discover_node)
graph.add_node("ui_ux", uiux_node)

graph.add_edge(START,"supervisor")
app=graph.compile(checkpointer=memory)


# With the graph created, we can now invoke it and see how it performs!
config = {"configurable": {
    "thread_id": 1
}}


# def get_ba_graph_response(user_input: str):
#     messages = [HumanMessage(content=user_input)]
#     response = app.invoke({"messages": messages}, config=config)
#     print(f"AI: {response["messages"][-1].content}")
#     return response["messages"][-1].content





# while True:
#     user_input = input("\nWhat is your question: ")
#     if user_input.lower() in ['exit', 'quit']:
#         break
    
#     print("\n=== ANSWER ===")
#     messages = [HumanMessage(content=user_input)]
#     # for s in app.stream({"messages": messages}, subgraphs=True, config=config):
#     #     print(s)
#     #     print("----")

#     response = app.invoke({"messages": messages}, config=config)
#     print(f"AI: {response["messages"][-1].content}")

