import json
from fastapi import APIRouter
from pydantic import BaseModel
from graphs.ba_dynamic_graph import get_ba_graph_response, refresh_ba_graph
from utils.response_processor import parse_and_save_ai_responses
from mongodb.actions.response_crud import get_all_response_by_phase_id

# Thay vì app = FastAPI(), ta dùng router
router = APIRouter()


# 2. Định nghĩa cấu trúc dữ liệu body
class AgentRequest(BaseModel):
    input: str
    phase_id: str
    thread_id: str




@router.post("/get_branching_response")
def get_bra_response(request: AgentRequest):
    input = request.input
    phase_id = request.phase_id
    thread_id = request.thread_id
    
    result = get_ba_graph_response(input)  # Content of AIMessage
    print(f"===get_bra_response====: {result}")

    # Parse, loại bỏ duplicates, thêm phaseId và lưu vào MongoDB
    parse_and_save_ai_responses(result, phase_id)

    # Lấy tất cả responses từ database theo phase_id
    all_responses = get_all_response_by_phase_id(phase_id)
    
    # Chuyển đổi ObjectId thành string để có thể serialize JSON
    for response in all_responses:
        if "_id" in response:
            response["_id"] = str(response["_id"])

    # --- KẾT QUẢ ---
    print("Dữ liệu đã xử lý thành công:")
    print(f"======ALL_RESPONSES: {all_responses}")
    
    return {
        "message": all_responses
    }


@router.put("/refresh_agent")
def refresh_agent_config():
    print("REFRESHHHHHH")
    #refresh_agent()
    refresh_ba_graph()
    return {
        "message": "Refresh successfully"
    }


@router.get("/get_responses_by_phase/{phase_id}")
def get_responses_by_phase(phase_id: str):
    """
    Lấy toàn bộ AI responses theo phaseId
    
    Args:
        phase_id: ID của phase cần lấy responses
        
    Returns:
        List các AI responses đã được lưu trong database
    """
    try:
        # Lấy tất cả responses từ database theo phase_id
        all_responses = get_all_response_by_phase_id(phase_id)
        
        # Chuyển đổi ObjectId thành string để có thể serialize JSON
        for response in all_responses:
            if "_id" in response:
                response["_id"] = str(response["_id"])
        
        print(f"✅ Đã lấy {len(all_responses)} responses cho phase: {phase_id}")
        
        return {
            "success": True,
            "phase_id": phase_id,
            "count": len(all_responses),
            "data": all_responses
        }
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy responses: {e}")
        return {
            "success": False,
            "phase_id": phase_id,
            "error": str(e),
            "data": []
        }


        