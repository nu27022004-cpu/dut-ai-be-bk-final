# CHANGELOG — Bản Final v2 (đã QA toàn diện)

Bản này gộp toàn bộ các sửa lỗi sau đợt kiểm thử cực đoan (backend, giao diện Chrome thật, tải đồng thời, bảo mật).
Mọi hạng mục dưới đây đều đã được kiểm chứng lại bằng `test_suite.py`, `test_regression.py` và `ui_smoke_test.py`.

## Chạy kiểm thử
| Lệnh | Nội dung | Kết quả bản này |
|---|---|---|
| `python test_suite.py` | 30 acceptance test, 12 kịch bản QA, 78 tuyến A*, FSM | 100% đạt |
| `python test_regression.py` | 106 câu hỏi thực tế, bẫy khớp chuỗi con, FSM, API/bảo mật | 100% đạt |
| `python ui_smoke_test.py http://127.0.0.1:5000` | 48 kiểm tra giao diện trên Chrome thật (cần `pip install playwright && playwright install chromium`) | 48/48 đạt |

## Backend
- **Mất session giữa 2 worker (lỗi nặng nhất):** `render.yaml` giờ tự sinh `DUT_AI_SECRET`; trước đây mỗi worker có khóa riêng nên hội thoại nhiều lượt đứt ngẫu nhiên (~20–35% lượt).
- **Khớp chuỗi con nhận nhầm địa điểm:** "nhà hàng…" → Tòa H, "nhà em…" → Khu E, "khu ăn uống" → Tòa A… Nay khớp nguyên cụm từ (`_has_term`).
- **Luồng "đã đăng ký chưa?" nuốt câu hỏi khác:** "cô lài bán gì", "thư viện có mở cửa không", "chuẩn bị giấy tờ gì" không còn bị coi là trả lời có/chưa. Chỉ nhận câu trả lời gồm các từ trả lời (`REGISTERED_ANSWER_WORDS`).
- **Sửa lỗi gõ (fuzzy):** "học pji" → "học phí" chạy đúng như tài liệu (ngưỡng 0.85 + điều kiện từng từ ≥ 0.6, tránh "cho tân sinh viên" → "công tác sinh viên"); thêm "hc 1c", "zone six", "smart building", "study cafe".
- **Nhận diện intent:** "căn tin mấy giờ đóng cửa", "thư viện có mở cửa không", "cf chạy dl", "ddut/tkb/lịch thi", "miễn giảm học phí", "chuyển ngành", "điểm chuẩn / tuyển sinh" (ngoài phạm vi).
- **Đang chờ chọn cổng mà hỏi chuyện ngoài phạm vi rõ ràng** (vd bitcoin) → thoát chờ thay vì hỏi lại cổng.
- **Payload lạ:** JSON dạng mảng, `message` là dict/số không còn gây lỗi trong log.
- **Bảo mật:** giới hạn body 16KB (trả 413; trước đây nhận cả 200MB làm RAM mỗi worker tăng gấp đôi), header `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Cache-Control: no-store` cho API, cookie `HttpOnly` + `SameSite=Lax` + `Secure` (tự bật khi chạy trên Render).
- **Cổng chạy local đọc từ biến `PORT`** (mặc định 5000) để tránh xung đột với AirPlay Receiver trên macOS.
- **`/healthz`:** endpoint nhẹ cho Render health check (không đụng tới model).
- **Cấu hình gunicorn:** `--workers 1 --threads 4 --timeout 60` — RAM ~172MB thay vì ~365MB (gói free chỉ 512MB), vẫn ~280 req/s, 80 hội thoại đồng thời không lẫn phiên.
- **Lời đáp** không còn nói "sơ đồ bên cạnh" (sai trên điện thoại, nơi bản đồ nằm bên dưới).

## Giao diện (`templates/index.html`)
- **Phông chữ:** 7 chỗ `font: … inherit` là cú pháp không hợp lệ → nút Gửi, nút lựa chọn, ô nhập rơi về Arial 13px. Nay dùng biến `--font-ui`.
- **Lỗi mạng:** thông báo dễ hiểu (không nhắc "cửa sổ chạy Flask"), tự mở lại nút lựa chọn để thử lại, timeout 45s, ghi chú "server miễn phí đang khởi động" sau 6s chờ.
- **Gửi chồng / sai thứ tự:** khóa nút Gửi khi đang chờ; Enter lúc chờ bị bỏ qua nhưng giữ chữ gõ dở.
- **Nút lựa chọn cũ** bị khóa khi người dùng trả lời bằng cách gõ.
- **IME:** Enter dùng để chốt chữ khi gõ dấu không còn gửi tin.
- **Esc** đóng ảnh phóng to (và splash). Bấm ảnh/nút trên thẻ quán dùng `data-*` thay vì `onclick` chèn chuỗi.
- **Ban đêm được nhớ** sau khi tải lại; ô nhập tự focus; thêm 4 ô gợi ý khởi đầu (CSS đã có sẵn nhưng HTML thiếu).
- **Khung chat tự cuộn xuống cuối sau khi bản đồ mở / ảnh thẻ quán tải xong** (trước đây thẻ "Giải mã phòng" và thẻ quán có thể bị cắt mép dưới sau khi bấm nút chọn cổng; phát hiện khi chạy kịch bản demo trên Chrome thật).
- **Điện thoại:** tự cuộn tới bản đồ sau khi có tuyến; khung chat co theo chiều cao màn hình để ô nhập luôn thấy được (kể cả 360×640, 320×568).
- **Truy cập (a11y):** nhãn cho ô nhập, `role="log" aria-live`, mascot dùng được bằng bàn phím, viền focus rõ.
- **Hiệu năng:** ảnh sơ đồ 888KB chỉ tải khi cần (`loading="lazy"`); `esc()` escape thêm dấu nháy; thẻ lộ trình cao hơn để tuyến dài không bị cắt.

## Test
- `test_suite.py`: sửa kỳ vọng sai ("gợi ý" không tồn tại trong câu trả lời thật) — README cũ ghi 100% nhưng thực tế còn 1 lỗi.
- Thêm `test_regression.py` và `ui_smoke_test.py`.

## Đã biết, chưa xử lý (cần quyết định của nhóm)
- Sheet `FAQ_Answers` trong Excel được nạp nhưng **không** nguồn nào dùng; câu trả lời đang viết cứng trong `app.py`.
- Chưa có dữ liệu giờ mở cửa Thư viện / Căn tin / KTX (bot trả lời "chưa có dữ liệu" thay vì đoán).
- Câu hỏi kép ("thư viện ở đâu và mở cửa mấy giờ") chỉ được xử lý đầy đủ cho HC1C.
- Smart Building và 3 phòng (CTSV, Đào tạo, Tài chính) dùng chung một tọa độ trên bản đồ.
- Độ chính xác phân loại ML (cross-validation 5-fold) khoảng 84%; phần còn lại dựa vào luật. Thêm dữ liệu huấn luyện sẽ cải thiện.
- Chưa kiểm thử Firefox/Safari và Google Fonts thật (môi trường kiểm thử chỉ có Chrome, không có internet).

## Bổ sung
- `CAU_HOI_DEMO.md`: danh sách 20 câu demo đã kiểm chứng (luật cố định, 200 lượt liên tục 0 lỗi, Chrome ở 4 độ phân giải 0 lỗi) + danh sách câu cần tránh + checklist trước giờ demo.
