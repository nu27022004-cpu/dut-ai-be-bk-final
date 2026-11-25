"""
ui_smoke_test.py — Kiểm thử giao diện bằng Chrome thật (Playwright). KHÔNG bắt buộc để chạy web.

Cài một lần:   pip install playwright && playwright install chromium
Chạy:          python ui_smoke_test.py http://127.0.0.1:5000
               (mở server trước bằng:  python app.py  hoặc  gunicorn app:app)
Biến môi trường tùy chọn:
  CHROME_PATH=/usr/bin/google-chrome   dùng Chrome có sẵn thay cho Chromium của Playwright
  NO_FONTS=1                           chặn Google Fonts (chạy trong môi trường không có internet)
Thoát mã 0 nếu mọi mục đạt.
"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

URL = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000").rstrip("/") + "/"
results = []
js_errors = []


def ok(label, cond, extra=""):
    results.append(bool(cond))
    print(("[PASS] " if cond else "[FAIL] ") + label + (f"  | {extra}" if extra and not cond else ""))


def new_ctx(b, w=1440, h=900, mobile=False, init=None):
    ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile)
    if os.environ.get("NO_FONTS"):
        ctx.route("**/fonts.*/**", lambda r: r.abort())
    if init:
        ctx.add_init_script(init)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: js_errors.append(str(e)))
    return ctx, pg


def start(pg):
    pg.goto(URL)
    pg.click(".splash-btn")
    time.sleep(0.8)


def users(pg):
    return pg.locator(".row.user").count()


def ask(pg, q, wait=".row.bot"):
    n = pg.locator(".row.bot").count()
    pg.fill("#q", q)
    pg.press("#q", "Enter")
    pg.wait_for_function(f"document.querySelectorAll('.row.bot').length>{n}", timeout=15000)
    time.sleep(0.3)


def main():
    launch_kw = {"args": ["--no-sandbox"]}
    if os.environ.get("CHROME_PATH"):
        launch_kw["executable_path"] = os.environ["CHROME_PATH"]
    with sync_playwright() as p:
        b = p.chromium.launch(**launch_kw)

        print("== 1. Splash, gợi ý, font, a11y ==")
        ctx, pg = new_ctx(b)
        reqs = []
        pg.on("request", lambda r: reqs.append(r.url))
        pg.goto(URL, wait_until="networkidle")
        ok("bản đồ không tải khi vào trang", not any("dut_map.png" in u for u in reqs))
        pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=10000)
        ok("splash tự ẩn", True)
        pg.click(".mascot-badge", force=True)
        ok("bấm mascot -> splash hiện lại", pg.evaluate("!document.getElementById('splash').classList.contains('hide')"))
        pg.keyboard.press("Escape")
        time.sleep(0.8)
        ok("Esc đóng splash", pg.evaluate("document.getElementById('splash').classList.contains('hide')"))
        ok("ô nhập tự focus", pg.evaluate("document.activeElement.id") == "q")
        st = pg.evaluate("""(()=>{const c=getComputedStyle(document.querySelector('.btn-send'));
            return [c.fontSize,c.fontWeight,getComputedStyle(document.body).fontFamily.split(',')[0]===c.fontFamily.split(',')[0]]})()""")
        ok("nút Gửi đúng font/cỡ chữ", st[0] == "14px" and st[1] == "700" and st[2], str(st))
        ok("4 ô gợi ý khởi đầu", pg.locator(".hero-tile").count() == 4)
        ok("a11y: nhãn ô nhập + role=log", pg.evaluate("!!document.getElementById('q').getAttribute('aria-label') && document.getElementById('msgs').getAttribute('role')==='log'"))

        print("== 2. Tìm phòng -> chọn cổng -> bản đồ ==")
        ask(pg, "E2.101")
        ok("thẻ giải mã phòng", pg.locator(".room-card").count() == 1)
        ok("ô nhập được xóa sau khi gửi", pg.input_value("#q") == "")
        pg.click(".choices button:has-text('Cổng khu C')")
        pg.wait_for_selector("#routeSvg polyline", timeout=10000)
        time.sleep(0.6)
        ok("bản đồ mở + vẽ tuyến", pg.locator("#routeSvg polyline").count() == 2 and pg.locator("#routeSvg circle").count() == 3)
        ok("ảnh sơ đồ tải được", pg.evaluate("document.querySelector('.map-stage img').naturalWidth") > 0)
        ok("nút chọn cũ bị khóa", pg.locator(".choices button:not([disabled])").count() == 0)
        ok("không tràn ngang", pg.evaluate("document.documentElement.scrollWidth<=innerWidth"))
        ok("ô nhập nằm trong khung nhìn", pg.evaluate("document.getElementById('q').getBoundingClientRect().bottom<=innerHeight"))

        print("== 3. Thẻ quán, lightbox, nút chỉ đường ==")
        ask(pg, "cà phê học bài 24/7")
        pg.wait_for_selector(".place-card")
        time.sleep(1)
        ok("2 thẻ quán, ảnh tải được", pg.locator(".place-card").count() == 2 and pg.evaluate("[...document.querySelectorAll('.place-img')].every(i=>i.naturalWidth>0)"))
        sc = pg.evaluate("(()=>{const m=document.getElementById('msgs');return m.scrollTop+m.clientHeight>=m.scrollHeight-4})()")
        ok("chat cuộn tới đáy sau khi ảnh tải", sc)
        pg.locator(".place-img-box").first.click()
        ok("bấm ảnh mở lightbox", pg.evaluate("!document.getElementById('lightbox').classList.contains('hidden')"))
        pg.keyboard.press("Escape")
        ok("Esc đóng lightbox", pg.evaluate("document.getElementById('lightbox').classList.contains('hidden')"))
        ask(pg, "ăn sáng")
        pg.locator(".place-map-btn").last.click()
        pg.wait_for_function("[...document.querySelectorAll('.choices')].pop().innerText.includes('Cổng')", timeout=10000)
        ok("nút 'Chỉ đường trên bản đồ' hỏi cổng", True)

        print("== 4. Nút cũ, IME, XSS, AI Inspector, theme, reset ==")
        pg.click("text=Cuộc trò chuyện mới")
        time.sleep(0.6)
        ask(pg, "Thư viện ở đâu?")
        ask(pg, "Cổng chính")
        pg.wait_for_selector("#routeSvg polyline")
        ok("trả lời bằng cách gõ thì nút cũ cũng khóa", pg.locator(".choices button:not([disabled])").count() == 0)
        n0 = users(pg)
        pg.fill("#q", "thu vien")
        pg.evaluate("document.getElementById('q').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',isComposing:true,keyCode:229,bubbles:true,cancelable:true}))")
        time.sleep(0.8)
        ok("Enter khi đang gõ IME không gửi", users(pg) == n0)
        pg.evaluate("window.__x=0")
        for payload in ["<img src=x onerror=window.__x=1>", "<script>window.__x=2</script>", "**<img src=x onerror=window.__x=3>**"]:
            pg.fill("#q", payload)
            pg.press("#q", "Enter")
            time.sleep(0.8)
        ok("XSS không chạy", pg.evaluate("window.__x") == 0)
        pg.click("#xaiBtn")
        ok("AI Inspector hiện", pg.locator(".xai").last.is_visible())
        pg.click("#themeBtn")
        pg.reload()
        time.sleep(0.6)
        ok("ban đêm được nhớ sau reload", pg.evaluate("document.documentElement.dataset.theme") == "dark" and pg.inner_text("#themeBtn") == "Tươi sáng")
        pg.click(".splash-btn")          # sau reload splash hiện lại: tắt nó trước khi bấm nút khác
        time.sleep(0.8)
        pg.click("#themeBtn")
        pg.click("text=Cuộc trò chuyện mới")
        time.sleep(0.6)
        ok("reset: còn hero card, bản đồ thu lại", pg.locator(".row").count() == 0 and pg.evaluate("document.getElementById('mapPanel').classList.contains('hidden')"))
        ctx.close()

        print("== 5. Lỗi mạng ==")
        ctx, pg = new_ctx(b)
        start(pg)
        ask(pg, "thư viện ở đâu")
        pg.route("**/api/chat", lambda r: r.abort("connectionrefused"))
        pg.click(".choices button:has-text('Cổng chính')")
        pg.wait_for_function("document.querySelector('.row.bot:last-child') && !document.getElementById('typingRow') && document.querySelector('.row.bot:last-child').innerText.includes('server')", timeout=10000)
        msg = pg.locator(".row.bot").last.inner_text()
        ok("thông báo lỗi dễ hiểu (không nhắc Flask)", "Flask" not in msg and "kết nối" in msg, msg[:60])
        ok("nút lựa chọn và nút Gửi mở lại để thử lại", pg.locator(".choices button:not([disabled])").count() == 3 and not pg.evaluate("document.querySelector('.btn-send').disabled"))
        pg.unroute("**/api/chat")
        pg.locator(".choices button:not([disabled])").first.click()
        pg.wait_for_selector("#routeSvg polyline", timeout=10000)
        ok("thử lại sau khi mạng hồi phục thì ra tuyến", True)
        pg.route("**/api/chat", lambda r: r.fulfill(status=200, content_type="text/html", body="<html>Application loading</html>"))
        ask(pg, "xin chào")
        ok("server trả HTML (đang khởi động) -> báo lỗi, không treo", pg.locator("#typingRow").count() == 0)
        ctx.close()

        print("== 6. Server chậm (giả lập cold start 8s) ==")
        ctx, pg = new_ctx(b, init="""const f=window.fetch.bind(window);window.fetch=(u,o)=>String(u).includes('/api/chat')?new Promise(r=>setTimeout(()=>r(f(u,o)),8000)):f(u,o);""")
        start(pg)
        pg.fill("#q", "giá gửi xe")
        pg.press("#q", "Enter")
        time.sleep(1)
        ok("nút Gửi bị khóa khi đang chờ", pg.evaluate("document.querySelector('.btn-send').disabled"))
        pg.fill("#q", "cảm ơn")
        pg.press("#q", "Enter")
        time.sleep(0.5)
        ok("Enter khi đang chờ bị bỏ qua, chữ gõ dở được giữ", users(pg) == 1 and pg.input_value("#q") == "cảm ơn")
        time.sleep(6)
        ok("sau 6s hiện ghi chú server đang khởi động", pg.locator("#typingRow").count() == 1 and "khởi động" in pg.locator("#typingRow").inner_text())
        pg.wait_for_function("!document.getElementById('typingRow')", timeout=20000)
        ok("thứ tự hội thoại đúng (U,B)", pg.evaluate("[...document.querySelectorAll('.row')].map(r=>r.classList.contains('user')?'U':'B').join('')") == "UB")
        ctx.close()

        print("== 7. Responsive (5 kích thước) ==")
        for w, h, mob in [(1280, 720, False), (1024, 768, False), (768, 1024, False), (390, 844, True), (360, 640, True)]:
            ctx, pg = new_ctx(b, w, h, mob)
            start(pg)
            ok(f"{w}x{h}: trang chủ không tràn ngang, ô nhập thấy ngay", pg.evaluate("document.documentElement.scrollWidth<=innerWidth && document.getElementById('q').getBoundingClientRect().bottom<=innerHeight"))
            ask(pg, "Thư viện ở đâu")
            (pg.tap if mob else pg.click)(".choices button:has-text('Cổng chính')")
            pg.wait_for_selector("#routeSvg polyline")
            time.sleep(2.2)
            m = pg.evaluate("""(()=>{const r=document.getElementById('routeCard').getBoundingClientRect();
                return {w:document.documentElement.scrollWidth,vw:innerWidth,vh:innerHeight,routeBottom:r.bottom,stage:document.querySelector('.map-stage').getBoundingClientRect().width}})()""")
            ok(f"{w}x{h}: có bản đồ không tràn ngang", m["w"] <= m["vw"], str(m))
            if w < 920:
                ok(f"{w}x{h}: thẻ lộ trình hiện trọn trong màn hình sau khi tự cuộn", m["routeBottom"] <= m["vh"], str(m))
            ctx.close()

        ok("không có lỗi JavaScript trong suốt quá trình test", not js_errors, str(js_errors[:3]))
        b.close()

    passed, total = sum(results), len(results)
    print(f"\n{passed}/{total} mục đạt")
    return passed == total


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
