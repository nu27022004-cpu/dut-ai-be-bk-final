"""
test_regression.py — Bộ kiểm thử hồi quy cho Bé BK (chạy: python test_regression.py).

Gồm:
  1. ~100 câu sinh viên hay hỏi (có dấu / không dấu / viết tắt / lỗi gõ) với intent mong đợi.
  2. Kịch bản hội thoại nhiều lượt (FSM chọn cổng, FSM "đã đăng ký chưa?").
  3. Các "bẫy" khớp chuỗi con tiếng Việt (nhà hàng, nhà em, cô/có...).
  4. Kiểm tra API: payload dị dạng, giới hạn kích thước, header bảo mật, /healthz.
Thoát mã 0 nếu mọi mục đạt, mã 1 nếu có lỗi.
"""
import os
import sys
import warnings

warnings.filterwarnings("ignore")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import app as dut_app  # noqa: E402

T, D, H, V, O, G = "TIM_DUONG", "DOI_SONG", "THU_TUC_HANH_CHINH", "HOC_VU", "OUT_OF_SCOPE", "GREETING"

QUERIES = [
    # --- GREETING ---
    ("xin chào", G), ("hello", G), ("hi bạn", G), ("chào bé bk", G), ("cảm ơn nha", G), ("tạm biệt", G),
    ("bạn làm được gì", G), ("alo", G), ("chao", G), ("cam on ban nhieu", G),
    # --- TIM_DUONG ---
    ("e2.101 ở đâu", T), ("phòng C301 đi lối nào", T), ("thư viện ở đâu", T), ("nhà xe khu B", T),
    ("chỉ đường đến căn tin", T), ("đi từ cổng chính đến ktx", T), ("tòa nhà A nằm ở đâu", T),
    ("san bong o dau", T), ("smart building ở đâu", T), ("phòng đào tạo ở đâu", T), ("S06.08", T),
    ("ctsv nằm ở đâu", T), ("nha xe khu f o dau", T), ("khu giảng đường F", T), ("ktx nhà 2 ở đâu", T),
    ("hanh chinh mot cua o dau", T), ("tôi muốn tới phòng HC1C và HC1C mở cửa lúc mấy giờ", T),
    ("phòng học B101 ở tầng mấy", T), ("sân vườn ở đâu", T), ("e1.203", T), ("tim phong d205", T),
    ("toi muon den thu vien", T), ("cho minh hoi nha xe khu s", T), ("bãi gửi xe khu E nằm chỗ nào", T),
    ("hc 1c o dau", T), ("thu vin o dau", T),
    # --- DOI_SONG ---
    ("ăn sáng ở đâu rẻ", D), ("cơm trưa 20k", D), ("quán cà phê học bài", D), ("zone six giá bao nhiêu", D),
    ("photo tài liệu ở đâu", D), ("gửi xe bao nhiêu tiền", D), ("giá gửi xe thứ 7", D),
    ("câu lạc bộ nào ở bách khoa", D), ("chạy bộ ở đâu", D), ("in đồ án ở đâu", D),
    ("gui xe may het bao nhieu", D), ("quán nào mở xuyên đêm", D), ("bánh mì cô hạnh có gì", D),
    ("thư viện mở cửa mấy giờ", D), ("căn tin mấy giờ đóng cửa", D), ("thư viện có mở cửa không", D),
    ("an gi o gan truong", D), ("trạm 247 có điều hòa không", D), ("cf chạy dl ở đâu", D),
    ("giá nước zone 6", D), ("tìm quán ăn gần trường", D), ("có chỗ nào chơi thể thao không", D),
    ("câu lạc bộ truyền thông", D), ("zon six", D), ("com co lay gia bao nhieu", D),
    # --- THU_TUC_HANH_CHINH ---
    ("xin giấy xác nhận sinh viên", H), ("làm lại thẻ sinh viên", H), ("hoàn nghĩa vụ quân sự thế nào", H),
    ("HC1C làm việc mấy giờ", H), ("hc1c có làm thứ 7 không", H), ("phúc khảo điểm", H),
    ("bảng điểm lấy ở đâu", H), ("em muốn lấy bản điểm", H), ("bảo lưu kết quả học tập", H),
    ("chuyển ngành thế nào", H), ("học bổng khuyến khích", H), ("điểm rèn luyện bị sai", H),
    ("mượn học bạ", H), ("miễn giảm học phí", H), ("vay vốn sinh viên", H), ("đóng học phí ở đâu", H),
    ("sai điểm thi thì sao", H), ("xnsv lấy ở đâu", H), ("thôi học cần làm gì", H), ("nop hoc phi o dau", H),
    ("dong hoc pi", H), ("lay ban diem o dau", H),
    # --- HOC_VU ---
    ("lịch thi học kỳ này", V), ("học phí tính như thế nào", V), ("đăng ký tín chỉ khi nào", V),
    ("tkb xem ở đâu", V), ("ddut là gì", V), ("năm nhất ai xếp lịch", V), ("học kỳ 2 tự đăng ký", V),
    ("hoc pji tinh sao", V), ("đăng ký học phần trễ được không", V), ("hoc phi mot tin chi bao nhieu", V),
    ("xem thời khóa biểu ở đâu", V),
    # --- OUT_OF_SCOPE ---
    ("thời tiết hôm nay", O), ("giá iphone 16", O), ("giải phương trình bậc 2", O), ("viết code python", O),
    ("bitcoin hôm nay", O), ("đh bách khoa hà nội ở đâu", O), ("kể chuyện cười đi", O), ("cách nấu phở", O),
    ("ai là tổng thống mỹ", O), ("điểm chuẩn tuyển sinh năm nay", O), ("hôm nay ăn gì ở sài gòn", O),
    ("dịch sang tiếng anh giúp mình", O),
]

