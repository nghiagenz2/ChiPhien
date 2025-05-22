import pandas as pd
import glob
import os

# Đường dẫn tới các file đặc trưng CSV cần hợp nhất
target_dir = '.'  # Thư mục hiện tại
csv_files = [
    'feature_vectors_syscalls_frequency_5_Cat.csv',
    'feature_vectors_static.csv',
    'feature_vectors_syscallsbinders_frequency_5_Cat.csv'
]

# Đọc và merge các file CSV theo cột chung (giả sử cùng thứ tự mẫu APK)
def merge_features(csv_files, output_file='training_data_merged.csv', chunksize=1000):
    # Chỉ merge 2 file đầu để giảm tải bộ nhớ
    file1, file2 = csv_files[0], csv_files[1]
    if not (os.path.exists(file1) and os.path.exists(file2)):
        print('Không tìm thấy file đặc trưng!')
        return
    reader1 = pd.read_csv(file1, low_memory=False, chunksize=chunksize, on_bad_lines='skip')
    reader2 = pd.read_csv(file2, low_memory=False, chunksize=chunksize, on_bad_lines='skip')
    with open(output_file, 'w', encoding='utf-8') as out_f:
        header_written = False
        for chunk1, chunk2 in zip(reader1, reader2):
            # Chỉ loại bỏ cột 'Class' ở chunk1 (file đầu), giữ nguyên ở chunk2 (file cuối)
            if 'Class' in chunk1.columns:
                chunk1 = chunk1.drop(columns=['Class'])
            merged = pd.concat([chunk1, chunk2], axis=1)
            if not header_written:
                merged.to_csv(out_f, index=False, header=True)
                header_written = True
            else:
                merged.to_csv(out_f, index=False, header=False)
    print(f'Đã lưu file đặc trưng tổng hợp: {output_file}')

if __name__ == '__main__':
    merge_features(csv_files)
