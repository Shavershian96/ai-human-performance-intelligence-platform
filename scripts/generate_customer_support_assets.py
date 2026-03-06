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


def gray(v: int) -> tuple[int, int, int]:
    return (v, v, v)


def gradient(size: tuple[int, int], top: int, bottom: int) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        value = lerp(top, bottom, y / max(h - 1, 1))
        c = gray(value)
        for x in range(w):
            px[x, y] = c
    return img


def rounded(draw: ImageDraw.ImageDraw, box, radius=14, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def shadow(draw: ImageDraw.ImageDraw, box, offset=5):
    x1, y1, x2, y2 = box
    rounded(draw, (x1 + offset, y1 + offset, x2 + offset, y2 + offset), radius=14, fill=gray(8))


def draw_metric(draw: ImageDraw.ImageDraw, box, label: str, value: str):
    shadow(draw, box, offset=4)
    rounded(draw, box, radius=12, fill=gray(23), outline=gray(58), width=1)
    draw.text((box[0] + 14, box[1] + 14), label, font=load_font(14, bold=True), fill=gray(160))
    draw.text((box[0] + 14, box[1] + 42), value, font=load_font(36, bold=True), fill=gray(236))


def draw_trend_grid(draw: ImageDraw.ImageDraw, box):
    x1, y1, x2, y2 = box
    for i in range(8):
        y = y1 + int((y2 - y1) * i / 5)
        draw.line((x1, y, x2, y), fill=gray(44), width=1)
    for i in range(13):
        x = x1 + int((x2 - x1) * i / 12)
        draw.line((x, y1, x, y2), fill=gray(38), width=1)


def draw_series(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], tone: int, width: int):
    draw.line(points, fill=gray(tone), width=width)
    for p in points[::2]:
        draw.ellipse((p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2), fill=gray(min(245, tone + 12)))


def build_wave_points(
    x1: int,
    y1: int,
    width: int,
    baseline: int,
    amp_a: float,
    amp_b: float,
    phase: float,
    freq_a: float,
    freq_b: float,
    count: int,
) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    for i in range(count):
        x = x1 + int(width * i / (count - 1))
        t = i / (count - 1)
        y = y1 + baseline - int(amp_a * math.sin((t * freq_a * math.pi * 2.0) + phase) + amp_b * math.cos((t * freq_b * math.pi * 2.0) + phase * 0.7))
        points.append((x, y))
    return points


def draw_heatmap(draw: ImageDraw.ImageDraw, box):
    x1, y1, x2, y2 = box
    cols, rows, gap = 16, 5, 6
    cell_w = (x2 - x1 - (cols - 1) * gap) // cols
    cell_h = (y2 - y1 - (rows - 1) * gap) // rows
    for r in range(rows):
        for c in range(cols):
            tone = 34 + ((r * 17 + c * 9 + r * c * 4) % 150)
            cx1 = x1 + c * (cell_w + gap)
            cy1 = y1 + r * (cell_h + gap)
            cx2 = cx1 + cell_w
            cy2 = cy1 + cell_h
            rounded(draw, (cx1, cy1, cx2, cy2), radius=4, fill=gray(tone), outline=gray(min(218, tone + 20)), width=1)


def banner_frame() -> Image.Image:
    w, h = 1280, 640
    img = gradient((w, h), 9, 18)
    draw = ImageDraw.Draw(img)

    shadow(draw, (30, 24, 1250, 614), offset=6)
    rounded(draw, (30, 24, 1250, 614), radius=18, fill=gray(14), outline=gray(54), width=1)

    # Swiss-style left title block integrated in the grid.
    rounded(draw, (56, 48, 744, 160), radius=10, fill=gray(20), outline=gray(58), width=1)
    draw.text((76, 72), "AI HUMAN PERFORMANCE", font=load_font(34, bold=True), fill=gray(236))
    draw.text((76, 110), "INTELLIGENCE PLATFORM", font=load_font(34, bold=True), fill=gray(236))
    draw.text((78, 142), "NEXT-GENERATION ANALYTICS FOR HUMAN PERFORMANCE", font=load_font(11, bold=True), fill=gray(165))

    # Top modular metric row.
    x = 764
    for label, value in [("TOTAL PREDICTIONS", "5k+"), ("MEAN SCORE", "89.1"), ("ACTIVE SUBJECTS", "150+")]:
        draw_metric(draw, (x, 48, x + 150, 160), label, value)
        x += 164

    # Main trend panel.
    trend_panel = (56, 184, 1224, 430)
    shadow(draw, trend_panel, offset=4)
    rounded(draw, trend_panel, radius=14, fill=gray(20), outline=gray(60), width=1)
    draw.text((82, 204), "TREND INSIGHTS (SWISS DATA ANALYSIS)", font=load_font(13, bold=True), fill=gray(168))
    rounded(draw, (76, 228, 1204, 356), radius=8, fill=gray(16), outline=gray(48), width=1)
    draw_trend_grid(draw, (90, 240, 1190, 344))

    line_1 = build_wave_points(90, 240, 1100, 62, 13, 6, 0.2, 1.8, 3.2, 30)
    line_2 = build_wave_points(90, 240, 1100, 74, 10, 4, 1.1, 1.6, 2.8, 30)
    line_3 = build_wave_points(90, 240, 1100, 86, 8, 3, 1.9, 1.4, 2.2, 30)
    draw_series(draw, line_1, 226, 3)
    draw_series(draw, line_2, 192, 2)
    draw_series(draw, line_3, 158, 2)

    rounded(draw, (76, 366, 1204, 416), radius=8, fill=gray(16), outline=gray(48), width=1)
    draw_heatmap(draw, (92, 380, 1188, 408))

    # Bottom two structured content panels.
    left_info = (56, 446, 632, 576)
    right_info = (648, 446, 1224, 576)
    for box in (left_info, right_info):
        shadow(draw, box, offset=4)
        rounded(draw, box, radius=12, fill=gray(21), outline=gray(60), width=1)

    draw.text((78, 468), "END-TO-END MLOPS STACK", font=load_font(16, bold=True), fill=gray(232))
    draw.text((78, 495), "- INGESTION", font=load_font(14), fill=gray(186))
    draw.text((78, 516), "- TRAINING", font=load_font(14), fill=gray(186))
    draw.text((78, 537), "- PRODUCTION", font=load_font(14), fill=gray(186))
    draw.text((78, 558), "- MONITORING", font=load_font(14), fill=gray(186))

    draw.text((670, 468), "PRODUCTION-READY ARCHITECTURE", font=load_font(16, bold=True), fill=gray(232))
    draw.text((670, 495), "- MICROSERVICES", font=load_font(14), fill=gray(186))
    draw.text((670, 516), "- KUBERNETES", font=load_font(14), fill=gray(186))
    draw.text((670, 537), "- OBSERVABILITY", font=load_font(14), fill=gray(186))

    # Bottom control bar metadata.
    rounded(draw, (56, 586, 1224, 606), radius=6, fill=gray(17), outline=gray(42), width=1)
    tiny = load_font(11, bold=True)
    draw.text((70, 590), "ENGLISH | DEUTSCH", font=tiny, fill=gray(130))
    draw.text((1040, 590), "REPLACE GITHUB PATH", font=tiny, fill=gray(116))
    return img


