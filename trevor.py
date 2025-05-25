import json

def filter_unique_public_id(input_file='result.json', output_file='results.json'):
    # Đọc file JSON
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {input_file}: {str(e)}")
        return
    
    # Lọc public_id trùng lặp, giữ bản ghi đầu tiên
    seen_public_ids = set()
    unique_data = []
    
    for item in data:
        public_id = item['public_id']
        if public_id not in seen_public_ids:
            seen_public_ids.add(public_id)
            unique_data.append(item)
    
    # Lưu vào file JSON mới
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_data, f, ensure_ascii=False, indent=4)
        print(f"Filtered data saved to {output_file}. Total unique candidates: {len(unique_data)}")
    except Exception as e:
        print(f"Error writing to {output_file}: {str(e)}")

if __name__ == '__main__':
    filter_unique_public_id()