# Pixel to Vector (Desktop App)

## Chạy ứng dụng

```bash
cd pixel_to_vector
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Tính năng hiện có
- Mở ảnh PNG/JPG/WebP.
- Chọn số màu K (2-32).
- Quantize ảnh bằng K-Means trên LAB.
- Trích contour và xuất SVG theo layer màu.

## Dùng thử trên Windows

### Cách 1 (nhanh nhất)
1. Clone/tải repository về máy.
2. Mở thư mục `pixel_to_vector`.
3. Double-click file `run_windows.bat`.

Script sẽ tự:
- tạo môi trường ảo `.venv`
- cài dependencies
- chạy app

### Cách 2 (chạy bằng Terminal)
Mở **PowerShell** trong thư mục `pixel_to_vector` rồi chạy:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

> Nếu PowerShell báo lỗi execution policy, chạy tạm lệnh sau rồi thử lại:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
