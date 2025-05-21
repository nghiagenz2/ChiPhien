# APK Malware Analyzer (Phân tích mã độc APK)

## Mục đích
Hệ thống cho phép người dùng kiểm tra file APK Android có chứa mã độc hay không bằng cách:
- Trích xuất đặc trưng (system call) từ APK
- Dự đoán bằng mô hình máy học (Random Forest)

---

## Cấu trúc thư mục
```
Project_ultimate/
├── index.html                # Giao diện web frontend
├── services.js               # Xử lý upload và giao tiếp backend (nếu có)
├── train_model.py            # Script huấn luyện model Random Forest
├── random_forest_model.py    # Định nghĩa class/model Random Forest
├── ml_processor.py           # Xử lý dự đoán ML từ feature
├── collect_training_data.py  # Script thu thập/trích xuất feature từ APK
├── training_data.csv         # Dữ liệu huấn luyện (feature + nhãn)
├── random_forest_model.joblib# Model đã huấn luyện
├── feature_importance.png    # Biểu đồ tầm quan trọng feature
├── confusion_matrix.png      # Ma trận nhầm lẫn
├── requirements.txt          # Thư viện Python cần thiết
├── uploads/                  # (Tạm) Lưu file APK upload
├── apk_samples/              # (Tùy chọn) Lưu các file APK mẫu
├── node_modules/, package*.json # (Nếu có dùng Node.js cho frontend/backend)
└── README.md                 # File hướng dẫn này
```

---

## Quy trình tổng quát
1. **Thu thập dữ liệu APK**: Tải file APK benign (sạch) và malicious (mã độc) từ các nguồn uy tín.
2. **Trích xuất feature**: Sử dụng `collect_training_data.py` để tạo file `training_data.csv` (mỗi dòng là 1 APK, mỗi cột là 1 system call, cột cuối là nhãn `Class`).
3. **Tiền xử lý/gộp nhãn**: Khi train, nhãn sẽ tự động gộp: `Class == 1` là benign, còn lại là malicious (0).
4. **Huấn luyện model**: Chạy `python train_model.py` để train model Random Forest, lưu model vào file `.joblib`.
5. **Sử dụng giao diện web**: Mở `index.html` (hoặc chạy server nếu có) để upload file APK, hệ thống sẽ trích xuất feature, dự đoán và hiển thị kết quả.

---

## Hướng dẫn cài đặt & sử dụng
### 1. Cài đặt môi trường Python
- Cài Python >= 3.8
- Cài các thư viện cần thiết:
  ```
  pip install -r requirements.txt
  ```

### 2. (Tùy chọn) Cài Node.js nếu dùng backend JS
- Cài Node.js >= 16
- Cài dependencies:
  ```
  npm install
  ```

### 3. Huấn luyện model máy học
- Đảm bảo đã có file `training_data.csv` đúng format (feature + nhãn `Class`)
- Chạy lệnh:
  ```
  python train_model.py
  ```
- Model sẽ được lưu vào `random_forest_model.joblib`

### 4. Sử dụng giao diện web
- Mở `index.html` trên trình duyệt (hoặc chạy server nếu có backend JS)
- Upload file APK cần kiểm tra
- Xem kết quả dự đoán: Benign (lành tính) hoặc Malicious (mã độc)

---

## Giải thích các file/thư mục chính
- **index.html**: Giao diện web cho phép upload và xem kết quả
- **train_model.py**: Huấn luyện model Random Forest từ file CSV
- **random_forest_model.py**: Định nghĩa class/model Random Forest
- **ml_processor.py**: Xử lý dự đoán ML từ feature
- **collect_training_data.py**: Thu thập/trích xuất feature từ APK
- **training_data.csv**: Dữ liệu huấn luyện (feature + nhãn)
- **random_forest_model.joblib**: Model đã huấn luyện
- **feature_importance.png/confusion_matrix.png**: Biểu đồ đánh giá model
- **uploads/**: Thư mục tạm lưu file APK upload
- **apk_samples/**: (Tùy chọn) Lưu các file APK mẫu

---

## Lưu ý
- Dữ liệu mã độc nên đa dạng, cân bằng với benign để model dự đoán tốt.
- Nếu model dự đoán lệch về benign, hãy bổ sung thêm dữ liệu mã độc hoặc dùng `class_weight='balanced'` khi train.
- Không commit file `.pyc`, `__pycache__/`, hoặc file tạm không cần thiết.

---

**Tác giả:** Bạn
**Ngày cập nhật:** 16/05/2025
