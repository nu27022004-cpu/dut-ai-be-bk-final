"""
app.py — Backend Flask cho Bé BK · DUT AI Student Assistant (Bản Final).

Tính năng hoàn chỉnh:
- Hybrid NLP (FeatureUnion Word + Char-wb + LinearSVC + High-Precision Semantic Rules).
- Giải mã phòng học thông minh (tách E1/E2: E2.101 -> Tòa E2, tầng 1, phòng đầu tiên; Smart Building; Khu A–H).
- Thuật toán tìm đường ngắn nhất A* cho 78 tuyến (gồm cả Bánh Mỳ cô Hạnh & Cơm cô Lài trên sơ đồ mới).
- Smart Flow Đời sống sinh viên với 7 thẻ địa điểm có ảnh thật, nhãn giá nổi bật và nút chỉ đường 1 chạm.
"""
import json
import os
import secrets
import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request, session
from werkzeug.exceptions import HTTPException

from nlp_utils import LOCATION_LABELS, extract_entities, extract_gate, norm, preprocess_for_ml
from routing import astar_route
from keyword_engine import analyze_context_keys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "intent_model.joblib")
EVAL_PATH = os.path.join(BASE_DIR, "models", "evaluation.json")
EXCEL_PATH = os.path.join(BASE_DIR, "data", "DUT_AI_Dataset_V5_Patch.xlsx")
MAP_PATH = os.path.join(BASE_DIR, "static", "dut_map.png")
PLACES_DIR = os.path.join(BASE_DIR, "static", "places")

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.secret_key = os.environ.get("DUT_AI_SECRET") or secrets.token_hex(24)
app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024,                 # tin nhắn tối đa 500 ký tự, 16KB là dư
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),   # Render luôn chạy HTTPS
)


@app.after_request
def _security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


@app.errorhandler(413)
def _too_large(_e):
    return jsonify(_build_response("OUT_OF_SCOPE", "Tin nhắn quá dài, bạn rút gọn lại giúp Bé BK nhé!", confidence=0.0, source="validation", provenance="SYSTEM")), 413

model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None


def load_faq_knowledge() -> dict[str, dict]:
    if not os.path.exists(EXCEL_PATH):
        return {}
    df = pd.read_excel(EXCEL_PATH, sheet_name="FAQ_Answers")
    kb = {}
    for _, row in df.iterrows():
        fid = str(row.get("FAQ_ID", "")).strip()
        if fid:
            kb[fid] = {
                "answer": str(row.get("Câu trả lời chuẩn", "")).strip(),
                "provenance": str(row.get("Provenance", "USER_PROVIDED")).strip(),
            }
    return kb


FAQ_KB = load_faq_knowledge()

# Từ được chấp nhận khi trả lời câu hỏi "đã đăng ký chưa?". Có từ nào ngoài danh sách
# (vd "banh", "thu", "vien") thì coi là người dùng đổi chủ đề, không nuốt vào luồng này.
REGISTERED_ANSWER_WORDS = {
    "em", "minh", "toi", "ban", "da", "dang", "ky", "gui", "roi", "rui", "r", "xong", "hoan", "tat",
    "co", "chua", "khong", "ko", "k", "vang", "u", "uh", "ok", "oke", "a", "ah", "nha", "nhe", "ne",
    "ha", "het", "dc", "duoc", "ro",
}

GATE_CHOICES = ["Cổng chính", "Cổng khu C", "Lối vào nhà xe khu E"]
REG_CHOICES = ["Đã đăng ký", "Chưa đăng ký"]
LIFESTYLE_CHOICES = [
    "Ăn sáng (Bánh mỳ)",
    "Cơm trưa sinh viên",
    "Cà phê học bài 24/7",
    "Photo & Tài liệu",
    "Thể thao & Vui chơi",
    "Giá gửi xe",
    "Câu lạc bộ DUT",
]

# Danh mục 7 địa điểm có ảnh thật + giá/điểm mạnh nổi bật + liên kết bản đồ A*
PLACES_CATALOG = {
    "banh_my_co_hanh": {
        "name": "Bánh Mỳ cô Hạnh",
        "tag": "Ăn sáng & Đồ uống",
        "price": "Bánh mỳ 17k · Nước 5k–20k",
        "perk": "Full topping · Có cà phê & sữa đậu nành",
        "location": "Đường Ngô Sĩ Liên (sát Khu E)",
        "note": "Bán bánh mỳ full topping 17k cực chắc bụng, kèm cà phê và nhiều loại đồ uống chỉ từ 5k đến 20k.",
        "slug": "banh_my_co_hanh",
        "map_query": "Chỉ đường đến Bánh Mỳ cô Hạnh",
    },
    "com_co_lai": {
        "name": "Quán Cơm cô Lài",
        "tag": "Cơm trưa sinh viên",
        "price": "20k – 30k / suất",
        "perk": "Miễn phí cơm thêm & canh thêm",
        "location": "Đường Ngô Sĩ Liên (khu Ký túc xá)",
        "note": "Các suất cơm ngon – bổ – rẻ, sạch sẽ chuẩn sinh viên (20k–30k tùy món bạn chọn), đặc biệt cơm thêm và canh thêm hoàn toàn miễn phí.",
        "slug": "com_co_lai",
        "map_query": "Chỉ đường đến Cơm cô Lài",
    },
    "zone_six": {
        "name": "Zone Six (Zone 6)",
        "tag": "Cà phê học bài 24/7",
        "price": "30k – 50k",
        "perk": "Mở cửa 24/7 · Tụ điểm sinh viên",
        "location": "19 Phạm Như Xương",
        "note": "Nơi tụ họp học nhóm, chạy deadline quen thuộc của sinh viên Bách khoa. Điểm mạnh là mở cửa 24/7, giá nước từ 30k đến 50k.",
        "slug": "zone_six",
        "map_query": None,
    },
    "tram_247": {
        "name": "Trạm 247 Study Cafe",
        "tag": "Cà phê học bài 24/7",
        "price": "35k – 60k",
        "perk": "Mở cửa 24/7 · Mát mẻ, văn minh",
        "location": "Gần khu vực Bách khoa Đà Nẵng",
        "note": "Mở cửa 24/7, không gian học tập mát mẻ, yên tĩnh và văn minh; giá đồ uống dao động từ 35k đến 60k.",
        "slug": "tram_247",
        "map_query": None,
    },
    "photo_tai_nguyen": {
        "name": "Quán Photo Tài Nguyên",
        "tag": "Photocopy & In ấn",
        "price": "Giá sinh viên",
        "perk": "In ấn nhanh · Gần cổng trường",
        "location": "Đường Ngô Sĩ Liên (gần trường)",
        "note": "Tiệm photo quen thuộc của sinh viên Bách khoa để in báo cáo, đồ án và photo tài liệu học tập.",
        "slug": "photo_tai_nguyen",
        "map_query": None,
    },
    "photo_thanh_cong": {
        "name": "Quán Photo Thành Công",
        "tag": "Tài liệu & Giáo trình",
        "price": "Giá rẻ sinh viên",
        "perk": "Nhiều tài liệu môn học có sẵn",
        "location": "Kề cạnh Photo Tài Nguyên (Ngô Sĩ Liên)",
        "note": "Nằm ngay sát cạnh Photo Tài Nguyên, có sẵn rất nhiều tài liệu, đề cương và giáo trình các môn học giá rẻ cho sinh viên.",
        "slug": "photo_thanh_cong",
        "map_query": None,
    },
    "cong_vien_lien_chieu": {
        "name": "Công viên Liên Chiểu",
        "tag": "Thể thao & Vui chơi",
        "price": "Miễn phí vào cửa",
        "perk": "Tập thể dục · Chơi thể thao · Hóng mát",
        "location": "Đường Nguyễn Sinh Sắc",
        "note": "Không gian rộng rãi, thoáng mát — địa điểm quen thuộc để sinh viên đến chạy bộ, tập thể dục, chơi thể thao và tụ tập vui chơi buổi chiều tối.",
        "slug": "cong_vien_lien_chieu",
        "map_query": None,
    },
}

