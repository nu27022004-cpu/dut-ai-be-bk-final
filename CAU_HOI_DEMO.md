# Câu hỏi demo AN TOÀN — Bé BK · Trợ lý Sinh viên Bách khoa

Tất cả câu dưới đây đã được kiểm chứng:
- Đều được xử lý bằng **luật cố định** (không phụ thuộc mô hình ML ~84%) → cùng câu hỏi luôn ra cùng câu trả lời.
- Chạy liên tục 200 lượt × 20 câu (bật và tắt mô hình ML): **0 lỗi, 1 kết quả duy nhất**.
- Chạy trên Chrome thật ở 1920×1080, 1366×768, 1280×720, 1024×768: **0 lỗi**, thời gian phản hồi trung bình ~100–150 ms (chạy local).

**Quy tắc vàng: COPY–PASTE đúng từng câu bên dưới, đừng gõ tay.** Câu gõ khác đi một chút có thể rơi vào phần mô hình ML (đúng ~84%).

Trước khi bắt đầu: bấm **Chế độ chấm điểm AI** (góc trên phải) để thấy Intent / Tin cậy / Engine dưới mỗi câu trả lời.

---

## Phần 1 — Giới thiệu
| # | Gõ | Sẽ thấy | Ý nói |
|---|---|---|---|
| 1 | `xin chào` | Bé BK chào và gợi ý các việc bot làm được (mã phòng, chỉ đường, ăn uống, thủ tục…) | Trợ lý riêng của sinh viên DUT |

## Phần 2 — Tìm phòng học (giải mã mã phòng + chỉ đường A*)
| # | Gõ | Bấm | Sẽ thấy |
|---|---|---|---|
| 2 | `e2.101` | **Cổng khu C** | Thẻ "Giải mã phòng E2.101": Tòa nhà E2 · Tầng 1 · phòng đầu tiên (số 01). Bản đồ mở, đường đỏ ~84 m · 1 phút |
| 3 | `C301` | **Cổng chính** | Tòa nhà C · Tầng 3, đường đỏ trên bản đồ |
| 4 | `S05.08` | **Lối vào nhà xe khu E** | Phòng Đào tạo · Tầng 5 |

Ý nói: hiểu quy tắc đặt tên phòng (E1/E2/S/A–H); đường đi tính bằng thuật toán **A\*** trên đồ thị khuôn viên (3 lối vào × 26 địa điểm = 78 tuyến).

## Phần 3 — Chỉ đường tới địa điểm (nên bấm **Cuộc trò chuyện mới** trước câu 5)
| # | Gõ | Bấm | Sẽ thấy |
|---|---|---|---|
| 5 | `Thư viện ở đâu?` | **Cổng chính** | Tuyến tới Thư viện |
| 6 | `Chỉ đường đến Cơm cô Lài` | **Cổng khu C** | Tuyến ~100 m + thẻ ảnh thật "Quán Cơm cô Lài" 20k–30k, miễn phí cơm/canh thêm |
| 7 | `Chỉ đường đến Bánh Mỳ cô Hạnh` | **Lối vào nhà xe khu E** | Tuyến + thẻ ảnh "Bánh Mỳ cô Hạnh" |

## Phần 4 — Câu hỏi KÉP (điểm nhấn)
| # | Gõ | Bấm | Sẽ thấy |
|---|---|---|---|
| 8 | `tôi muốn tới phòng HC1C và HC1C mở cửa lúc mấy giờ` | **Cổng chính** | Trả lời cả hai ý: giờ làm việc 08:00–11:00, 13:30–16:30 **và** chỉ đường tới Hành chính một cửa |

> Chỉ câu kép về **HC1C** là chắc chắn. Đừng đổi sang "thư viện ở đâu và mở cửa mấy giờ" (xem phần Tránh).

## Phần 5 — Thủ tục hành chính (hội thoại nhiều lượt)
| # | Gõ | Bấm | Sẽ thấy |
|---|---|---|---|
| 9 | `Em xin giấy hoãn nghĩa vụ quân sự` | **Chưa đăng ký** | Bot hỏi "đã đăng ký chưa?" → hướng dẫn lên sv.dut.udn.vn rồi ghé HC1C |
| 10 | `HC1C làm việc mấy giờ` | — | 08:00–11:00 và 13:30–16:30 |

Ý nói: máy trạng thái hữu hạn (FSM) nhớ ngữ cảnh qua nhiều lượt.

