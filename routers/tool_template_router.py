from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from graphs.ba_dynamic_graph import refresh_ba_graph
import re
from mongodb.actions.tool_template import (
    get_templates_by_agent_source,
    add_templates,
    update_template,
    delete_template,
    set_template_in_use,
    get_template_by_id
)
from mongodb.actions.crud import get_tool_by_name, update_tool_by_id
from mongodb.models.types import ToolSchema

router = APIRouter()


# Pydantic models
class TemplateItem(BaseModel):
    header: str
    content: str


class TemplateCreate(BaseModel):
    agent_source: str
    template_name: str
    is_default: bool
    is_in_use: bool
    template: List[TemplateItem]


class TemplateUpdate(BaseModel):
    agent_source: str = None
    template_name: str = None
    template: List[TemplateItem] = None


@router.post("/templates")
def create_template(template: TemplateCreate):
    """
    Tạo template mới
    
    Body:
        {
            "agent_source": "requirement_agent",
            "template_name": "Template 1",
            "is_default": "true",
            "is_in_use": "false"
            "template": [
                {"header": "Header 1", "content": "Content 1"},
                {"header": "Header 2", "content": "Content 2"}
            ]
        }
    """
    try:
        template_dict = template.dict()
        inserted_id = add_templates(template_dict)
        
        return {
            "success": True,
            "message": "Template created successfully",
            "template_id": str(inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/templates/update/{template_id}")
def update_template_by_id(template_id: str, template: TemplateUpdate):
    """
    Update template theo ID
    
    Args:
        template_id: ID của template cần update
        
    Body:
        {
            "agent_source": "new_agent_source",
            "template": [
                {"header": "Updated Header", "content": "Updated Content"}
            ]
        }
    """
    print(f"Update Template")
    try:
        # Chỉ update các field không None
        update_data = {}
        if template.agent_source is not None:
            update_data["agent_source"] = template.agent_source
        if template.template is not None:
            update_data["template"] = [item.dict() for item in template.template]
        if template.template_name is not None:
            update_data["template_name"] = template.template_name
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")
        
        modified_count = update_template(template_id, update_data)
        
        if modified_count == 0:
            raise HTTPException(status_code=404, detail="Template not found or no changes made")
        
        return {
            "success": True,
            "message": "Template updated successfully",
            "template_id": template_id,
            "modified_count": modified_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/templates/{template_id}")
def delete_template_by_id(template_id: str):
    """
    Xóa template theo ID
    
    Args:
        template_id: ID của template cần xóa
    """
    try:
        deleted_count = delete_template(template_id)
        
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "success": True,
            "message": "Template deleted successfully",
            "template_id": template_id,
            "deleted_count": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/templates/set-active/{template_id}")
def set_template_active(template_id: str, agent_source: str):
    """
    Set template làm active (is_in_use = true), set các template khác thành inactive,
    tạo DataSchema XML từ template và cập nhật vào agentInstruction của tool
    
    Args:
        template_id: ID của template cần set active
        agent_source: Agent source (query parameter) để xác định nhóm template
        
    Example:
        PUT /tool_template/templates/697044466cfc75cfb78e4652/set-active?agent_source=requirement_agent
    """
    try:
        # Bước 1: Lấy template theo ID
        template = get_template_by_id(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Bước 2: Tạo XML columns từ template
        columns_xml = ""
        template_items = template.get("template", [])
        
        for item in template_items:
            header = item.get("header", "")
            content = item.get("content", "")
            
            # Tạo Column XML cho mỗi cặp header-content
            column_xml = f"""<Column name="{header}">
<Description>{content}</Description>
<Language>Vietnamese</Language>
<Required>true</Required>
</Column>
"""
            columns_xml += column_xml
        
        # Thêm column _action
        columns_xml += """<Column name="_action">
<Description>Action áp dụng lên dòng dữ liệu.</Description>
<AllowedValues>create, update, delete</AllowedValues>
<Required>true</Required>
</Column>
"""
        
        # Bước 3: Tạo DataSchema hoàn chỉnh
        new_data_schema = f"""<DataSchema priority="HIGHEST">
<Format>csv</Format>
<Delimiter>|</Delimiter>
<Columns>
{columns_xml}</Columns>
<OutputExample>
ID|Type|Name|Description|Rationale|....(Label of other header)....|_action
FR-01|FR|Xuất báo cáo|Hệ thống cho phép xuất báo cáo: PDF, Excel, Word|Người dùng cần linh hoạt|.....(result of the content of the header).....|create
  </OutputExample>
<Rules>
<Escaping>If a cell contains comma (,), newline (
) or double-quote ("), wrap in double-quotes.</Escaping>
<Mandatory>_action column is required in every row.</Mandatory>
</Rules>
</DataSchema>"""
        
        # Bước 4: Lấy tool theo toolName = agent_source
        tool = get_tool_by_name(agent_source)
        
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool with name '{agent_source}' not found")
        
        # Bước 5: Lấy agentInstruction và thay thế DataSchema cũ bằng mới
        agent_instruction = tool.get("agentInstruction", "")
        
        # Pattern để tìm và thay thế DataSchema block
        data_schema_pattern = r'<DataSchema[^>]*>.*?</DataSchema>'
        
        # Kiểm tra xem có DataSchema trong instruction không
        if re.search(data_schema_pattern, agent_instruction, re.DOTALL):
            # Thay thế DataSchema cũ bằng mới
            updated_instruction = re.sub(
                data_schema_pattern, 
                new_data_schema, 
                agent_instruction, 
                flags=re.DOTALL
            )
        else:
            # Nếu chưa có DataSchema, thêm vào cuối instruction
            updated_instruction = agent_instruction + "\n\n" + new_data_schema
        
        # Bước 6: Update tool với agentInstruction mới
        tool["agentInstruction"] = updated_instruction
        tool_schema = ToolSchema(**tool)
        update_tool_by_id(str(tool["_id"]), tool_schema)
        
        # Bước 7: Set template active
        result = set_template_in_use(template_id, agent_source)
        
        if not result["activated"]:
            raise HTTPException(status_code=404, detail="Failed to activate template")
        
        refresh_ba_graph()
        print(f"[SUCCESS] Updated tool '{agent_source}' with new DataSchema")
        
        return {
            "success": True,
            "message": f"Template {template_id} is now active and tool instruction updated",
            "template_id": template_id,
            "tool_name": agent_source,
            "deactivated_count": result["deactivated_count"],
            "data_schema": new_data_schema
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{agent_source}")
def get_templates(agent_source: str):
    """
    Lấy tất cả templates theo agent_source
    
    Args:
        agent_source: Tên của agent source (ví dụ: "requirement_agent")
        
    Returns:
        List các template của agent đó
    """
    try:
        templates = list(get_templates_by_agent_source(agent_source))
        
        # Convert ObjectId to string
        for template in templates:
            if "_id" in template:
                template["_id"] = str(template["_id"])
        
        return {
            "success": True,
            "agent_source": agent_source,
            "count": len(templates),
            "data": templates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
