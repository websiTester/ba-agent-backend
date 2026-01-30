from typing import Literal
from langchain_core.messages import AIMessage
from langgraph.types import Command
from graph_nodes.apikey_helper import get_llm as get_llm_helper
from models.state import State
import json


def create_reporter_node(model_name: str = "gemini-2.5-flash-lite"):
    """
    Tạo Reporter Agent node để tổng hợp thông tin từ các subagent
    """
    llm = get_llm_helper(model_name)
    
    system_prompt = """
    Bạn là Reporter Agent - Chuyên gia tổng hợp và trình bày thông tin.
    
    NHIỆM VỤ:
    - Thu thập tất cả kết quả từ các Sub-agent đã thực thi
    - Tổng hợp thành một báo cáo có cấu trúc rõ ràng
    - Giữ nguyên nội dung từ các Sub-agent trong detailed_report dưới dạng list
    
    QUY TẮC:
    - KHÔNG bịa đặt hoặc sửa đổi thông tin từ các Sub-agent
    - Giữ NGUYÊN VẸN nội dung trả về từ mỗi Sub-agent
    - detailed_report phải là một list, mỗi phần tử chứa kết quả từ một Sub-agent
    - Chỉ tạo summary ngắn gọn để tổng quan
    
    OUTPUT FORMAT:
    Trả về một JSON object với cấu trúc:
    {
        "agent_source": "reporter_agent",
        "report_title": "Tiêu đề báo cáo",
        "summary": "Tóm tắt ngắn gọn về các thông tin đã thu thập",
        "detailed_report": [
            {
                "agent_name": "tên_agent_1",
                "content": "nội dung trả về từ agent 1 (giữ nguyên)"
            },
            {
                "agent_name": "tên_agent_2", 
                "content": "nội dung trả về từ agent 2 (giữ nguyên)"
            }
        ],
        "sources": ["danh sách tên các agent đã đóng góp"]
    }
    """
    
    def reporter_node(state: State) -> Command[Literal["supervisor"]]:
        """
        Node function xử lý việc tổng hợp thông tin
        """
        messages = state.get("messages", [])
        
        # Lọc các message từ AI agents (bỏ qua HumanMessage và system message)
        agent_results = []
        for msg in messages:
            if isinstance(msg, AIMessage) and hasattr(msg, 'name') and msg.name:
                # Bỏ qua message từ supervisor
                if msg.name.lower() != "supervisor":
                    agent_results.append({
                        "agent_name": msg.name,
                        "content": msg.content
                    })
        
        # Tạo context cho Reporter
        context = f"""
        Dưới đây là kết quả từ {len(agent_results)} Sub-agent(s):
        
        """
        
        for idx, result in enumerate(agent_results, 1):
            context += f"\n--- KẾT QUẢ TỪ {result['agent_name'].upper()} ---\n"
            context += f"{result['content']}\n"
        
        # Thêm yêu cầu gốc từ user
        user_request = ""
        for msg in messages:
            if hasattr(msg, 'type') and msg.type == "human":
                user_request = msg.content
                break
        
        if user_request:
            context = f"YÊU CẦU GỐC TỪ NGƯỜI DÙNG:\n{user_request}\n\n" + context
        
        # Gọi LLM để tổng hợp
        reporter_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context}
        ]
        
        response = llm.invoke(reporter_messages)
        
        # Parse response content
        report_content = response.content
        print(f"REPORT_CONTENT: {report_content}")
        # Thử parse JSON nếu LLM trả về đúng format
        # try:
        #     report_json = json.loads(report_content)
            
        #     # Format detailed_report từ list
        #     detailed_sections = ""
        #     for item in report_json.get('detailed_report', []):
        #         agent_name = item.get('agent_name', 'Unknown Agent')
        #         content = item.get('content', '')
        #         detailed_sections += f"\n### 🔹 {agent_name.upper()}\n{content}\n"
            
        #     # Format lại thành markdown đẹp hơn
        #     formatted_report = f"""
        #     # {report_json.get('report_title', 'BÁO CÁO TỔNG HỢP')}

        #     ## 📋 Tóm tắt
        #     {report_json.get('summary', '')}

        #     ## 📝 Chi tiết từ các Sub-agent
        #     {detailed_sections}

        #     ---
        #     *Nguồn thông tin: {', '.join(report_json.get('sources', []))}*
        #     """
        #     final_content = formatted_report
        # except json.JSONDecodeError:
        #     # Nếu không parse được JSON, dùng content gốc
        #     final_content = report_content
        
        print(f"[REPORTER] Đã tổng hợp báo cáo từ {len(agent_results)} agent(s)")
        
        return Command(
            update={
                "messages": [
                    AIMessage(
                        content=report_content,
                        name="reporter_agent"
                    )
                ]
            },
            goto="supervisor"
        )
    
    return reporter_node
