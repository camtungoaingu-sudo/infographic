# Kế Hoạch Ứng Dụng Python: Phân Tích & Vector Hóa Màu Ảnh

## 🎯 Mục tiêu
Xây dựng ứng dụng desktop Python để:
- Phân tích pixel ảnh đầu vào (PNG/JPG).
- Gom nhóm màu tương đồng theo cảm nhận thị giác.
- Tách vùng theo từng màu.
- Vector hóa thành các lớp SVG/PDF khít nhau, phục vụ in DTF/Screen Printing.

## 🏗️ Kiến trúc tổng thể

### 1) GUI Layer (PySide6/PyQt6)
- **Preview Canvas**: hiển thị ảnh và layer, hỗ trợ zoom/pan.
- **Color Palette Panel**: danh sách màu, ẩn/hiện layer, merge/split màu.
- **Export/Tools Panel**: thông số pipeline, export SVG/PDF/PNG.

### 2) Core Processing Engine
- **Color Quantizer**: K-Means trong không gian LAB + Delta-E merge.
- **Region Extractor**: tạo mask và contour cho từng lớp màu.
- **Vector Generator**: dựng path SVG bằng marching squares / polygon ops.

### 3) Data Layer
- `numpy.ndarray`: biểu diễn ảnh, label map, mask.
- Định dạng xuất: SVG/PDF/PNG.

---

## 📦 Stack thư viện đề xuất
- **GUI**: `PySide6` (khuyến nghị) hoặc `PyQt6`.
- **Ảnh**: `Pillow`, `opencv-python`.
- **Gom màu**: `scikit-learn`, `scipy`, `scikit-image`.
- **Toán hình học**: `shapely`.
- **Vector**: `svgwrite` (+ tùy chọn `potrace`/`pypotrace`).
- **Export**: `cairosvg`, `reportlab`.
- **Hiệu năng số học**: `numpy`.

---

## 🔢 Giai đoạn 1: Phân tích & gom màu

### 1.1 Đọc và chuẩn hóa ảnh
1. Nạp ảnh PNG/JPG vào RGBA.
2. Chuyển RGB → LAB (loại alpha ra riêng).
3. Reshape thành mảng `(H*W, 3)`.

### 1.2 Thuật toán gom màu
1. **K-Means (LAB)** với mặc định `K=10` (UI cho phép 2–32).
2. **Merge cụm gần nhau** bằng Delta-E 2000 (`ΔE00 < threshold`).
3. **Gán lại pixel** vào tâm màu gần nhất sau merge.
4. Trả về:
   - `label_map: (H, W)`
   - `palette_lab`, `palette_rgb`

### 1.3 Độ nhạy gom màu
- Slider “Độ nhạy” ánh xạ vào ngưỡng Delta-E.
- `Low`: giữ nhiều màu (chi tiết cao).
- `High`: merge mạnh (ít màu hơn).

---

## 🗺️ Giai đoạn 2: Tách vùng & vector hóa chính xác

### 2.1 Tách vùng từ label map
Với mỗi nhãn màu `k`:
1. Tạo `mask = (label_map == k)`.
2. Làm sạch mask:
   - `remove_small_holes`
   - `remove_small_objects`
3. Trích xuất contour:
   - OpenCV `RETR_CCOMP` nếu cần giữ lỗ vùng.
   - Hoặc marching squares để nội suy biên sub-pixel.

### 2.2 Vector hóa contour
Ba chiến lược:
1. **Potrace**: mượt đường cong Bezier.
2. **Pixel-perfect rect merge**: chính xác tuyệt đối, phù hợp bản in kỹ thuật.
3. **Marching Squares + Simplify**: cân bằng chính xác/nhẹ file (khuyến nghị mặc định).

### 2.3 Đảm bảo gap-free giữa layer
- **A. Underprint Expansion**: nở lớp dưới ~0.5 px.
- **B. Shared Edge (Shapely)**: vùng kề dùng chung biên tọa độ.
- **C. Full Coverage Base**: lớp nền phủ full canvas, lớp trên cắt trừ dần.

Khuyến nghị:
- Mặc định dùng **B + fallback A** để giảm hở cạnh trong export.

---

## 🖥️ Giai đoạn 3: Thiết kế GUI

### Layout chính
- Trái: canvas preview (zoom tới 1600%).
- Phải: danh sách màu (chip/circle), toggles ẩn/hiện.
- Dưới: toolbar (open/export), slider số màu, slider độ nhạy.

### Chức năng trọng tâm
- Mở ảnh và xem toàn bộ / từng layer.
- Merge nhiều màu thành một màu.
- Split một màu dựa threshold / vùng chọn.
- Chỉnh màu đại diện bằng color picker.
- Load/save preset palette.
- Export SVG/PDF/PNG.

---

## ⚙️ Giai đoạn 4: Pipeline chuẩn hóa chất lượng

```python
# pseudocode
img = load_image_rgba(path)
label_map, palette = color_quantize(img, k=10, sensitivity=0.5)

layers = []
for k in labels(label_map):
    mask = clean_mask(label_map == k, min_area=4)
    contours = marching_squares(mask)
    paths = simplify(contours, epsilon=0.3)
    layers.append(build_svg_layer(paths, palette[k]))

validate_coverage(layers, image_size=img.shape[:2])
export_svg(layers, strategy="shared_edge")
```

### Validation bắt buộc
- Union tất cả layer == toàn bộ canvas ảnh.
- Không tồn tại vùng trống giữa hai vùng kề nhau.
- Không self-intersection trong path sau simplify.

---

## 📁 Cấu trúc thư mục đề xuất

```text
pixel_to_vector/
├── main.py
├── requirements.txt
├── core/
│   ├── color_quantizer.py
│   ├── region_extractor.py
│   ├── vector_builder.py
│   ├── gap_filler.py
│   └── exporter.py
├── gui/
│   ├── main_window.py
│   ├── canvas_widget.py
│   ├── palette_panel.py
│   ├── toolbar.py
│   └── color_editor.py
├── utils/
│   ├── image_utils.py
│   └── math_utils.py
└── assets/
    └── presets/
```

---

## 🗓️ Roadmap triển khai (ước lượng ~15 ngày)
1. **Phase 1 (3–4 ngày)**: load ảnh, quantize LAB, sinh `label_map`.
2. **Phase 2 (3–4 ngày)**: contour + vector path + export SVG cơ bản.
3. **Phase 3 (2–3 ngày)**: shared-edge/underprint chống hở.
4. **Phase 4 (4–5 ngày)**: GUI đầy đủ + async xử lý nền.
5. **Phase 5 (2–3 ngày)**: tối ưu hiệu năng, preset, undo/redo, QA.

---

## ✅ Tiêu chí nghiệm thu
- Ảnh bất kỳ gom được ≤10 màu (mặc định) và tùy chỉnh 2–32 màu.
- Slider thay đổi realtime không lag (dùng worker thread).
- SVG xuất ra phủ 100% diện tích ảnh (không gap).
- Preview zoom/pan mượt ở mức 1600%.
- Export theo từng layer màu cho quy trình in.

## Gợi ý kỹ thuật quan trọng
- Dùng `QThreadPool`/`QRunnable` để tránh block UI khi quantize.
- Cache `label_map` trung gian để giảm thời gian khi đổi hiển thị layer.
- Chỉ simplify contour ở mức nhỏ để tránh sai hình học.
- Lưu metadata layer (tên, mã màu, visible) trong JSON cạnh file SVG.