# Câu bình thường KHÔNG được bị hiểu là chỉ đường tới một tòa nhà (lỗi khớp chuỗi con "nha h", "nha e"...)
NOT_BUILDING = [
    "nhà hàng nào ngon gần trường ở đâu", "nhà em ở đâu mà xa trường quá", "khu ăn uống ở đâu",
    "khu dân cư gần trường ở đâu", "nhà anh ở đâu", "có lại học bù không",
]

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  [FAIL] {msg}")


def main() -> bool:
    client = dut_app.app.test_client()

    def ask(q, reset=True):
        if reset:
            client.post("/api/reset")
        return client.post("/api/chat", json={"message": q}).get_json()

    print(f"=== 1. {len(QUERIES)} câu sinh viên hay hỏi ===")
    ok = 0
    for q, exp in QUERIES:
        r = ask(q)
        if r["intent"] == exp:
            ok += 1
        else:
            check(False, f"{q!r}: mong đợi {exp}, nhận {r['intent']} [{r['source']}]")
    print(f"  -> {ok}/{len(QUERIES)} đúng ({100 * ok / len(QUERIES):.0f}%)")

    print("=== 2. Bẫy khớp chuỗi con ===")
    for q in NOT_BUILDING:
        r = ask(q)
        bad = r["destination"] in {"BUILDING_A", "BUILDING_B", "BUILDING_C", "BUILDING_D", "BUILDING_E", "BUILDING_H"}
        check(not bad, f"{q!r} bị chỉ đường tới {r['destination']}")

    print("=== 3. FSM 'đã đăng ký chưa?' ===")
    answers = {"có rồi": "fsm_admin", "có": "fsm_admin", "em chưa": "fsm_admin", "Em chưa có đăng ký": "fsm_admin",
               "da dang ky roi": "fsm_admin", "không": "fsm_admin", "gửi rồi": "fsm_admin", "chưa gửi": "fsm_admin"}
    others = {"banh mi co hanh o dau": T, "cô lài bán gì": D, "hoc phi co tang khong": V,
              "trưa nay ăn cơm ở đâu": D, "thu vien co mo cua khong": D}
    for f, exp in {**answers, **others}.items():
        client.post("/api/reset")
        ask("xin giấy hoãn nghĩa vụ quân sự", reset=False)
        r = ask(f, reset=False)
        got = "fsm_admin" if r["source"] == "fsm_admin" else r["intent"]
        check(got == exp, f"sau 'xin giấy…' hỏi {f!r}: mong đợi {exp}, nhận {got}")

    print("=== 4. FSM chọn cổng ===")
    r = ask("thư viện ở đâu"); check(bool(r.get("choices")), "hỏi 'thư viện ở đâu' phải ra nút chọn cổng")
    r = ask("Cổng chính", reset=False); check(r["map"] is True and r["destination"] == "LIBRARY", "chọn Cổng chính phải vẽ tuyến tới Thư viện")
    ask("thư viện ở đâu"); r = ask("2", reset=False); check(r["map"] is True, "gõ '2' phải chọn Cổng khu C")
    ask("thư viện ở đâu"); r = ask("bitcoin giá bao nhiêu", reset=False)
    check(r["intent"] == O, f"đang chờ chọn cổng mà hỏi bitcoin phải thoát sang ngoài phạm vi, nhận {r['intent']}")
    ask("thư viện ở đâu"); r = ask("trưa nay ăn cơm ở đâu", reset=False); check(r["intent"] == D, "đang chờ chọn cổng mà hỏi ăn trưa phải đổi chủ đề")

    print("=== 5. API & bảo mật ===")
    client.post("/api/reset")
    r = client.post("/api/chat", json=[1, 2]); check(r.status_code == 200 and r.get_json()["source"] == "validation", "JSON dạng mảng phải bị từ chối nhẹ nhàng")
    r = client.post("/api/chat", json={"message": {"a": 1}}); check(r.status_code == 200 and r.get_json()["source"] == "validation", "message dạng dict phải bị từ chối nhẹ nhàng")
    r = client.post("/api/chat", json={"message": 123}); check(r.status_code == 200, "message dạng số không được làm sập")
    r = client.post("/api/chat", data=b'{"message":"' + b"a" * 20000 + b'"}', content_type="application/json")
    check(r.status_code == 413, f"body 20KB phải bị từ chối 413, nhận {r.status_code}")
    r = client.post("/api/chat", json={"message": "a" * 500}); check(r.status_code == 200, "tin 500 ký tự vẫn được nhận")
    r = client.post("/api/chat", json={"message": "x" * 5000}); check(r.status_code == 200, "tin 5000 ký tự bị cắt chứ không lỗi")
    r = client.get("/")
    for h in ("X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy"):
        check(h in r.headers, f"thiếu header {h}")
    r = client.get("/healthz"); check(r.status_code == 200 and r.get_json()["ok"] is True, "/healthz phải trả ok")
    for bad in ("/app.py", "/models/intent_model.joblib", "/data/intent_dataset_final.csv", "/static/../app.py", "/.env"):
        check(client.get(bad).status_code == 404, f"{bad} không được lộ")
    r = client.post("/api/chat", json={"message": "thư viện ở đâu"})
    cookie = r.headers.get("Set-Cookie", "")
    check("HttpOnly" in cookie and "SameSite=Lax" in cookie, f"cookie thiếu HttpOnly/SameSite: {cookie[:80]}")

    print("\n" + "=" * 55)
    if failures:
        print(f"PHÁT HIỆN {len(failures)} LỖI.")
        return False
    print("TẤT CẢ KIỂM THỬ HỒI QUY ĐỀU ĐẠT.")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
