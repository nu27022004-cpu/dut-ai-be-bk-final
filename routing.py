"""
routing.py — Thuật toán tìm đường ngắn nhất A* (A-Star Search) trên đồ thị
khuôn viên Trường Đại học Bách khoa — Đại học Đà Nẵng (Bản Final).

Hỗ trợ 3 lối vào x 26 địa điểm đích = 78 tuyến đường (bao gồm Tòa nhà E1, E2,
Bánh Mỳ cô Hạnh và Quán Cơm cô Lài khớp chính xác với bản đồ mới).
"""
import heapq
import math
from nlp_utils import LOCATION_LABELS

NODES = {
    # 3 Lối vào chính
    "GATE_MAIN": (495, 535),
    "GATE_C": (795, 365),
    "GATE_E_PARKING": (940, 210),

    # Các nút giao lộ nội bộ & đường Ngô Sĩ Liên
    "J_SOUTH": (540, 480),
    "J_WEST_B": (405, 445),
    "J_C_MID": (660, 405),
    "J_C_EAST": (755, 375),
    "J_GARDEN_N": (555, 315),
    "J_WEST_D": (430, 265),
    "J_A_EAST": (730, 290),
    "J_E_GATE": (875, 235),
    "J_NGO_SI_LIEN": (790, 445),

    # 24 địa điểm trong khuôn viên + 2 quán ăn trên sơ đồ mới
    "LIBRARY": (390, 515),
    "PARKING_S": (350, 480),
    "PARKING_F": (325, 430),
    "BUILDING_B": (455, 445),
    "PARKING_B": (475, 465),
    "GARDEN": (555, 420),
    "LECTURE_F": (440, 375),
    "BUILDING_H": (345, 330),
    "BUILDING_D": (355, 195),
    "BUILDING_A": (595, 200),
    "HC1C": (645, 245),
    "CANTEEN": (695, 305),
    "BUILDING_C": (660, 445),
    "PARKING_STAFF": (635, 495),
    "SMART_BUILDING": (810, 245),
    "OFFICE_CTSV": (810, 245),
    "OFFICE_DAOTAO": (810, 245),
    "OFFICE_FINANCE": (810, 245),
    "BUILDING_E1": (875, 225),
    "BUILDING_E2": (800, 300),
    "BUILDING_E": (835, 265),
    "PARKING_E": (885, 200),
    "FOOTBALL": (935, 330),
    "DORMITORY": (825, 470),
    "DORM_1": (835, 435),
    "DORM_2": (905, 535),
    "DORM_5": (965, 475),

    # 2 quán ăn mới gắn tọa độ trực tiếp theo bản đồ người dùng cập nhật
    "FOOD_BANH_MY_HANH": (858, 292),
    "FOOD_COM_CO_LAI": (845, 495),
}

RAW_EDGES = [
    ("GATE_MAIN", "J_SOUTH"),
    ("GATE_MAIN", "LIBRARY"),
    ("GATE_C", "J_C_EAST"),
    ("GATE_C", "J_NGO_SI_LIEN"),
    ("GATE_C", "FOOTBALL"),
    ("GATE_C", "FOOD_BANH_MY_HANH"),
    ("GATE_E_PARKING", "PARKING_E"),
    ("GATE_E_PARKING", "J_E_GATE"),
    ("GATE_E_PARKING", "FOOD_BANH_MY_HANH"),
    ("J_SOUTH", "BUILDING_B"),
    ("J_SOUTH", "PARKING_B"),
    ("J_SOUTH", "PARKING_STAFF"),
    ("J_SOUTH", "BUILDING_C"),
    ("J_SOUTH", "J_C_MID"),
    ("J_SOUTH", "LIBRARY"),
    ("LIBRARY", "PARKING_S"),
    ("PARKING_S", "PARKING_F"),
    ("PARKING_F", "J_WEST_B"),
    ("J_WEST_B", "BUILDING_B"),
    ("J_WEST_B", "LECTURE_F"),
    ("BUILDING_B", "PARKING_B"),
    ("BUILDING_B", "GARDEN"),
    ("GARDEN", "J_C_MID"),
    ("GARDEN", "J_GARDEN_N"),
    ("LECTURE_F", "J_GARDEN_N"),
    ("LECTURE_F", "BUILDING_H"),
    ("BUILDING_H", "J_WEST_D"),
    ("J_WEST_D", "BUILDING_D"),
    ("J_WEST_D", "J_GARDEN_N"),
    ("J_GARDEN_N", "BUILDING_A"),
    ("J_GARDEN_N", "HC1C"),
    ("J_GARDEN_N", "J_C_MID"),
    ("BUILDING_A", "HC1C"),
    ("HC1C", "CANTEEN"),
    ("HC1C", "J_A_EAST"),
    ("CANTEEN", "J_C_MID"),
    ("CANTEEN", "J_A_EAST"),
    ("J_C_MID", "BUILDING_C"),
    ("J_C_MID", "J_C_EAST"),
    ("J_C_EAST", "J_A_EAST"),
    ("J_C_EAST", "BUILDING_E2"),
    ("J_A_EAST", "SMART_BUILDING"),
    ("J_A_EAST", "BUILDING_E2"),
    ("BUILDING_E2", "BUILDING_E"),
    ("BUILDING_E2", "SMART_BUILDING"),
    ("BUILDING_E2", "FOOD_BANH_MY_HANH"),
    ("BUILDING_E", "BUILDING_E1"),
    ("BUILDING_E1", "FOOD_BANH_MY_HANH"),
    ("SMART_BUILDING", "OFFICE_CTSV"),
    ("SMART_BUILDING", "OFFICE_DAOTAO"),
    ("SMART_BUILDING", "OFFICE_FINANCE"),
    ("SMART_BUILDING", "J_E_GATE"),
    ("BUILDING_E1", "J_E_GATE"),
    ("BUILDING_E1", "PARKING_E"),
    ("J_E_GATE", "PARKING_E"),
    # Khu Ký túc xá & Quán Cơm cô Lài dọc đường Ngô Sĩ Liên
    ("J_NGO_SI_LIEN", "DORMITORY"),
    ("J_NGO_SI_LIEN", "DORM_1"),
    ("J_NGO_SI_LIEN", "FOOD_COM_CO_LAI"),
    ("DORMITORY", "DORM_1"),
    ("DORMITORY", "DORM_2"),
    ("DORMITORY", "DORM_5"),
    ("DORMITORY", "FOOD_COM_CO_LAI"),
    ("FOOD_COM_CO_LAI", "DORM_2"),
    ("FOOD_COM_CO_LAI", "DORM_5"),
    ("DORM_1", "DORM_5"),
    ("DORM_2", "DORM_5"),
]

