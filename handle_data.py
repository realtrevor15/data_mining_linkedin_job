import pandas as pd

# # Đọc dữ liệu từ hai file CSV
# labeled_data = pd.read_csv('data/labeled_data.csv')
# profile_info = pd.read_csv('data/experience.csv')

# # Lọc các hàng trong profile_info mà public_id xuất hiện trong labeled_data
# filtered_profile_info = profile_info[profile_info['public_id'].isin(labeled_data['public_id'])]

# # Bỏ cột 'id' nếu tồn tại
# if 'id' in filtered_profile_info.columns:
#     filtered_profile_info = filtered_profile_info.drop(columns=['id'])

# # Lưu kết quả vào file profile_info_filter.csv

df = pd.read_csv('data/job_posting.csv', nrows=4306)

df.to_csv('job_posting_filter.csv', index=False)