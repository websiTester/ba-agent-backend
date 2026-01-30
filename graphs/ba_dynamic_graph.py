import time
from google.api_core.exceptions import ResourceExhausted, ServerError as GoogleApiServerError
from google.genai.errors import ServerError as GenaiServerError, APIError as GenaiAPIError
from langchain_core.messages import HumanMessage
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from graph_nodes.create_node_from_db import create_new_graph_from_db
from graph_nodes.apikey_helper import refresh_api_key

_GLOBAL_BA_GRAPH = None

def get_ba_compile_graph():
    
    global _GLOBAL_BA_GRAPH
    
    if _GLOBAL_BA_GRAPH is None:
        _GLOBAL_BA_GRAPH = create_new_graph_instance()
        
    return _GLOBAL_BA_GRAPH



def get_ba_graph_response(user_input: str):
    config = {"configurable": {
    "thread_id": 1
    }}
    messages = [HumanMessage(content=user_input)]
    query = user_input
    attempt = 0
    max_retries = 1
    while attempt < max_retries:
        print(f"INPUT RETRY: {user_input}")
        try:
            app = get_ba_compile_graph()
            
            response = app.invoke({"messages": messages}, config=config)
            print(f"RESPONSE123: {response}")
            allContents = getAllResponse(response["messages"])
            #allContents = response["messages"][-1].content
            print(f"allContents: {allContents}")
            return allContents
            
        except (ResourceExhausted, GoogleApiServerError, ChatGoogleGenerativeAIError, GenaiServerError, GenaiAPIError) as e:
            # Lỗi API của Google (429, 500, etc.)
            attempt += 1
            print(f"Lỗi Google API (Lần thử {attempt}/{max_retries}): {type(e).__name__}. Đang retry...")
            
            # Backoff delay
            wait_time = min(2 ** attempt, 30)
            print(f"Đợi {wait_time}s trước khi retry...")
            time.sleep(wait_time)
            
            # Refresh API key từ database và tạo lại graph
            if attempt < max_retries:
                refresh_api_key()
                refresh_ba_graph()
            
        except Exception as e:
            # Nếu là lỗi khác (code sai, logic sai) thì throw luôn, không retry
            raise e
            
    raise Exception("Đã retry tối đa nhưng vẫn gặp lỗi API!") 

def refresh_ba_graph():
    global _GLOBAL_BA_GRAPH
    _GLOBAL_BA_GRAPH = create_new_graph_instance()


def create_new_graph_instance():
    return create_new_graph_from_db()


def getAllResponse(messages:any):
    human_last_index = -1
    for i in range(len(messages)-1,-1,-1):
        if isinstance(messages[i], HumanMessage):
            human_last_index = i
            break
    
    aiMessages = messages[human_last_index+1:]
    contents = [msg.content for msg in aiMessages]
    return contents
    

    