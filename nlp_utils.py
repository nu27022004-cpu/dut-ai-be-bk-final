"""
nlp_utils.py — Tiền xử lý tiếng Việt, giải mã mã phòng học DUT (E1/E2, Smart Building, A–H)
và Trích xuất thực thể địa điểm & quán ăn trên bản đồ (Bản Final).
"""
import re
import unicodedata

LOCATION_LABELS = {
    "GATE_MAIN": "Cổng chính",
    "GATE_C": "Cổng khu C",
    "GATE_E_PARKING": "Lối vào nhà xe khu E",
    "PARKING_B": "Nhà xe khu B",
    "PARKING_E": "Nhà giữ xe khu E",
    "PARKING_F": "Nhà giữ xe khu F",
    "PARKING_S": "Nhà giữ xe khu S",
    "PARKING_STAFF": "Nhà xe cán bộ",
    "LIBRARY": "Thư viện DUT",
    "DORM_1": "Ký túc xá Nhà 1",
    "DORM_2": "Ký túc xá Nhà 2",
    "DORM_5": "Ký túc xá Nhà 5",
    "DORMITORY": "Khu Ký túc xá",
    "CANTEEN": "Căng tin khu A",
    "FOOTBALL": "Sân bóng đá",
    "GARDEN": "Sân vườn trung tâm",
    "HC1C": "Hành chính Một cửa (HC1C — Khu A)",
    "SMART_BUILDING": "Smart Building (Khu S)",
    "BUILDING_A": "Tòa nhà A",
    "BUILDING_B": "Khu B",
    "BUILDING_C": "Tòa nhà C",
    "BUILDING_D": "Tòa nhà D",
    "BUILDING_E1": "Tòa nhà E1",
    "BUILDING_E2": "Tòa nhà E2",
    "BUILDING_E": "Khu E (Tòa E1 & E2)",
    "BUILDING_H": "Tòa nhà H",
    "LECTURE_F": "Khu Giảng đường F",
    "OFFICE_CTSV": "Phòng Công tác Sinh viên (S06.08)",
    "OFFICE_DAOTAO": "Phòng Đào tạo (S05.08)",
    "OFFICE_FINANCE": "Phòng Tài chính & Kế hoạch (Smart Building)",
    # 2 quán ăn đã được gắn tọa độ trực tiếp trên sơ đồ DUT mới
    "FOOD_BANH_MY_HANH": "Bánh Mỳ cô Hạnh (đường Ngô Sĩ Liên)",
    "FOOD_COM_CO_LAI": "Quán Cơm cô Lài (khu KTX — Ngô Sĩ Liên)",
}

DESTINATION_PATTERNS = [
    ("FOOD_BANH_MY_HANH", ["banh my co hanh", "banh mi co hanh", "co hanh"]),
    ("FOOD_COM_CO_LAI", ["com co lai", "quan co lai", "co lai"]),
    ("OFFICE_CTSV", ["phong cong tac sinh vien", "phong ctsv", "ctsv", "s06.08", "s0608"]),
    ("OFFICE_DAOTAO", ["phong dao tao", "s05.08", "s0508"]),
    ("OFFICE_FINANCE", ["phong tai chinh", "phong ke hoach tai chinh", "ke hoach tai chinh"]),
    ("SMART_BUILDING", ["smart building", "smartbuilding", "khu s", "toa nha s"]),
    ("HC1C", ["hc1c", "hanh chinh mot cua", "hanh chinh 1 cua", "mot cua"]),
    ("PARKING_STAFF", ["nha xe can bo", "bai xe can bo", "nha giu xe can bo"]),
    ("PARKING_B", ["nha xe khu b", "nha giu xe khu b", "nha xe b", "bai xe khu b", "bai gui xe khu b", "bai giu xe khu b", "gui xe o khu b", "gui xe khu b"]),
    ("PARKING_E", ["nha xe khu e", "nha giu xe khu e", "nha xe e", "bai xe khu e", "bai gui xe khu e", "gui xe o khu e", "gui xe khu e"]),
    ("PARKING_F", ["nha xe khu f", "nha giu xe khu f", "nha xe f", "bai xe khu f", "bai gui xe khu f", "gui xe o khu f", "gui xe khu f"]),
    ("PARKING_S", ["nha xe khu s", "nha giu xe khu s", "nha xe s", "bai xe khu s", "bai gui xe khu s", "gui xe o khu s", "gui xe khu s"]),
    ("DORM_5", ["ky tuc xa nha 5", "ktx nha 5", "nha 5 ky tuc xa", "nha 5 ktx"]),
    ("DORM_2", ["ky tuc xa nha 2", "ktx nha 2", "nha 2 ky tuc xa", "nha 2 ktx"]),
    ("DORM_1", ["ky tuc xa nha 1", "ktx nha 1", "nha 1 ky tuc xa", "nha 1 ktx"]),
    ("DORMITORY", ["ky tuc xa", "ktx"]),
    ("LIBRARY", ["thu vien"]),
    ("CANTEEN", ["can tin", "cang tin", "canteen"]),
    ("FOOTBALL", ["san bong da", "san bong"]),
    ("GARDEN", ["san vuon"]),
    ("LECTURE_F", ["khu giang duong f", "giang duong f", "khu f", "toa nha f"]),
    ("BUILDING_E1", ["toa nha e1", "toa e1", "nha e1", "khu e1"]),
    ("BUILDING_E2", ["toa nha e2", "toa e2", "nha e2", "khu e2"]),
    ("BUILDING_A", ["toa nha a", "khu a", "nha a"]),
    ("BUILDING_B", ["toa nha b", "khu b", "nha b"]),
    ("BUILDING_C", ["toa nha c", "khu c", "nha c"]),
    ("BUILDING_D", ["toa nha d", "khu d", "nha d"]),
    ("BUILDING_E", ["toa nha e", "khu e", "nha e"]),
    ("BUILDING_H", ["toa nha h", "khu h", "nha h"]),
]