# Ánh xạ đích trên bản đồ sang Place Card để hiện luôn thẻ ảnh khi chỉ đường tới quán ăn!
DEST_TO_PLACE = {
    "FOOD_BANH_MY_HANH": "banh_my_co_hanh",
    "FOOD_COM_CO_LAI": "com_co_lai",
}


def _resolve_place_cards(keys: list[str]) -> list[dict]:
    cards = []
    for k in keys:
        item = PLACES_CATALOG.get(k)
        if not item:
            continue
        img_url = None
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            cand = os.path.join(PLACES_DIR, item["slug"] + ext)
            if os.path.exists(cand):
                img_url = f"/static/places/{item['slug']}{ext}"
                break
        cards.append({
            "name": item["name"],
            "tag": item["tag"],
            "price": item["price"],
            "perk": item["perk"],
            "location": item["location"],
            "note": item["note"],
            "image_url": img_url,
            "map_query": item["map_query"],
        })
    return cards


def _is_greeting_or_social(n: str) -> str | None:
    if not n:
        return None
    if any(x in n for x in ["xin chao", "chao ban", "chao bot", "chao be bk", "chao ad"]) or n in {"chao", "hello", "hi", "hey", "alo", "hi bot"}:
        return "greet"
    if any(x in n for x in ["cam on", "thank", "thanks"]):
        return "thanks"
    if any(x in n for x in ["tam biet", "bye", "hen gap lai"]):
        return "bye"
    if any(x in n for x in ["ban lam duoc gi", "giup gi cho minh", "ho tro nhung gi", "chuc nang gi"]):
        return "help"
    return None


