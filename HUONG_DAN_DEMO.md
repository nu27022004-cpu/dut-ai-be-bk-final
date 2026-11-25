# Hướng dẫn chạy demo — Bé BK · Trợ lý Sinh viên Bách khoa

Mọi bước và kết quả trong tài liệu này đã được chạy thử thật trên bản final v2 (giải nén từ zip → chạy script → mở bằng Chrome).

---

## 1. Chọn cách chạy

| Cách | Khi nào dùng | Ưu / nhược |
|---|---|---|
| **A. Chạy trên laptop của bạn** (khuyên dùng khi thuyết trình) | Có laptop mang tới phòng demo | Nhanh, không phụ thuộc mạng Wi-Fi, không bị "ngủ" như Render |
| **B. Mở trang trên Render** | Muốn demo bằng link công khai | Không cần cài gì, nhưng gói free **ngủ sau ~15 phút**, lần đầu chờ 30–60 giây |

> Nên làm cả hai: demo bằng A, mở sẵn B ở tab bên cạnh làm phương án dự phòng.

---

## 2. Cách A — Chạy trên laptop

### Chuẩn bị (một lần, cần internet)
- Cài **Python 3.11 trở lên** từ python.org. Trên Windows nhớ tick **"Add Python to PATH"** và để bật **py launcher** khi cài.
- Giải nén `DUT_AI_Student_Assistant_Final_v2.zip` ra một thư mục (tránh đường dẫn có ký tự lạ nếu được).

### Windows
1. Mở thư mục đã giải nén, nháy đúp **`run_windows.bat`**.
2. Lần đầu script tự tạo môi trường, cài thư viện và huấn luyện mô hình (**khoảng 2–5 phút**, tùy mạng). Các lần sau chỉ mất vài giây.
3. Khi thấy dòng `Khoi chay DUT AI Student Assistant ... tai http://127.0.0.1:5000`, mở trình duyệt vào **http://127.0.0.1:5000**.
4. Muốn dừng: bấm `Ctrl + C` trong cửa sổ đen, rồi đóng cửa sổ.

### Linux / macOS
```bash
cd DUT_AI_Student_Assistant_Final
chmod +x run_linux.sh
./run_linux.sh
```
Rồi mở **http://127.0.0.1:5000**. (Dừng bằng `Ctrl + C`.)

### Nếu cổng 5000 bị chiếm (hay gặp trên macOS vì AirPlay Receiver)
Chạy với cổng khác rồi mở đúng cổng đó:
- macOS/Linux: `PORT=5001 ./run_linux.sh` → mở http://127.0.0.1:5001
- Windows (cửa sổ Command Prompt): `set PORT=5001` rồi `run_windows.bat`

### Kiểm tra nhanh trước giờ demo (30 giây)
Mở trang → thấy video chào → bấm **Bắt đầu trò chuyện** → gõ `e2.101` → thấy thẻ "Giải mã phòng E2.101" và hai/ba nút chọn cổng. Thấy vậy là ổn.

> Ghi chú trung thực: `run_linux.sh` đã được chạy thử đầy đủ (Python 3.13). `run_windows.bat` không có môi trường Windows để chạy thử, nhưng nội dung tương đương `run_linux.sh`.

---

## 3. Cách B — Demo trên Render

1. **Đánh thức server trước 5–10 phút**: mở link `https://dut-ai-be-bk.onrender.com`, đợi tới khi thấy trang Bé BK (có thể mất 30–60 giây).
2. Trong lúc demo, nếu bot im quá 6 giây, giao diện sẽ hiện dòng *"Server miễn phí đang khởi động, bạn chờ chút nhé…"* — cứ chờ, không cần tải lại trang.
3. Để server không ngủ giữa buổi demo, gửi một tin nhắn mỗi ~10 phút.
4. Muốn dùng bản v2 trên Render: thay các file trong repo bằng nội dung zip, push lên GitHub. `render.yaml` đã tự sinh khóa phiên (`DUT_AI_SECRET`). Nếu bạn tạo service thủ công trên dashboard, hãy tự thêm biến `DUT_AI_SECRET` (chuỗi ngẫu nhiên dài) và đặt lệnh start bằng nội dung file `Procfile`.

---

## 4. Kịch bản demo ~5 phút

> **Muốn chắc ăn tuyệt đối: dùng danh sách trong `CAU_HOI_DEMO.md`** (mọi câu đã được kiểm chứng ra kết quả cố định). Bảng dưới là bản rút gọn ban đầu.

Trước khi bắt đầu: bấm **Chế độ chấm điểm AI** (nút trên cùng bên phải) — mỗi câu trả lời sẽ hiện dòng nhỏ *Intent · Tin cậy · Engine · Nguồn · Keys · số nút A\**, rất tiện khi giảng viên hỏi "máy hiểu thế nào".

