"""
keyword_engine.py — Thuật toán trích xuất & chấm điểm từ khóa ngữ cảnh (Context-Aware
Weighted Keyword Disambiguation + Fuzzy Typo Matching) cho DUT AI Student Assistant.

Mục tiêu:
- Tách bạch rõ THỰC THỂ (Entity: HC1C, Thư viện, Nhà xe, Bánh Mỳ cô Hạnh, Cơm cô Lài, phòng E2.101...)
  khỏi Ý ĐỊNH HÀNH ĐỘNG (Action/Context Keys: đi tới/vị trí vs giờ mở cửa vs giá cả vs thủ tục).
- Chống lỗi chính tả tiếng Việt phổ biến (VD: "bản điểm" -> "bảng điểm", "học pji" -> "học phí")
  bằng so khớp mờ (Fuzzy SequenceMatcher trên n-gram).
- Hỗ trợ phát hiện CÂU HỎI KÉP (VD: "tôi muốn tới phòng HC1C và HC1C mở cửa lúc mấy giờ")
  để trả lời đủ cả 2 ý trong cùng 1 lượt.
"""
import re
from difflib import SequenceMatcher
from nlp_utils import norm

# Từ điển sửa lỗi chính tả ngữ cảnh phổ biến của sinh viên (fuzzy + exact)
FUZZY_CANONICAL_TERMS = [
    "bang diem",
    "hoc phi",
    "thu vien",
    "ky tuc xa",
    "hanh chinh mot cua",
    "cong tac sinh vien",
    "hoan nghia vu",
    "xac nhan sinh vien",
    "rut hoc ba",
    "rut ho so",
    "banh my co hanh",
    "com co lai",
    "cong vien lien chieu",
    "photo thanh cong",
    "photo tai nguyen",
    "zone six",
    "smart building",
    "study cafe",
]

# Các nhóm từ khóa hành động / ngữ cảnh có trọng số (Weighted Context Keys)
CONTEXT_KEY_GROUPS: dict[str, list[tuple[str, float]]] = {
    "ACTION_ROUTE": [
        ("chi duong", 3.5), ("tim duong", 3.5), ("di duong nao", 3.5),
        ("di tu", 3.5), ("tu cong", 3.5), ("loi vao", 3.0),
        ("muon toi", 3.4), ("muon den", 3.4), ("muon qua", 3.0), ("muon ra", 2.8),
        ("toi phong", 3.4), ("den phong", 3.4), ("tim phong", 3.4),
        ("den nha xe", 3.4), ("den thu vien", 3.4), ("den ktx", 3.4),
        ("den ky tuc xa", 3.4), ("den can tin", 3.4), ("den khu", 3.2),
        ("den toa", 3.2), ("den hc1c", 3.4), ("toi hc1c", 3.4),
        ("den smart", 3.4), ("ra banh", 3.2), ("den banh", 3.2),
        ("qua com", 3.2), ("den com", 3.2), ("ban do", 3.0),
        ("nam o dau", 3.0), ("nam cho nao", 3.0), ("o dau", 2.2),
        ("tang may", 3.0), ("toa nao", 3.0), ("khu nao", 2.6),
    ],
    "ACTION_HOURS": [
        ("gio lam viec", 4.0), ("lam viec luc nao", 4.0), ("lam viec may gio", 4.0),
        ("mo cua luc may gio", 4.2), ("mo cua may gio", 4.2), ("gio mo cua", 4.2),
        ("dong cua may gio", 4.0), ("gio phuc vu", 4.0), ("mo cua", 3.5),
        ("dong cua", 3.5), ("may gio", 3.2), ("co lam viec", 3.6),
        ("co lam ko", 3.6), ("lam viec", 3.0), ("thu 7", 2.5), ("t7", 2.4),
        ("thu bay", 2.5), ("chu nhat", 2.5), ("cn", 2.2),
    ],
    "ACTION_PRICE": [
        ("bao nhieu tien", 4.0), ("bao nhieu", 3.4), ("bao nhiu", 3.4),
        ("bnhiu", 3.5), ("may nghin", 3.5), ("gia bao nhieu", 4.0),
        ("gia gui xe", 4.2), ("phi gui xe", 4.2), ("gia ve xe", 4.0),
        ("gia nuoc", 3.8), ("gia mon", 3.6), ("ban gi", 3.2),
        ("co ban", 2.8), ("mien phi", 3.4), ("free", 3.2),
        ("17k", 3.0), ("20k", 3.0), ("30k", 3.0), ("7 tieng", 3.6), ("10 tieng", 3.6),
    ],
    "ACTION_ADMIN": [
        ("xin giay", 3.8), ("lay giay", 3.8), ("cap giay", 3.8),
        ("xac nhan sinh vien", 4.2), ("chung nhan sinh vien", 4.2), ("xnsv", 4.2),
        ("hoan nghia vu", 4.2), ("nvqs", 4.2), ("giay hoan", 4.0),
        ("bang diem", 3.8), ("ban diem", 3.8),
        ("rut hoc ba", 4.4), ("muon hoc ba", 4.4), ("hoc ba", 3.8),
        ("rut ho so", 4.4), ("ho so sinh vien", 4.2), ("thoi hoc", 4.2),
        ("bao luu", 4.2), ("nghi hoc tam thoi", 4.2), ("chuyen nganh", 4.0),
        ("the sinh vien", 4.0), ("mien giam", 4.0), ("vay von", 4.0),
        ("sai diem", 4.4), ("nhap nham", 4.0), ("phuc khao", 4.4),
        ("hoc bong", 3.8), ("diem ren luyen", 3.8), ("cong tac sinh vien", 3.6),
        ("dong hoc phi", 4.0), ("nop hoc phi", 4.0), ("thanh toan hoc phi", 4.0),
        ("khoan thu", 3.8),
    ],
    "ACTION_HOC_VU": [
        ("lich hoc", 4.0), ("lich thi", 4.0), ("thoi khoa bieu", 4.2), ("tkb", 4.2),
        ("ddut", 4.2), ("dang ky hoc phan", 4.2), ("dang ky tin chi", 4.2),
        ("nam nhat", 3.6), ("ky dau", 3.6), ("hoc ky dau", 3.6),
        ("ky 2", 3.4), ("hoc ky 2", 3.4), ("ai xep lich", 4.0),
        ("tinh hoc phi", 4.2), ("hoc phi tinh", 4.2), ("don gia", 3.6),
    ],
    "ACTION_LIFESTYLE": [
        ("an sang", 3.8), ("sang nay", 3.2), ("buoi sang", 3.2), ("do an sang", 3.8),
        ("an trua", 3.8), ("trua nay", 3.2), ("buoi trua", 3.2), ("com trua", 3.8),
        ("quan com", 3.6), ("quan an", 3.6), ("an uong", 3.6),
        ("ca phe", 3.8), ("cafe", 3.8), ("cf", 3.5), ("24/7", 4.0), ("247", 3.8),
        ("zone 6", 4.2), ("zone six", 4.2), ("tram 247", 4.2), ("study cafe", 4.2),
        ("chay deadline", 4.0), ("chay dl", 4.0), ("xuyen dem", 3.8), ("thau dem", 3.8),
        ("photo", 3.8), ("photocopy", 3.8), ("in an", 3.8), ("in do an", 4.0),
        ("in bao cao", 4.0), ("tai lieu", 3.6), ("giao trinh", 3.6),
        ("cong vien", 4.0), ("lien chieu", 4.0), ("nguyen sinh sac", 4.0),
        ("tap the duc", 3.8), ("chay bo", 3.8), ("the thao", 3.4), ("vui choi", 3.4),
        ("cau lac bo", 4.0), ("clb", 4.0), ("pioneer", 4.0), ("bkmedia", 4.0),
        ("sclub", 4.0), ("bkmaker", 4.0), ("ctxh", 4.0), ("cong tac xa hoi", 4.0),
    ],
}


