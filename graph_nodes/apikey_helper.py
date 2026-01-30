"""
Helper function để lấy API key từ database
Nếu database không có API key thì dùng key mặc định
Sử dụng Singleton pattern để cache API key
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from mongodb.actions.apikey_crud import get_apikey

DEFAULT_API_KEY = "AIzaSyCh6jEzMugrYE6WCmkUVqoin2n_KDM5eWw"

# Singleton instance
_cached_api_key = None


def get_api_key_from_db() -> str:
    """
    Lấy API key từ database (sử dụng cache)
    Chỉ query database một lần duy nhất, các lần sau dùng cached value
    
    Returns:
        str: API key
    """
    global _cached_api_key
    
    # Nếu đã có cache, return luôn
    if _cached_api_key is not None:
        print(f"✅ Sử dụng cached API key: {_cached_api_key[:5]}****")
        return _cached_api_key
    
    # Chưa có cache, lấy từ database
    try:
        apikeys = get_apikey()
        if apikeys and len(apikeys) > 0:
            api_key = apikeys[0].get("api_key", "")
            if api_key and api_key.strip():
                _cached_api_key = api_key
                print(f"✅ Đã cache API key từ database")
                return _cached_api_key
        
        # Database không có, dùng key mặc định
        _cached_api_key = DEFAULT_API_KEY
        print(f"⚠️ Database không có API key, đã cache key mặc định")
        return _cached_api_key
    except Exception as e:
        print(f"❌ Lỗi khi lấy API key từ database: {e}")
        _cached_api_key = DEFAULT_API_KEY
        print(f"⚠️ Đã cache key mặc định do lỗi")
        return _cached_api_key


def refresh_api_key():
    """
    Làm mới API key từ database (clear cache và lấy lại)
    Gọi function này khi cần update API key mới
    """
    global _cached_api_key
    _cached_api_key = None
    print(f"🔄 Đã clear cache API key, sẽ lấy lại từ database")
    return get_api_key_from_db()


def get_llm(model_name: str = "gemini-2.5-flash"):
    """
    Tạo LLM instance với API key từ cache
    
    Args:
        model_name: Tên model Gemini
        
    Returns:
        ChatGoogleGenerativeAI: LLM instance
    """
    api_key = get_api_key_from_db()
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0
    )
