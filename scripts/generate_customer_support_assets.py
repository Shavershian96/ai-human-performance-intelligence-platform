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


def gray(v: int) -> tuple[int, int, int]:
    return (v, v, v)


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


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


def draw_line_graph(draw: ImageDraw.ImageDraw, box, tone: int, variant: int = 0):
    x1, y1, x2, y2 = box
    if variant == 0:
        points = [(x1 + 14, y2 - 44), (x1 + 130, y2 - 74), (x1 + 250, y2 - 66), (x1 + 380, y2 - 98), (x1 + 520, y2 - 88), (x1 + 660, y2 - 112), (x1 + 790, y2 - 96), (x1 + 910, y2 - 120)]
    elif variant == 1:
        points = [(x1 + 14, y2 - 62), (x1 + 130, y2 - 80), (x1 + 250, y2 - 108), (x1 + 380, y2 - 94), (x1 + 520, y2 - 126), (x1 + 660, y2 - 116), (x1 + 790, y2 - 96), (x1 + 910, y2 - 78)]
    else:
        points = [(x1 + 14, y2 - 36), (x1 + 130, y2 - 58), (x1 + 250, y2 - 54), (x1 + 380, y2 - 70), (x1 + 520, y2 - 62), (x1 + 660, y2 - 84), (x1 + 790, y2 - 72), (x1 + 910, y2 - 90)]

    draw.line(points, fill=gray(tone), width=3)
    for p in points:
        draw.ellipse((p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3), fill=gray(min(242, tone + 10)))


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
            rounded(draw, (cx1, cy1, cx1 + cell_w, cy1 + cell_h), radius=4, fill=gray(tone), outline=gray(min(210, tone + 22)), width=1)


def generate_banner() -> None:
    img = gradient((1280, 640), 8, 18)
    draw = ImageDraw.Draw(img)

    shadow(draw, (28, 22, 1252, 614), offset=6)
    rounded(draw, (28, 22, 1252, 614), radius=18, fill=gray(14), outline=gray(52), width=1)

    rounded(draw, (56, 48, 872, 178), radius=12, fill=gray(19), outline=gray(58), width=1)
    draw.text((80, 76), "AI HUMAN PERFORMANCE", font=load_font(40, bold=True), fill=gray(236))
    draw.text((80, 120), "INTELLIGENCE PLATFORM", font=load_font(40, bold=True), fill=gray(236))
    draw.text((82, 158), "NEXT-GENERATION ANALYTICS FOR HUMAN PERFORMANCE", font=load_font(12, bold=True), fill=gray(165))

    rounded(draw, (892, 48, 1224, 108), radius=10, fill=gray(21), outline=gray(60), width=1)
    rounded(draw, (892, 118, 1224, 178), radius=10, fill=gray(21), outline=gray(60), width=1)
    draw.text((914, 68), "END-TO-END STACK", font=load_font(16, bold=True), fill=gray(225))
    draw.text((914, 90), "INGESTION | TRAINING | PREDICTION", font=load_font(12), fill=gray(176))
    draw.text((914, 138), "BUILT FOR PRODUCTION", font=load_font(16, bold=True), fill=gray(225))
    draw.text((914, 160), "MICROSERVICES | K8S | OBSERVABILITY", font=load_font(12), fill=gray(176))

    rounded(draw, (56, 206, 1224, 580), radius=14, fill=gray(19), outline=gray(58), width=1)
    draw.text((80, 232), "TREND INSIGHTS", font=load_font(26, bold=True), fill=gray(232))
    rounded(draw, (80, 274, 1200, 446), radius=10, fill=gray(16), outline=gray(46), width=1)

    for i in range(7):
        y = 296 + i * 22
        draw.line((96, y, 1184, y), fill=gray(40), width=1)
    for i in range(11):
        x = 96 + i * 108
        draw.line((x, 296, x, 430), fill=gray(34), width=1)

    draw_line_graph(draw, (96, 296, 1184, 430), 226, 0)
    draw_line_graph(draw, (96, 296, 1184, 430), 186, 1)
    draw_line_graph(draw, (96, 296, 1184, 430), 152, 2)

    rounded(draw, (80, 456, 1200, 560), radius=10, fill=gray(16), outline=gray(46), width=1)
    draw_heatmap(draw, (98, 474, 1182, 542))
    draw.text((82, 590), "ENGLISH | DEUTSCH", font=load_font(11, bold=True), fill=gray(130))
    draw.text((1034, 590), "REPLACE GITHUB PATH", font=load_font(11, bold=True), fill=gray(116))

    img.save(ASSETS / "banner.png", format="PNG")


