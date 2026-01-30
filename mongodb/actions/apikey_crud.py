from typing import Optional
from bson import ObjectId
from mongodb.actions.connection import get_connection


def get_collection():
    """Lấy collection apikey từ database"""
    db = get_connection()
    return db["apikey"]


def get_apikey():

    collection = get_collection()
    result = collection.find({})
    return list(result)


def add_apikey(apikey_string: str):
    """
    Thêm hoặc update apikey trong MongoDB
    Database chỉ lưu 1 apikey duy nhất dưới dạng string
    Nếu đã có apikey thì update, chưa có thì thêm mới
    
    Args:
        apikey_string: API key dưới dạng string
        
    Returns:
        tuple: (apikey_id, is_new) - ID của apikey và flag cho biết là tạo mới hay update
    """
    collection = get_collection()
    
    # Kiểm tra xem đã có apikey nào chưa
    existing_apikey = collection.find_one({})
    
    if existing_apikey:
        # Đã có apikey => Update
        apikey_id = existing_apikey["_id"]
        
        collection.update_one(
            {"_id": apikey_id},
            {"$set": {"api_key": apikey_string}}
        )
        print(f"✅ Apikey updated successfully with ID: {apikey_id}")
        return (apikey_id, False)  # False = không phải tạo mới
    else:
        # Chưa có apikey => Insert mới
        result = collection.insert_one({"api_key": apikey_string})
        print(f"✅ Apikey added successfully with ID: {result.inserted_id}")
        return (result.inserted_id, True)  # True = tạo mới


def update_apikey(apikey_id: str, apikey_string: str):
    """
    Update apikey theo apikey_id
    
    Args:
        apikey_id: ID của apikey cần update
        apikey_string: API key mới dưới dạng string
    """
    collection = get_collection()
    
    result = collection.update_one(
        {"_id": ObjectId(apikey_id)},
        {"$set": {"api_key": apikey_string}}
    )
    
    if result.modified_count > 0:
        print(f"✅ Apikey updated successfully for ID: {apikey_id}")
    else:
        print(f"⚠️ No response found or no changes made for ID: {apikey_id}")
    
    return result
