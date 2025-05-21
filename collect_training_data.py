import os
import pandas as pd
from tqdm import tqdm

def extract_features_from_apk(apk_path):
    # TODO: Thay thế bằng logic trích xuất đặc trưng thực tế từ APK
    # Ví dụ: số lượng permission, API call, ...
    # Ở đây chỉ là ví dụ placeholder
    # Trả về dict các feature
    return {f'feature_{i}': 0 for i in range(20)}

def main():
    apk_dir = 'apk_samples/'
    data = []
    for apk_file in tqdm(os.listdir(apk_dir)):
        if apk_file.endswith('.apk'):
            features = extract_features_from_apk(os.path.join(apk_dir, apk_file))
            # Thêm nhãn nếu có (ví dụ: từ tên file hoặc file label đi kèm)
            features['Class'] = 1 if 'benign' in apk_file else 0
            data.append(features)
    df = pd.DataFrame(data)
    df.to_csv('training_data.csv', index=False)

if __name__ == '__main__':
    main()