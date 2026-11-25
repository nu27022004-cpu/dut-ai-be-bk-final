"""
test_suite.py — Bộ kiểm thử QA toàn diện theo góc nhìn người dùng cho
Bé BK · DUT AI Student Assistant (Bản Final).
"""
import os
import sys
import types
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

try:
    import flask  # noqa: F401
    USE_MOCK_FLASK = False
except ImportError:
    USE_MOCK_FLASK = True
    mock_session = {}
    flask_mod = types.ModuleType("flask")

    class _MockFlask:
        def __init__(self, *a, **kw):
            self.secret_key = None

        def route(self, *a, **kw):
            return lambda fn: fn

        def run(self, *a, **kw):
            pass

    flask_mod.Flask = _MockFlask
    flask_mod.render_template = lambda *a, **kw: ""
    flask_mod.request = types.SimpleNamespace(get_json=lambda silent=True: {})
    flask_mod.jsonify = lambda x: x
    flask_mod.session = mock_session
    sys.modules["flask"] = flask_mod

try:
    import joblib  # noqa: F401
except ImportError:
    joblib_mod = types.ModuleType("joblib")
    joblib_mod.load = lambda p: None
    sys.modules["joblib"] = joblib_mod

import app as dut_app
from nlp_utils import extract_entities, parse_room
from routing import astar_route


