from typing import Annotated, Dict, Optional
from pydantic import BaseModel, BeforeValidator, Field
from bson import ObjectId

# 1. Định nghĩa cấu trúc cho phần "field" (Nested Object)
class ToolField(BaseModel):
    user_input: str
    phase_id: str


PyObjectId = Annotated[str, BeforeValidator(str)]
# 2. Định nghĩa cấu trúc chính cho "Tool"
class ToolSchema(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    toolName: str
    toolDescription: str
    toolPrompt: Optional[str] = None
    agent_parentId: Optional[str] = None
    phaseId: str
    agentToolName: str
    agentToolDescription: str
    agentInstruction: str
    qa_system_prompt: str
    field: Dict[str, str] 
    model: str


class AgentSchema(BaseModel):
    agentName: str
    agentInstruction: str
    model: str
    

class MentionSchema(BaseModel):
    label: str;
    description: str;
    type: str;
    fileId: Optional[str] = None;
    phaseId: Optional[str] = None;
    toolId: Optional[str] = None;


class ApiKeySchema(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    api_key: str


class ApiKeyCreate(BaseModel):
    apiKey: str


class ApiKeyUpdate(BaseModel):
    apiKey: str
    
    
    
    