def gif_frame(index: int, total: int) -> Image.Image:
    # Dedicated seamless Swiss-style looped trend panel animation.
    w, h = 1280, 720
    img = gradient((w, h), 8, 18)
    draw = ImageDraw.Draw(img)
    panel = (70, 66, 1210, 654)
    shadow(draw, panel, offset=6)
    rounded(draw, panel, radius=16, fill=gray(15), outline=gray(54), width=1)

    draw.text((98, 96), "TREND OVERVIEW", font=load_font(20, bold=True), fill=gray(228))
    draw.text((98, 124), "HUMAN PERFORMANCE OVER 1 MONTH", font=load_font(12, bold=True), fill=gray(160))

    phase = (2.0 * math.pi * index) / max(total, 1)
    predictions = int(5124 + (index * 3))
    score = 89.1 + 0.7 * math.sin(phase * 1.2)

    draw_metric(draw, (92, 150, 410, 252), "CURRENT TOTAL PREDICTIONS", f"{predictions:,}")
    draw_metric(draw, (426, 150, 744, 252), "LATEST PERFORMANCE SCORE", f"{score:.1f}")

    graph_box = (92, 278, 1188, 560)
    rounded(draw, graph_box, radius=10, fill=gray(16), outline=gray(48), width=1)
    gx1, gy1, gx2, gy2 = 106, 294, 1174, 546
    draw_trend_grid(draw, (gx1, gy1, gx2, gy2))

    line_a = build_wave_points(gx1, gy1, gx2 - gx1, 92, 16, 8, phase, 1.6, 3.2, 44)
    line_b = build_wave_points(gx1, gy1, gx2 - gx1, 114, 12, 6, phase + 1.1, 1.2, 2.6, 44)
    line_c = build_wave_points(gx1, gy1, gx2 - gx1, 136, 10, 4, phase + 2.1, 1.0, 2.0, 44)

    # Subtle area fills for premium depth.
    area = [(gx1, gy2)] + line_b + [(gx2, gy2)]
    draw.polygon(area, fill=gray(28))
    area2 = [(gx1, gy2)] + line_c + [(gx2, gy2)]
    draw.polygon(area2, fill=gray(24))

    draw_series(draw, line_a, 230, 3)
    draw_series(draw, line_b, 196, 2)
    draw_series(draw, line_c, 164, 2)

    # Dynamic but seamless x-axis labels.
    shift = int((index / max(total - 1, 1)) * 6)
    labels = ["W1", "W2", "W3", "W4", "W5", "W6", "W7"]
    for i in range(7):
        x = gx1 + int((gx2 - gx1) * i / 6)
        label = labels[(i + shift) % len(labels)]
        draw.text((x - 10, gy2 + 10), label, font=load_font(11, bold=True), fill=gray(140))

    rounded(draw, (92, 586, 1188, 628), radius=8, fill=gray(17), outline=gray(46), width=1)
    draw.text((108, 600), "SEAMLESS DATA STREAM | STRUCTURED SWISS GRID | DARK-MODE EXECUTIVE VIEW", font=load_font(12, bold=True), fill=gray(140))
    return img


def generate_banner() -> None:
    banner_frame().save(ASSETS / "banner.png", format="PNG")


def generate_gif() -> None:
    total = 42
    frames = [gif_frame(i, total) for i in range(total)]
    frames[0].save(
        ASSETS / "demo.gif",
        save_all=True,
        append_images=frames[1:],
        duration=170,
        loop=0,
        optimize=True,
    )


if __name__ == "__main__":
    generate_banner()
    generate_gif()
    print(f"Generated: {ASSETS / 'banner.png'}")
    print(f"Generated: {ASSETS / 'demo.gif'}")