def dashboard_slide(title: str, subtitle: str, metrics: list[tuple[str, str]], variant: int) -> Image.Image:
    img = gradient((1280, 720), 8, 18)
    draw = ImageDraw.Draw(img)

    shadow(draw, (30, 22, 1248, 694), offset=6)
    rounded(draw, (30, 22, 1248, 694), radius=16, fill=gray(14), outline=gray(54), width=1)

    # Title without emoji, matching the "remove emoji" baseline.
    rounded(draw, (58, 44, 1220, 126), radius=12, fill=gray(19), outline=gray(58), width=1)
    draw.text((84, 68), title, font=load_font(42, bold=True), fill=gray(236))
    draw.text((86, 108), subtitle, font=load_font(20), fill=gray(168))

    x = 66
    for label, value in metrics:
        rounded(draw, (x, 152, x + 276, 286), radius=14, fill=gray(22), outline=gray(60), width=1)
        draw.text((x + 18, 178), label.upper(), font=load_font(14, bold=True), fill=gray(166))
        draw.text((x + 18, 220), value, font=load_font(36, bold=True), fill=gray(236))
        x += 294

    rounded(draw, (66, 314, 1214, 668), radius=14, fill=gray(18), outline=gray(56), width=1)
    draw.text((92, 340), "Trend Overview", font=load_font(24, bold=True), fill=gray(228))
    graph_box = (92, 380, 1188, 566)
    rounded(draw, graph_box, radius=10, fill=gray(15), outline=gray(44), width=1)

    gx1, gy1, gx2, gy2 = 108, 396, 1172, 550
    for i in range(7):
        y = gy1 + i * 22
        draw.line((gx1, y, gx2, y), fill=gray(40), width=1)
    for i in range(13):
        x_grid = gx1 + int((gx2 - gx1) * i / 12)
        draw.line((x_grid, gy1, x_grid, gy2), fill=gray(34), width=1)

    draw_line_graph(draw, (gx1, gy1, gx2, gy2), 226, variant)
    draw_line_graph(draw, (gx1, gy1, gx2, gy2), 190, (variant + 1) % 3)
    draw_line_graph(draw, (gx1, gy1, gx2, gy2), 156, (variant + 2) % 3)

    rounded(draw, (92, 578, 1188, 654), radius=10, fill=gray(15), outline=gray(44), width=1)
    draw_heatmap(draw, (108, 596, 1172, 640))

    return img


def generate_gif() -> None:
    slides = [
        dashboard_slide(
            "AI HUMAN PERFORMANCE DASHBOARD",
            "Model Predictions",
            [("Total Predictions", "5,124"), ("Latest Score", "89.1"), ("Active Subjects", "150+"), ("Model Version", "v2.1")],
            0,
        ),
        dashboard_slide(
            "AI HUMAN PERFORMANCE DASHBOARD",
            "Performance Metrics",
            [("Test R²", "0.93"), ("Test MAE", "2.96"), ("Test RMSE", "4.71"), ("Req/Sec", "18.4")],
            1,
        ),
        dashboard_slide(
            "AI HUMAN PERFORMANCE DASHBOARD",
            "Historical Data",
            [("Records", "74,920"), ("Date Range", "36 months"), ("Avg Recovery", "7.8"), ("Avg Stress", "4.4")],
            2,
        ),
    ]
    slides[0].save(
        ASSETS / "demo.gif",
        save_all=True,
        append_images=slides[1:],
        duration=[1400, 1400, 1400],
        loop=0,
        optimize=True,
    )


if __name__ == "__main__":
    generate_banner()
    generate_gif()
    print(f"Generated: {ASSETS / 'banner.png'}")
    print(f"Generated: {ASSETS / 'demo.gif'}")
