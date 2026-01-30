import csv
import io
import re
from typing import List
import pandas as pd
from json_repair import repair_json
from mongodb.actions.response_crud import upsert_response


def parse_psv_to_array(psv_string: str) -> List[dict]:
    """Parse Pipe-Separated Values"""
    if not psv_string or not isinstance(psv_string, str):
        return []
    
    try:
        psv_string = psv_string.lstrip('\ufeff').strip()
        csv_file = io.StringIO(psv_string)
        reader = csv.DictReader(csv_file, delimiter='|')
        
        result = []
        for row in reader:
            cleaned_row = {
                k.strip(): v.strip() if v else ""
                for k, v in row.items()
                if k and k.strip()
            }
            if cleaned_row:
                result.append(cleaned_row)
        
        print(f"✅ Đã parse PSV thành công: {len(result)} rows")
        return result
        
    except Exception as e:
        print(f"⚠️ Lỗi khi parse PSV: {e}")
        return []


def preprocess_csv_data(csv_string: str) -> str:
    """
    Tiền xử lý dữ liệu CSV sử dụng pandas để đảm bảo độ chính xác.
    
    Args:
        csv_string: Chuỗi CSV gốc từ AI response
        
    Returns:
        Chuỗi CSV đã được làm sạch
    """
    if not csv_string or not isinstance(csv_string, str):
        return ""
    
    try:
        # Loại bỏ BOM và chuẩn hóa line endings
        cleaned = csv_string.lstrip('\ufeff')
        cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
        
        # FIX 1: Xử lý escaped quotes \" thành ""
        # CSV standard sử dụng "" để escape quote trong quoted field
        cleaned = cleaned.replace('\\"', '""')
        
        # FIX 2: Xử lý literal \n trong quoted fields
        # Sử dụng regex để tìm và replace \n trong quoted fields
        def replace_literal_newlines_in_quotes(text):
            """
            Replace literal \\n with space inside quoted CSV fields
            Xử lý cả trường hợp có escaped quotes
            """
            result = []
            in_quotes = False
            i = 0
            
            while i < len(text):
                char = text[i]
                
                # Toggle quote state
                if char == '"':
                    # Check if it's escaped quote ""
                    if i + 1 < len(text) and text[i + 1] == '"':
                        result.append('""')
                        i += 2
                        continue
                    else:
                        in_quotes = not in_quotes
                        result.append(char)
                        i += 1
                        continue
                
                # Replace \n with space when inside quotes
                if in_quotes and char == '\\' and i + 1 < len(text) and text[i + 1] == 'n':
                    result.append(' ')  # Replace \n with space
                    i += 2
                    continue
                
                result.append(char)
                i += 1
            
            return ''.join(result)
        
        cleaned = replace_literal_newlines_in_quotes(cleaned)
        
        # Đọc CSV bằng pandas với các tùy chọn xử lý lỗi
        df = pd.read_csv(
            io.StringIO(cleaned),
            skipinitialspace=True,  # Bỏ khoảng trắng đầu field
            skip_blank_lines=True,   # Bỏ dòng trống
            on_bad_lines='skip',     # Bỏ qua dòng lỗi
            encoding='utf-8',
            quotechar='"',
            doublequote=True,  # Xử lý "" như escaped quote
            escapechar=None    # Không dùng escape char
        )
        
        # Loại bỏ các dòng trùng lặp
        df = df.drop_duplicates()
        
        # Loại bỏ các dòng có tất cả giá trị là NaN
        df = df.dropna(how='all')
        
        # Trim khoảng trắng cho tất cả các cột string
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()
        
        # Chuyển đổi lại thành CSV string
        cleaned_csv = df.to_csv(index=False, lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
        
        print(f"🧹 Đã tiền xử lý CSV bằng pandas: {len(csv_string)} -> {len(cleaned_csv)} ký tự, {len(df)} rows")
        
        return cleaned_csv
        
    except Exception as e:
        print(f"⚠️ Lỗi khi xử lý CSV bằng pandas: {e}")
        print(f"⚠️ CSV gây lỗi (100 ký tự đầu): {csv_string[:100]}")
        print("🔄 Fallback sang xử lý thủ công...")
        
        # Fallback: xử lý cơ bản nếu pandas thất bại
        cleaned = csv_string.lstrip('\ufeff')
        cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
        cleaned = cleaned.replace('\\"', '""')
        
        # Replace literal \n in quoted fields (simple version)
        def replace_literal_newlines_in_quotes(text):
            result = []
            in_quotes = False
            i = 0
            
            while i < len(text):
                char = text[i]
                
                if char == '"':
                    if i + 1 < len(text) and text[i + 1] == '"':
                        result.append('""')
                        i += 2
                        continue
                    else:
                        in_quotes = not in_quotes
                        result.append(char)
                        i += 1
                        continue
                
                if in_quotes and char == '\\' and i + 1 < len(text) and text[i + 1] == 'n':
                    result.append(' ')
                    i += 2
                    continue
                
                result.append(char)
                i += 1
            
            return ''.join(result)
        
        cleaned = replace_literal_newlines_in_quotes(cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned


def parse_csv_to_array(csv_string: str) -> List[dict]:
    """
    Parse chuỗi CSV thành danh sách các dictionary.
    
    Args:
        csv_string: Chuỗi CSV với header ở dòng đầu tiên
        
    Returns:
        List các dictionary, mỗi dictionary là một row của CSV
    """
    if not csv_string or not isinstance(csv_string, str):
        return []
    
    try:
        # Tiền xử lý CSV trước khi parse
        cleaned_csv = preprocess_csv_data(csv_string)
        
        if not cleaned_csv:
            return []
        
        # Sử dụng StringIO để đọc CSV từ string
        csv_file = io.StringIO(cleaned_csv)
        reader = csv.DictReader(csv_file)
        
        # Chuyển đổi thành list of dictionaries và làm sạch values
        result = []
        for row in reader:
            # Làm sạch giá trị của mỗi field
            cleaned_row = {
                key: value.strip() if isinstance(value, str) else value
                for key, value in row.items()
                if key is not None  # Bỏ qua các cột không có header
            }
            result.append(cleaned_row)
        
        print(f"✅ Đã parse CSV thành công: {len(result)} rows")
        return result
        
    except Exception as e:
        print(f"⚠️ Lỗi khi parse CSV: {e}")
        return []


def parse_and_save_ai_responses(raw_responses: List[str], phase_id: str) -> List[dict]:
    """
    Parse danh sách JSON responses từ AI, loại bỏ duplicates theo agent_source,
    chuyển đổi data từ CSV sang array, thêm phaseId và lưu vào MongoDB.
    
    Args:
        raw_responses: Danh sách các chuỗi JSON từ AI response
        phase_id: ID của phase để gắn vào mỗi response
        
    Returns:
        List các response đã được parse và lưu thành công
    """
    list_result = []
    
    # Parse JSON và loại bỏ duplicates theo agent_source
    for jsondata in raw_responses:
        try:
            final_data = repair_json(jsondata, return_objects=True)
            
            # Kiểm tra final_data có phải dict không
            if not isinstance(final_data, dict):
                print(f"⚠️ repair_json trả về không phải dict: {type(final_data)}")
                # Nếu là list, lấy phần tử đầu tiên
                if isinstance(final_data, list) and len(final_data) > 0:
                    final_data = final_data[0]
                    print(f"✅ Đã lấy phần tử đầu tiên từ list")
                else:
                    print(f"⚠️ Bỏ qua response không hợp lệ")
                    continue
            
            # Kiểm tra xem agent_source đã tồn tại chưa
            existing_item = next(
                (item for item in list_result if item.get('agent_source') == final_data.get('agent_source')), 
                None
            )
            
            if existing_item:
                # Cập nhật item cũ với data mới
                idx = list_result.index(existing_item)
                list_result[idx] = final_data
            else:
                list_result.append(final_data)
                
        except Exception as e:
            print(f"⚠️ Lỗi khi parse JSON: {e}")
            continue
    
    # Thêm phaseId và lưu vào MongoDB
    saved_results = []
    for item in list_result:
        # Kiểm tra item có phải dict không
        if not isinstance(item, dict):
            print(f"⚠️ Item không phải dict, bỏ qua: {type(item)} - {item}")
            continue
        
        # Thêm phaseId vào item
        item["phaseId"] = phase_id
        
        # Parse data từ CSV sang array nếu data_format là "csv"
        data_format = item.get("data_format", "").lower()
        if data_format == "csv" and item.get("data"):
            csv_data = item.get("data", "")
            #parsed_data = parse_csv_to_array(csv_data)
            parsed_data = parse_psv_to_array(csv_data)
            print(f"Parsed CSV: {parsed_data}")
            item["data"] = parsed_data
            print(f"📊 Đã chuyển đổi CSV sang array cho agent: {item.get('agent_source')}")
        
        # Lấy agent_source để làm key cho upsert
        agent_source = item.get("agent_source", "")
        
        # Chỉ lưu nếu có agent_source (bỏ qua các response không hợp lệ)
        if agent_source:
            try:
                upsert_response(phase_id, agent_source, item)
                print(f"✅ Đã lưu response từ agent: {agent_source}")
                saved_results.append(item)
            except Exception as e:
                print(f"❌ Item bị lỗi: {item}")
                print(f"❌ Lỗi khi lưu response từ agent {agent_source}: {e}")
        else:
            # Vẫn thêm vào kết quả trả về dù không lưu được
            saved_results.append(item)
    
    return saved_results


def parse_ai_responses(raw_responses: List[str]) -> List[dict]:
    """
    Parse danh sách JSON responses từ AI, loại bỏ duplicates theo agent_source.
    Không lưu vào MongoDB.
    
    Args:
        raw_responses: Danh sách các chuỗi JSON từ AI response
        
    Returns:
        List các response đã được parse
    """
    list_result = []
    
    for jsondata in raw_responses:
        try:
            final_data = repair_json(jsondata, return_objects=True)
            
            # Kiểm tra xem agent_source đã tồn tại chưa
            existing_item = next(
                (item for item in list_result if item.get('agent_source') == final_data.get('agent_source')), 
                None
            )
            
            if existing_item:
                idx = list_result.index(existing_item)
                list_result[idx] = final_data
            else:
                list_result.append(final_data)
                
        except Exception as e:
            print(f"⚠️ Lỗi khi parse JSON: {e}")
            continue
    
    return list_result
