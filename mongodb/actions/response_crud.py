from typing import Optional
from bson import ObjectId
from mongodb.actions.connection import get_connection


def get_collection():
    """Lấy collection aiResponse từ database"""
    db = get_connection()
    return db["aiResponse"]


def get_all_response_by_phase_id(phase_id: str):
    """
    Lấy toàn bộ response theo phaseId
    
    Args:
        phase_id: ID của phase cần lấy response
        
    Returns:
        List các response documents
    """
    collection = get_collection()
    result = collection.find({"phaseId": phase_id})
    return list(result)


def add_response(response_data: dict):
    """
    Thêm response mới vào MongoDB
    
    Args:
        response_data: Dictionary chứa thông tin response với format:
            {
                "phaseId": "",
                "agent_source": "",
                "response_type": "",
                "title": "",
                "data_format": "",
                "data": ""
            }
            
    Returns:
        ID của document vừa được thêm
    """
    collection = get_collection()
    result = collection.insert_one(response_data)
    print(f"✅ Response added successfully with ID: {result.inserted_id}")
    return result.inserted_id


def update_response_by_agent_source(phase_id: str, agent_source: str, update_data: dict):
    """
    Update response theo agent_source và phaseId
    
    Args:
        phase_id: ID của phase
        agent_source: Tên agent source cần update
        update_data: Dictionary chứa các trường cần update
        
    Returns:
        UpdateResult object
    """
    collection = get_collection()
    
    # Xóa các trường không nên update
    if "_id" in update_data:
        del update_data["_id"]
    if "id" in update_data:
        del update_data["id"]
    
    result = collection.update_one(
        {"phaseId": phase_id, "agent_source": agent_source},
        {"$set": update_data}
    )
    
    if result.modified_count > 0:
        print(f"✅ Response updated successfully for agent_source: {agent_source}")
    else:
        print(f"⚠️ No response found or no changes made for agent_source: {agent_source}")
    
    return result


def get_response_by_agent_source(phase_id: str, agent_source: str) -> Optional[dict]:
    """
    Lấy response theo agent_source và phaseId
    
    Args:
        phase_id: ID của phase
        agent_source: Tên agent source cần lấy
        
    Returns:
        Response document hoặc None nếu không tìm thấy
    """
    collection = get_collection()
    result = collection.find_one({"phaseId": phase_id, "agent_source": agent_source})
    return result