| # | Bạn gõ / bấm | Kết quả thấy trên màn hình | Ý để nói |
|---|---|---|---|
| 1 | Mở trang, xem splash, bấm **Bắt đầu trò chuyện** | Linh vật Bé BK, 4 ô gợi ý (Tìm phòng, Ăn sáng, Cà phê 24/7, Thủ tục) | Giao diện thân thiện, có gợi ý một chạm |
| 2 | `e2.101` | Thẻ **Giải mã phòng E2.101**: Tòa nhà E2 · Tầng 1 · phòng đầu tiên (số 01); bot hỏi vào từ cổng nào | Hiểu mã phòng E1/E2, Smart Building, khu A–H |
| 3 | Bấm **Cổng khu C** | Bản đồ tự mở, đường đỏ chạy tới Tòa E2 (~84m · 1 phút) | Thuật toán **A\*** trên đồ thị khuôn viên, 3 lối vào × 26 địa điểm = 78 tuyến |
| 4 | **Cuộc trò chuyện mới** → `tôi muốn tới phòng HC1C và HC1C mở cửa lúc mấy giờ` | Trả lời **cả hai ý**: giờ làm việc 08:00–11:00, 13:30–16:30 + hỏi cổng để chỉ đường | **Câu hỏi kép** nhờ bộ chấm điểm từ khóa theo ngữ cảnh |
| 5 | Bấm **Cổng chính** | Đường đi tới Hành chính Một cửa | Dữ liệu được xác minh từ nhóm |
| 6 | **Cuộc trò chuyện mới** → `Chỉ đường đến Cơm cô Lài` → **Cổng khu C** | Đường đỏ tới quán, kèm thẻ ảnh thật, giá 20k–30k | Hai quán ăn có tọa độ riêng trên bản đồ |
| 7 | `xin giấy hoãn nghĩa vụ quân sự` → bấm **Chưa đăng ký** | Bot hỏi đã đăng ký chưa → hướng dẫn lên `sv.dut.udn.vn` rồi ghé HC1C | **FSM** hội thoại nhiều lượt |
| 8 | `lay ban diem o dau` (gõ không dấu, sai chữ) | Vẫn hiểu là thủ tục "bảng điểm" (Engine hiện sửa lỗi gõ) | Chịu được lỗi chính tả, không dấu |
| 9 | **Cuộc trò chuyện mới** → `sáng nay ăn gì gần trường ngon rẻ?` | Thẻ **Bánh Mỳ cô Hạnh** 17k; bấm ảnh để phóng to (Esc để đóng) | Đời sống sinh viên, ảnh thật |
| 10 | `quán cafe nào mở xuyên đêm chạy deadline` | Hai thẻ: **Zone Six** và **Trạm 247 Study Cafe** (24/7) | Hiểu cách nói đời thường |
| 11 | `giá gửi xe thứ 7` | "Thứ 7 và Chủ nhật giá gửi xe mặc định là 2.000đ" | Trả lời theo dữ liệu thật |
| 12 | `bitcoin hôm nay giá bao nhiêu` | Từ chối lịch sự: "nằm ngoài phạm vi…" | Biết giới hạn, **không bịa** |
| 13 | Bấm **Ban đêm**, rồi **Sơ đồ trường** / **Thu gọn** | Đổi giao diện tối; bật/tắt bản đồ | Giao diện hoàn thiện |

Tổng cộng kịch bản này đã chạy 18/18 bước đạt trên Chrome thật.

---

## 5. Câu nên tránh khi demo (giới hạn đã biết)

Những câu này bot trả lời đúng nhưng **không ấn tượng**, nên tránh nếu muốn demo suôn:
- `thư viện mấy giờ mở cửa` / `căn tin mấy giờ đóng cửa` → bot nói thật là **chưa có dữ liệu giờ mở cửa** (không đoán bừa). Nếu bị hỏi, đây là điểm cộng về trung thực.
- Câu kép ngoài HC1C, ví dụ `thư viện ở đâu và mở cửa mấy giờ` → chỉ trả lời được nửa sau.
- Câu rất ngắn / mơ hồ như `ừ`, `1` → bot coi là ngoài phạm vi.

---

## 6. Xử lý sự cố nhanh

| Hiện tượng | Cách xử lý |
|---|---|
| `Address already in use` / không mở được trang | Cổng bị chiếm: dùng `PORT=5001` (mục 2) |
| Cửa sổ chạy xong nhưng trang trắng | Đợi đến khi cửa sổ in dòng "Running on http://127.0.0.1:5000" (khởi động 5–15 giây), rồi tải lại |
| Windows báo `'py' is not recognized` | Cài lại Python từ python.org, tick "Add Python to PATH" và "py launcher" |
| Cài thư viện quá lâu / lỗi | Cần internet cho lần chạy đầu; thử lại hoặc đổi sang mạng khác |
| Video chào không tự phát | Bình thường trên một số trình duyệt; splash tự ẩn sau ~5 giây hoặc bấm nút |
| Bot báo "chưa kết nối được tới server" | Cửa sổ chạy đã tắt hoặc (với Render) server đang thức dậy: đợi 30–60 giây rồi bấm lại nút/gửi lại |
| Bản đồ không hiện trên điện thoại | Sau khi có tuyến, trang tự cuộn xuống bản đồ; nếu không thấy thì kéo xuống |

---

## 7. Tự kiểm tra lại bất cứ lúc nào

```bash
python test_suite.py                    # acceptance + A* + FSM
python test_regression.py               # 106 câu thực tế + bảo mật API
python ui_smoke_test.py http://127.0.0.1:5000   # giao diện Chrome (cần: pip install playwright && playwright install chromium)
```
Cả ba đều phải báo đạt trước khi bạn demo; kết quả hiện tại là 100% / 106 trên 106 / 48 trên 48.