VALID_BUILDING_PREFIXES = {
    "A": "BUILDING_A",
    "B": "BUILDING_B",
    "C": "BUILDING_C",
    "D": "BUILDING_D",
    "E": "BUILDING_E",
    "F": "LECTURE_F",
    "H": "BUILDING_H",
    "S": "SMART_BUILDING",
}


def norm(s: str) -> str:
    """Chuẩn hóa chữ thường, bỏ dấu tiếng Việt, chuyển đ->d và giữ dấu chấm/gạch mã phòng."""
    if not s:
        return ""
    s = str(s).lower().strip()
    s = "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )
    s = s.replace("đ", "d")
    s = re.sub(r"[^\w\s\.\-\/]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def preprocess_for_ml(text: str) -> str:
    raw = re.sub(r"\s+", " ", str(text).lower().strip())
    unaccented = norm(text)
    if raw == unaccented:
        return unaccented
    return f"{raw} {unaccented}"


def _room_order_phrase(num: int, suffix: str = "") -> str:
    suf = f" (nhánh {suffix})" if suffix else ""
    if num == 1:
        return f"phòng đầu tiên (số 01){suf}"
    return f"phòng thứ {num} (số {num:02d}){suf}"


def parse_room(dest_text: str) -> dict | None:
    """Giải mã chi tiết mã phòng học DUT: E1/E2 (E2.101), Smart Building (S05.08), Khu A–H (C301)."""
    # 1. Khu E1 / E2: E1.101, E2.101, E2-203, E1 104, E2101
    m_e = re.search(r"\b(e[12])[\.\-\s]?(\d)(\d{2})([a-z]?)\b", dest_text)
    if m_e:
        bldg_code = m_e.group(1).upper()
        floor = int(m_e.group(2))
        rnum = int(m_e.group(3))
        suf = m_e.group(4).upper()
        code = f"{bldg_code}.{floor}{rnum:02d}{suf}"
        bldg_id = f"BUILDING_{bldg_code}"
        bldg_name = LOCATION_LABELS[bldg_id]
        order_txt = _room_order_phrase(rnum, suf)
        return {
            "code": code,
            "building_id": bldg_id,
            "building_name": bldg_name,
            "floor": floor,
            "room_num": rnum,
            "room_order": order_txt,
            "summary": f"Phòng **{code}** nằm ở **{bldg_name}**, **tầng {floor}**, {order_txt}.",
        }

    # 2. Smart Building: S05.08, S06.08
    m_s = re.search(r"\b(s)(\d{2})\.(\d{2})\b", dest_text)
    if m_s:
        floor = int(m_s.group(2))
        rnum = int(m_s.group(3))
        code = f"S{floor:02d}.{rnum:02d}"
        if code == "S05.08":
            bldg_id, bldg_name = "OFFICE_DAOTAO", "Smart Building — Phòng Đào tạo"
        elif code == "S06.08":
            bldg_id, bldg_name = "OFFICE_CTSV", "Smart Building — Phòng Công tác Sinh viên"
        else:
            bldg_id, bldg_name = "SMART_BUILDING", "Smart Building (Khu S)"
        order_txt = _room_order_phrase(rnum)
        return {
            "code": code,
            "building_id": bldg_id,
            "building_name": bldg_name,
            "floor": floor,
            "room_num": rnum,
            "room_order": order_txt,
            "summary": f"Phòng **{code}** nằm ở **{bldg_name}**, **tầng {floor}**, {order_txt}.",
        }

    # 3. Các khu giảng đường tiêu chuẩn: C301, B101, C102B, A 204, F101
    m_std = re.search(r"\b([a-dfh])[\.\-\s]?(\d)(\d{2})([a-z]?)\b", dest_text)
    if m_std:
        prefix = m_std.group(1).upper()
        floor = int(m_std.group(2))
        rnum = int(m_std.group(3))
        suf = m_std.group(4).upper()
        code = f"{prefix}{floor}{rnum:02d}{suf}"
        bldg_id = VALID_BUILDING_PREFIXES[prefix]
        bldg_name = LOCATION_LABELS[bldg_id]
        order_txt = _room_order_phrase(rnum, suf)
        return {
            "code": code,
            "building_id": bldg_id,
            "building_name": bldg_name,
            "floor": floor,
            "room_num": rnum,
            "room_order": order_txt,
            "summary": f"Phòng **{code}** thuộc **{bldg_name}**, **tầng {floor}**, {order_txt}.",
        }

    return None


def _has_term(text: str, term: str) -> bool:
    """Khớp nguyên cụm (không khớp chuỗi con): 'nha h' không khớp 'nha hang'."""
    return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None


def extract_gate(text: str, allow_standalone: bool = False) -> str | None:
    n = norm(text)
    if any(_has_term(n, x) for x in ["cong chinh", "loi vao gan thu vien", "cong nguyen luong bang"]):
        return "GATE_MAIN"
    if allow_standalone and n in {"chinh", "cong 1", "1"}:
        return "GATE_MAIN"

    if any(_has_term(n, x) for x in ["cong khu c", "loi vao khu c", "loi vao toa nha c", "cong c"]):
        return "GATE_C"
    if allow_standalone and n in {"khu c", "toa c", "c", "2"}:
        return "GATE_C"

    if any(_has_term(n, x) for x in ["loi vao nha xe khu e", "loi nha xe khu e", "loi vao khu e", "cong khu e", "cong e"]):
        return "GATE_E_PARKING"
    if "nha xe khu e" in n and (allow_standalone or any(x in n for x in ["di tu", "tu ", "loi vao", "loi ", "vao tu", "xuat phat"])):
        return "GATE_E_PARKING"
    if allow_standalone and n in {"khu e", "e", "3"}:
        return "GATE_E_PARKING"

    return None


def _strip_origin_clause(n: str) -> str:
    m = re.search(r"(?:di\s+)?tu\s+.+?\s+(?:den|toi|qua|sang|ve|ra)\s+(.+)", n)
    if m:
        return m.group(1).strip()

    cleaned = n
    origin_phrases = [
        "loi vao nha xe khu e",
        "loi nha xe khu e",
        "di tu nha xe khu e",
        "tu nha xe khu e",
        "loi vao khu e",
        "loi vao toa nha c",
        "cong khu c",
        "cong chinh",
        "loi vao gan thu vien",
    ]
    for p in origin_phrases:
        cleaned = cleaned.replace(p, " ")
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_entities(text: str) -> dict:
    n = norm(text)
    gate = extract_gate(text, allow_standalone=False)
    dest_text = _strip_origin_clause(n) if gate else n

    room_info = parse_room(dest_text)
    room_code = room_info["code"] if room_info else None
    dest = room_info["building_id"] if room_info else None

    if not dest:
        for code, terms in DESTINATION_PATTERNS:
            if any(_has_term(dest_text, t) for t in terms):
                dest = code
                break

    return {
        "room_code": room_code,
        "room_info": room_info,
        "destination": dest,
        "destination_label": LOCATION_LABELS.get(dest) if dest else None,
        "gate": gate,
        "gate_label": LOCATION_LABELS.get(gate) if gate else None,
    }
