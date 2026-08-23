import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

html_path = Path(__file__).resolve().parent / "workflow.html"
out_path = Path(__file__).resolve().parent / "workflow.png"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium/chrome-linux/chrome" if False else None)
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 1000}, device_scale_factor=2)
    page.goto(f"file://{html_path}")
    page.wait_for_timeout(150)
    page.screenshot(path=str(out_path), full_page=True)
    browser.close()

print(f"Wrote {out_path}")
