
from fastapi import APIRouter
from pymongo.cursor import List

from chains.branching_chain import refresh_agent
from graphs.ba_dynamic_graph import refresh_ba_graph
from mongodb.actions.crud import add_tool, delete_tool_by_id, get_tools_by_phaseId, update_tool_by_id
from mongodb.models.types import ToolSchema


router = APIRouter()



@router.post("/create_tool")
def create_tool(formData: ToolSchema):
    print(formData)
    formData.agentToolName = formData.agentToolName.replace(" ", "_")
    formData.toolName = formData.toolName.replace(" ", "_")


    add_tool(formData)
    #refresh_agent()
    refresh_ba_graph()
    return {"message": "Tool created successfully"}

# response_model=List[ToolSchema] sẽ báo cho FastAPI biết:
# "Hãy lấy dữ liệu trả về, lọc bỏ rác, ép kiểu _id thành string theo đúng khuôn mẫu này"
@router.get("/get_tools/{phaseId}", response_model=List[ToolSchema])
def get_tools(phaseId: str):
    print(f"Getting tools for phaseId: {phaseId}")
    cursor = get_tools_by_phaseId(phaseId)
    
    return list(cursor)


@router.delete("/delete_tool/{toolId}")
def delete_tool(toolId: str):
    print(f"Deleting tool with id: {toolId}")
    result = delete_tool_by_id(toolId)
    print(f"Result: {result}")
    #refresh_agent()
    refresh_ba_graph()
    return {"message": "Tool deleted successfully"}


@router.put("/update_tool/{toolId}")
def update_tool(toolId: str, tool: ToolSchema):
    print(f"Update tool with id: {toolId}")
    tool.agentToolName = tool.agentToolName.replace(" ", "_")
    tool.toolName = tool.toolName.replace(" ", "_")
    print(f"Updated tool: {tool}")
    result = update_tool_by_id(toolId, tool)
    print(f"Result: {result}")
    #refresh_agent()
    refresh_ba_graph()
    return {"message": "Tool updated successfully"}