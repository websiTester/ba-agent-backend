from typing import Literal
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command
from graph_nodes.apikey_helper import get_llm
from models.state import State


def make_agent_node(agent_config):
    """Hàm này trả về một hàm node dựa trên config"""
    model_name = agent_config['model']
    node_name = agent_config["toolName"]
    instruction = agent_config["agentInstruction"]

    # Đây là hàm thực sự sẽ chạy trong Graph
    def _node_func(state: State) -> Command[Literal["supervisor"]]:
        # Số lần thử
        max_attempts = 1
        last_error = None
        empty_response_count = 0
        
        for attempt in range(max_attempts):
            # Lấy LLM với API key từ database
            current_llm = get_llm(model_name)
            try:
                # Tạo agent "nóng" tại runtime với LLM hiện tại
                agent = create_agent(current_llm, system_prompt=instruction)
                result = agent.invoke(state)
                
                content = result['messages'][-1].content if result.get('messages') else ''
                print(f"Content TYPE: {type(content)}")
                
                # Validate response - không cho phép response rỗng
                if not content or (isinstance(content, str) and content.strip() == ''):
                    empty_response_count += 1
                    print(f"⚠️ Agent {node_name} trả về response rỗng (lần {empty_response_count})")
                    
                    # Chỉ retry 2 lần cho empty response, KHÔNG đổi key
                    if empty_response_count < 2:
                        print(f"🔄 Retry lại với cùng key (không phải lỗi quota)")
                        continue
                    else:
                        # Sau 3 lần rỗng, trả về error
                        content = f'{{"error": "Agent {node_name} trả về response rỗng sau {empty_response_count} lần thử. Có thể do instruction không phù hợp hoặc input không hợp lệ.", "status": "empty_response"}}'
                        print(f"❌ Agent {node_name} response rỗng quá nhiều lần, dừng retry")
                
                return Command(
                    update={
                        "messages": [
                            # Quan trọng: name phải khớp với node_name trong DB
                            AIMessage(content=content, name=node_name)
                        ]
                    },
                    goto="supervisor",
                )
                
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e)
                
                print(f"❌ Agent {node_name} gặp lỗi (lần {attempt + 1}/{max_attempts}): {error_type}: {error_msg}")
                
                # Chỉ rotate key khi gặp lỗi quota/rate limit
                is_quota_error = (
                    'quota' in error_msg.lower() or 
                    'rate limit' in error_msg.lower() or
                    '429' in error_msg or
                    'resource exhausted' in error_msg.lower()
                )
                
                if is_quota_error and attempt < max_attempts - 1:
                    # Lấy lại LLM (sẽ check API key mới từ database nếu có)
                    current_llm = get_llm(model_name)
                    print(f"🔄 Retry với API key từ database cho agent {node_name} (lỗi quota)")
                elif not is_quota_error:
                    # Lỗi khác (không phải quota), không retry
                    print(f"⚠️ Lỗi không phải quota, dừng retry")
                    break
        
        # Nếu tất cả keys đều thất bại, trả về error message thay vì crash
        error_content = f'{{"error": "Agent {node_name} thất bại sau khi thử {max_attempts} lần: {str(last_error)}", "status": "failed"}}'
        print(f"❌ Agent {node_name} thất bại hoàn toàn, trả về error response")
        return Command(
            update={
                "messages": [
                    AIMessage(content=error_content, name=node_name)
                ]
            },
            goto="supervisor",
        )
    
    return _node_func