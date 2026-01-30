from key_manager.gemini_key_manager import key_manager
from google.api_core.exceptions import ResourceExhausted

def run_agent_with_retry(agent_executor, user_input, max_retries=8):
    """
    Hàm này sẽ thử chạy agent. Nếu hết quota, nó tự đổi key và chạy lại.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            # Cố gắng chạy agent
            result = agent_executor.invoke({"input": user_input})
            return result
            
        except ResourceExhausted:
            # Đây là lỗi 429 (Hết quota) của Google
            attempt += 1
            print(f"Lỗi Quota (Lần thử {attempt}/{max_retries}). Đang đổi API Key...")
            
            # 1. Xoay key sang cái tiếp theo
            new_key = key_manager.rotate_key()
            
            # 2. CẬP NHẬT LẠI LLM TRONG AGENT
            # Lưu ý: Bạn phải gán lại api_key mới cho model bên trong agent
            # Tùy vào cách bạn build agent, thường LLM nằm ở agent.llm hoặc agent.agent.llm_chain.llm
            # Đây là ví dụ chung, bạn cần trỏ đúng vào object LLM của bạn:
            
            # Nếu dùng AgentExecutor cũ:
            agent_executor.agent.llm_chain.llm.google_api_key = new_key
            
            # Nếu dùng LangGraph hoặc cơ chế mới, cách đơn giản nhất là 
            # Re-build lại agent với LLM mới từ key_manager.get_llm()
            # (Xem phần lưu ý bên dưới)
            
        except Exception as e:
            # Nếu là lỗi khác (code sai, logic sai) thì throw luôn, không retry
            raise e
            
    raise Exception("Đã thử tất cả API Key nhưng vẫn đều hết Quota!")