from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)


def load_font(size: int, bold: bool = False):
    candidates: list[str] = []
    if bold:
        candidates.extend(["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"])
    else:
        candidates.extend(["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"])
    for item in candidates:
        p = Path(item)
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    image = Image.new("RGB", size)
    px = image.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = (
            lerp(top[0], bottom[0], t),
            lerp(top[1], bottom[1], t),
            lerp(top[2], bottom[2], t),
        )
        for x in range(w):
            px[x, y] = c
    return image


def rounded(draw: ImageDraw.ImageDraw, box, radius=12, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def shadow(draw: ImageDraw.ImageDraw, box, offset=4):
    x1, y1, x2, y2 = box
    rounded(draw, (x1 + offset, y1 + offset, x2 + offset, y2 + offset), radius=12, fill=(8, 10, 14))


def text_h(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def draw_heatmap(draw: ImageDraw.ImageDraw, box):
    x1, y1, x2, y2 = box
    cols, rows, gap = 16, 4, 6
    cell_w = (x2 - x1 - (cols - 1) * gap) // cols
    cell_h = (y2 - y1 - (rows - 1) * gap) // rows
    for r in range(rows):
        for c in range(cols):
            tone = 36 + ((r * 19 + c * 11 + r * c * 5) % 110)
            cx1 = x1 + c * (cell_w + gap)
            cy1 = y1 + r * (cell_h + gap)
            rounded(
                draw,
                (cx1, cy1, cx1 + cell_w, cy1 + cell_h),
                radius=4,
                fill=(tone, tone, tone),
                outline=(min(210, tone + 22),) * 3,
                width=1,
            )


def draw_banner() -> None:
    img = gradient((1280, 640), (10, 12, 17), (18, 21, 28))
    draw = ImageDraw.Draw(img)

    outer = (28, 24, 1252, 614)
    shadow(draw, outer, offset=6)
    rounded(draw, outer, radius=18, fill=(16, 19, 25), outline=(52, 57, 66), width=1)

    title_panel = (56, 48, 872, 208)
    rounded(draw, title_panel, radius=12, fill=(19, 23, 30), outline=(60, 66, 76), width=1)
    title_font = load_font(40, bold=True)
    sub_font = load_font(14, bold=True)

    y = 74
    for line in ["AI HUMAN PERFORMANCE", "INTELLIGENCE PLATFORM"]:
        draw.text((82, y), line, font=title_font, fill=(232, 236, 242))
        y += text_h(draw, line, title_font) + 6
    subtitle = "NEXT-GENERATION ANALYTICS FOR HUMAN PERFORMANCE"
    draw.text((84, y + 2), subtitle, font=sub_font, fill=(166, 174, 186))

    info1 = (892, 48, 1224, 122)
    info2 = (892, 134, 1224, 208)
    for panel in (info1, info2):
        rounded(draw, panel, radius=10, fill=(21, 24, 32), outline=(60, 66, 76), width=1)

    draw.text((914, 70), "MICROSERVICES STACK", font=load_font(16, bold=True), fill=(226, 232, 240))
    draw.text((914, 95), "INGESTION | TRAINER | API | DASHBOARD(API)", font=load_font(12), fill=(165, 174, 186))
    draw.text((914, 156), "PLATFORM", font=load_font(16, bold=True), fill=(226, 232, 240))
    draw.text((914, 180), "KUBERNETES | CI/CD | OBSERVABILITY | RETRIES", font=load_font(12), fill=(165, 174, 186))

    trend = (56, 232, 1224, 468)
    rounded(draw, trend, radius=14, fill=(18, 22, 29), outline=(58, 64, 74), width=1)
    draw.text((82, 256), "TREND INSIGHTS", font=load_font(26, bold=True), fill=(230, 236, 244))

    chart_box = (82, 296, 1198, 444)
    rounded(draw, chart_box, radius=10, fill=(14, 17, 23), outline=(50, 56, 66), width=1)

    cx1, cy1, cx2, cy2 = 98, 314, 1182, 430
    for i in range(7):
        y_grid = cy1 + i * 19
        draw.line((cx1, y_grid, cx2, y_grid), fill=(40, 45, 54), width=1)
    for i in range(13):
        x_grid = cx1 + int((cx2 - cx1) * i / 12)
        draw.line((x_grid, cy1, x_grid, cy2), fill=(34, 39, 47), width=1)

    line1 = [(cx1 + 0, cy2 - 42), (cx1 + 120, cy2 - 66), (cx1 + 240, cy2 - 54), (cx1 + 360, cy2 - 79), (cx1 + 480, cy2 - 70), (cx1 + 600, cy2 - 90), (cx1 + 720, cy2 - 78), (cx1 + 840, cy2 - 98), (cx1 + 980, cy2 - 84)]
    line2 = [(cx1 + 0, cy2 - 58), (cx1 + 120, cy2 - 74), (cx1 + 240, cy2 - 86), (cx1 + 360, cy2 - 73), (cx1 + 480, cy2 - 95), (cx1 + 600, cy2 - 86), (cx1 + 720, cy2 - 68), (cx1 + 840, cy2 - 58), (cx1 + 980, cy2 - 64)]
    line3 = [(cx1 + 0, cy2 - 30), (cx1 + 120, cy2 - 50), (cx1 + 240, cy2 - 44), (cx1 + 360, cy2 - 60), (cx1 + 480, cy2 - 56), (cx1 + 600, cy2 - 72), (cx1 + 720, cy2 - 64), (cx1 + 840, cy2 - 80), (cx1 + 980, cy2 - 74)]
    for points, tone in [(line1, 226), (line2, 188), (line3, 154)]:
        draw.line(points, fill=(tone, tone, tone), width=3)
        for p in points:
            draw.ellipse((p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2), fill=(min(240, tone + 8),) * 3)

    modules = [(56, 490, 338, 580), (352, 490, 634, 580), (648, 490, 930, 580), (944, 490, 1224, 580)]
    labels = [("DATA INGESTION", "Validated JSON/CSV intake"), ("ML TRAINER", "Scheduled + on-demand training"), ("PREDICTION API", "Low-latency model serving"), ("DASHBOARD/API MODE", "API-first + graceful demo fallback")]
    for panel, (head, body) in zip(modules, labels):
        rounded(draw, panel, radius=12, fill=(20, 24, 31), outline=(58, 64, 74), width=1)
        draw.text((panel[0] + 16, panel[1] + 18), head, font=load_font(16, bold=True), fill=(226, 232, 240))
        draw.text((panel[0] + 16, panel[1] + 48), body, font=load_font(12), fill=(166, 174, 186))

    draw.text((66, 592), "ENGLISH | DEUTSCH", font=load_font(11, bold=True), fill=(130, 138, 150))
    draw.text((1040, 592), "REPLACE <owner>/<repo> PATH", font=load_font(11, bold=True), fill=(116, 124, 136))

    img.save(ASSETS / "banner.png", format="PNG")


def draw_metric_card(draw: ImageDraw.ImageDraw, x: int, label: str, value: str):
    panel = (x, 154, x + 274, 286)
    rounded(draw, panel, radius=12, fill=(21, 25, 32), outline=(60, 66, 76), width=1)
    draw.text((x + 16, 178), label.upper(), font=load_font(14, bold=True), fill=(166, 174, 186))
    draw.text((x + 16, 220), value, font=load_font(36, bold=True), fill=(232, 236, 242))


def gif_frame(step: int, total: int) -> Image.Image:
    img = gradient((1280, 720), (9, 12, 18), (18, 21, 28))
    draw = ImageDraw.Draw(img)

    outer = (30, 22, 1248, 694)
    shadow(draw, outer, offset=6)
    rounded(draw, outer, radius=16, fill=(16, 19, 25), outline=(54, 60, 70), width=1)

    rounded(draw, (58, 44, 1220, 126), radius=12, fill=(19, 23, 30), outline=(60, 66, 76), width=1)
    draw.text((84, 68), "AI HUMAN PERFORMANCE DASHBOARD", font=load_font(42, bold=True), fill=(232, 236, 242))

    phase = step / max(1, total - 1)
    predictions = 5124 + int(phase * 86)
    score = 89.1 + 0.4 * math.sin(phase * math.pi * 2.0)
    active = 150 + int(phase * 6)

    draw_metric_card(draw, 66, "Total Predictions", f"{predictions:,}")
    draw_metric_card(draw, 356, "Latest Score", f"{score:.1f}")
    draw_metric_card(draw, 646, "Active Subjects", f"{active}+")
    draw_metric_card(draw, 936, "Model Version", "v2.1")

    rounded(draw, (66, 314, 914, 668), radius=14, fill=(18, 22, 29), outline=(56, 62, 72), width=1)
    draw.text((92, 340), "Trend Overview", font=load_font(24, bold=True), fill=(228, 234, 242))

    chart = (92, 378, 888, 544)
    rounded(draw, chart, radius=10, fill=(14, 17, 23), outline=(48, 54, 64), width=1)
    gx1, gy1, gx2, gy2 = 108, 394, 872, 528
    for i in range(7):
        y_grid = gy1 + i * 22
        draw.line((gx1, y_grid, gx2, y_grid), fill=(40, 45, 54), width=1)
    for i in range(11):
        x_grid = gx1 + int((gx2 - gx1) * i / 10)
        draw.line((x_grid, gy1, x_grid, gy2), fill=(34, 39, 47), width=1)

    offset = int(phase * 22)
    p1 = [(gx1 + 0, gy2 - 44 + offset // 8), (gx1 + 86, gy2 - 66), (gx1 + 172, gy2 - 58), (gx1 + 258, gy2 - 82), (gx1 + 344, gy2 - 76), (gx1 + 430, gy2 - 94), (gx1 + 516, gy2 - 82), (gx1 + 602, gy2 - 102), (gx1 + 688, gy2 - 90), (gx1 + 764, gy2 - 108 + offset // 10)]
    p2 = [(gx1 + 0, gy2 - 62), (gx1 + 86, gy2 - 78), (gx1 + 172, gy2 - 88), (gx1 + 258, gy2 - 76), (gx1 + 344, gy2 - 96), (gx1 + 430, gy2 - 88), (gx1 + 516, gy2 - 72), (gx1 + 602, gy2 - 62), (gx1 + 688, gy2 - 66), (gx1 + 764, gy2 - 58)]
    p3 = [(gx1 + 0, gy2 - 34), (gx1 + 86, gy2 - 52), (gx1 + 172, gy2 - 46), (gx1 + 258, gy2 - 62), (gx1 + 344, gy2 - 56), (gx1 + 430, gy2 - 72), (gx1 + 516, gy2 - 66), (gx1 + 602, gy2 - 80), (gx1 + 688, gy2 - 76), (gx1 + 764, gy2 - 86)]
    for points, tone in [(p1, 228), (p2, 190), (p3, 156)]:
        draw.line(points, fill=(tone, tone, tone), width=3)
        for p in points:
            draw.ellipse((p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2), fill=(min(242, tone + 8),) * 3)

    heat = (92, 560, 888, 654)
    rounded(draw, heat, radius=10, fill=(14, 17, 23), outline=(48, 54, 64), width=1)
    draw_heatmap(draw, (108, 578, 872, 640))

    rounded(draw, (932, 314, 1214, 668), radius=14, fill=(18, 22, 29), outline=(56, 62, 72), width=1)
    draw.text((954, 340), "Workflow", font=load_font(24, bold=True), fill=(228, 234, 242))
    steps = ["INGESTION", "TRAINING", "PREDICTION", "MONITORING"]
    active_idx = min(3, int(phase * 4.0))
    y = 390
    for i, label in enumerate(steps):
        panel = (954, y, 1192, y + 56)
        tone_fill = (35, 39, 47) if i == active_idx else (22, 26, 34)
        tone_text = (236, 240, 246) if i == active_idx else (170, 178, 190)
        rounded(draw, panel, radius=10, fill=tone_fill, outline=(66, 72, 82), width=1)
        draw.text((972, y + 18), label, font=load_font(16, bold=True), fill=tone_text)
        y += 68

    status = ["Data validation complete", "Model retrained successfully", "Predictions served to API", "Health probes and retries active"][active_idx]
    rounded(draw, (954, 598, 1192, 654), radius=10, fill=(20, 24, 31), outline=(58, 64, 74), width=1)
    draw.text((970, 620), status, font=load_font(12), fill=(174, 182, 194))

    return img


def draw_gif() -> None:
    total = 32
    frames = [gif_frame(i, total) for i in range(total)]
    frames[0].save(
        ASSETS / "demo.gif",
        save_all=True,
        append_images=frames[1:],
        duration=180,
        loop=0,
        optimize=True,
    )


if __name__ == "__main__":
    draw_banner()
    draw_gif()
    print(f"Generated: {ASSETS / 'banner.png'}")
    print(f"Generated: {ASSETS / 'demo.gif'}")