## Phần 6 — Học vụ
| # | Gõ | Sẽ thấy |
|---|---|---|
| 11 | `học phí tính như thế nào` | Công thức: Số tín chỉ đăng ký × Đơn giá/tín chỉ; xem số tiền cụ thể trên sv.dut.udn.vn |
| 12 | `Năm nhất ai xếp lịch học` | Học kỳ đầu năm nhất nhà trường xếp sẵn lịch, xem TKB trên sv.dut.udn.vn hoặc app Ddut |

## Phần 7 — Đời sống sinh viên (nên **Cuộc trò chuyện mới** trước câu 13)
| # | Gõ | Sẽ thấy |
|---|---|---|
| 13 | `Bánh mỳ cô Hạnh giá bao nhiêu?` | 17k + thẻ ảnh Bánh Mỳ cô Hạnh (bấm ảnh để phóng to, Esc để đóng) |
| 14 | `quán cafe nào mở xuyên đêm chạy deadline gần bk?` | Thẻ Zone Six (24/7) và quán 24/7 khác |
| 15 | `giá gửi xe thứ 7` | Thứ 7 và Chủ nhật giá gửi xe 2.000đ |
| 16 | `in báo cáo ở đâu` | Thẻ Photo Thành Công |
| 17 | `chiều đi chạy bộ tập thể dục ở đâu gần trường?` | Gợi ý Công viên Liên Chiểu trên đường Nguyễn Sinh Sắc + thẻ quán/địa điểm |
| 18 | `Câu lạc bộ DUT` | Danh sách CLB: Pioneer, BKMAKER, Sclub, BKMEDIA, Đội Công tác Xã hội |

## Phần 8 — Biết giới hạn + kết thúc
| # | Gõ | Sẽ thấy |
|---|---|---|
| 19 | `bitcoin hôm nay giá bao nhiêu` | Từ chối lịch sự: "nằm ngoài phạm vi", gợi ý các nhóm câu hỏi bot hỗ trợ — không bịa |
| 20 | `cảm ơn bạn` | "Không có chi nè!…" |

Cuối buổi: bấm **Ban đêm** (đổi giao diện tối), **Sơ đồ trường / Thu gọn**.

**Gợi ý rút gọn 3 phút** (nếu ít thời gian): 1 → 2 → 6 → 8 → 9 → 14 → 19.

---

## TRÁNH khi demo (đúng nhưng không ổn định / ít ấn tượng)
Các câu sau đi qua **mô hình ML** (độ chính xác ~84%), có thể ra intent khác với dự kiến:
- `ăn sáng ở bánh mỳ cô hạnh`, `photo tài liệu ở đâu`, `clb ở bách khoa có gì`, `trưa nay ăn cơm ở đâu miễn phí cơm thêm?`
- Hai ô gợi ý **Ăn sáng (Bánh mỳ)** và **Photo & Tài liệu** trên màn hình đầu (đi qua ML) → dùng câu 13 và 16 thay thế.

Bot trả lời đúng nhưng **thiếu dữ liệu** (bot nói thật "chưa có dữ liệu", không bịa):
- `thư viện mấy giờ mở cửa`, `căn tin mấy giờ đóng cửa`, giờ KTX.
- Câu kép ngoài HC1C: `thư viện ở đâu và mở cửa mấy giờ`.
- Câu rất ngắn/mơ hồ: `ừ`, `1`.

Nếu thầy/cô hỏi bất ngờ và bot trả lời chưa tốt: nói thẳng "đây là phần ML ~84%, nhóm sẽ bổ sung dữ liệu huấn luyện" — trung thực được điểm hơn che giấu.

---

## Danh sách kiểm tra trước giờ demo
1. [ ] Demo trên **laptop** (cách A trong HUONG_DAN_DEMO.md) — nhanh, không phụ thuộc Wi-Fi. Render chỉ làm dự phòng.
2. [ ] Nếu dùng Render: **đánh thức trước 5–10 phút** (mở link, đợi thấy trang Bé BK), cứ ~10 phút gửi một tin để không bị ngủ.
3. [ ] Chạy `python test_suite.py` và `python test_regression.py` trên đúng máy sẽ demo — phải báo đạt.
4. [ ] Mở sẵn file này, copy từng câu; zoom trình duyệt 100% (Ctrl+0), tắt thông báo, bật chế độ toàn màn hình (F11).
5. [ ] Bật **Chế độ chấm điểm AI** trước khi bắt đầu.
6. [ ] Giữa các nhóm chủ đề bấm **Cuộc trò chuyện mới** để bắt đầu sạch (đặc biệt trước câu 5, 13).
7. [ ] Nếu bot "chưa kết nối được server": đợi 30–60 giây (Render đang thức dậy) rồi bấm lại nút / gửi lại.
