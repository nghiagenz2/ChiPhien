import sys
import json
import numpy as np
from random_forest_model import RandomForestModel

def extract_features_from_apk(apk_path):
    # Trả về đúng 139 feature (giả lập, tất cả bằng 0)
    return np.zeros((1, 139))

def main():
    apk_path = sys.argv[1]
    model = RandomForestModel()
    try:
        model.load_model()
        # Fit lại scaler nếu số lượng feature thay đổi
        model.fit_scaler(features)
    except:
        # Nếu chưa có model, tạo model mẫu
        X_sample = np.zeros((3, 139))
        y_sample = np.array([1, 0, 1])
        model.train(X_sample, y_sample)
        model.save_model()
    features = extract_features_from_apk(apk_path)
    prediction = model.predict(features)
    result = {
        'ml_verdict': 'Malicious' if prediction[0] == 1 else 'Benign',
        'ml_confidence': float(model.model.predict_proba(features)[0][1])
    }
    print(json.dumps(result))

if __name__ == '__main__':
    main()