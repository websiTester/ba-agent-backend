import time
from enum import Enum, StrEnum
from tkinter import END
from langgraph.graph import START, StateGraph
from langgraph.types import Command
from pydantic import Field, create_model
from graph_nodes.create_agent_node import make_agent_node
from graph_nodes.memory import get_memory
from graph_nodes.apikey_helper import get_llm as get_llm_helper
from models.state import State
from mongodb.actions.agent_crud import get_agent_by_name
from mongodb.actions.crud import get_all_tools
from langchain_core.tools import tool 
from graph_nodes.reporterAgent import create_reporter_node

def create_new_graph_from_db():
    print("Creating nodes from database...")
    toolList = get_all_tools()
    print(f"ToolList: {toolList}")
    graph = StateGraph(State)
    members = []
    member_descriptions = ""

    for tool in toolList:
        print(f"toolName: {tool["toolName"]}")
        #name = tool["toolName"]
        name = str(tool["toolName"]).strip().lower()
        # Tạo hàm node
        node_func = make_agent_node(tool)
        # Add vào graph
        graph.add_node(name, node_func)
        
        # Cập nhật thông tin cho Supervisor
        members.append(name)
        member_descriptions += f"{name}: {tool['toolDescription']}\n"
    
    print(f"ALL TOOl names: {members}\n\n")
    print(f"ALL TOOl description: {member_descriptions}\n\n")
    # 3. Cập nhật Supervisor Node (Cần render prompt động)
    # system_prompt = f"""
    # You are a supervisor, tasked with managing a conversation between the following workers: {members}. 
    # Here are the job descriptions for each worker:
    # {member_descriptions}

    # Given the following user request, respond with the worker to act next. 
    # Each worker will perform a task and respond with their results and status. 
    # When finished, respond with FINISH.
    # ...
    # """

    system_prompt = f"""
    You are a supervisor, tasked with managing a conversation between the following workers: {members}. 
    Here are the job descriptions for each worker:
    {member_descriptions}

    YOUR CORE OBJECTIVE:
    Orchestrate the workers to fulfill the user's request completely. You act as the project manager, breaking down complex requests into steps and assigning them to the right worker sequentially.

    EVALUATION & ROUTING LOGIC:
    1.  **Analyze the User Request:** Identify all distinct tasks required (e.g., "Analyze requirements" AND "Generate Code" are two separate tasks).
    2.  **Review Progress:** Look at the most recent output from the workers.
    3.  **Gap Analysis:** Compare the User Request against the Completed Work.
        * *Ask yourself:* "Has the latest worker's response fully satisfied the ENTIRE user request?"
        * *If NO (Partial Completion):* Identify which part is missing and select the next worker best suited to finish that specific part.
        * *If YES (Complete):* Respond with FINISH.

    HANDLING WORKER FAILURES:
    - If a worker returns an empty response or a response containing "error" or "failed", consider that task as FAILED.
    - If a task has failed, you may retry by calling the same worker again (max 1 retry per worker).
    - If a worker has already been called twice and still fails, skip that task and proceed with FINISH.
    - DO NOT get stuck in infinite loops trying to call the same failing worker.

    Given the following user request and conversation history, respond with the worker to act next. 
    When all tasks in the user request are confirmed done (or have failed after retry), respond with FINISH.
    """
    # reporter_node_func = create_reporter_node()
    # graph.add_node("reporter_agent", reporter_node_func)
    # members.append("reporter_agent")
    # member_descriptions += "reporter_agent: Tổng hợp và trình bày báo cáo cuối cùng từ tất cả các Sub-agent\n"


    # system_prompt = f"""
    # Bạn là một Supervisor (Người quản lý) trong hệ thống AI Business Analyst. 
    # Nhiệm vụ của bạn là điều phối các Sub-agent (Agent con) để hoàn thành yêu cầu của người dùng.

    # DỮ LIỆU ĐẦU VÀO:
    # 1. Yêu cầu của người dùng (User Request).
    # 2. Lịch sử các kết quả đã nhận được từ Sub-agents (danh sách `results`).

    # QUY TRÌNH RA QUYẾT ĐỊNH (SUY LUẬN):
    # Bước 1: Phân tích yêu cầu người dùng để xác định các nhiệm vụ cần thực hiện. 
    # - Ví dụ: "Xác định requirement và tạo câu hỏi phỏng vấn" => Cần 2 nhiệm vụ chuyên môn: Requirement và Interview.

    # Bước 2: Kiểm tra danh sách `results` hiện có trong ngữ cảnh (Context).
    # - Mỗi Sub-agent khi hoàn thành sẽ trả về một JSON object có trường "agent_source" (ví dụ: "requirement_agent", "interview_agent", "reporter_agent").
    # - Bạn hãy xem những agent nào ĐÃ trả về kết quả hợp lệ.

    # Bước 3: So sánh & Điều phối (Gap Analysis & Routing).
    # - So sánh [Nhiệm vụ chuyên môn cần làm] với [Kết quả đã có].
    # - TRƯỜNG HỢP 1: Nếu còn thiếu nhiệm vụ chuyên môn (Requirement, Interview...) => Gọi Sub-agent chuyên trách tương ứng.
    #   (Lưu ý: Gọi theo trình tự logic).
    # - TRƯỜNG HỢP 2: Nếu TẤT CẢ nhiệm vụ chuyên môn đã hoàn thành, nhưng **chưa có báo cáo tổng hợp** (chưa có kết quả từ `reporter_agent`) => BẮT BUỘC gọi `reporter_agent`.

    # Bước 4: Kết thúc (Termination).
    # - Kiểm tra điều kiện dừng:
    #   1. Các Sub-agent chuyên môn đã hoàn thành.
    #   2. `reporter_agent` ĐÃ được gọi và ĐÃ trả về kết quả.
    # - NẾU thỏa mãn cả 2 điều kiện trên => TRẢ VỀ: "FINISH".

    # CÁC SUB-AGENT HIỆN CÓ:
    # {member_descriptions}

    # QUY TẮC QUAN TRỌNG:
    # - KHÔNG tự bịa ra câu trả lời. Nhiệm vụ của bạn chỉ là ĐIỀU PHỐI.
    # - KHÔNG sửa đổi nội dung JSON mà Sub-agent trả về.
    # - QUY TẮC VÀNG: Tuyệt đối KHÔNG trả về "FINISH" ngay sau khi các Sub-agent chuyên môn làm xong. Bạn PHẢI gọi `reporter_agent` để tổng hợp thông tin trước, sau đó mới được FINISH.
    
    # OUTPUT FORMAT:
    # Bạn PHẢI trả về một JSON object với định dạng chính xác như sau:
    # {{
    #     "next": "tên_agent_tiếp_theo"
    # }}
    
    # Trong đó "next" có thể là:
    # - Tên của một Sub-agent cần gọi tiếp theo (ví dụ: "requirement_agent", "reporter_agent")
    # - Hoặc "FINISH" nếu tất cả công việc đã hoàn thành
    
    # VÍ DỤ OUTPUT HỢP LỆ:
    # {{"next": "requirement_agent"}}
    # {{"next": "reporter_agent"}}
    # {{"next": "FINISH"}}
    
    # TUYỆT ĐỐI KHÔNG trả về chỉ chuỗi "FINISH" hoặc "requirement_agent" mà PHẢI là JSON object.
    # """


    agentObject = get_agent_by_name("Orchestration_Agent")
    supervisor_node = create_supervisor_node(system_prompt, agentObject, members)
    # (Khai báo supervisor_node như cũ nhưng dùng system_prompt mới này)
    graph.add_node("supervisor", supervisor_node)
    graph.add_edge(START, "supervisor")

    # 4. Compile
    app = graph.compile(checkpointer=get_memory())
    print(app.get_graph().print_ascii())
    return app


