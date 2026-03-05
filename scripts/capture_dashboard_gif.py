from pathlib import Path
import time

from PIL import Image
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

frames = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8501", wait_until="networkidle")
    page.wait_for_timeout(2500)

    # Frame 1: default view
    f1 = ASSETS / "dashboard-frame-1.png"
    page.screenshot(path=str(f1), full_page=True)
    frames.append(f1)

    # Frame 2: Performance Metrics
    try:
        page.get_by_text("Performance Metrics", exact=True).click()
        page.wait_for_timeout(2000)
        f2 = ASSETS / "dashboard-frame-2.png"
        page.screenshot(path=str(f2), full_page=True)
        frames.append(f2)
    except Exception:
        pass

    # Frame 3: Historical Data
    try:
        page.get_by_text("Historical Data", exact=True).click()
        page.wait_for_timeout(2000)
        f3 = ASSETS / "dashboard-frame-3.png"
        page.screenshot(path=str(f3), full_page=True)
        frames.append(f3)
    except Exception:
        pass

    browser.close()

images = [Image.open(frame).convert("P", palette=Image.ADAPTIVE) for frame in frames if frame.exists()]
if images:
    gif_path = ASSETS / "dashboard-demo.gif"
    images[0].save(
        gif_path,
        save_all=True,
        append_images=images[1:],
        duration=1100,
        loop=0,
        optimize=True,
    )
    print(f"GIF created: {gif_path}")
else:
    raise RuntimeError("No frames captured. Could not create GIF.")