GRAPH: dict[str, list[tuple[str, float]]] = {k: [] for k in NODES}


def _dist(a: str, b: str) -> float:
    x1, y1 = NODES[a]
    x2, y2 = NODES[b]
    return math.hypot(x2 - x1, y2 - y1)


for u, v in RAW_EDGES:
    w = _dist(u, v)
    GRAPH[u].append((v, w))
    GRAPH[v].append((u, w))

LANDMARK_NAMES = {
    "J_SOUTH": "trục chính gần Thư viện và Khu B",
    "J_WEST_B": "đoạn giữa Khu B và Giảng đường F",
    "J_C_MID": "lối đi dọc Khu C và Sân vườn",
    "J_C_EAST": None,
    "J_GARDEN_N": "vòng xuyến trung tâm trước Khu A",
    "J_WEST_D": "ngã tư giữa Tòa D và Tòa H",
    "J_A_EAST": "khu vực Căng tin A — Smart Building",
    "J_E_GATE": None,
    "J_NGO_SI_LIEN": "đường Ngô Sĩ Liên phía Ký túc xá",
}


def astar_route(start: str, goal: str) -> dict | None:
    if start not in NODES or goal not in NODES:
        return None

    open_heap = [(0.0, 0.0, start, [start])]
    best_g = {start: 0.0}
    expanded = 0

    while open_heap:
        _, g_score, current, path = heapq.heappop(open_heap)
        expanded += 1
        if current == goal:
            points = [{"id": n, "x": NODES[n][0], "y": NODES[n][1]} for n in path]
            est_meters = max(20, int(round(g_score * 0.65)))
            est_minutes = max(1, int(round(est_meters / 75.0)))
            steps, natural_sentence = _describe_path(path, est_minutes)
            return {
                "algorithm": "A* (Euclidean heuristic)",
                "start": start,
                "goal": goal,
                "start_label": LOCATION_LABELS.get(start, start),
                "goal_label": LOCATION_LABELS.get(goal, goal),
                "path": path,
                "points": points,
                "nodes_expanded": expanded,
                "est_meters": est_meters,
                "est_minutes": est_minutes,
                "steps": steps,
                "natural_summary": natural_sentence,
            }

        if g_score > best_g.get(current, float("inf")):
            continue

        for nxt, weight in GRAPH.get(current, []):
            new_g = g_score + weight
            if new_g < best_g.get(nxt, float("inf")):
                best_g[nxt] = new_g
                h = _dist(nxt, goal)
                heapq.heappush(open_heap, (new_g + h, new_g, nxt, path + [nxt]))

    return None


def _describe_path(path: list[str], est_minutes: int) -> tuple[list[str], str]:
    start_lbl = LOCATION_LABELS.get(path[0], path[0])
    goal_lbl = LOCATION_LABELS.get(path[-1], path[-1])

    if len(path) == 1:
        s = f"Bạn đang ở ngay khu vực **{goal_lbl}** rồi nè!"
        return [s], s

    landmarks = []
    for mid in path[1:-1]:
        lm = LANDMARK_NAMES[mid] if mid in LANDMARK_NAMES else LOCATION_LABELS.get(mid)
        if lm and lm not in landmarks and lm != start_lbl and lm != goal_lbl:
            landmarks.append(lm)

    steps = [f"Từ {start_lbl}, di chuyển theo tuyến đã đánh dấu."]
    for lm in landmarks:
        steps.append(f"Đi qua {lm}.")
    steps.append(f"Tới ngay {goal_lbl}.")

    if landmarks:
        via_txt = " rồi qua ".join(landmarks[:2])
        natural = (
            f"Từ **{start_lbl}**, bạn đi qua **{via_txt}** là tới ngay **{goal_lbl}** "
            f"(đi bộ khoảng **{est_minutes} phút**). Mình đã vẽ sẵn tuyến đường màu đỏ trên sơ đồ khuôn viên rồi nha!"
        )
    else:
        natural = (
            f"Gần lắm luôn! Từ **{start_lbl}** bạn đi thẳng một đoạn ngắn là thấy ngay **{goal_lbl}** "
            f"(khoảng **{est_minutes} phút** đi bộ). Xem đường vẽ sẵn trên sơ đồ khuôn viên nhé!"
        )
    return steps, natural
