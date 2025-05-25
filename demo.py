import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Hàm làm sạch văn bản
def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text

# Hàm tạo biểu diễn văn bản cho job
def get_job_text(row, job_cols=['job_description', 'job_requirements'], company_cols=['company_description']):
    job_text = ' '.join([clean_text(row.get(col, '')) for col in job_cols])
    company_text = ' '.join([clean_text(row.get(col, '')) for col in company_cols])
    return f"{job_text} {company_text}".strip()

# Hàm tạo biểu diễn văn bản cho candidate
def get_candidate_text(row, profile_cols=['profile_summary', 'skills'], exp_cols=['experience_details']):
    profile_text = ' '.join([clean_text(row.get(col, '')) for col in profile_cols])
    exp_text = ' '.join([clean_text(row.get(col, '')) for col in exp_cols])
    return f"{profile_text} {exp_text}".strip()

# Hàm recommendation
def recommend_jobs(candidate_id, job_posting_df, company_detail_df, profile_info_df, experience_df, model, top_k=5):
    candidate_profile = profile_info_df[profile_info_df['candidate_id'] == candidate_id]
    candidate_exp = experience_df[experience_df['candidate_id'] == candidate_id]
    if candidate_profile.empty:
        return None, "Không tìm thấy thông tin ứng viên."
    
    candidate_text = get_candidate_text(candidate_profile.iloc[0]) + ' '.join(
        [get_candidate_text(exp_row) for _, exp_row in candidate_exp.iterrows()]
    )
    
    job_texts = []
    job_ids = []
    for _, job_row in job_posting_df.iterrows():
        job_id = job_row['job_id']
        company_info = company_detail_df[company_detail_df['company_id'] == job_row['company_id']]
        company_text = get_candidate_text(company_info.iloc[0]) if not company_info.empty else ''
        job_text = get_job_text(job_row) + ' ' + company_text
        job_texts.append(job_text)
        job_ids.append(job_id)
    
    candidate_embedding = model.encode([candidate_text])[0]
    job_embeddings = model.encode(job_texts)
    similarities = util.cos_sim(candidate_embedding, job_embeddings)[0]
    
    top_k_indices = np.argsort(similarities)[::-1][:top_k]
    recommendations = [
        {'job_id': job_ids[i], 'job_title': job_posting_df.iloc[i]['job_title'], 'similarity_score': similarities[i].item()}
        for i in top_k_indices
    ]
    
    candidate_info = {
        'candidate_id': candidate_id,
        'profile_summary': candidate_profile.iloc[0].get('profile_summary', ''),
        'skills': candidate_profile.iloc[0].get('skills', ''),
        'experience': [exp_row.get('experience_details', '') for _, exp_row in candidate_exp.iterrows()]
    }
    
    return candidate_info, recommendations

# Load dữ liệu và mô hình
job_posting_df = pd.read_csv('job_posting.csv')
company_detail_df = pd.read_csv('company_detail.csv')
profile_info_df = pd.read_csv('profile_info.csv')
experience_df = pd.read_csv('experience.csv')
model = SentenceTransformer('all-MiniLM-L6-v2')  # Thay bằng mô hình đã huấn luyện

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    candidate_id = int(data.get('candidate_id', 0))
    top_k = int(data.get('top_k', 5))
    
    candidate_info, result = recommend_jobs(
        candidate_id, job_posting_df, company_detail_df, profile_info_df, experience_df, model, top_k
    )
    
    if candidate_info is None:
        return jsonify({'error': result}), 404
    
    return jsonify({
        'candidate_info': candidate_info,
        'recommendations': result
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)