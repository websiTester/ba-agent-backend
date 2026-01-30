

from bson import ObjectId
from mongodb.actions.connection import get_connection
from mongodb.models.types import ToolSchema


def get_collection(collection_name: str):
    db = get_connection()
    
    collection = db[collection_name]
    return collection


def add_tool(tool: ToolSchema):
    collection = get_collection("tools")
    result = collection.insert_one(tool.model_dump())
    print("Result: ", result.inserted_id)
    print("Tool added successfully")


def get_tool(parentId: str):
    collection = get_collection("tools")
    result = collection.find({"parentId": parentId})
    return result

def get_all_tools():
    collection = get_collection("tools")
    result = collection.find({})
    return result


def get_tool_by_name(tool_name: str):
    """
    Lấy tool theo toolName
    
    Args:
        tool_name: Tên của tool (ví dụ: "requirement_agent")
    
    Returns:
        Tool document hoặc None nếu không tìm thấy
    """
    collection = get_collection("tools")
    result = collection.find_one({"toolName": tool_name})
    return result

def get_tools_by_phaseId(phaseId: str):
    collection = get_collection("tools")
    result = collection.find({"phaseId": phaseId})
    return result


def delete_tool_by_id(toolId: str):
    query_id = ObjectId(toolId)
    collection = get_collection("tools")
    result = collection.delete_one({"_id": query_id})
    return result


def update_tool_by_id(toolId: str, tool: ToolSchema):
    query_id = ObjectId(toolId)
    collection = get_collection("tools")

    # 1. Chuyển Pydantic Object thành Dictionary
    # by_alias=True để đảm bảo các trường map đúng tên (nếu có alias)
    # exclude_unset=True (tuỳ chọn) nếu bạn chỉ muốn update các trường được gửi lên
    update_data = tool.model_dump(by_alias=True) # Nếu dùng Pydantic v1 thì là tool.dict()

    # 2. Quan trọng: Xóa trường _id khỏi data update
    # Nếu để _id trong update_data, Mongo sẽ báo lỗi "Performing an update on the path '_id' would modify the immutable field '_id'"
    if "_id" in update_data:
        del update_data["_id"]
    if "id" in update_data:
        del update_data["id"]

    
    # 3. Gọi lệnh update với toán tử $set
    result = collection.update_one(
        {"_id": query_id}, 
        {"$set": update_data} # <-- Phải bọc trong $set
    )
    return result