def fuzzy_normalize_query(text: str) -> tuple[str, list[str]]:
    """
    Sửa nhẹ lỗi gõ tiếng Việt trên cụm 2–3 từ (VD: 'ban diem' -> 'bang diem',
    'thu vienn' -> 'thu vien') bằng SequenceMatcher ngưỡng cao (>= 0.86) để
    không làm biến dạng từ bình thường.
    """
    n = norm(text)
    n = re.sub(r"\bhc\s+1\s*c\b", "hc1c", n)     # "hc 1c" -> "hc1c"
    toks = n.split()
    corrections = []
    if len(toks) < 2:
        return n, corrections

    fixed_text = n
    for term in FUZZY_CANONICAL_TERMS:
        if term in fixed_text:
            continue
        t_len = len(term.split())
        if len(toks) < t_len:
            continue
        for i in range(len(toks) - t_len + 1):
            window = " ".join(toks[i : i + t_len])
            if abs(len(window) - len(term)) > 2:
                continue
            ratio = SequenceMatcher(None, window, term).ratio()
            # Cả cụm phải giống >= 0.85 VÀ từng từ phải gần với từ chuẩn tương ứng (>= 0.6),
            # để "cho tan sinh vien" không bị sửa nhầm thành "cong tac sinh vien".
            words_ok = all(
                SequenceMatcher(None, w, tw).ratio() >= 0.6
                for w, tw in zip(window.split(), term.split())
            )
            if ratio >= 0.85 and words_ok:
                fixed_text = fixed_text.replace(window, term, 1)
                corrections.append(f"{window}->{term}")
                break
    return fixed_text, corrections


def analyze_context_keys(text: str) -> dict:
    """
    Chấm điểm tất cả nhóm từ khóa ngữ cảnh trên câu hỏi.
    Trả về:
      - normalized: chuỗi đã chuẩn hóa + sửa lỗi chính tả mờ
      - corrections: danh sách lỗi gõ đã tự sửa
      - scores: điểm số từng nhóm ACTION_*
      - matched_keys: danh sách từ khóa khớp được (dùng để giải thích trong AI Inspector)
      - is_dual_hc1c: True nếu người dùng hỏi CẢ đường tới HC1C VÀ giờ mở cửa HC1C
    """
    n, corrections = fuzzy_normalize_query(text)
    scores: dict[str, float] = {k: 0.0 for k in CONTEXT_KEY_GROUPS}
    matched_by_group: dict[str, list[str]] = {k: [] for k in CONTEXT_KEY_GROUPS}

    for group, pairs in CONTEXT_KEY_GROUPS.items():
        for kw, weight in pairs:
            if kw in n:
                scores[group] += weight
                matched_by_group[group].append(kw)

    all_matched = []
    for g, kws in matched_by_group.items():
        if kws:
            all_matched.append(f"{g.replace('ACTION_', '')}:{kws[0]}")

    has_hc1c = any(x in n for x in ["hc1c", "hanh chinh mot cua", "hanh chinh 1 cua", "mot cua"])
    is_dual_hc1c = has_hc1c and scores["ACTION_ROUTE"] >= 2.5 and scores["ACTION_HOURS"] >= 3.0

    return {
        "normalized": n,
        "corrections": corrections,
        "scores": scores,
        "matched_by_group": matched_by_group,
        "matched_keys": all_matched,
        "is_dual_hc1c": is_dual_hc1c,
    }
