# 1. Hàm tạo Schema động từ Dict
from pydantic import BaseModel, create_model, Field


def create_dynamic_schema(tool_name: str, fields_dict: dict) -> type[BaseModel]:
    """
    Tạo ra một Pydantic Model class động.
    fields_dict: {"field_name": "description"}
    """
    pydantic_fields = {}
    
    for field_name, field_desc in fields_dict.items():
        # Cấu trúc: name = (type, Field(description=...))
        # Ở đây mặc định type là str như bạn yêu cầu
        pydantic_fields[field_name] = (str, Field(description=field_desc))
    
    # Tạo class Dynamic
    # create_model(TenClass, **cac_field)
    DynamicModel = create_model(f"{tool_name}Schema", **pydantic_fields)
    
    return DynamicModel