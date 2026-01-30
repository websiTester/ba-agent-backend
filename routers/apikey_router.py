from fastapi import APIRouter, HTTPException
from mongodb.actions.apikey_crud import (
    get_apikey,
    add_apikey,
    update_apikey
)
from mongodb.models.types import ApiKeyCreate, ApiKeyUpdate
from graph_nodes.apikey_helper import refresh_api_key
from graphs.ba_dynamic_graph import refresh_ba_graph


router = APIRouter()


@router.get("/apikey")
def get_current_apikey():
    """
    Lấy API key hiện tại (chỉ có 1 API key duy nhất trong database)
    
    Returns:
        {
            "success": True,
            "api_key": "..."
        }
    """
    try:
        apikeys = get_apikey()
        
        if not apikeys:
            return {
                "success": True,
                "message": "No API key found",
                "api_key": None
            }
        
        # Lấy API key đầu tiên (chỉ có 1)
        apikey = apikeys[0]
        
        return {
            "success": True,
            "api_key": apikey.get("api_key", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apikey")
def create_or_update_apikey(apiKey: ApiKeyCreate):
    """
    Thêm hoặc update API key
    Database chỉ lưu 1 API key duy nhất dưới dạng string
    Nếu đã có API key thì sẽ update, chưa có thì tạo mới
    
    Body:
        {
            "api_key": "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        }
    
    Returns:
        {
            "success": True,
            "message": "API key created/updated successfully",
            "apikey_id": "...",
            "is_new": true/false
        }
    """
    try:
        # Add or update API key
        apikey_id, is_new = add_apikey(apiKey.apiKey)
        
        message = "API key created successfully" if is_new else "API key updated successfully"
        
        refresh_api_key()
        refresh_ba_graph()
        return {
            "success": True,
            "message": message,
            "apikey_id": str(apikey_id),
            "is_new": is_new
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/apikey")
def update_current_apikey(apiKey: ApiKeyUpdate):
    """
    Update API key hiện tại
    
    Body:
        {
            "api_key": "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        }
    
    Returns:
        {
            "success": True,
            "message": "API key updated successfully"
        }
    """
    try:
        # Lấy API key hiện tại
        existing_keys = get_apikey()
        
        if not existing_keys:
            raise HTTPException(
                status_code=404,
                detail="No API key found. Please create one first using POST /apikey"
            )
        
        apikey_id = str(existing_keys[0]["_id"])
        
        # Update in database
        result = update_apikey(apikey_id, apiKey.apiKey)
        
        return {
            "success": True,
            "message": "API key updated successfully",
            "modified_count": result.modified_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