def create_supervisor_node(system_prompt: str, agentObject: any, members: any):
    llm = get_llm_helper("gemini-2.5-flash")
    
    # 2. Tạo Router động (Chỉ mất 2 dòng)
    # StrEnum tự động coi các giá trị là string, không cần type=str
    route_options = members + ["finish"]
    enum_choices = {name: name for name in route_options}
    DynamicEnum = StrEnum("DynamicEnum", enum_choices)

    # # Phải dùng (Type, Field(...)) hoặc (Type, DefaultValue)
    # # Nếu viết next=(DynamicEnum), Pydantic hiểu DynamicEnum là default value chứ không phải type
    RouterDynamic = create_model(
        "Router", 
        next=(DynamicEnum, Field(description="The next worker to act or FINISH"))
    )


    def supervisor_node(state: State):
        messages = [{"role": "system", "content": system_prompt},] + state["messages"]
        print(f"State supervisor_node: {state}")
        
        # Số lần thử
        max_attempts = 3
        last_error = None
        current_llm = llm
        
        for attempt in range(max_attempts):
            try:
                response = current_llm.with_structured_output(RouterDynamic).invoke(messages)
                print(f"Response supervisor_node: {response}")
                goto = str(response.next)

                print("below my goto**********************************")
                print(goto)

                if goto.lower() == "finish":
                    goto = END

                return Command(goto=goto, update={"next": goto})
                
            except Exception as e:
                last_error = e
                print(f"❌ Supervisor LLM gặp lỗi (lần {attempt + 1}/{max_attempts}): {type(e).__name__}: {e}")
                
                if attempt < max_attempts - 1:
                    # Lấy lại LLM (sẽ check API key mới từ database nếu có)
                    current_llm = get_llm_helper("gemini-2.5-flash")
                    print(f"🔄 Retry với API key từ database...")
        
        # Nếu tất cả keys đều thất bại, kết thúc workflow
        print(f"❌ Supervisor thất bại sau khi thử tất cả {max_attempts} API keys. Kết thúc workflow.")
        return Command(goto=END, update={"next": "finish", "error": str(last_error)})

    return supervisor_node

