require('dotenv').config();
const express = require('express');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const PORT = process.env.PORT || 3000;

// Đảm bảo thư mục uploads và logs tồn tại
const uploadsDir = path.join(__dirname, 'uploads');
const logsDir = path.join(__dirname, 'logs');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
}
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir);
}

const app = express();
app.use(cors());
app.use(express.json());

// Phục vụ file tĩnh (index.html) ở thư mục gốc
app.use(express.static(__dirname));

const storage = multer.diskStorage({
  destination: uploadsDir,
  filename: (req, file, cb) => {
    const timestamp = Date.now();
    cb(null, `${timestamp}${path.extname(file.originalname)}`);
  },
});
const upload = multer({ storage });

// Phân tích APK bằng model đã huấn luyện
async function analyzeWithML(apkPath) {
  return new Promise((resolve, reject) => {
    const timestamp = Date.now();
    const logFile = path.join(logsDir, `analysis_${timestamp}.log`);
    
    // Tạo file log
    fs.writeFileSync(logFile, `=== Bắt đầu phân tích APK: ${path.basename(apkPath)} ===\n`);
    
    const pythonProcess = spawn('python', ['train_and_predict.py']);
    
    let result = '';
    let error = '';

    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      result += output;
      fs.appendFileSync(logFile, output);
      process.stdout.write(output);
    });

    pythonProcess.stderr.on('data', (data) => {
      const errorOutput = data.toString();
      error += errorOutput;
      fs.appendFileSync(logFile, `ERROR: ${errorOutput}`);
      process.stderr.write(errorOutput);
    });

    pythonProcess.on('close', (code) => {
      // Ghi kết thúc log
      fs.appendFileSync(logFile, `\n=== Kết thúc phân tích (code: ${code}) ===\n`);
      
      if (code !== 0) {
        reject(new Error(`Python process exited with code ${code}: ${error}`));
        return;
      }

      try {
        // Kiểm tra nếu không có kết quả
        if (result.includes("Không tìm thấy file APK để phân tích")) {
          resolve({
            error: "Không tìm thấy file APK để phân tích",
            logFile: logFile
          });
          return;
        }

        // Parse kết quả từ output của Python
        const lines = result.trim().split('\n');
        const prediction = lines.find(line => line.startsWith('Phân Loại:'))?.split(': ')[1];
        const confidence = lines.find(line => line.startsWith('Độ Tin Cậy:'))?.split(': ')[1];
        
        // Parse xác suất các lớp
        const probabilities = {};
        let inProbabilities = false;
        for (const line of lines) {
          if (line.startsWith('Xác Suất Các Lớp:')) {
            inProbabilities = true;
            continue;
          }
          if (inProbabilities && line.includes(':')) {
            const [class_name, prob] = line.split(': ');
            probabilities[class_name] = parseFloat(prob.replace('%', '')) / 100;
          }
        }

        if (!prediction || !confidence) {
          throw new Error('Không thể parse kết quả từ Python');
        }

        resolve({
          prediction,
          confidence: parseFloat(confidence.replace('%', '')) / 100,
          probabilities,
          logFile: logFile
        });
      } catch (err) {
        reject(new Error('Failed to parse Python output: ' + err.message));
      }
    });
  });
}

// API endpoint để xem log
app.get('/logs', (req, res) => {
  try {
    const logs = fs.readdirSync(logsDir)
      .filter(file => file.endsWith('.log'))
      .map(file => {
        const stats = fs.statSync(path.join(logsDir, file));
        return {
          filename: file,
          timestamp: stats.mtime,
          size: stats.size
        };
      })
      .sort((a, b) => b.timestamp - a.timestamp);
    
    res.json({ status: 'ok', logs });
  } catch (err) {
    res.status(500).json({ status: 'error', message: err.message });
  }
});

// API endpoint để xem nội dung log
app.get('/logs/:filename', (req, res) => {
  try {
    const logPath = path.join(logsDir, req.params.filename);
    if (!fs.existsSync(logPath)) {
      return res.status(404).json({ status: 'error', message: 'Log file not found' });
    }
    
    const content = fs.readFileSync(logPath, 'utf-8');
    res.json({ status: 'ok', content });
  } catch (err) {
    res.status(500).json({ status: 'error', message: err.message });
  }
});

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

// Bắt tất cả các route GET khác trả về index.html (SPA fallback)
app.get(/.*/, (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
});
