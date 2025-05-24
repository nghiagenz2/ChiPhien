import os
import logging
import joblib
import numpy as np
from androguard.core.bytecodes.apk import APK
import sys
import io

# Thiết lập encoding cho stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')
logger = logging.getLogger(__name__)

def get_all_features(apk):
    """Lấy tất cả các đặc trưng có thể có từ APK"""
    features = set()
    
    # Thêm permissions
    permissions = apk.get_permissions()
    if permissions:
        features.update(permissions)
    
    # Thêm activities
    activities = apk.get_activities()
    if activities:
        features.update(activities)
    
    # Thêm receivers
    receivers = apk.get_receivers()
    if receivers:
        features.update(receivers)
    
    # Thêm services
    services = apk.get_services()
    if services:
        features.update(services)
    
    # Thêm providers
    providers = apk.get_providers()
    if providers:
        features.update(providers)
    
    # Thêm intent filters
    for act in activities:
        for intent in apk.get_intent_filters('activity', act):
            features.add(intent)
    
    return features

def extract_features_from_apk(apk_path, feature_names):
    """Trích xuất đặc trưng từ file APK, đảm bảo đủ số lượng features như feature_names.txt"""
    try:
        apk = APK(apk_path)
        
        # Lấy thông tin tĩnh từ APK
        permissions = set(apk.get_permissions())
        activities = set(apk.get_activities())
        receivers = set(apk.get_receivers())
        services = set(apk.get_services())
        providers = set(apk.get_providers())
        intent_filters = set()
        for act in activities:
            for intent in apk.get_intent_filters('activity', act):
                intent_filters.add(intent)
        
        # Tập hợp tất cả đặc trưng tĩnh có thể lấy được
        static_features = permissions | activities | receivers | services | providers | intent_filters
        
        # Tạo vector đặc trưng đúng thứ tự feature_names.txt
        features = np.zeros(len(feature_names), dtype=np.float32)
        for i, feat in enumerate(feature_names):
            # Nếu là đặc trưng tĩnh và có trong APK thì gán 1, còn lại (đặc trưng động) luôn để 0
            if feat in static_features:
                features[i] = 1
            # Nếu là đặc trưng động (syscalls, syscallsbinder) thì luôn để 0 vì không trích xuất được từ APK
            # (Có thể bổ sung logic nếu sau này trích xuất được)
        return features.reshape(1, -1)
    except Exception as e:
        logger.error(f"Lỗi khi phân tích APK: {str(e)}")
        return None

def analyze_apk(apk_path):
    """Phân tích APK và trả về kết quả"""
    try:
        # Kiểm tra xem mô hình đã được huấn luyện chưa
        if not os.path.exists('random_forest_model.joblib'):
            logger.error("Không tìm thấy mô hình đã huấn luyện!")
            return None

        # Tải mô hình và các thành phần tiền xử lý
        model = joblib.load('random_forest_model.joblib')
        scaler = joblib.load('scaler.joblib')
        imputer = joblib.load('imputer.joblib')
        
        # Tải danh sách feature names
        with open('feature_names.txt', 'r', encoding='utf-8') as f:
            feature_names = [line.strip() for line in f if line.strip() != ""]
        
        # Trích xuất đặc trưng
        features = extract_features_from_apk(apk_path, feature_names)
        if features is None:
            return None
        
        # Tự động cắt hoặc padding feature cho khớp với model
        model_feature_count = imputer.statistics_.shape[0]
        current_feature_count = features.shape[1]
        if current_feature_count < model_feature_count:
            # Padding thêm 0 ở cuối
            pad_width = model_feature_count - current_feature_count
            features = np.pad(features, ((0,0),(0,pad_width)), 'constant')
            logger.warning(f"Tự động padding {pad_width} feature 0 cho khớp với model.")
        elif current_feature_count > model_feature_count:
            # Cắt bớt feature ở cuối
            features = features[:, :model_feature_count]
            logger.warning(f"Tự động cắt bớt {current_feature_count - model_feature_count} feature ở cuối cho khớp với model.")
        
        # Tiền xử lý đặc trưng
        features_imputed = imputer.transform(features)
        features_scaled = scaler.transform(features_imputed)
        
        # Dự đoán
        prediction = model.predict(features_scaled)[0]
        probability = model.predict_proba(features_scaled)[0]
        
        # Ánh xạ số lớp sang nhãn
        class_mapping = {
            1: 'Adware',
            2: 'Banking',
            3: 'SMS_MALWARE',
            4: 'Riskware',
            5: 'Lành Tính'
        }
        
        result = {
            'prediction': class_mapping.get(prediction, 'Không Xác Định'),
            'confidence': float(max(probability)),
            'probabilities': {
                class_mapping.get(i, f'Lớp_{i}'): float(prob)
                for i, prob in enumerate(probability, 1)
            }
        }
        
        return result
    except Exception as e:
        logger.error(f"Lỗi trong quá trình dự đoán: {str(e)}")
        return None

def analyze_uploaded_apk():
    """Phân tích APK từ thư mục uploads"""
    try:
        # Kiểm tra thư mục uploads
        uploads_dir = 'uploads'
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            logger.info(f"Đã tạo thư mục {uploads_dir}")
            return None

        # Tìm file APK trong thư mục uploads
        apk_files = [f for f in os.listdir(uploads_dir) if f.lower().endswith('.apk')]
        if not apk_files:
            logger.info("Không tìm thấy file APK trong thư mục uploads")
            return None

        # Lấy file APK mới nhất
        latest_apk = max(apk_files, key=lambda x: os.path.getctime(os.path.join(uploads_dir, x)))
        apk_path = os.path.join(uploads_dir, latest_apk)
        
        logger.info(f"Đang phân tích file: {latest_apk}")
        result = analyze_apk(apk_path)
        
        # Xóa file APK sau khi phân tích
        try:
            os.remove(apk_path)
            logger.info(f"Đã xóa file {latest_apk}")
        except Exception as e:
            logger.error(f"Lỗi khi xóa file: {str(e)}")
        
        return result
    except Exception as e:
        logger.error(f"Lỗi khi phân tích APK: {str(e)}")
        return None

if __name__ == '__main__':
    # Phân tích APK từ thư mục uploads
    result = analyze_uploaded_apk()
    
    if result:
        print("\nKết Quả Phân Tích:")
        print(f"Phân Loại: {result['prediction']}")
        print(f"Độ Tin Cậy: {result['confidence']:.2%}")
        print("\nXác Suất Các Lớp:")
        for class_name, prob in result['probabilities'].items():
            print(f"{class_name}: {prob:.2%}")
    else:
        print("Không tìm thấy file APK để phân tích") 