def classify_intent(q: str, ent: dict, ctx: dict | None = None) -> tuple[str, float, str]:
    ctx = ctx or analyze_context_keys(q)
    n = ctx["normalized"]
    sc = ctx["scores"]

    # 1. Xã giao
    if _is_greeting_or_social(n):
        return "GREETING", 0.99, "rule"

    # 1b. Chặn sớm các câu hỏi ngoài phạm vi DUT rõ ràng (trường khác, toán/code, giá điện thoại...)
    if any(x in n for x in ["ha noi", "sai gon", "tphcm", "tp hcm", "iphone", "samsung", "bitcoin", "chung khoan", "gia vang", "phuong trinh", "giai toan", "viet code", "thoi tiet", "co mua khong", "diem chuan", "tuyen sinh"]):
        return "OUT_OF_SCOPE", 0.96, "rule_oos"

    # 1c. Câu hỏi kép HC1C (hỏi CẢ đường tới HC1C VÀ giờ mở cửa HC1C) -> xử lý ưu tiên
    if ctx.get("is_dual_hc1c"):
        return "TIM_DUONG", 0.99, "keyword_dual"

    # 2. Gõ trực tiếp mã phòng học (E2.101, E1.203, C301, S05.08) -> TIM_DUONG ngay
    if ent.get("room_info") and not any(x in n for x in ["sai diem", "phuc khao", "hoc phi"]):
        return "TIM_DUONG", 0.99, "rule"

    # 3. Các nút Smart Flow của Đời sống sinh viên
    if any(x in n for x in [
        "ca phe hoc bai", "cafe hoc bai", "quan cafe", "quan ca phe", "zone 6", "zone six",
        "tram 247", "study cafe", "24/7", "247", "chay deadline", "xuyen dem", "thau dem",
        "cong vien lien chieu", "nguyen sinh sac", "tap the duc", "chay bo", "the thao & vui choi",
        "the thao va vui choi", "vui choi", "hong mat", "an sang (banh my)", "com trua sinh vien",
        "photo & tai lieu", "photo va tai lieu", "cau lac bo dut", "in do an", "in bao cao", "photocopy", "photo tai nguyen", "photo thanh cong", "chay dl",
    ]) or "cf" in n.split():
        return "DOI_SONG", 0.98, "rule"

    # 4. Giá gửi xe -> DOI_SONG
    if any(x in n for x in ["gia gui xe", "gui xe bao nhieu", "phi gui xe", "gia ve xe", "gui xe 7", "gui xe 10", "gui xe thu", "gui xe chu nhat"]) or (
        any(x in n for x in ["gui xe", "giu xe"]) and any(x in n for x in ["bao nhieu", "bao nhiu", "bnhiu", "nhiu", "may nghin", "gia", "phi", "tieng", "thu 7", "t7", "thu bay", "chu nhat", "cn"])
    ):
        return "DOI_SONG", 0.98, "rule"

    # 5. Phân biệt hỏi GIÁ/MÓN vs hỏi ĐƯỜNG cho Bánh Mỳ cô Hạnh & Cơm cô Lài
    if ent.get("destination") in {"FOOD_BANH_MY_HANH", "FOOD_COM_CO_LAI"}:
        asking_route = any(x in n for x in ["chi duong", "tim duong", "di tu", "tu cong", "duong nao", "ban do", "o dau", "nam cho nao", "nam o dau"])
        asking_food_info = any(x in n for x in ["gia", "bao nhieu", "ban gi", "co ban", "mien phi", "ngon", "menu", "do uong", "full topping", "gioi thieu"])
        if asking_route and not asking_food_info:
            return "TIM_DUONG", 0.98, "rule"
        if asking_food_info:
            return "DOI_SONG", 0.98, "rule"

    # 6. Giờ mở cửa Thư viện / Căn tin / KTX -> DOI_SONG
    if any(x in n for x in ["gio mo cua", "mo cua may gio", "gio phuc vu", "dong cua may gio", "may gio dong cua", "may gio mo cua", "mo cua khong", "co mo cua", "co dong cua"]) and any(
        x in n for x in ["thu vien", "can tin", "cang tin", "ky tuc xa", "ktx", "san bong"]
    ):
        return "DOI_SONG", 0.97, "rule"

    # 7. Giờ làm việc HC1C -> THU_TUC_HANH_CHINH
    if any(x in n for x in ["hc1c", "hanh chinh mot cua", "hanh chinh 1 cua", "mot cua khu a"]) and any(
        x in n for x in ["gio lam viec", "lam viec", "co lam", "may gio", "mo cua", "dong cua", "khi nao", "thu may", "thu 7", "t7", "thu bay", "chu nhat", "cn"]
    ):
        return "THU_TUC_HANH_CHINH", 0.98, "rule"

    # 8. Sai điểm thi / phúc khảo / điểm rèn luyện / học bổng -> THU_TUC_HANH_CHINH
    if any(x in n for x in ["sai diem", "nhap nham", "phuc khao", "thac mac diem", "bang diem dao tao", "khieu nai diem", "hoc bong", "diem ren luyen"]):
        return "THU_TUC_HANH_CHINH", 0.97, "rule"

    # 8b. Công cụ / lịch học vụ -> HOC_VU
    if any(x in n.split() for x in ["ddut", "tkb"]) or any(x in n for x in ["thoi khoa bieu", "lich thi", "lich hoc", "dang ky hoc phan", "dang ky tin chi"]):
        return "HOC_VU", 0.97, "rule"

    # 9. Học phí: nếu hỏi đường từ cổng đến Smart Building thì nhường TIM_DUONG; ngược lại phân tách Hành chính vs Học vụ
    if any(x in n for x in ["hoc phi", "khoan thu", "tien hoc"]) and not any(x in n for x in ["mien giam", "vay von"]):
        if not any(x in n for x in ["di tu", "tu cong", "chi duong", "di duong nao"]):
            if any(x in n for x in ["dong", "nop", "thanh toan", "o dau", "phong tai chinh", "phong nao", "gap phong"]):
                return "THU_TUC_HANH_CHINH", 0.97, "rule"
            return "HOC_VU", 0.96, "rule"

    # 10. Xin giấy tờ hành chính / CTSV
    if any(x in n for x in ["xac nhan sinh vien", "chung nhan sinh vien", "xnsv", "hoan nghia vu", "nvqs", "giay hoan", "giay to da dang ky", "bang diem", "ban diem", "cong tac sinh vien", "rut hoc ba", "muon hoc ba", "hoc ba", "rut ho so", "ho so sinh vien", "bao luu", "thoi hoc", "the sinh vien", "mien giam", "vay von", "chuyen nganh", "nghi hoc tam thoi"]):
        if not any(x in n for x in ["chi duong", "di tu", "den phong", "tim duong"]):
            return "THU_TUC_HANH_CHINH", 0.96, "rule"

    # 11. Tìm đường khi có tín hiệu vị trí + địa điểm/phòng/cổng
    location_cue = any(
        x in n
        for x in [
            "o dau", "nam o dau", "nam cho nao", "chi duong", "tim duong", "di duong nao",
            "di tu", "tu cong", "loi vao", "tim phong", "tim nha xe", "ban do",
            "den nha xe", "den thu vien", "den ky tuc xa", "den ktx", "den can tin",
            "den khu", "den toa", "den san", "den phong", "den hc1c", "den smart",
            "den banh", "den com", "ra banh", "qua com", "tang may", "toa nao",
            "muon toi", "muon den", "toi phong", "toi hc1c", "toi thu vien", "toi quan",
        ]
    )
    if (location_cue or sc["ACTION_ROUTE"] >= 3.0) and (ent["destination"] or ent["room_code"] or ent["gate"]):
        # Nếu từ khóa giờ mở cửa mạnh hơn hẳn từ khóa đi đường -> nhường nhánh giờ mở cửa
        if sc["ACTION_HOURS"] > sc["ACTION_ROUTE"] and not ctx.get("is_dual_hc1c"):
            if ent["destination"] == "HC1C":
                return "THU_TUC_HANH_CHINH", 0.98, "keyword_hours"
            if ent["destination"] in {"LIBRARY", "CANTEEN", "DORMITORY", "DORM_1", "DORM_2", "DORM_5"}:
                return "DOI_SONG", 0.97, "keyword_hours"
        return "TIM_DUONG", 0.97, "keyword_route"

    # 12. Mô hình ML (LinearSVC) + ngưỡng từ chối câu ngoài phạm vi
    if model is not None:
        proc = preprocess_for_ml(q)
        pred = str(model.predict([proc])[0])
        conf = 0.75
        if hasattr(model, "decision_function"):
            scores = np.asarray(model.decision_function([proc])).ravel()
            if scores.size >= 2:
                sorted_s = np.sort(scores)
                top1, top2 = float(sorted_s[-1]), float(sorted_s[-2])
                margin = top1 - top2
                conf = round(float(1.0 / (1.0 + np.exp(-2.2 * (top1 + 0.25)))), 2)
                if top1 < -0.35 and margin < 0.25:
                    return "OUT_OF_SCOPE", conf, "ml_threshold"
        return pred, conf, "ml"

    return "OUT_OF_SCOPE", 0.0, "fallback"