def upsert_response(phase_id: str, agent_source: str, response_data: dict):
    """
    Thêm mới hoặc cập nhật response nếu đã tồn tại (dựa trên phaseId và agent_source)
    Xử lý _action (create/update/delete) cho từng object trong data nếu data_format là csv
    
    Args:
        phase_id: ID của phase
        agent_source: Tên agent source
        response_data: Dictionary chứa thông tin response
        
    Returns:
        UpsertResult object hoặc None nếu bỏ qua
    """
    collection = get_collection()
    
    # Đảm bảo phaseId và agent_source trong response_data
    response_data["phaseId"] = phase_id
    response_data["agent_source"] = agent_source
    
    # Xóa _id nếu có để tránh lỗi
    if "_id" in response_data:
        del response_data["_id"]
    
    # Kiểm tra data_format
    data_format = response_data.get("data_format", "").lower()
    
    # LOGIC MỚI: Kiểm tra điều kiện upsert cho CSV
    if data_format == "csv":
        data = response_data.get("data")
        
        # Nếu data không phải list, bỏ qua không upsert
        if not isinstance(data, list):
            print(f"⚠️ Bỏ qua upsert cho agent '{agent_source}': data_format='csv' nhưng data không phải list (type: {type(data)})")
            return None
        
        # Nếu data là list rỗng, cũng bỏ qua
        if len(data) == 0:
            print(f"⚠️ Bỏ qua upsert cho agent '{agent_source}': data_format='csv' nhưng data là list rỗng")
            return None
        
        print(f"✅ Data hợp lệ cho CSV: list với {len(data)} items")
    
    # Xử lý _action cho CSV data
    if data_format == "csv" and isinstance(response_data.get("data"), list):
        # Lấy response hiện tại từ database
        existing_response = get_response_by_agent_source(phase_id, agent_source)
        
        if existing_response:
            print(f"EXISTING RESPONSE FROM DB LENGTH: {len(existing_response.get('data', []))}")
        else:
            print(f"📝 Không có response cũ trong DB cho agent: {agent_source}")
        
        if existing_response and isinstance(existing_response.get("data"), list):
            # Có dữ liệu cũ, kiểm tra điều kiện để xử lý _action
            existing_data = existing_response.get("data", [])
            new_data = response_data.get("data", [])
            
            # Tạo dict để tra cứu nhanh existing items theo id
            existing_dict = {item.get("id"): item for item in existing_data if item.get("id")}
            
            # ✅ Kiểm tra nếu có item nào action="create" và ID đã tồn tại
            # Nếu có, bỏ qua xử lý _action, chỉ clean data và update toàn bộ
            skip_action_processing = False
            for new_item in new_data:
                action = new_item.get("_action", "").lower()
                item_id = new_item.get("id") or new_item.get("ID")
                
                if action == "create" and item_id and item_id in existing_dict:
                    print(f"⚠️ Phát hiện action='create' với ID '{item_id}' đã tồn tại")
                    print(f"📌 Bỏ qua xử lý _action, update toàn bộ response_data")
                    skip_action_processing = True
                    break
            
            if skip_action_processing:
                # Xóa toàn bộ response cũ và replace với data mới
                delete_response_by_agent_source(phase_id, agent_source)
                
                # Clean _action field khỏi data
                cleaned_data = []
                for item in new_data:
                    cleaned_item = {k: v for k, v in item.items() if k != "_action"}
                    cleaned_data.append(cleaned_item)
                response_data["data"] = cleaned_data
                
                print(f"🗑️ Đã xóa response cũ cho agent '{agent_source}'")
                print(f"📊 Cleaned {len(cleaned_data)} items (xóa _action field)")
                
                # Insert fresh data
                result = collection.insert_one(response_data)
                print(f"✅ Response replaced with fresh data, ID: {result.inserted_id}")
                return result
            else:
                # Không có conflict, tiếp tục xử lý _action bình thường
                # Danh sách kết quả sau khi xử lý
                final_data = []
                
                # Xử lý từng item trong new_data
                for new_item in new_data:
                    action = new_item.get("_action", "").lower()
                    
                    #Người dùng có thể sửa tên id hoặc ID khi update template, check khi lấy
                    item_id = new_item.get("id")
                    if not item_id: 
                        item_id = new_item.get("ID") 
                    
                    
                    if not item_id:
                        # Không có id, bỏ qua
                        print(f"⚠️ Item không có id, bỏ qua: {new_item}")
                        continue
                    
                    if action == "create":
                        # Thêm mới (nếu ID đã tồn tại, cập nhật lại với data mới)
                        # Tạo bản sao item mới và loại bỏ field _action trước khi lưu vào database
                        item_to_add = {k: v for k, v in new_item.items() if k != "_action"}
                        final_data.append(item_to_add)
                        if item_id in existing_dict:
                            print(f"➕ CREATE: {item_id} (ID đã tồn tại, cập nhật lại với data mới)")
                        else:
                            print(f"➕ CREATE: {item_id}")
                    
                    elif action == "update":
                        # Cập nhật (nếu tồn tại)
                        if item_id in existing_dict:
                            # Merge data cũ với data mới
                            updated_item = {**existing_dict[item_id], **new_item}
                            # Xóa field _action khỏi item đã merge
                            if "_action" in updated_item:
                                del updated_item["_action"]
                            final_data.append(updated_item)
                            print(f"✏️ UPDATE: {item_id}")
                        else:
                            # Không tồn tại, thêm mới luôn
                            # Tạo bản sao item mới và loại bỏ field _action
                            item_to_add = {k: v for k, v in new_item.items() if k != "_action"}
                            final_data.append(item_to_add)
                            print(f"➕ UPDATE->CREATE: {item_id} (không tồn tại, tạo mới)")
                    
                    elif action == "delete":
                        # Xóa (không thêm vào final_data)
                        if item_id in existing_dict:
                            print(f"🗑️ DELETE: {item_id}")
                        else:
                            print(f"⚠️ DELETE: {item_id} không tồn tại")
                        # Không thêm vào final_data
                    
                    else:
                        # Không có _action hoặc _action không hợp lệ, giữ nguyên
                        # Tạo bản sao item và loại bỏ field _action (nếu có)
                        item_to_add = {k: v for k, v in new_item.items() if k != "_action"}
                        final_data.append(item_to_add)
                        print(f"ℹ️ NO ACTION: {item_id}, thêm vào")
                
                # Thêm các item cũ không có trong new_data (giữ nguyên)
                new_ids = {item.get("id") for item in new_data if item.get("id")}
                for old_id, old_item in existing_dict.items():
                    if old_id not in new_ids:
                        final_data.append(old_item)
                        print(f"📌 KEEP: {old_id} (không có trong request mới)")
                
                # Cập nhật data đã xử lý
                response_data["data"] = final_data
                print(f"📊 Tổng kết: {len(final_data)} items sau khi xử lý _action")
        else:
            # Không có dữ liệu cũ, xóa _action và lưu tất cả
            cleaned_data = []
            for item in response_data.get("data", []):
                # Dictionary comprehension: tạo dict mới chỉ chứa các key-value không phải "_action"
                cleaned_item = {k: v for k, v in item.items() if k != "_action"}
                cleaned_data.append(cleaned_item)
            response_data["data"] = cleaned_data
            print(f"📊 Không có dữ liệu cũ, lưu {len(cleaned_data)} items mới")
    
    # Thực hiện upsert
    result = collection.update_one(
        {"phaseId": phase_id, "agent_source": agent_source},
        {"$set": response_data},
        upsert=True
    )
    
    if result.upserted_id:
        print(f"✅ Response inserted with ID: {result.upserted_id}")
    else:
        print(f"✅ Response updated for agent_source: {agent_source}")
    
    return result


def delete_response_by_agent_source(phase_id: str, agent_source: str):
    """
    Xóa response theo agent_source và phaseId
    
    Args:
        phase_id: ID của phase
        agent_source: Tên agent source cần xóa
        
    Returns:
        DeleteResult object
    """
    collection = get_collection()
    result = collection.delete_one({"phaseId": phase_id, "agent_source": agent_source})
    
    if result.deleted_count > 0:
        print(f"✅ Response deleted for agent_source: {agent_source}")
    else:
        print(f"⚠️ No response found to delete for agent_source: {agent_source}")
    
    return result


def delete_all_responses_by_phase_id(phase_id: str):
    """
    Xóa tất cả responses theo phaseId
    
    Args:
        phase_id: ID của phase cần xóa tất cả responses
        
    Returns:
        DeleteResult object
    """
    collection = get_collection()
    result = collection.delete_many({"phaseId": phase_id})
    print(f"✅ Deleted {result.deleted_count} responses for phaseId: {phase_id}")
    return result
