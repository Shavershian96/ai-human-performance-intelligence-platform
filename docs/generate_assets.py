"""
Generate all visual assets for the AI Human Performance Intelligence Platform.
Creates: banner.png, demo.gif, grafana-screenshot.png, prometheus-screenshot.png
"""

import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
TEAL = "#00d4aa"
ORANGE = "#f4a400"
BG_DARK = "#0d1117"
BG_CARD = "#161b22"
BG_PANEL = "#181b1f"
WHITE = "#ffffff"
GRAY = "#8b949e"
GREEN = "#3fb950"
BLUE = "#326ce5"
DIVIDER = "#21262d"


def hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c*2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def blend(color_hex, alpha, bg_hex="#0d1117"):
    """Blend color with alpha over background."""
    fg = hex_to_rgb(color_hex)
    bg = hex_to_rgb(bg_hex)
    return tuple(int(fg[i] * alpha + bg[i] * (1 - alpha)) for i in range(3))


def load_font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/ArialBD.TTF" if bold else "C:/Windows/Fonts/Arial.TTF",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_grid(draw, w, h, spacing=40, color="#1a2332"):
    rgb = hex_to_rgb(color)
    for x in range(0, w, spacing):
        draw.line([(x, 0), (x, h)], fill=rgb, width=1)
    for y in range(0, h, spacing):
        draw.line([(0, y), (w, y)], fill=rgb, width=1)


def draw_box(draw, x, y, w, h, label, font, border_color=TEAL, text_color=WHITE):
    draw.rectangle([x, y, x+w, y+h], fill=hex_to_rgb(BG_CARD))
    draw.rectangle([x, y, x+w, y+h], outline=hex_to_rgb(border_color), width=2)
    bbox = font.getbbox(label)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = x + (w - tw) // 2
    ty = y + (h - th) // 2
    draw.text((tx, ty), label, fill=hex_to_rgb(text_color), font=font)


def draw_arrow_down(draw, x, y1, y2, color=TEAL):
    rgb = hex_to_rgb(color)
    draw.line([(x, y1), (x, y2-6)], fill=rgb, width=2)
    draw.polygon([(x-5, y2-6), (x+5, y2-6), (x, y2)], fill=rgb)


def draw_dashed_line(draw, x0, y0, x1, y1, color=ORANGE, dash=8):
    rgb = hex_to_rgb(color)
    dx = x1 - x0
    dy = y1 - y0
    length = math.sqrt(dx*dx + dy*dy)
    if length == 0:
        return
    steps = int(length / (dash * 2))
    for i in range(steps):
        t0 = (i * 2 * dash) / length
        t1 = min(((i * 2 + 1) * dash) / length, 1.0)
        sx = int(x0 + t0 * dx)
        sy = int(y0 + t0 * dy)
        ex = int(x0 + t1 * dx)
        ey = int(y0 + t1 * dy)
        draw.line([(sx, sy), (ex, ey)], fill=rgb, width=2)


# ─── BANNER ────────────────────────────────────────────────────────────────────

