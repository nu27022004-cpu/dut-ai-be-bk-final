# Bé BK — DUT AI Student Assistant (Bản Final)

Trợ lý ảo thông minh dành cho sinh viên **Trường Đại học Bách khoa — Đại học Đà Nẵng (DUT)** xây dựng theo kiến trúc **Hybrid AI** (Machine Learning NLP + Giải mã phòng học E1/E2 + FSM hội thoại nhiều lượt + Tìm đường ngắn nhất A* trên bản đồ khuôn viên).

## Hướng dẫn chạy nhanh
- **Windows**: Giải nén và nháy đúp `run_windows.bat`, sau đó mở `http://127.0.0.1:5000`.
- **Linux / macOS**: Chạy `chmod +x run_linux.sh && ./run_linux.sh`, sau đó mở `http://127.0.0.1:5000`.
- **Kiểm thử tự động**: `python test_suite.py` (acceptance + A*), `python test_regression.py` (106 câu hỏi thực tế + bảo mật API), `python ui_smoke_test.py http://127.0.0.1:5000` (giao diện Chrome, cần Playwright). Xem `CHANGELOG.md`.

**Chạy demo / thuyết trình:** xem `HUONG_DAN_DEMO.md` (cách chạy, kịch bản 13 bước, xử lý sự cố). Bị chiếm cổng 5000 thì chạy với `PORT=5001`.

## Triển khai Render (gói free)
- `render.yaml` đã cấu hình sẵn: build `pip install -r requirements.txt && python train.py`, chạy `gunicorn app:app --workers 1 --threads 4`, health check `/healthz`, và **tự sinh `DUT_AI_SECRET`** (bắt buộc để session hội thoại không đứt).
- Gói free ngủ sau ~15 phút không có truy cập; lần đầu mở lại mất khoảng 30–60 giây. Giao diện sẽ hiện ghi chú "server đang khởi động" sau 6 giây chờ.
- Nếu tự cấu hình thay vì dùng `render.yaml`, nhớ đặt biến môi trường `DUT_AI_SECRET` (chuỗi ngẫu nhiên dài).

## Các điểm nổi bật của bản Final
1. **Splash Welcome Animation & Linh vật Bé BK**: Màn hình chào mừng sinh viên Bách khoa cùng linh vật 3D Bé BK (`static/mascot.jpg`), nền ảnh trường làm mờ tươi sáng (`static/dut_bg.jpg`), hệ màu nhấn nịnh mắt và bố cục `100dvh` không cắt khung nhập.
2. **Tìm phòng học & Chỉ đường ngắn nhất A\* (78 tuyến)**:
   - Hỗ trợ giải mã trực tiếp mã phòng **E1/E2** (`E2.101` → Tòa nhà E2, tầng 1, phòng đầu tiên), **Smart Building** (`S05.08`, `S06.08`) và các khu giảng đường **A–H** (`C301`, `B101`).
   - Tích hợp bản đồ DUT mới nhất (`static/dut_map.png`) kèm tọa độ **Bánh Mỳ cô Hạnh** và **Quán Cơm cô Lài**, vẽ tuyến A* động trực tiếp bằng SVG.
3. **Smart Flow Đời sống sinh viên & 7 Thẻ ảnh thật**:
   - **Ăn sáng**: Bánh Mỳ cô Hạnh (full topping 17k, cà phê & đồ uống 5k–20k) + nút chỉ đường 1 chạm.
   - **Cơm trưa**: Quán Cơm cô Lài (20k–30k, cơm thêm & canh thêm miễn phí) + nút chỉ đường 1 chạm.
   - **Cà phê học bài 24/7**: Zone Six (19 Phạm Như Xương, 30k–50k) và Trạm 247 Study Cafe (35k–60k, mát mẻ văn minh).
   - **In ấn & Tài liệu**: Photo Tài Nguyên và Photo Thành Công (nhiều tài liệu môn học có sẵn giá rẻ).
   - **Thể thao & Vui chơi**: Công viên Liên Chiểu (đường Nguyễn Sinh Sắc).
4. **Dữ liệu mở rộng nhiều cách hỏi đồng nghĩa**: `data/intent_dataset_final.csv` (232 mẫu cân bằng 6 lớp, đánh giá bằng 5-Fold Stratified CV cho cả tiếng Việt có dấu và không dấu).
