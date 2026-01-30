from langgraph.checkpoint.memory import MemorySaver


_GLOBAL_MEMORY = None

def get_memory():
    global _GLOBAL_MEMORY
    if _GLOBAL_MEMORY is None:
        _GLOBAL_MEMORY = MemorySaver()
    
    return _GLOBAL_MEMORY