def _build_response(
    intent: str,
    answer_text: str,
    *,
    confidence: float = 0.95,
    source: str = "rule",
    provenance: str = "USER_PROVIDED",
    show_map: bool = False,
    route: dict | None = None,
    entities: dict | None = None,
    room_info: dict | None = None,
    places: list[dict] | None = None,
    choices: list[str] | None = None,
    highlight_choices: list[str] | None = None,
    matched_keys: list[str] | None = None,
) -> dict:
    return {
        "intent": intent,
        "confidence": confidence,
        "source": source,
        "provenance": provenance,
        "answer": answer_text,
        "map": show_map,
        "route": route,
        "destination": (entities or {}).get("destination") or (route or {}).get("goal"),
        "gate": (entities or {}).get("gate") or (route or {}).get("start"),
        "entities": entities or {},
        "room_info": room_info,
        "places": places,
        "choices": choices,
        "highlight_choices": highlight_choices or [],
        "matched_keys": matched_keys or [],
    }


def _route_response(gate: str, dest: str, room_info: dict | None, conf: float, src: str) -> dict:
    route = astar_route(gate, dest)
    dest_label = LOCATION_LABELS.get(dest, dest)

    parts = []
    if room_info:
        parts.append(room_info["summary"])
    if route:
        parts.append(route["natural_summary"])
    else:
        parts.append(f"Điểm đến của bạn là **{dest_label}**. Bạn xem vị trí trên sơ đồ khuôn viên nhé!")

    # Nếu điểm đến là Bánh Mỳ cô Hạnh hoặc Cơm cô Lài -> đính kèm luôn thẻ ảnh thật & giá!
    place_key = DEST_TO_PLACE.get(dest)
    places = _resolve_place_cards([place_key]) if place_key else None

    return _build_response(
        "TIM_DUONG",
        "\n\n".join(parts),
        confidence=conf,
        source=src,
        provenance="USER_PROVIDED",
        show_map=True,
        route=route,
        room_info=room_info,
        places=places,
        entities={
            "destination": dest,
            "gate": gate,
            "room_code": room_info["code"] if room_info else None,
        },
    )


