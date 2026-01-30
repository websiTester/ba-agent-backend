from functools import partial
from typing import Dict
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model
from mongodb.actions.crud import get_all_tools
from mongodb.models.types import ToolSchema
from tools.utils.create_dynamic_agent import create_dynamic_agent
from tools.utils.create_dynamic_schema import create_dynamic_schema
from tools.utils.create_dynamic_tool import tool_function




def create_tool_from_db():
    print("Creating tools from database...")
    # Return a list of dictionaries
    # each dictionary is a tool
    toolList = get_all_tools()
    tools = []


    print(type(toolList))
    for tool in toolList:
        orchestrated_tool = load_dynamic_tool(tool)
        tools.append(orchestrated_tool)

    print("Tools created successfully")
    return tools
        




    

def load_dynamic_tool(tool: dict):
    tool_name = tool["toolName"]
    fields_dict = tool["field"]
    DynamicModel = create_dynamic_schema(tool_name, fields_dict)
    

    agent_tool = StructuredTool.from_function(
        name=tool["toolName"],
        func=tool_function,
        description=tool["toolDescription"],
        args_schema=DynamicModel,
    )

    agent = create_dynamic_agent(tool, [agent_tool])

    # 3. KỸ THUẬT PARTIAL (QUAN TRỌNG NHẤT)
    # Tạo ra một hàm riêng cho tool này, với agent_executor đã được "ghim" sẵn
    # Thay vì dùng partial, ta khai báo một hàm wrapper tại chỗ.
    # Hàm này sẽ "bắt" (capture) biến 'agent' từ scope bên ngoài.
    # Sử dụng **kwargs để nhận mọi tham số từ DynamicModel truyền vào.
    def wrapped_func(**kwargs):
        # Gọi hàm logic gốc, truyền agent và bung lụa các tham số khác
        return create_tool_from_agent(agent=agent, **kwargs)


    orchestrated_tool = StructuredTool.from_function(
            func=wrapped_func,                 # Hàm đã gắn agent
            name=tool["agentToolName"],                  # Tên tool (VD: "Discovery_Requirements")
            description=tool["agentToolDescription"], # Mô tả để Agent điều phối hiểu
            args_schema=DynamicModel        # Schema đầu vào (user_input, phase_id...)
        )
    
    return orchestrated_tool


def create_tool_from_agent(agent,user_input: str, phase_id: str):
    response  = agent.invoke(
        {"messages": [{"role": "user", "content": "Phase ID: " + phase_id + "\nUser Input: " + user_input}]},
    )
    print(f"==========create_tool_from_agent:======== {response}")
    return response["messages"][-1].content