def make_banner():
    W, H = 1280, 640
    img = Image.new("RGB", (W, H), hex_to_rgb(BG_DARK))
    draw = ImageDraw.Draw(img)

    draw_grid(draw, W, H, spacing=40, color="#141d29")

    draw.rectangle([0, 0, 4, H], fill=hex_to_rgb(TEAL))
    draw.rectangle([638, 0, 640, H], fill=hex_to_rgb("#1c2d3f"))

    font_tiny = load_font(12)
    font_sm = load_font(14)
    font_md = load_font(18)
    font_lg = load_font(32, bold=True)
    font_xl = load_font(48, bold=True)

    draw.text((30, 60), "Architecture", fill=hex_to_rgb(GRAY), font=font_sm)

    boxes = [
        (30, 110, 200, 44, "Data Ingestion", TEAL),
        (30, 195, 230, 44, "PostgreSQL + PgBouncer", TEAL),
        (30, 280, 200, 44, "ML Trainer", TEAL),
        (30, 365, 200, 44, "Predictions API", TEAL),
        (30, 450, 200, 44, "Dashboard :8501", TEAL),
    ]
    for (bx, by, bw, bh, label, col) in boxes:
        draw_box(draw, bx, by, bw, bh, label, font_sm, border_color=col)

    for i in range(len(boxes)-1):
        bx, by, bw, bh = boxes[i][:4]
        _, ny = boxes[i+1][:2]
        cx = bx + bw // 2
        draw_arrow_down(draw, cx, by+bh, ny, color=TEAL)

    draw_box(draw, 270, 280, 150, 44, "Prometheus", font_sm, border_color=ORANGE)
    draw_box(draw, 270, 365, 150, 44, "Grafana", font_sm, border_color=ORANGE)

    api_bx, api_by, api_bw, api_bh = boxes[3][:4]
    draw_dashed_line(draw, api_bx+api_bw, api_by+api_bh//2, 270, 280+22)
    draw_dashed_line(draw, api_bx+api_bw, api_by+api_bh//2, 270, 365+22)
    draw.line([(345, 324), (345, 365)], fill=hex_to_rgb(ORANGE), width=2)

    # Right side
    rx = 680
    title1 = "AI Performance"
    title2 = "Intelligence Platform"
    sub = "Production ML  .  FastAPI  .  Kubernetes  .  Prometheus"

    draw.text((rx + 20, 160), title1, fill=hex_to_rgb(WHITE), font=font_xl)
    draw.text((rx + 20, 215), title2, fill=hex_to_rgb(WHITE), font=font_xl)
    draw.text((rx + 20, 285), sub, fill=hex_to_rgb(TEAL), font=font_md)

    badges = [
        ("Python 3.11", "#306998"),
        ("FastAPI", "#009688"),
        ("PostgreSQL", "#336791"),
        ("Kubernetes", "#326ce5"),
        ("Grafana", "#f46800"),
    ]
    bx_pos = rx + 20
    by_pos = 330
    for label, bg in badges:
        bbox = font_sm.getbbox(label)
        bw = bbox[2] - bbox[0] + 20
        bh = 28
        draw.rounded_rectangle([bx_pos, by_pos, bx_pos+bw, by_pos+bh], radius=14, fill=hex_to_rgb(bg))
        draw.text((bx_pos+10, by_pos+7), label, fill=hex_to_rgb(WHITE), font=font_tiny)
        bx_pos += bw + 10

    tag = "Built for Production  .  DACH Region  .  Senior Platform Engineering"
    draw.text((rx + 20, 500), tag, fill=hex_to_rgb(GRAY), font=font_sm)

    for i, col in enumerate([TEAL, ORANGE, "#5794f2"]):
        draw.ellipse([W - 60 + i*18, 20, W - 46 + i*18, 34], fill=hex_to_rgb(col))

    img.save(OUT / "banner.png", "PNG")
    print(f"banner.png: {(OUT/'banner.png').stat().st_size:,} bytes")


# ─── GIF FRAMES ────────────────────────────────────────────────────────────────

def make_header(draw, W, frame_label, font_sm, font_tiny):
    draw.rectangle([0, 0, W, 44], fill=hex_to_rgb(BG_CARD))
    draw.text((16, 12), "AI Performance Intelligence Platform", fill=hex_to_rgb(WHITE), font=font_sm)
    draw.ellipse([W-130, 15, W-118, 27], fill=hex_to_rgb(GREEN))
    draw.text((W-113, 12), "Live", fill=hex_to_rgb(GREEN), font=font_tiny)
    draw.text((W-75, 12), frame_label, fill=hex_to_rgb(GRAY), font=font_tiny)
    draw.line([(0, 44), (W, 44)], fill=hex_to_rgb(DIVIDER), width=1)


def frame_overview(W, H, fonts):
    img = Image.new("RGB", (W, H), hex_to_rgb(BG_DARK))
    draw = ImageDraw.Draw(img)
    draw_grid(draw, W, H, spacing=30, color="#111820")
    font_tiny, font_sm, font_md, font_lg, font_xl = fonts

    make_header(draw, W, "1/8 Overview", font_sm, font_tiny)

    kpis = [("247", "Athletes"), ("1,842", "Predictions"), ("94.3%", "Model Accuracy"), ("12ms", "Avg Response")]
    card_w = (W - 60) // 4
    card_h = 130
    cy = 80
    for i, (val, label) in enumerate(kpis):
        cx = 15 + i * (card_w + 15)
        draw.rounded_rectangle([cx, cy, cx+card_w, cy+card_h], radius=8, fill=hex_to_rgb(BG_CARD))
        draw.rounded_rectangle([cx, cy, cx+card_w, cy+4], radius=2, fill=hex_to_rgb(TEAL))
        bbox = font_lg.getbbox(val)
        vw = bbox[2]-bbox[0]
        draw.text((cx + (card_w-vw)//2, cy+20), val, fill=hex_to_rgb(TEAL), font=font_lg)
        bbox = font_tiny.getbbox(label)
        lw = bbox[2]-bbox[0]
        draw.text((cx + (card_w-lw)//2, cy+65), label, fill=hex_to_rgb(GRAY), font=font_tiny)

    draw.text((W//2-160, 240), "Production ML Platform -- All Systems Operational", fill=hex_to_rgb(WHITE), font=font_sm)
    draw.text((W//2-80, 270), "4 microservices  .  PostgreSQL  .  Kubernetes", fill=hex_to_rgb(GRAY), font=font_tiny)
    draw.text((W//2-100, H-25), "All Systems Operational", fill=hex_to_rgb(TEAL), font=font_tiny)
    return img


def frame_latency_chart(W, H, fonts):
    img = Image.new("RGB", (W, H), hex_to_rgb(BG_DARK))
    draw = ImageDraw.Draw(img)
    draw_grid(draw, W, H, spacing=30, color="#111820")
    font_tiny, font_sm, font_md, font_lg, font_xl = fonts

    make_header(draw, W, "2/8 Latency", font_sm, font_tiny)
    draw.text((20, 55), "Prediction Latency Over Time (Last 60 min)", fill=hex_to_rgb(WHITE), font=font_sm)

    cx0, cy0, cx1, cy1 = 70, 80, W-30, H-60
    chart_w = cx1 - cx0
    chart_h = cy1 - cy0
    draw.rectangle([cx0, cy0, cx1, cy1], fill=hex_to_rgb("#0a0e16"))

    for i in range(5):
        y = cy0 + i * chart_h // 4
        draw.line([(cx0, y), (cx1, y)], fill=hex_to_rgb("#1c2333"), width=1)
        ms_val = 50 - i * 12
        draw.text((cx0-40, y-6), f"{ms_val}ms", fill=hex_to_rgb(GRAY), font=font_tiny)

    N = 60
    random.seed(42)
    p50 = [12 + 3*math.sin(i*0.3) + random.uniform(-1, 1) for i in range(N)]
    p95 = [25 + 4*math.sin(i*0.2 + 1) + random.uniform(-2, 2) for i in range(N)]

    def y_to_px(val):
        return int(cy1 - (val / 50) * chart_h)

    def x_to_px(i):
        return int(cx0 + (i / (N-1)) * chart_w)

    poly_p50 = [(x_to_px(i), y_to_px(p50[i])) for i in range(N)]
    poly_p50_filled = poly_p50 + [(cx1, cy1), (cx0, cy1)]
    fill_color = blend(TEAL, 0.15, BG_DARK)
    draw.polygon(poly_p50_filled, fill=fill_color)
    for i in range(N-1):
        draw.line([poly_p50[i], poly_p50[i+1]], fill=hex_to_rgb(TEAL), width=2)

    poly_p95 = [(x_to_px(i), y_to_px(p95[i])) for i in range(N)]
    for i in range(N-1):
        draw.line([poly_p95[i], poly_p95[i+1]], fill=hex_to_rgb(ORANGE), width=2)

    for i in [0, 15, 30, 45, 59]:
        draw.text((x_to_px(i)-10, cy1+5), f"{60-i}m", fill=hex_to_rgb(GRAY), font=font_tiny)

    draw.ellipse([cx0+10, cy0+8, cx0+22, cy0+20], fill=hex_to_rgb(TEAL))
    draw.text((cx0+26, cy0+6), "p50", fill=hex_to_rgb(TEAL), font=font_tiny)
    draw.ellipse([cx0+60, cy0+8, cx0+72, cy0+20], fill=hex_to_rgb(ORANGE))
    draw.text((cx0+76, cy0+6), "p95", fill=hex_to_rgb(ORANGE), font=font_tiny)

    return img


def frame_bar_chart(W, H, fonts):
    img = Image.new("RGB", (W, H), hex_to_rgb(BG_DARK))
    draw = ImageDraw.Draw(img)
    draw_grid(draw, W, H, spacing=30, color="#111820")
    font_tiny, font_sm, font_md, font_lg, font_xl = fonts

    make_header(draw, W, "3/8 Sports", font_sm, font_tiny)
    draw.text((20, 55), "Athlete Performance Scores by Sport", fill=hex_to_rgb(WHITE), font=font_sm)

    sports = ["Swimming", "Cycling", "Running", "Triathlon", "Rowing", "Tennis"]
    values = [87.2, 84.1, 82.5, 89.3, 78.6, 81.4]
    colors = [TEAL, "#00b8d4", "#0099ff", TEAL, "#00b8d4", "#0099ff"]

    cx0, cy0, cx1, cy1 = 80, 90, W-30, H-50
    chart_w = cx1 - cx0
    chart_h = cy1 - cy0
    draw.rectangle([cx0, cy0, cx1, cy1], fill=hex_to_rgb("#0a0e16"))

    bar_w = chart_w // len(sports) - 20
    max_val = 100

    for i in range(5):
        y = cy0 + i * chart_h // 4
        draw.line([(cx0, y), (cx1, y)], fill=hex_to_rgb("#1c2333"), width=1)
        draw.text((cx0-35, y-6), str(100 - i*25), fill=hex_to_rgb(GRAY), font=font_tiny)

    for i, (sport, val, col) in enumerate(zip(sports, values, colors)):
        bx = cx0 + 10 + i * (bar_w + 20)
        bar_h = int((val / max_val) * chart_h)
        by = cy1 - bar_h
        draw.rectangle([bx, by, bx+bar_w, cy1], fill=hex_to_rgb(col))
        draw.text((bx + bar_w//2 - 10, by-18), f"{val}", fill=hex_to_rgb(WHITE), font=font_tiny)
        bbox = font_tiny.getbbox(sport)
        sw = bbox[2]-bbox[0]
        draw.text((bx + (bar_w-sw)//2, cy1+5), sport, fill=hex_to_rgb(GRAY), font=font_tiny)

    return img


def frame_training_table(W, H, fonts):
    img = Image.new("RGB", (W, H), hex_to_rgb(BG_DARK))
    draw = ImageDraw.Draw(img)
    font_tiny, font_sm, font_md, font_lg, font_xl = fonts

    make_header(draw, W, "4/8 Training", font_sm, font_tiny)
    draw.text((20, 55), "Model Training History", fill=hex_to_rgb(WHITE), font=font_sm)

    headers = ["Date", "Version", "Samples", "MAE", "R2", "Status"]
    rows = [
        ["2026-03-08", "v1.4.2", "4,200", "1.82", "0.943", "Success"],
        ["2026-03-07", "v1.4.1", "4,100", "1.91", "0.938", "Success"],
        ["2026-03-06", "v1.4.0", "3,950", "2.04", "0.931", "Success"],
        ["2026-03-05", "v1.3.9", "3,800", "2.11", "0.927", "Success"],
        ["2026-03-04", "v1.3.8", "3,750", "2.18", "0.921", "Success"],
    ]
    col_ws = [120, 80, 80, 60, 60, 100]
    tx0 = 20
    ty0 = 90
    row_h = 36

    draw.rectangle([tx0, ty0, W-20, ty0+row_h], fill=hex_to_rgb(BG_CARD))
    cx = tx0 + 10
    for h, cw in zip(headers, col_ws):
        draw.text((cx, ty0+10), h, fill=hex_to_rgb(TEAL), font=font_tiny)
        cx += cw
    draw.line([(tx0, ty0+row_h), (W-20, ty0+row_h)], fill=hex_to_rgb(DIVIDER), width=1)

    for ri, row in enumerate(rows):
        ry = ty0 + row_h + ri * row_h
        row_bg = "#0d1117" if ri % 2 == 0 else "#0f1318"
        draw.rectangle([tx0, ry, W-20, ry+row_h], fill=hex_to_rgb(row_bg))
        cx = tx0 + 10
        for ci, (cell, cw) in enumerate(zip(row, col_ws)):
            color = GREEN if ci == 5 else WHITE
            draw.text((cx, ry+10), cell, fill=hex_to_rgb(color), font=font_tiny)
            cx += cw
        draw.line([(tx0, ry+row_h), (W-20, ry+row_h)], fill=hex_to_rgb(DIVIDER), width=1)

    return img


def frame_scatter(W, H, fonts):
    img = Image.new("RGB", (W, H), hex_to_rgb(BG_DARK))
    draw = ImageDraw.Draw(img)
    draw_grid(draw, W, H, spacing=30, color="#111820")
    font_tiny, font_sm, font_md, font_lg, font_xl = fonts

    make_header(draw, W, "5/8 Accuracy", font_sm, font_tiny)
    draw.text((20, 55), "Predicted vs Actual Performance Score", fill=hex_to_rgb(WHITE), font=font_sm)

    cx0, cy0, cx1, cy1 = 80, 90, W-50, H-60
    chart_w = cx1 - cx0
    chart_h = cy1 - cy0
    draw.rectangle([cx0, cy0, cx1, cy1], fill=hex_to_rgb("#0a0e16"))

    for i in range(5):
        y = cy0 + i * chart_h // 4
        x = cx0 + i * chart_w // 4
        draw.line([(cx0, y), (cx1, y)], fill=hex_to_rgb("#1c2333"), width=1)
        draw.line([(x, cy0), (x, cy1)], fill=hex_to_rgb("#1c2333"), width=1)
        draw.text((cx0-30, y-6), str(100-i*25), fill=hex_to_rgb(GRAY), font=font_tiny)
        draw.text((x-8, cy1+5), str(i*25), fill=hex_to_rgb(GRAY), font=font_tiny)

    draw_dashed_line(draw, cx0, cy1, cx1, cy0, color="#444455", dash=6)

    random.seed(7)
    for _ in range(50):
        actual = random.uniform(30, 95)
        predicted = actual + random.gauss(0, 4)
        predicted = max(20, min(100, predicted))
        px = int(cx0 + (actual/100) * chart_w)
        py = int(cy1 - (predicted/100) * chart_h)
        r = 4
        draw.ellipse([px-r, py-r, px+r, py+r], fill=blend(TEAL, 0.85, BG_DARK))

    draw.text((cx0+10, cy0+10), "R2 = 0.943", fill=hex_to_rgb(WHITE), font=font_sm)
    draw.text((W//2-40, cy1+5), "Actual Score", fill=hex_to_rgb(GRAY), font=font_tiny)

    return img


def frame_health(W, H, fonts):
    img = Image.new("RGB", (W, H), hex_to_rgb(BG_DARK))
    draw = ImageDraw.Draw(img)
    font_tiny, font_sm, font_md, font_lg, font_xl = fonts

    make_header(draw, W, "6/8 Health", font_sm, font_tiny)
    draw.text((20, 55), "Live Service Health", fill=hex_to_rgb(WHITE), font=font_sm)

    services = [
        ("Predictions API", "Healthy", ":8000"),
        ("Data Ingestion", "Healthy", ":8081"),
        ("ML Trainer", "Healthy", ":8080"),
        ("Dashboard", "Healthy", ":8501"),
    ]
    card_h = 70
    for i, (svc, status, port) in enumerate(services):
        cy = 90 + i * (card_h + 10)
        draw.rounded_rectangle([20, cy, W-20, cy+card_h], radius=6, fill=hex_to_rgb(BG_CARD))
        draw.rounded_rectangle([20, cy, 24, cy+card_h], radius=3, fill=hex_to_rgb(GREEN))
        draw.ellipse([34, cy+24, 46, cy+36], fill=hex_to_rgb(GREEN))
        draw.text((55, cy+12), svc, fill=hex_to_rgb(WHITE), font=font_sm)
        draw.text((55, cy+38), status, fill=hex_to_rgb(GREEN), font=font_tiny)
        draw.text((W-80, cy+12), port, fill=hex_to_rgb(GRAY), font=font_sm)

    draw.text((W//2-120, H-45), "Uptime: 99.98%  |  Last check: 0s ago", fill=hex_to_rgb(GRAY), font=font_tiny)
    return img


def frame_grafana_metrics(W, H, fonts):
    img = Image.new("RGB", (W, H), hex_to_rgb("#111111"))
    draw = ImageDraw.Draw(img)
    font_tiny, font_sm, font_md, font_lg, font_xl = fonts

    draw.rectangle([0, 0, W, 44], fill=hex_to_rgb("#0d0d0d"))
    draw.text((16, 12), "Platform Metrics -- Request Rate", fill=hex_to_rgb(WHITE), font=font_sm)
    draw.text((W-120, 12), "7/8 Grafana", fill=hex_to_rgb(GRAY), font=font_tiny)

    draw.rounded_rectangle([W-200, 10, W-135, 30], radius=4, fill=hex_to_rgb("#e05f20"))
    draw.text((W-196, 14), "Prometheus", fill=hex_to_rgb(WHITE), font=font_tiny)

    cx0, cy0, cx1, cy1 = 60, 60, W-20, H-40
    chart_w = cx1 - cx0
    chart_h = cy1 - cy0

    for i in range(6):
        y = cy0 + i * chart_h // 5
        draw.line([(cx0, y), (cx1, y)], fill=hex_to_rgb("#222233"), width=1)
        draw.text((cx0-35, y-6), f"{10-i*2}", fill=hex_to_rgb(GRAY), font=font_tiny)

    N = 60
    random.seed(13)
    rates = [4 + 3*math.sin(i*0.25) + random.uniform(-0.8, 0.8) for i in range(N)]

    def to_px(i, v):
        px = int(cx0 + (i/(N-1)) * chart_w)
        py = int(cy1 - (v/12) * chart_h)
        return px, py

    points = [to_px(i, rates[i]) for i in range(N)]
    poly = points + [(cx1, cy1), (cx0, cy1)]
    fill_col = blend(TEAL, 0.2, "#111111")
    draw.polygon(poly, fill=fill_col)
    for i in range(N-1):
        draw.line([points[i], points[i+1]], fill=hex_to_rgb(TEAL), width=2)

    draw.text((cx0+10, cy0+8), "http_requests_total rate[5m]", fill=hex_to_rgb(TEAL), font=font_tiny)
    draw.text((cx0-50, cy0 + chart_h//2 - 10), "req/s", fill=hex_to_rgb(GRAY), font=font_tiny)

    return img


def frame_complete(W, H, fonts):
    img = Image.new("RGB", (W, H), hex_to_rgb(BG_DARK))
    draw = ImageDraw.Draw(img)
    draw_grid(draw, W, H, spacing=30, color="#111820")
    font_tiny, font_sm, font_md, font_lg, font_xl = fonts

    make_header(draw, W, "8/8 Complete", font_sm, font_tiny)

    kpis = [("247", "Athletes"), ("1,842", "Predictions"), ("94.3%", "Accuracy"), ("12ms", "Response")]
    card_w = (W - 60) // 4
    card_h = 110
    cy = 65
    for i, (val, label) in enumerate(kpis):
        cx = 15 + i * (card_w + 15)
        draw.rounded_rectangle([cx, cy, cx+card_w, cy+card_h], radius=8, fill=hex_to_rgb(BG_CARD))
        draw.rounded_rectangle([cx, cy, cx+card_w, cy+4], radius=2, fill=hex_to_rgb(TEAL))
        bbox = font_lg.getbbox(val)
        vw = bbox[2]-bbox[0]
        draw.text((cx + (card_w-vw)//2, cy+15), val, fill=hex_to_rgb(TEAL), font=font_lg)
        bbox = font_tiny.getbbox(label)
        lw = bbox[2]-bbox[0]
        draw.text((cx + (card_w-lw)//2, cy+55), label, fill=hex_to_rgb(GRAY), font=font_tiny)

    msg = "All Systems Operational"
    bbox = font_lg.getbbox(msg)
    mw = bbox[2]-bbox[0]
    draw.text(((W-mw)//2, 215), msg, fill=hex_to_rgb(TEAL), font=font_lg)

    check = "[ OK ]"
    bbox = font_md.getbbox(check)
    cw = bbox[2]-bbox[0]
    draw.text(((W-cw)//2, 270), check, fill=hex_to_rgb(GREEN), font=font_md)

    tagline = "Platform v1.0.0  .  Built for Production  .  Zurich Ready"
    bbox = font_sm.getbbox(tagline)
    tw = bbox[2]-bbox[0]
    draw.text(((W-tw)//2, H-45), tagline, fill=hex_to_rgb(GRAY), font=font_sm)

    return img


def make_demo_gif():
    W, H = 900, 500
    font_tiny = load_font(11)
    font_sm = load_font(14)
    font_md = load_font(18, bold=True)
    font_lg = load_font(28, bold=True)
    font_xl = load_font(44, bold=True)
    fonts = (font_tiny, font_sm, font_md, font_lg, font_xl)

    frames = [
        frame_overview(W, H, fonts),
        frame_latency_chart(W, H, fonts),
        frame_bar_chart(W, H, fonts),
        frame_training_table(W, H, fonts),
        frame_scatter(W, H, fonts),
        frame_health(W, H, fonts),
        frame_grafana_metrics(W, H, fonts),
        frame_complete(W, H, fonts),
    ]

    frames[0].save(
        OUT / "demo.gif",
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=600,
        optimize=False,
    )
    print(f"demo.gif: {(OUT/'demo.gif').stat().st_size:,} bytes ({len(frames)} frames)")


# ─── GRAFANA SCREENSHOT ─────────────────────────────────────────────────────────

def make_grafana_screenshot():
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), hex_to_rgb("#111217"))
    draw = ImageDraw.Draw(img)

    font_tiny = load_font(11)
    font_sm = load_font(13)
    font_md = load_font(16, bold=True)
    font_lg = load_font(22, bold=True)

    draw.rectangle([0, 0, 48, H], fill=hex_to_rgb("#0b0c0f"))
    for y in [80, 130, 180, 230, 280]:
        draw.rectangle([6, y, 42, y+36], fill=hex_to_rgb("#1a1d23"), outline=hex_to_rgb("#2d3139"), width=1)

    draw.rectangle([48, 0, W, 48], fill=hex_to_rgb("#0d0e12"))
    draw.line([(48, 48), (W, 48)], fill=hex_to_rgb("#2d3139"), width=1)

    draw.rounded_rectangle([56, 8, 88, 40], radius=4, fill=hex_to_rgb("#f46800"))
    draw.text((61, 14), "Gf", fill=hex_to_rgb(WHITE), font=font_md)

    draw.text((100, 16), "AI Performance Platform", fill=hex_to_rgb(GRAY), font=font_sm)
    draw.text((270, 16), "/", fill=hex_to_rgb("#444"), font=font_sm)
    draw.text((285, 16), "API Performance Dashboard", fill=hex_to_rgb(WHITE), font=font_sm)

    draw.rounded_rectangle([W-180, 10, W-10, 38], radius=4, fill=hex_to_rgb("#1a1d23"), outline=hex_to_rgb("#2d3139"), width=1)
    draw.text((W-170, 18), "Last 1 hour", fill=hex_to_rgb(WHITE), font=font_sm)

    draw.rectangle([48, 48, W, 84], fill=hex_to_rgb("#161b22"))
    draw.text((60, 60), "AI Performance Platform -- Metrics", fill=hex_to_rgb(WHITE), font=font_lg)

    draw.ellipse([W-120, 60, W-110, 70], fill=hex_to_rgb(GREEN))
    draw.text((W-105, 57), "Prometheus", fill=hex_to_rgb(GRAY), font=font_tiny)

    panels = [
        (60, 95, 590, 350, "Request Rate (req/s)", "timeseries_teal"),
        (610, 95, W-10, 350, "Latency p50 / p95", "timeseries_dual"),
        (60, 360, 590, 620, "Predictions / hour", "bar"),
        (610, 360, W-10, 620, "Services Up", "gauge"),
    ]

    random.seed(5)
    for (px0, py0, px1, py1, title, ptype) in panels:
        draw.rounded_rectangle([px0, py0, px1, py1], radius=4, fill=hex_to_rgb(BG_PANEL), outline=hex_to_rgb("#2d3139"), width=1)
        draw.rectangle([px0, py0, px1, py0+28], fill=hex_to_rgb("#13151a"))
        draw.text((px0+10, py0+7), title, fill=hex_to_rgb(WHITE), font=font_sm)

        cw = px1 - px0 - 20
        ch = py1 - py0 - 50
        cx0_ = px0 + 10
        cy0_ = py0 + 38
        cx1_ = px1 - 10
        cy1_ = py1 - 10

        if ptype == "timeseries_teal":
            N = 40
            pts = [(int(cx0_ + i*cw/(N-1)), int(cy1_ - (4+3*math.sin(i*0.4)+random.uniform(-0.5,0.5))/10*ch)) for i in range(N)]
            poly = pts + [(cx1_, cy1_), (cx0_, cy1_)]
            draw.polygon(poly, fill=blend(TEAL, 0.15, BG_PANEL))
            for i in range(N-1):
                draw.line([pts[i], pts[i+1]], fill=hex_to_rgb(TEAL), width=2)

        elif ptype == "timeseries_dual":
            N = 40
            pts50 = [(int(cx0_ + i*cw/(N-1)), int(cy1_ - (12+2*math.sin(i*0.3))/50*ch)) for i in range(N)]
            pts95 = [(int(cx0_ + i*cw/(N-1)), int(cy1_ - (25+3*math.sin(i*0.2+1))/50*ch)) for i in range(N)]
            for i in range(N-1):
                draw.line([pts50[i], pts50[i+1]], fill=hex_to_rgb(TEAL), width=2)
                draw.line([pts95[i], pts95[i+1]], fill=hex_to_rgb(ORANGE), width=2)

        elif ptype == "bar":
            bw = cw // 8
            for i in range(7):
                bx = cx0_ + i*(bw+8)
                bh = int(random.uniform(0.4, 0.9) * ch)
                draw.rectangle([bx, cy1_-bh, bx+bw, cy1_], fill=hex_to_rgb(TEAL))

        elif ptype == "gauge":
            gcx = (cx0_ + cx1_) // 2
            gcy = (cy0_ + cy1_) // 2
            gr = min(cw, ch) // 3
            draw.arc([gcx-gr, gcy-gr, gcx+gr, gcy+gr], start=150, end=390, fill=hex_to_rgb("#2d3139"), width=12)
            draw.arc([gcx-gr, gcy-gr, gcx+gr, gcy+gr], start=150, end=390, fill=hex_to_rgb(GREEN), width=12)
            draw.text((gcx-12, gcy-10), "3/3", fill=hex_to_rgb(GREEN), font=font_lg)
            draw.text((gcx-30, gcy+20), "Services UP", fill=hex_to_rgb(GRAY), font=font_tiny)

    draw.text((W//2-200, H-18), "Grafana Dashboard -- Platform Metrics (simulated)", fill=hex_to_rgb("#444"), font=font_tiny)

    img.save(OUT / "grafana-screenshot.png", "PNG")
    print(f"grafana-screenshot.png: {(OUT/'grafana-screenshot.png').stat().st_size:,} bytes")


# ─── PROMETHEUS SCREENSHOT ──────────────────────────────────────────────────────

def make_prometheus_screenshot():
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), (245, 245, 245))
    draw = ImageDraw.Draw(img)

    font_tiny = load_font(11)
    font_sm = load_font(13)
    font_md = load_font(15, bold=True)
    font_lg = load_font(20, bold=True)

    draw.rectangle([0, 0, W, 50], fill=(43, 43, 43))
    draw.text((16, 14), "PROMETHEUS", fill=(255, 255, 255), font=font_md)
    for i, nav in enumerate(["Alerts", "Graph", "Status", "Help"]):
        draw.text((200 + i*100, 17), nav, fill=(200, 200, 200), font=font_sm)

    draw.text((20, 70), "Targets", fill=(0, 0, 0), font=font_lg)
    draw.text((20, 100), "4 / 4 active targets", fill=(50, 50, 50), font=font_sm)

    tx0, ty0 = 20, 130
    col_ws = [280, 80, 220, 130, 130, 80]
    headers = ["Endpoint", "State", "Labels", "Last Scrape", "Duration", "Error"]
    row_h = 40

    rows = [
        ("http://api:8000/metrics", "UP", 'job="api"', "2.341s ago", "3.2ms", ""),
        ("http://data-ingestion:8081/metrics", "UP", 'job="data-ingestion"', "2.341s ago", "2.8ms", ""),
        ("http://ml-trainer:8080/metrics", "UP", 'job="ml-trainer"', "2.341s ago", "4.1ms", ""),
        ("http://localhost:9090/metrics", "UP", 'job="prometheus"', "2.341s ago", "1.2ms", ""),
    ]

    draw.rectangle([tx0, ty0, W-20, ty0+row_h], fill=(220, 220, 220))
    cx = tx0 + 8
    for h, cw in zip(headers, col_ws):
        draw.text((cx, ty0+12), h, fill=(0, 0, 0), font=font_md)
        cx += cw
    draw.line([(tx0, ty0+row_h), (W-20, ty0+row_h)], fill=(180, 180, 180), width=1)

    for ri, row in enumerate(rows):
        ry = ty0 + row_h + ri * row_h
        row_bg = (255, 255, 255) if ri % 2 == 0 else (248, 248, 252)
        draw.rectangle([tx0, ry, W-20, ry+row_h], fill=row_bg)
        cx = tx0 + 8
        for ci, (cell, cw) in enumerate(zip(row, col_ws)):
            if ci == 1:
                draw.rounded_rectangle([cx, ry+10, cx+38, ry+30], radius=4, fill=(0, 153, 51))
                draw.text((cx+8, ry+14), cell, fill=(255, 255, 255), font=font_tiny)
            else:
                color = (60, 60, 60) if ci != 0 else (0, 102, 204)
                draw.text((cx, ry+13), cell, fill=color, font=font_sm)
            cx += cw
        draw.line([(tx0, ry+row_h), (W-20, ry+row_h)], fill=(220, 220, 220), width=1)

    draw.text((W//2-230, H-20), "Prometheus Targets -- All Services UP (simulated)", fill=(180, 180, 180), font=font_tiny)

    img.save(OUT / "prometheus-screenshot.png", "PNG")
    print(f"prometheus-screenshot.png: {(OUT/'prometheus-screenshot.png').stat().st_size:,} bytes")


if __name__ == "__main__":
    print("Generating assets...")
    make_banner()
    make_demo_gif()
    make_grafana_screenshot()
    make_prometheus_screenshot()
    print("Done.")
