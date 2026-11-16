"""Headless browser check of the explorer page.

Run from lz-event-audit/:  python3 web/smoke_test.py [base_url]
Starts nothing itself: serve the folder first, e.g. python3 -m http.server 8765
"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765/web/index.html"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp"

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    results = {}
    for name, vp in [("desktop", {"width": 1366, "height": 900}), ("mobile", {"width": 390, "height": 844})]:
        pg = br.new_page(viewport=vp, device_scale_factor=2 if name == "mobile" else 1)
        errors = []
        pg.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        pg.goto(BASE + "?b=rodd-higgsino", wait_until="networkidle")
        pg.wait_for_timeout(800)
        read = lambda: {k: pg.inner_text(sel) for k, sel in
                        [("count", "#r-count"), ("sb", "#r-sb"), ("chi", "#r-chi"), ("time", "#r-time"),
                         ("peak", "#r-peak"), ("audit", "#r-audit"), ("verdict", "#verdict")]}
        r = {"rodd": read()}
        pg.screenshot(path=f"{OUT}/explorer-{name}.png", full_page=False)
        # Switch benchmark, change halo, fix cross-section
        pg.select_option("#bench", "baer-barger-500b")
        pg.wait_for_timeout(300)
        r["baer500b"] = read()
        pg.goto(BASE + "?b=fan-reece&s=7.4e-39", wait_until="networkidle")
        pg.wait_for_timeout(500)
        r["fan_common"] = read()
        pg.click("button[data-halo=lz]")
        pg.wait_for_timeout(300)
        r["fan_lz"] = read()
        pg.click("#paper-halo")
        pg.wait_for_timeout(300)
        r["fan_own_halo"] = read()
        # Forbidden point
        pg.goto(BASE + "?m=50&d=400", wait_until="networkidle")
        pg.wait_for_timeout(400)
        r["forbidden"] = read()
        # Map click
        pg.goto(BASE, wait_until="networkidle")
        pg.wait_for_timeout(400)
        pg.locator("#map").scroll_into_view_if_needed()
        pg.wait_for_timeout(300)
        box = pg.locator("#map").bounding_box()
        pg.mouse.click(box["x"] + box["width"] * 0.3, box["y"] + box["height"] * 0.6)
        pg.wait_for_timeout(600)
        r["after_map_click_url"] = pg.url
        pg.locator("#map").scroll_into_view_if_needed()
        pg.screenshot(path=f"{OUT}/explorer-{name}-map.png", full_page=False)
        # Timing of one update
        ms = pg.evaluate("""async () => { const t=performance.now(); const el=document.querySelector('#delta');
            el.value=350; el.dispatchEvent(new Event('input')); await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
            return performance.now()-t; }""")
        r["update_ms"] = round(ms, 1)
        r["errors"] = errors
        results[name] = r
        pg.close()
    br.close()
print(json.dumps(results, indent=1, ensure_ascii=False))
