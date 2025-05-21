import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

def load_and_prepare_data(csv_file='training_data.csv'):
    """Đọc và chuẩn bị dữ liệu huấn luyện"""
    df = pd.read_csv(csv_file)
    # Lấy tất cả các cột trừ cột 'Class' làm feature
    X = df.drop(columns=['Class'])
    # Lấy cột 'Class' làm nhãn
    y = df['Class']
    return X, y

def train_random_forest(X, y):
    """Huấn luyện Random Forest model với class_weight='balanced' và tăng số cây"""
    # Chia dữ liệu thành tập train và test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Khởi tạo và huấn luyện model
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=15,
        min_samples_split=3,
        min_samples_leaf=1,
        class_weight='balanced',
        random_state=42
    )
    
    # Huấn luyện model
    model.fit(X_train, y_train)
    
    # Đánh giá model
    y_pred = model.predict(X_test)
    
    # In báo cáo phân loại
    print("\nBáo cáo phân loại:")
    print(classification_report(y_test, y_pred))
    
    # In ma trận nhầm lẫn
    print("\nMa trận nhầm lẫn:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    
    # Vẽ ma trận nhầm lẫn
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Ma trận nhầm lẫn')
    plt.ylabel('Nhãn thực tế')
    plt.xlabel('Nhãn dự đoán')
    plt.savefig('confusion_matrix.png')
    
    # Đánh giá cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5)
    print(f"\nĐộ chính xác cross-validation: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    
    # Tính tầm quan trọng của các features
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTầm quan trọng của các features:")
    print(feature_importance)
    
    # Vẽ biểu đồ tầm quan trọng của features
    plt.figure(figsize=(10, 6))
    sns.barplot(x='importance', y='feature', data=feature_importance)
    plt.title('Tầm quan trọng của các features')
    plt.tight_layout()
    plt.savefig('feature_importance.png')
    
    return model

def save_model(model, filename='random_forest_model.joblib'):
    """Lưu model đã huấn luyện"""
    joblib.dump(model, filename)
    print(f"\nĐã lưu model vào {filename}")

def main():
    try:
        # Đọc và chuẩn bị dữ liệu
        print("Đang đọc dữ liệu...")
        X, y = load_and_prepare_data()
        
        # Kiểm tra lại tỷ lệ nhãn `Class` trong file CSV
        print("\nTỷ lệ nhãn `Class` trong file CSV:")
        print(y.value_counts())
        
        # Huấn luyện model
        print("\nĐang huấn luyện model...")
        
        model = train_random_forest(X, y)
        
        # Lưu model
        save_model(model)
        
        print("\nHuấn luyện hoàn tất!")
        print("Các biểu đồ đã được lưu vào:")
        print("- confusion_matrix.png")
        print("- feature_importance.png")
        
    except Exception as e:
        print(f"Có lỗi xảy ra: {str(e)}")

if __name__ == "__main__":
    main()