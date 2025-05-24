import pandas as pd
import numpy as np
import os
import re
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_and_preprocess_data():
    """Tải và tiền xử lý tất cả các tập dữ liệu đặc trưng"""
    logger.info("Đang tải và tiền xử lý dữ liệu...")
    
    # Định nghĩa các mẫu đặc trưng
    patterns = {
        'F1_permissions':    r'permission',
        'F2_api_calls':      r'api_call|call_',
        'F3_intents':        r'android\.intent\.action',
        'F4_components':     r'activity|provider',
        'F5_packages':       r'package',
        'F6_services':       r'service(_|$)',
        'F7_receivers':      r'receiver'
    }
    
    # Tải đặc trưng tĩnh
    static_cols = pd.read_csv('feature_vectors_static.csv', nrows=0).columns.tolist()
    usecols = []
    for pat in patterns.values():
        usecols += [c for c in static_cols if re.search(pat, c, flags=re.IGNORECASE)]
    
    # Loại bỏ các cột trùng lặp nhưng vẫn giữ thứ tự
    seen = set()
    usecols = [c for c in usecols if not (c in seen or seen.add(c))]
    logger.info(f"Đã chọn {len(usecols)} đặc trưng tĩnh")
    
    # Tải đặc trưng tĩnh
    df_static = pd.read_csv(
        'feature_vectors_static.csv',
        usecols=usecols,
        index_col=0,
        low_memory=False
    )
    df_static = df_static.apply(pd.to_numeric, errors='coerce').astype('float32')
    
    # Tải đặc trưng động
    df_sys5 = pd.read_csv('feature_vectors_syscalls_frequency_5_Cat.csv')
    df_sys_binder = pd.read_csv('feature_vectors_syscallsbinders_frequency_5_Cat.csv')
    
    # Kết hợp các đặc trưng
    X_static = df_static.values
    X_sys5 = df_sys5.drop(columns='Class').values
    X_binder = df_sys_binder.drop(columns='Class').values
    
    X = np.hstack([X_static, X_sys5, X_binder])
    y = df_sys_binder['Class'].values
    
    logger.info(f"Kích thước ma trận đặc trưng cuối cùng: {X.shape}")
    return X, y, usecols

def train_and_evaluate_model(X, y):
    """Huấn luyện và đánh giá mô hình với cross-validation"""
    logger.info("Đang huấn luyện và đánh giá mô hình...")
    
    # Chia dữ liệu
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, stratify=y, random_state=42
    )
    
    # Xử lý giá trị thiếu
    imp = SimpleImputer(
        missing_values=np.nan,
        strategy='constant',
        fill_value=0,
        keep_empty_features=True
    )
    X_train_imputed = imp.fit_transform(X_train)
    X_test_imputed = imp.transform(X_test)
    
    # Chuẩn hóa đặc trưng
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_imputed)
    X_test_scaled = scaler.transform(X_test_imputed)
    
    # Huấn luyện mô hình
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    
    # Cross-validation
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
    logger.info(f"Điểm cross-validation: {cv_scores}")
    logger.info(f"Điểm trung bình CV: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    
    # Huấn luyện cuối cùng
    model.fit(X_train_scaled, y_train)
    
    # Đánh giá trên tập kiểm thử
    y_pred = model.predict(X_test_scaled)
    logger.info("\nBáo cáo phân loại:")
    logger.info(classification_report(y_test, y_pred))
    
    # Lưu mô hình và scaler
    joblib.dump(model, 'random_forest_model.joblib')
    joblib.dump(scaler, 'scaler.joblib')
    joblib.dump(imp, 'imputer.joblib')
    
    # Vẽ biểu đồ tầm quan trọng của đặc trưng
    plot_feature_importance(model)
    
    # Vẽ ma trận nhầm lẫn
    plot_confusion_matrix(y_test, y_pred)
    
    return model

def plot_feature_importance(model):
    """Vẽ biểu đồ tầm quan trọng của đặc trưng"""
    plt.figure(figsize=(10, 6))
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    plt.title('Tầm Quan Trọng của Đặc Trưng')
    plt.bar(range(len(importances)), importances[indices])
    plt.xticks(range(len(importances)), indices, rotation=90)
    plt.tight_layout()
    plt.savefig('feature_importance.png')
    plt.close()

def plot_confusion_matrix(y_true, y_pred):
    """Vẽ ma trận nhầm lẫn"""
    plt.figure(figsize=(8, 6))
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Ma Trận Nhầm Lẫn')
    plt.ylabel('Nhãn Thực Tế')
    plt.xlabel('Nhãn Dự Đoán')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png')
    plt.close()

if __name__ == '__main__':
    # Huấn luyện mô hình
    logger.info("Bắt đầu quá trình huấn luyện mô hình...")
    X, y, feature_names_static = load_and_preprocess_data()

    # Lấy tên các đặc trưng động
    df_sys5 = pd.read_csv('feature_vectors_syscalls_frequency_5_Cat.csv')
    df_sys_binder = pd.read_csv('feature_vectors_syscallsbinders_frequency_5_Cat.csv')
    feature_names_sys5 = df_sys5.drop(columns='Class').columns.tolist()
    feature_names_binder = df_sys_binder.drop(columns='Class').columns.tolist()
    all_feature_names = feature_names_static + feature_names_sys5 + feature_names_binder
    # Loại bỏ trùng lặp nhưng giữ thứ tự
    seen = set()
    all_feature_names = [x for x in all_feature_names if not (x in seen or seen.add(x))]
    # Loại bỏ phần tử rỗng
    all_feature_names = [name for name in all_feature_names if name.strip() != ""]
    with open('feature_names.txt', 'w', encoding='utf-8') as f:
        for name in all_feature_names:
            f.write(f"{name}\n")

    # Huấn luyện và đánh giá mô hình
    model = train_and_evaluate_model(X, y)
    logger.info("Đã hoàn thành quá trình huấn luyện mô hình!") 