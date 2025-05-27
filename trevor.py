import json

input_file = 'job_candidate_result.json'
output_file = 'job_candidate_result_unique.json'

# Đọc file JSON đầu vào
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Xử lý loại bỏ candidate_id trùng lặp
for job in data:
    # Tạo dictionary để lưu candidate_id với similarity_score cao nhất
    unique_candidates = {}
    
    # Duyệt qua danh sách recommended_candidates
    for candidate in job['recommended_candidates']:
        candidate_id = candidate['public_id']
        score = candidate['similarity_score']
        
        # Nếu candidate_id chưa có hoặc score mới cao hơn, cập nhật
        if candidate_id not in unique_candidates or score > unique_candidates[candidate_id]['similarity_score']:
            unique_candidates[candidate_id] = {
                'public_id': candidate_id,
                'similarity_score': score
            }
    
    # Cập nhật lại danh sách recommended_candidates
    job['recommended_candidates'] = list(unique_candidates.values())

# Lưu kết quả vào file JSON mới
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Đã lưu kết quả vào {output_file}")