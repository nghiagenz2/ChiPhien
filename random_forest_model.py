import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

class RandomForestModel:
    def __init__(self, n_estimators=100, random_state=42):
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=random_state
        )
        self.scaler = StandardScaler()
        
    def preprocess_data(self, X):
        """Tiền xử lý dữ liệu"""
        return self.scaler.fit_transform(X)
    
    def train(self, X, y):
        """Huấn luyện model"""
        X_scaled = self.preprocess_data(X)
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        return self.model.score(X_test, y_test)
    
    def predict(self, X):
        """Dự đoán kết quả"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def save_model(self, model_path='random_forest_model.joblib'):
        """Lưu cả model và scaler"""
        joblib.dump({'model': self.model, 'scaler': self.scaler}, model_path)
    
    def load_model(self, model_path='random_forest_model.joblib'):
        """Tải cả model và scaler"""
        data = joblib.load(model_path)
        self.model = data['model']
        self.scaler = data['scaler']

    def fit_scaler(self, X):
        """Fit lại scaler với dữ liệu mới nếu cần thiết"""
        self.scaler.fit(X)