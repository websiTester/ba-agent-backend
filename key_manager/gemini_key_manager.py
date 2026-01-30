import os
import itertools
from dotenv import load_dotenv
from langchain_google_genai  import ChatGoogleGenerativeAI

load_dotenv()
class GeminiKeyManager:
    def __init__(self):
        # 1. Lấy chuỗi key từ env và tách thành list
        keys_str = os.getenv("GOOGLE_API_KEYS", "")
        self.keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        
        if not self.keys:
            raise ValueError("Không tìm thấy GOOGLE_API_KEYS trong file .env")

        # 2. Tạo một vòng lặp vô tận (cycle) để xoay vòng key
        self.key_cycle = itertools.cycle(self.keys)
        self.current_key = next(self.key_cycle)
        print(f"Khởi động với Key: ...{self.current_key[-4:]}")

    def rotate_key(self):
        """Chuyển sang key tiếp theo trong danh sách"""
        self.current_key = next(self.key_cycle)
        print(f"⚠️ Hết quota! Đã chuyển sang Key: ...{self.current_key[-4:]}")
        return self.current_key

    def get_llm(self, agentModel: str="gemini-2.5-flash"):
        """Trả về một instance ChatGoogleGenerativeAI với key hiện tại"""
        print(f"GET_LLM KEY: {self.current_key}")
        return ChatGoogleGenerativeAI(
            model=agentModel, # Hoặc model bạn đang dùng
            api_key=self.current_key,
            
        )


    def get_key(self):
        print(f"GET_KEY: {self.current_key}")
        return self.current_key

    def get_keys_count(self):
        """Trả về số lượng API keys"""
        return len(self.keys)


# Khởi tạo singleton để dùng chung trong toàn bộ app
key_manager = GeminiKeyManager()