def handle_message(q: str) -> dict:
    ctx = analyze_context_keys(q)
    n = ctx["normalized"]
    ent = extract_entities(n)

    # ==========================================================
    # BƯỚC 1: XỬ LÝ TRẠNG THÁI CHỜ (PENDING STATE)
    # ==========================================================
    pending = session.get("pending")

    if pending == "gate":
        chosen_gate = extract_gate(q, allow_standalone=True)
        if chosen_gate:
            dest = session.get("destination")
            room_info = session.get("room_info")
            session.pop("pending", None)
            session["gate"] = chosen_gate
            if dest:
                return _route_response(chosen_gate, dest, room_info, 0.99, "fsm_gate")
        intent_check, _, src_check = classify_intent(q, ent, ctx)
        if intent_check in {"DOI_SONG", "HOC_VU", "THU_TUC_HANH_CHINH", "GREETING"} or src_check == "rule_oos" or (
            intent_check == "TIM_DUONG" and ent["destination"] and ent["destination"] != session.get("destination")
        ):
            session.pop("pending", None)
        else:
            return _build_response(
                "TIM_DUONG",
                "Bạn chọn giúp Bé BK 1 trong 3 lối vào bên dưới để vẽ đường ngắn nhất nha (hoặc nhắn câu khác nếu muốn đổi chủ đề):",
                confidence=0.9,
                source="fsm_gate",
                choices=GATE_CHOICES,
                highlight_choices=["Cổng chính", "Cổng khu C"],
            )

    if pending == "registered":
        toks = n.split()
        is_answer = 0 < len(toks) <= 6 and all(t in REGISTERED_ANSWER_WORDS for t in toks)
        is_no = is_answer and any(t in {"chua", "khong", "ko", "k"} for t in toks)
        is_yes = is_answer and not is_no
        if is_no:
            session.pop("pending", None)
            msg = (
                "Vậy bạn lên **website sinh viên DUT** (`sv.dut.udn.vn`) gửi đề nghị cấp giấy tờ trước nha!\n"
                "Sau khi gửi xong, bạn theo dõi trạng thái trên web — khi nào hệ thống báo **đã xử lý / có thể nhận** thì ghé **Hành chính Một cửa (HC1C — Khu A)** lấy là xong."
            )
            return _build_response("THU_TUC_HANH_CHINH", msg, confidence=0.99, source="fsm_admin", provenance="USER_PROVIDED")
        if is_yes:
            session.pop("pending", None)
            msg = (
                "Tuyệt rồi! Bạn đăng nhập `sv.dut.udn.vn` xem hồ sơ đã báo **có thể nhận** chưa rồi ghé **HC1C (Khu A)** lấy cho đỡ mất công nha.\n"
                "• **Giờ làm việc HC1C**: Thứ 2 – Thứ 6 · Sáng **08:00–11:00**, Chiều **13:30–16:30**."
            )
            return _build_response("THU_TUC_HANH_CHINH", msg, confidence=0.99, source="fsm_admin", provenance="USER_PROVIDED")
        session.pop("pending", None)

    # ==========================================================
    # BƯỚC 2: PHÂN LOẠI INTENT HYBRID
    # ==========================================================
    intent, conf, src = classify_intent(q, ent, ctx)

    if intent == "GREETING":
        social = _is_greeting_or_social(n)
        if social == "thanks":
            txt = "Không có chi nè! Cần tìm phòng học, hỏi thủ tục hay kiếm quán ngon / cà phê 24/7 quanh trường cứ gọi Bé BK nha."
        elif social == "bye":
            txt = "Tạm biệt bạn! Chúc bạn học tập thật vui và nhiều năng lượng ở Bách khoa nhé."
        else:
            txt = (
                "Chào bạn! Mình là **Bé BK** — trợ lý nhỏ của sinh viên Bách khoa Đà Nẵng.\n"
                "Bạn cứ gõ thẳng mã phòng (như **E2.101**, **C301**, **S05.08**), hỏi đường đến **nhà xe / thư viện / Bánh Mỳ cô Hạnh / Cơm cô Lài**, hoặc hỏi **ăn uống, cà phê 24/7, học vụ & thủ tục** đều được nha!"
            )
        return _build_response("GREETING", txt, confidence=conf, source=src, provenance="SYSTEM")

    # --- TIM_DUONG ---
    if intent == "TIM_DUONG":
        dest = ent["destination"]
        room_info = ent["room_info"]
        gate = ent["gate"]

        if not dest:
            return _build_response(
                "TIM_DUONG",
                "Bạn muốn tìm phòng hay địa điểm nào nè? Gõ thẳng mã phòng (VD: **E2.101**, **C301**, **S05.08**) hoặc tên nơi cần đến như **Thư viện**, **Nhà xe khu B**, **HC1C**, **Bánh Mỳ cô Hạnh**, **Cơm cô Lài** nhé!",
                confidence=conf,
                source=src,
                entities=ent,
            )

        session["destination"] = dest
        session["room_info"] = room_info

        if gate:
            session["gate"] = gate
            session.pop("pending", None)
            return _route_response(gate, dest, room_info, conf, src)

        session["pending"] = "gate"
        dest_label = LOCATION_LABELS.get(dest, dest)
        if room_info:
            prompt = (
                f"{room_info['summary']}\n\n"
                f"Bạn định đi vào trường từ cổng nào để mình vẽ đường ngắn nhất tới **{dest_label}** nha?"
            )
        elif ctx.get("is_dual_hc1c"):
            prompt = (
                "**Hành chính Một cửa (HC1C — Khu A)** làm việc **Thứ 2 – Thứ 6**: sáng **08:00–11:00**, chiều **13:30–16:30** (Thứ 7 & Chủ nhật nghỉ).\n\n"
                "Còn để chỉ đường ngắn nhất tới **HC1C**, bạn định đi vào từ lối nào nè?"
            )
        else:
            prompt = f"Mình tìm thấy **{dest_label}** rồi nè! Bạn định xuất phát từ lối nào để mình vẽ đường tiện nhất?"

        # Gợi ý cổng gần nhất làm nút nổi bật
        rec_gates = ["Cổng khu C", "Lối vào nhà xe khu E"] if dest in {"BUILDING_E1", "BUILDING_E2", "FOOD_BANH_MY_HANH", "FOOD_COM_CO_LAI", "SMART_BUILDING"} else ["Cổng chính", "Cổng khu C"]

        return _build_response(
            "TIM_DUONG",
            prompt,
            confidence=conf,
            source=src,
            entities=ent,
            room_info=room_info,
            choices=GATE_CHOICES,
            highlight_choices=rec_gates,
        )

    # --- THU_TUC_HANH_CHINH ---
    if intent == "THU_TUC_HANH_CHINH":
        if any(x in n for x in ["gio lam viec", "lam viec", "co lam", "may gio", "mo cua", "dong cua", "thu 7", "t7", "thu bay", "chu nhat", "cn"]) and any(
            x in n for x in ["hc1c", "hanh chinh", "mot cua"]
        ):
            msg = (
                "**Hành chính Một cửa (HC1C — Khu A)** làm việc từ **Thứ 2 đến Thứ 6**:\n"
                "• Buổi sáng: **08:00 – 11:00**\n"
                "• Buổi chiều: **13:30 – 16:30**\n"
                "Thứ 7 và Chủ nhật nghỉ nha bạn (nhớ ghé sớm trước giờ đóng cửa để kịp làm thủ tục)."
            )
            return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED", entities=ent)

        if any(x in n for x in ["hoc phi", "tien bac", "khoan thu", "dong hoc phi", "nop hoc phi", "tai chinh"]):
            msg = (
                "Về **đóng học phí, tiền bạc và các khoản thu**, bạn liên hệ **Phòng Tài chính & Kế hoạch** tại tòa **Smart Building (Khu S)** nhé.\n"
                "Lưu ý: Tuyệt đối không gửi mật khẩu hay thông tin thanh toán vào khung chat nha!"
            )
            return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED + OFFICIAL_WEB", entities=ent)

        if any(x in n for x in ["da dang ky", "da gui"]) and any(x in n for x in ["giay", "hoan nghia vu", "xac nhan", "bang diem", "ban diem", "ho so"]):
            extra = "\n• Nếu cần hỏi chuyên môn về điểm thi/phúc khảo thì qua **Phòng Đào tạo (S05.08)** nha." if "bang diem" in n else ""
            msg = (
                "Nếu đã gửi yêu cầu trên `sv.dut.udn.vn`, bạn kiểm tra trạng thái hồ sơ đã chuyển sang **có thể nhận** chưa rồi ghé **HC1C (Khu A)** lấy nhé!\n"
                "• Giờ làm việc HC1C: Thứ 2–Thứ 6 (**08:00–11:00** và **13:30–16:30**)."
                + extra
            )
            return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED", entities=ent)

        if any(x in n for x in ["rut hoc ba", "muon hoc ba", "hoc ba", "rut ho so", "ho so sinh vien", "thoi hoc"]):
            msg = (
                "Về thủ tục **rút/mượn học bạ hoặc rút hồ sơ sinh viên**, bạn liên hệ trực tiếp **Phòng Công tác Sinh viên — phòng S06.08** (tầng 6, Smart Building) để được hướng dẫn quy trình và giấy tờ cần mang theo nhé!\n"
                "• Nếu cần nộp/nhận đơn theo biểu mẫu một cửa sau khi được hướng dẫn, bạn ghé **HC1C (Khu A)** (Thứ 2–Thứ 6: **08:00–11:00**, **13:30–16:30**)."
            )
            return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED + OFFICIAL_WEB", entities=ent)

        if any(x in n for x in ["bao luu", "nghi hoc tam thoi", "chuyen nganh"]):
            msg = (
                "Về thủ tục **bảo lưu kết quả học tập, nghỉ học tạm thời hay chuyển ngành**, bạn liên hệ **Phòng Đào tạo — phòng S05.08** (tầng 5, Smart Building) và theo dõi hướng dẫn nộp đơn trên `sv.dut.udn.vn` nhé!"
            )
            return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED", entities=ent)

        if any(x in n for x in ["the sinh vien", "mien giam", "vay von"]):
            msg = (
                "Về **làm lại thẻ sinh viên, miễn giảm học phí hay xác nhận vay vốn**, bạn liên hệ **Phòng Công tác Sinh viên — phòng S06.08** (tầng 6, Smart Building) hoặc kiểm tra mục đăng ký giấy tờ trên `sv.dut.udn.vn` nhé!"
            )
            return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED + OFFICIAL_WEB", entities=ent)

        if any(x in n for x in ["thi cu", "diem thi", "sai diem", "nhap nham", "phuc khao", "bang diem dao tao", "dao tao"]):
            msg = (
                "Về **sai điểm thi, phúc khảo hay bảng điểm đào tạo**, bạn lên **Phòng Đào tạo — phòng S05.08** (tầng 5, Smart Building) để được hỗ trợ trực tiếp nhé.\n"
                "Còn nhận giấy tờ đã đăng ký online và đã duyệt thì nhận ở **HC1C (Khu A)**."
            )
            return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED", entities=ent)

        if any(x in n for x in ["giay", "hoan nghia vu", "nvqs", "xac nhan sinh vien", "chung nhan sinh vien", "xnsv", "bang diem", "ban diem"]):
            session["pending"] = "registered"
            return _build_response(
                intent,
                "Bạn đã đăng ký / gửi đề nghị cấp giấy tờ trên website sinh viên DUT (`sv.dut.udn.vn`) chưa nè?",
                confidence=conf,
                source=src,
                provenance="USER_PROVIDED",
                entities=ent,
                choices=REG_CHOICES,
                highlight_choices=["Đã đăng ký", "Chưa đăng ký"],
            )

        msg = (
            "Về **công tác sinh viên, học bổng hay điểm rèn luyện**, bạn ghé **Phòng Công tác Sinh viên — phòng S06.08** (tầng 6, Smart Building) nhé.\n"
            "Còn nhận giấy tờ đã đăng ký online thì ghé **HC1C (Khu A)** sau khi web báo đã xử lý xong."
        )
        return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED + OFFICIAL_WEB", entities=ent)

    # --- HOC_VU ---
    if intent == "HOC_VU":
        if any(x in n for x in ["hoc phi", "tien hoc", "tinh phi"]):
            msg = (
                "Học phí mỗi kỳ được tính theo công thức: **Số tín chỉ đăng ký × Đơn giá/tín chỉ**.\n"
                "Đơn giá cụ thể phụ thuộc vào từng khóa/chương trình nên bạn xem số tiền chính xác trên `sv.dut.udn.vn` hoặc hỏi **Phòng Tài chính & Kế hoạch (Smart Building)** nhé."
            )
            return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED", entities=ent)
        if any(x in n for x in ["nam nhat", "ky dau", "hoc ky dau", "ky 1", "ai xep lich"]):
            msg = (
                "Ở **học kỳ đầu năm nhất**, nhà trường sẽ **xếp sẵn lịch học** cho bạn — không cần tự canh đăng ký tín chỉ đâu!\n"
                "Bạn chỉ cần vào `sv.dut.udn.vn` hoặc mở app **Ddut** để xem thời khóa biểu là xong."
            )
            return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED", entities=ent)
        if any(x in n for x in ["dang ky tin chi", "dang ky hoc phan", "ky 2", "hoc ky 2", "tu dang ky"]):
            msg = (
                "Từ **học kỳ 2 trở đi**, bạn sẽ **chủ động tự đăng ký học phần** theo kế hoạch đào tạo.\n"
                "Đợt đăng ký thường mở gần cuối kỳ hiện tại — nhớ canh thông báo trên `sv.dut.udn.vn` để chọn lịch đẹp nha!"
            )
            return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED + OFFICIAL_WEB", entities=ent)

        msg = (
            "Bạn tra cứu **lịch học, thời khóa biểu và lịch thi** trên website sinh viên (`sv.dut.udn.vn`) hoặc ứng dụng **Ddut** bằng tài khoản sinh viên của mình nhé."
        )
        return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED + OFFICIAL_WEB", entities=ent)

    # --- DOI_SONG (SMART FLOW + 7 REAL PHOTO CARDS) ---
    if intent == "DOI_SONG":
        # 1. Giá gửi xe
        if any(x in n for x in ["gui xe", "giu xe", "ve xe"]):
            if "7 tieng" in n:
                msg = "Gửi xe **7 tiếng** (Thứ 2 – Thứ 6) là **1.000đ** nha bạn. Nhớ xem bảng giá tại nhà xe phòng khi có điều chỉnh nhé!"
            elif "10 tieng" in n:
                msg = "Gửi xe **10 tiếng** (Thứ 2 – Thứ 6) là **2.000đ** nha bạn. Nhớ xem bảng giá tại nhà xe phòng khi có điều chỉnh nhé!"
            elif any(x in n for x in ["chu nhat", "cn", "thu bay", "thu 7", "t7", "cuoi tuan"]):
                msg = "**Thứ 7 và Chủ nhật** giá gửi xe mặc định là **2.000đ** nha bạn!"
            else:
                msg = (
                    "Giá gửi xe tham khảo trong trường:\n"
                    "• **Thứ 2 – Thứ 6**: 7 tiếng là **1.000đ**, 10 tiếng là **2.000đ**\n"
                    "• **Thứ 7 & Chủ nhật**: **2.000đ** mặc định"
                )
            return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED", entities=ent)

        # 2. Giờ mở cửa Thư viện / Căn tin / KTX
        if any(x in n for x in ["gio mo cua", "mo cua may gio", "gio phuc vu", "dong cua", "mo cua"]) and any(
            x in n for x in ["thu vien", "can tin", "cang tin", "ky tuc xa", "ktx"]
        ):
            msg = (
                "Hiện Bé BK chưa có khung giờ mở cửa chính thức của Thư viện / Căn tin / KTX trong dữ liệu nên không đoán bừa nhé! "
                "Bạn xem giúp mình trên fanpage hoặc bảng thông báo tại đơn vị nha."
            )
            return _build_response(intent, msg, confidence=conf, source=src, provenance="NEEDS_VERIFICATION", entities=ent)

        # 3. Cà phê học bài 24/7 (Zone Six & Trạm 247 Study Cafe)
        if any(x in n for x in ["ca phe", "cafe", "zone 6", "zone six", "tram 247", "study cafe", "24/7", "247", "chay deadline", "chay dl", "xuyen dem", "thau dem", "hoc nhom", "hoc bai"]) or "cf" in n.split():
            if "zone" in n and "tram" not in n:
                cards = _resolve_place_cards(["zone_six"])
                msg = "Chạy deadline hay học nhóm ở **Zone Six (19 Phạm Như Xương)** là chuẩn bài luôn — quán mở **24/7**, giá nước **30k – 50k** nè!"
            elif "tram" in n and "zone" not in n:
                cards = _resolve_place_cards(["tram_247"])
                msg = "**Trạm 247 Study Cafe** mở **24/7** với không gian mát mẻ, văn minh, giá nước **35k – 60k** — ngồi học cực tập trung luôn!"
            else:
                cards = _resolve_place_cards(["zone_six", "tram_247"])
                msg = "Hai quán cà phê học bài mở **24/7** được sinh viên Bách khoa cực kỳ ưa chuộng nè — bạn bấm vào ảnh để xem rõ hơn nhé:"
            return _build_response(
                intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED",
                entities=ent, places=cards,
                choices=["Ăn sáng (Bánh mỳ)", "Cơm trưa sinh viên", "Thể thao & Vui chơi"],
            )

        # 4. Ăn sáng — Bánh Mỳ cô Hạnh
        if any(x in n for x in ["an sang", "sang nay", "buoi sang", "do an sang", "banh mi", "banh my", "co hanh", "full topping"]):
            return _build_response(
                intent,
                "Buổi sáng nạp năng lượng nhanh gọn thì ghé **Bánh Mỳ cô Hạnh** ngay đường Ngô Sĩ Liên nhé — bánh mỳ full topping **17k**, cà phê & đồ uống chỉ **5k – 20k**! Bạn có thể bấm nút bên dưới để xem đường đi trên bản đồ luôn.",
                confidence=conf, source=src, provenance="USER_PROVIDED",
                entities=ent, places=_resolve_place_cards(["banh_my_co_hanh"]),
                choices=["Cơm trưa sinh viên", "Cà phê học bài 24/7"],
            )

        # 5. Cơm trưa — Cơm cô Lài
        if any(x in n for x in ["an trua", "trua nay", "buoi trua", "com trua", "quan com", "com co lai", "co lai", "com binh dan", "com them", "20k", "30k"]):
            return _build_response(
                intent,
                "Cơm trưa ngon – bổ – rẻ, sạch sẽ chuẩn sinh viên thì thử **Quán Cơm cô Lài** nhé: giá chỉ **20k – 30k** tùy món, đặc biệt **cơm thêm và canh thêm miễn phí** luôn!",
                confidence=conf, source=src, provenance="USER_PROVIDED",
                entities=ent, places=_resolve_place_cards(["com_co_lai"]),
                choices=["Ăn sáng (Bánh mỳ)", "Cà phê học bài 24/7"],
            )

        # 6. Photo & Tài liệu (Tài Nguyên & Thành Công)
        if any(x in n for x in ["photo", "in an", "tai lieu", "in bao cao", "do an", "giao trinh", "tai nguyen", "thanh cong"]):
            if "thanh cong" in n and "tai nguyen" not in n:
                cards = _resolve_place_cards(["photo_thanh_cong"])
                msg = "**Quán Photo Thành Công** nằm ngay kề cạnh Photo Tài Nguyên — cực tiện vì có sẵn rất nhiều **tài liệu các môn học giá rẻ** cho sinh viên!"
            elif "tai nguyen" in n and "thanh cong" not in n:
                cards = _resolve_place_cards(["photo_tai_nguyen"])
                msg = "**Quán Photo Tài Nguyên** là tiệm in ấn quen thuộc ngay đường Ngô Sĩ Liên, kế bên là Photo Thành Công luôn nhé!"
            else:
                cards = _resolve_place_cards(["photo_tai_nguyen", "photo_thanh_cong"])
                msg = "Cần photo, in báo cáo hay tìm tài liệu môn học giá rẻ thì ghé **Photo Tài Nguyên** và **Photo Thành Công** (kề cạnh nhau trên đường Ngô Sĩ Liên — Thành Công có sẵn rất nhiều tài liệu các môn học giá sinh viên) nhé:"
            return _build_response(
                intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED",
                entities=ent, places=cards,
                choices=["Cà phê học bài 24/7", "Cơm trưa sinh viên"],
            )

        # 7. Thể thao & Vui chơi — Công viên Liên Chiểu
        if any(x in n for x in ["cong vien", "lien chieu", "nguyen sinh sac", "the duc", "chay bo", "the thao", "vui choi", "hong mat"]):
            return _build_response(
                intent,
                "Chiều tối muốn vận động hay hóng mát cùng bạn bè thì ra **Công viên Liên Chiểu** trên đường **Nguyễn Sinh Sắc** nhé — không gian thoáng rộng, sinh viên hay ra tập thể dục và chơi thể thao lắm!",
                confidence=conf, source=src, provenance="USER_PROVIDED",
                entities=ent, places=_resolve_place_cards(["cong_vien_lien_chieu"]),
                choices=["Cà phê học bài 24/7", "Cơm trưa sinh viên"],
            )

        # 8. Câu lạc bộ sinh viên DUT
        if any(x in n for x in ["cau lac bo", "clb", "pioneer", "bkmedia", "bk media", "sclub", "bkmaker", "ctxh", "cong tac xa hoi", "doi nhom", "truyen thong"]):
            msg = (
                "Ở Bách khoa có nhiều CLB hoạt động sôi nổi lắm nè:\n"
                "• **Học thuật & Kỹ thuật**: Pioneer, BKMAKER\n"
                "• **Hoạt động xã hội**: Đội Công tác Xã hội\n"
                "• **Kỹ năng mềm**: Sclub\n"
                "• **Truyền thông**: BKMEDIA\n"
                "Bạn theo dõi fanpage chính thức của từng CLB hoặc Phòng CTSV để cập nhật đợt tuyển thành viên nha!"
            )
            return _build_response(intent, msg, confidence=conf, source=src, provenance="USER_PROVIDED + OFFICIAL_WEB", entities=ent)

        # 9. Hỏi chung về quán ăn quanh trường -> hiện cả 2 quán ăn có ảnh thật + gợi ý tiếp
        if any(x in n for x in ["quan an", "an uong", "do an", "ngo si lien", "pham nhu xuong"]):
            return _build_response(
                intent,
                "Quanh Bách khoa có 2 quán siêu quen thuộc với sinh viên nè (đều có nút chỉ đường trên bản đồ luôn), ngoài ra bạn có thể khám phá thêm khu đường Phạm Như Xương nữa nhé:",
                confidence=conf, source=src, provenance="USER_PROVIDED",
                entities=ent, places=_resolve_place_cards(["banh_my_co_hanh", "com_co_lai"]),
                choices=["Cà phê học bài 24/7", "Photo & Tài liệu", "Thể thao & Vui chơi"],
            )

        # 10. Hỏi chung về Đời sống sinh viên -> SMART FLOW lựa chọn thông minh!
        if any(x in n for x in ["quanh truong", "doi song", "an", "uong", "choi", "tien ich", "goi y", "hay ho", "gan truong", "gan dut", "tan sinh vien"]):
            return _build_response(
                intent,
                "Quanh Bách khoa nhiều chỗ hay ho lắm! Bạn đang muốn bé BÊ KA hỗ trợ mục nào nè?",
                confidence=conf, source=src, provenance="USER_PROVIDED",
                entities=ent,
                choices=LIFESTYLE_CHOICES,
                highlight_choices=["Ăn sáng (Bánh mỳ)", "Cơm trưa sinh viên", "Cà phê học bài 24/7"],
            )
        return _build_response(
            "OUT_OF_SCOPE",
            "Câu này hiện nằm ngoài phạm vi của bé BÊ KA mất rồi! Em chuyên hỗ trợ **Tìm phòng & Chỉ đường trong DUT**, **Học vụ**, **Thủ tục hành chính**, và **Đời sống quanh trường** — bạn thử đặt câu hỏi thuộc các nhóm này nhé!",
            confidence=conf, source="ds_guard", provenance="SYSTEM",
            entities=ent,
        )

    # --- OUT_OF_SCOPE ---
    return _build_response(
        "OUT_OF_SCOPE",
        "Câu này hiện nằm ngoài phạm vi của bé BÊ KA mất rồi! Em chuyên hỗ trợ **Tìm phòng & Chỉ đường trong DUT**, **Học vụ**, **Thủ tục hành chính**, và **Đời sống quanh trường** — bạn thử đặt câu hỏi thuộc các nhóm này nhé!",
        confidence=conf, source=src, provenance="SYSTEM",
        entities=ent,
    )


