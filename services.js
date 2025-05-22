require('dotenv').config();
const express = require('express');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const PORT = process.env.PORT || 3000;

// Đảm bảo thư mục uploads tồn tại
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
}

const app = express();
app.use(cors());

// Phục vụ file tĩnh (index.html) ở thư mục gốc
app.use(express.static(__dirname));

const storage = multer.diskStorage({
  destination: uploadsDir,
  filename: (req, file, cb) => cb(null, Date.now() + path.extname(file.originalname)),
});
const upload = multer({ storage });

// Chỉ dùng ML, không còn code liên quan đến VirusTotal
async function analyzeWithML(apkPath) {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn('python', ['ml_processor.py', apkPath]);
    
    let result = '';
    let error = '';

    pythonProcess.stdout.on('data', (data) => {
      result += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      error += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Python process exited with code ${code}: ${error}`));
        return;
      }
      try {
        const mlResult = JSON.parse(result);
        resolve(mlResult);
      } catch (err) {
        reject(new Error('Failed to parse Python output: ' + err.message));
      }
    });
  });
}

app.post('/analyze', upload.single('apkFile'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ status: 'error', message: 'Chưa upload file.' });
  }
  try {
    const mlResult = await analyzeWithML(req.file.path);
    
    // Xoá file sau khi phân tích xong
    fs.unlink(req.file.path, () => {});
    res.json({ status: 'ok', data: mlResult });
  } catch (err) {
    // Xoá file nếu có lỗi
    if (req.file && req.file.path) fs.unlink(req.file.path, () => {});
    console.error(err.message);
    res.status(500).json({ status: 'error', message: err.message });
  }
});

// Trang chủ: chuyển hướng về index.html nếu truy cập /
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Bắt tất cả các route GET khác trả về index.html (SPA fallback, tránh Cannot GET /abc)
app.get(/.*/, (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
});
