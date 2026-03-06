from __future__ import annotations

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
    draw.text((box[0] + 16, box[1] + 14), label, font=load_font(18), fill=gray(172))
    draw.text((box[0] + 16, box[1] + 44), value, font=load_font(34, bold=True), fill=gray(236))


def draw_trend(draw: ImageDraw.ImageDraw, box):
    x1, y1, x2, y2 = box
    for i in range(6):
        y = y1 + int((y2 - y1) * i / 5)
        draw.line((x1, y, x2, y), fill=gray(44), width=1)
    for i in range(11):
        x = x1 + int((x2 - x1) * i / 10)
        draw.line((x, y1, x, y2), fill=gray(38), width=1)

    line_a = [(x1 + 0, y1 + 168), (x1 + 70, y1 + 146), (x1 + 140, y1 + 156), (x1 + 210, y1 + 123), (x1 + 280, y1 + 132), (x1 + 350, y1 + 106), (x1 + 420, y1 + 118), (x1 + 490, y1 + 92), (x1 + 560, y1 + 100), (x1 + 630, y1 + 82), (x1 + 700, y1 + 90), (x1 + 770, y1 + 75)]
    line_b = [(x1 + 0, y1 + 188), (x1 + 70, y1 + 180), (x1 + 140, y1 + 168), (x1 + 210, y1 + 156), (x1 + 280, y1 + 150), (x1 + 350, y1 + 142), (x1 + 420, y1 + 136), (x1 + 490, y1 + 124), (x1 + 560, y1 + 118), (x1 + 630, y1 + 113), (x1 + 700, y1 + 106), (x1 + 770, y1 + 98)]
    line_c = [(x1 + 0, y1 + 210), (x1 + 70, y1 + 202), (x1 + 140, y1 + 193), (x1 + 210, y1 + 186), (x1 + 280, y1 + 178), (x1 + 350, y1 + 171), (x1 + 420, y1 + 166), (x1 + 490, y1 + 158), (x1 + 560, y1 + 150), (x1 + 630, y1 + 141), (x1 + 700, y1 + 136), (x1 + 770, y1 + 128)]

    draw.line(line_a, fill=gray(224), width=4)
    draw.line(line_b, fill=gray(188), width=3)
    draw.line(line_c, fill=gray(154), width=3)

    for p in line_a:
        draw.ellipse((p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2), fill=gray(238))


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

    rounded(draw, (56, 48, 1008, 132), radius=12, fill=gray(19), outline=gray(60), width=1)
    draw.text((78, 70), "AI HUMAN PERFORMANCE INTELLIGENCE PLATFORM", font=load_font(33, bold=True), fill=gray(234))
    draw.text((80, 108), "Next-Generation Analytics for Human Performance", font=load_font(18), fill=gray(170))

    x = 56
    for label, value in [("Total Predictions", "5,124"), ("Mean Score", "89.1"), ("Active Subjects", "150+"), ("Model Version", "v2.1")]:
        draw_metric(draw, (x, 154, x + 220, 274), label, value)
        x += 236

    trend_panel = (56, 296, 1020, 586)
    shadow(draw, trend_panel, offset=4)
    rounded(draw, trend_panel, radius=14, fill=gray(20), outline=gray(60), width=1)
    draw.text((78, 318), "Trend Insights", font=load_font(26, bold=True), fill=gray(234))
    rounded(draw, (78, 358, 990, 486), radius=10, fill=gray(16), outline=gray(48), width=1)
    draw_trend(draw, (92, 372, 948, 466))
    rounded(draw, (78, 498, 990, 566), radius=10, fill=gray(16), outline=gray(48), width=1)
    draw_heatmap(draw, (96, 514, 972, 556))

    for box in [(1040, 296, 1228, 436), (1040, 446, 1228, 586)]:
        shadow(draw, box, offset=4)
        rounded(draw, box, radius=14, fill=gray(22), outline=gray(62), width=1)
    draw.text((1056, 320), "End-to-End MLOps Stack:", font=load_font(18, bold=True), fill=gray(232))
    draw.text((1056, 350), "Ingestion, Training,", font=load_font(16), fill=gray(188))
    draw.text((1056, 376), "Production, Monitoring.", font=load_font(16), fill=gray(188))
    draw.text((1056, 468), "Production-Ready", font=load_font(18, bold=True), fill=gray(232))
    draw.text((1056, 496), "Architecture:", font=load_font(18, bold=True), fill=gray(232))
    draw.text((1056, 526), "Microservices,", font=load_font(16), fill=gray(188))
    draw.text((1056, 552), "Kubernetes, Observability.", font=load_font(16), fill=gray(188))

    tiny = load_font(12)
    draw.text((58, 594), "English / Deutsch", font=tiny, fill=gray(118))
    draw.text((906, 594), "Replace <owner>/<repo> with your GitHub repository path.", font=tiny, fill=gray(110))
    return img


def gif_frame(index: int, total: int) -> Image.Image:
    img = banner_frame().resize((1280, 720))
    draw = ImageDraw.Draw(img)
    p = index / max(total - 1, 1)

    # subtle step animation in trend panel
    x0 = 92
    y0 = 414
    for i in range(0, 790, 40):
        if i / 790 <= p:
            draw.line((x0 + i, y0, x0 + i + 16, y0 - 20), fill=gray(242), width=2)

    # status line animation
    rounded(draw, (76, 662, 1206, 706), radius=10, fill=gray(17), outline=gray(52), width=1)
    steps = [
        "Collecting data...",
        "Running feature engineering...",
        "Scoring active subjects...",
        "Updating trend insights...",
        "Persisting results to database...",
        "Dashboard refresh complete.",
    ]
    active = min(len(steps) - 1, int(p * len(steps)))
    draw.text((96, 676), steps[active], font=load_font(18), fill=gray(212))
    return img


def generate_banner() -> None:
    banner_frame().save(ASSETS / "banner.png", format="PNG")


def generate_gif() -> None:
    frames = [gif_frame(i, 30) for i in range(30)]
    frames[0].save(
        ASSETS / "demo.gif",
        save_all=True,
        append_images=frames[1:],
        duration=240,
        loop=0,
        optimize=True,
    )


if __name__ == "__main__":
    generate_banner()
    generate_gif()
    print(f"Generated: {ASSETS / 'banner.png'}")
    print(f"Generated: {ASSETS / 'demo.gif'}")