@app.route("/")
def index():
    return render_template("index.html", map_exists=os.path.exists(MAP_PATH))


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            payload = {}
        raw_msg = payload.get("message", "")
        q = (raw_msg if isinstance(raw_msg, str) else "").strip()
        if not q:
            return jsonify(
                _build_response("GREETING", "Bạn gõ câu hỏi vào khung bên dưới để bé BÊ KA hỗ trợ nhé!", confidence=1.0, source="validation", provenance="SYSTEM")
            )
        if len(q) > 500:
            q = q[:500]
        ctx = analyze_context_keys(q)
        resp = handle_message(q)
        if not resp.get("matched_keys"):
            resp["matched_keys"] = ctx.get("matched_keys", [])
        return jsonify(resp)
    except HTTPException:
        raise            # 413... để errorhandler xử lý đúng mã HTTP
    except Exception as exc:
        app.logger.exception("Chat error: %s", exc)
        return jsonify(
            _build_response("OUT_OF_SCOPE", "Bé BÊ KA vừa gặp trục trặc nhỏ khi xử lý câu này, bạn thử nhắn lại giúp em nhé!", confidence=0.0, source="error_guard", provenance="SYSTEM")
        ), 200


@app.route("/healthz")
def healthz():
    return jsonify({"ok": True, "model_loaded": model is not None})


@app.route("/api/reset", methods=["POST"])
def reset():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/info", methods=["GET"])
def info():
    eval_data = {}
    if os.path.exists(EVAL_PATH):
        with open(EVAL_PATH, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
    return jsonify({
        "version": "Final",
        "model_loaded": model is not None,
        "faq_count": len(FAQ_KB),
        "locations_count": len(LOCATION_LABELS),
        "places_count": len(PLACES_CATALOG),
        "evaluation": eval_data,
    })


if __name__ == "__main__":
    # Cổng mặc định 5000; đổi bằng biến PORT nếu bị chiếm (macOS dùng 5000 cho AirPlay Receiver)
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
