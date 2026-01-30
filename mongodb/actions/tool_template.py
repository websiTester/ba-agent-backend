from mongodb.actions.connection import get_connection
from bson import ObjectId


def get_collection():
    db = get_connection()
    collection = db["toolTemplate"]
    return collection


def get_templates_by_agent_source(agent_source: str):
    collection = get_collection()
    result = collection.find({"agent_source": agent_source})
    return result

def add_templates(template: dict):
    collection = get_collection()
    result = collection.insert_one(template)
    return result.inserted_id

def update_template(template_id: str, updated_data: dict):
    """
    Update template theo ID
    
    Args:
        template_id: ID của template cần update (string)
        updated_data: Dictionary chứa dữ liệu cần update
                     Ví dụ: {"agent_source": "new_source", "template": [...]}
    
    Returns:
        Số lượng document được update (0 hoặc 1)
    """
    collection = get_collection()
    result = collection.update_one(
        {"_id": ObjectId(template_id)},
        {"$set": updated_data}
    )
    return result.modified_count

def delete_template(template_id: str):
    """
    Delete template theo ID
    
    Args:
        template_id: ID của template cần xóa (string)
    
    Returns:
        Số lượng document được xóa (0 hoặc 1)
    """
    collection = get_collection()
    result = collection.delete_one({"_id": ObjectId(template_id)})
    return result.deleted_count


def set_template_in_use(template_id: str, agent_source: str):
    """
    Set template làm active (is_in_use = true) và set các template khác của cùng agent_source thành inactive
    
    Args:
        template_id: ID của template cần set active (string)
        agent_source: Agent source để filter các template cùng loại
    
    Returns:
        Dictionary chứa số lượng template được update
    """
    collection = get_collection()
    
    # Bước 1: Set tất cả template của agent_source này thành is_in_use = false
    result_deactivate = collection.update_many(
        {"agent_source": agent_source},
        {"$set": {"is_in_use": False}}
    )
    
    # Bước 2: Set template được chọn thành is_in_use = true
    result_activate = collection.update_one(
        {"_id": ObjectId(template_id)},
        {"$set": {"is_in_use": True}}
    )
    
    return {
        "deactivated_count": result_deactivate.modified_count,
        "activated": result_activate.modified_count > 0
    }


def get_template_by_id(template_id: str):
    """
    Lấy template theo ID
    
    Args:
        template_id: ID của template (string)
    
    Returns:
        Template document hoặc None nếu không tìm thấy
    """
    collection = get_collection()
    result = collection.find_one({"_id": ObjectId(template_id)})
    return result