def run_all_tests() -> bool:
    failures = []

    def check(cond: bool, msg: str):
        if not cond:
            failures.append(msg)
            print(f"  [FAIL] {msg}")

    if not USE_MOCK_FLASK:
        client = dut_app.app.test_client()

        def reset_sess():
            client.post("/api/reset")

        def ask(q: str) -> dict:
            return client.post("/api/chat", json={"message": q}).get_json()
    else:
        def reset_sess():
            dut_app.session.clear()

        def ask(q: str) -> dict:
            return dut_app.handle_message(q)

    # 1. Kiểm tra toàn vẹn tài nguyên ảnh tĩnh (10 file ảnh thật)
    print("=== 1. Kiểm tra toàn vẹn 10 tài nguyên ảnh tĩnh ===")
    required_imgs = [
        "static/dut_map.png",
        "static/dut_bg.jpg",
        "static/mascot.jpg",
        "static/places/banh_my_co_hanh.jpg",
        "static/places/com_co_lai.jpg",
        "static/places/photo_tai_nguyen.jpg",
        "static/places/photo_thanh_cong.jpg",
        "static/places/cong_vien_lien_chieu.jpg",
        "static/places/zone_six.jpg",
        "static/places/tram_247.jpg",
    ]
    for rel in required_imgs:
        p = os.path.join(BASE_DIR, rel)
        check(os.path.exists(p) and os.path.getsize(p) > 5000, f"Thiếu hoặc lỗi file ảnh: {rel}")

    # 2. 30 Acceptance Tests gốc từ Excel
    print("=== 2. Kiểm thử 30 Acceptance Tests gốc ===")
    xl = pd.ExcelFile(os.path.join(BASE_DIR, "data", "DUT_AI_Dataset_V5_Patch.xlsx"))
    acc = xl.parse("Acceptance_Tests")
    passed_a = 0
    for _, r in acc.iterrows():
        tid = r["Test_ID"]
        q = str(r["Câu hỏi"])
        exp = str(r["Intent mong đợi"])
        if tid != "T23":
            reset_sess()
        res = ask(q)
        ok = res.get("intent") == exp
        ans_low = res.get("answer", "").lower()
        if tid == "T03":
            ok = ok and res.get("entities", {}).get("destination") == "DORM_5"
        elif tid == "T06":
            ok = ok and res.get("destination") == "LIBRARY" and res.get("gate") == "GATE_E_PARKING"
        elif tid == "T11":
            ok = ok and "cơm cô lài" in ans_low and bool(res.get("places")) and res["places"][0]["image_url"] is not None
        elif tid == "T24":
            ok = ok and "08:00" in ans_low and "13:30" in ans_low
        elif tid == "T26":
            ok = ok and "s05.08" in ans_low
        elif tid == "T28":
            ok = ok and "hc1c" in ans_low and not res.get("choices")
        if ok:
            passed_a += 1
        else:
            check(False, f"{tid} ({q}): exp={exp}, got={res.get('intent')}, ans={res.get('answer','')[:70]}")
    print(f"  -> Đạt {passed_a}/{len(acc)} Acceptance Tests.")

    # 3. QA Góc nhìn người dùng: Câu hỏi đồng nghĩa, tiếng Việt không dấu, 7 địa điểm thật & Smart Flow
    print("=== 3. Kiểm thử QA góc nhìn người dùng (Đồng nghĩa, 7 địa điểm, Smart Flow) ===")
    user_scenarios = [
        ("sáng nay ăn gì gần trường ngon rẻ?", "DOI_SONG", "17k", True),
        ("bánh mì cô hạnh bao nhiêu tiền?", "DOI_SONG", "17k", True),
        ("trưa nay ăn cơm ở đâu miễn phí cơm thêm?", "DOI_SONG", "20k", True),
        ("quán cafe nào mở xuyên đêm chạy deadline gần bk?", "DOI_SONG", "24/7", True),
        ("zone 6 ở đường nào và giá nước bao nhiêu?", "DOI_SONG", "phạm như xương", True),
        ("trạm 247 study cafe giá nước tầm bao nhiêu?", "DOI_SONG", "35k", True),
        ("chỗ nào có nhiều tài liệu môn học cũ giá rẻ?", "DOI_SONG", "thành công", True),
        ("chiều đi chạy bộ tập thể dục ở đâu gần trường?", "DOI_SONG", "nguyễn sinh sắc", True),
        ("cong vien lien chieu o dau", "DOI_SONG", "liên chiểu", True),
        ("quan ca phe hoc bai 24/7", "DOI_SONG", "24/7", True),
        ("com co lai gia bao nhieu", "DOI_SONG", "20k", True),
        ("quanh trường Bách khoa có gì hay ho không?", "DOI_SONG", "bạn đang muốn", False),
    ]
    for q, exp_intent, must_text, need_photo in user_scenarios:
        reset_sess()
        res = ask(q)
        ok_i = res.get("intent") == exp_intent
        ok_t = must_text in res.get("answer", "").lower()
        ok_p = (not need_photo) or (bool(res.get("places")) and all(p.get("image_url") for p in res["places"]))
        check(ok_i and ok_t and ok_p, f"QA '{q}': intent={res.get('intent')} (exp {exp_intent}), has_text={ok_t}, has_photo={ok_p}")

    # Bấm thử toàn bộ 7 nút trong Smart Flow Đời sống sinh viên
    for btn in dut_app.LIFESTYLE_CHOICES:
        reset_sess()
        res = ask(btn)
        check(res.get("intent") == "DOI_SONG", f"Smart Flow nút '{btn}' bị lệch intent: {res.get('intent')}")

    # 4. Chỉ đường A* tới Bánh Mỳ cô Hạnh & Cơm cô Lài (trên bản đồ mới + kèm thẻ ảnh)
    print("=== 4. Kiểm thử chỉ đường A* tới Bánh Mỳ cô Hạnh & Cơm cô Lài ===")
    reset_sess()
    r1 = ask("Chỉ đường đến Bánh Mỳ cô Hạnh")
    r2 = ask("Cổng khu C")
    check(r1["intent"] == "TIM_DUONG" and r1["map"] is False, f"Hỏi đường Bánh Mỳ cô Hạnh bước 1 lỗi: {r1}")
    check(
        r2["map"] is True and r2["destination"] == "FOOD_BANH_MY_HANH" and bool(r2.get("places")),
        f"Chỉ đường Bánh Mỳ cô Hạnh bước 2 lỗi: {r2}",
    )

    reset_sess()
    r1 = ask("Đi từ cổng khu C qua Cơm cô Lài")
    check(
        r1["intent"] == "TIM_DUONG" and r1["map"] is True and r1["destination"] == "FOOD_COM_CO_LAI" and bool(r1.get("places")),
        f"Chỉ đường thẳng Cơm cô Lài lỗi: {r1}",
    )

    # 5. Giải mã phòng học E1/E2 & gõ thẳng mã phòng
    print("=== 5. Kiểm thử giải mã phòng học E1/E2 & FSM nhiều lượt ===")
    r_e2 = parse_room("e2.101")
    check(r_e2 and r_e2["building_id"] == "BUILDING_E2" and r_e2["floor"] == 1 and r_e2["room_num"] == 1, f"E2.101 lỗi: {r_e2}")
    r_e1 = parse_room("phong e1.203")
    check(r_e1 and r_e1["building_id"] == "BUILDING_E1" and r_e1["floor"] == 2 and r_e1["room_num"] == 3, f"E1.203 lỗi: {r_e1}")

    reset_sess()
    t1 = ask("e2.101")
    t2 = ask("Cổng khu C")
    check(t1["intent"] == "TIM_DUONG" and t1["room_info"]["building_id"] == "BUILDING_E2", f"Gõ thẳng e2.101 lỗi: {t1}")
    check(t2["map"] is True and t2["destination"] == "BUILDING_E2", f"Vẽ đường E2.101 lỗi: {t2}")

    # FSM thoát pending khi người dùng đổi ý
    reset_sess()
    ask("Thư viện ở đâu?")
    sw = ask("Quán cà phê học bài 24/7")
    check(sw["intent"] == "DOI_SONG" and bool(sw.get("places")), f"FSM không thoát được pending gate: {sw}")

    reset_sess()
    ask("Em xin giấy hoãn nghĩa vụ quân sự")
    no_reg = ask("Em chưa có đăng ký")
    check(no_reg["intent"] == "THU_TUC_HANH_CHINH" and "sv.dut.udn.vn" in no_reg["answer"], f"FSM chưa có đăng ký lỗi: {no_reg}")

    # 6. Kiểm thử đồ thị A* (3 cổng x 26 địa điểm = 78 tuyến đường)
    print("=== 6. Kiểm thử đồ thị A* (78 tuyến đường) ===")
    loc_df = xl.parse("Location_Dictionary")
    non_gates = loc_df[loc_df["Loại"] != "Lối vào"]
    dests = [str(x) for x in non_gates["Entity_ID"].tolist()] + [
        "BUILDING_E1", "BUILDING_E2", "FOOD_BANH_MY_HANH", "FOOD_COM_CO_LAI"
    ]
    routes_ok = 0
    for g in ["GATE_MAIN", "GATE_C", "GATE_E_PARKING"]:
        for d in dests:
            rt = astar_route(g, d)
            if rt and len(rt["points"]) >= 2:
                routes_ok += 1
            else:
                check(False, f"A* lỗi tuyến {g} -> {d}")
    print(f"  -> A* thông suốt {routes_ok}/{3*len(dests)} tuyến đường.")

    print("\n" + "=" * 55)
    if not failures:
        print("TẤT CẢ KIỂM THỬ BẢN FINAL ĐỀU ĐẠT (100% PASS)!")
        return True
    print(f"PHÁT HIỆN {len(failures)} LỖI CẦN DEBUG.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)
