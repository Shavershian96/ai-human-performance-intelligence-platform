from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "C:/Windows/Fonts/segoeuib.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/arial.ttf",
            ]
        )
    for path in candidates:
        p = Path(path)
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def lerp_color(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def make_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        color = lerp_color(top, bottom, t)
        for x in range(w):
            px[x, y] = color
    return img


def rounded_rect(draw: ImageDraw.ImageDraw, xy, r, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def generate_banner() -> None:
    size = (1600, 480)
    base = make_gradient(size, (7, 17, 39), (8, 45, 73))
    draw = ImageDraw.Draw(base)

    # Decorative lines
    accent = (40, 210, 190)
    for y_off in [320, 355]:
        points = [(0, y_off), (250, y_off - 28), (520, y_off + 18), (840, y_off - 30), (1180, y_off + 12), (1600, y_off - 20)]
        draw.line(points, fill=accent, width=3)

    # Cards
    rounded_rect(draw, (80, 82, 640, 395), 22, fill=(255, 255, 255, 18), outline=(120, 200, 240), width=2)
    rounded_rect(draw, (690, 110, 1520, 220), 18, fill=(12, 32, 56), outline=(65, 170, 220), width=2)
    rounded_rect(draw, (690, 245, 1520, 355), 18, fill=(12, 32, 56), outline=(65, 170, 220), width=2)

    title_font = load_font(54, bold=True)
    subtitle_font = load_font(28)
    small_font = load_font(24, bold=True)
    body_font = load_font(22)

    draw.text((110, 120), "AI Human Performance", font=title_font, fill=(238, 246, 255))
    draw.text((110, 186), "Intelligence Platform", font=title_font, fill=(238, 246, 255))
    draw.text((110, 270), "Production-Grade MLOps", font=subtitle_font, fill=(155, 222, 255))
    draw.text((110, 315), "Microservices • Kubernetes • Observability", font=subtitle_font, fill=(155, 222, 255))

    draw.text((725, 140), "End-to-End Stack", font=small_font, fill=(173, 232, 255))
    draw.text((725, 175), "Ingestion • Training • Prediction • Monitoring", font=body_font, fill=(228, 241, 255))
    draw.text((725, 275), "Built for Production", font=small_font, fill=(173, 232, 255))
    draw.text((725, 310), "Resilience, CI/CD, and Recruiter-Ready Presentation", font=body_font, fill=(228, 241, 255))

    base.save(ASSETS / "banner-pro.png", format="PNG")


def dashboard_slide(title: str, subtitle: str, metrics: list[tuple[str, str]], chart_color: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", (1280, 720), (245, 248, 252))
    draw = ImageDraw.Draw(img)

    title_font = load_font(46, bold=True)
    sub_font = load_font(24)
    kpi_title = load_font(22, bold=True)
    kpi_value = load_font(30, bold=True)

    # Header
    rounded_rect(draw, (40, 28, 1240, 118), 14, fill=(12, 32, 56))
    draw.text((70, 55), title, font=title_font, fill=(236, 244, 255))
    draw.text((70, 94), subtitle, font=sub_font, fill=(172, 220, 246))

    # KPI cards
    x = 52
    for label, value in metrics:
        rounded_rect(draw, (x, 148, x + 280, 288), 16, fill=(255, 255, 255), outline=(214, 226, 241), width=2)
        draw.text((x + 20, 175), label, font=kpi_title, fill=(66, 90, 120))
        draw.text((x + 20, 220), value, font=kpi_value, fill=(18, 39, 68))
        x += 300

    # Chart area mock
    rounded_rect(draw, (52, 318, 1228, 682), 16, fill=(255, 255, 255), outline=(214, 226, 241), width=2)
    draw.text((80, 346), "Trend Overview", font=kpi_title, fill=(66, 90, 120))

    points = [(100, 620), (260, 560), (420, 590), (580, 510), (760, 535), (940, 470), (1120, 500)]
    draw.line(points, fill=chart_color, width=7)
    for p in points:
        draw.ellipse((p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6), fill=chart_color)

    return img


def generate_gif() -> None:
    slides = [
        dashboard_slide(
            "AI Human Performance Dashboard",
            "Model Predictions",
            [("Total Predictions", "1,284"), ("Latest Score", "86.2"), ("Athletes", "34"), ("Model Version", "v1.0")],
            (38, 170, 248),
        ),
        dashboard_slide(
            "AI Human Performance Dashboard",
            "Performance Metrics",
            [("Test R²", "0.91"), ("Test MAE", "3.42"), ("Test RMSE", "5.18"), ("Req/sec", "12.8")],
            (45, 192, 152),
        ),
        dashboard_slide(
            "AI Human Performance Dashboard",
            "Historical Data",
            [("Records", "58,420"), ("Date Range", "24 months"), ("Avg Recovery", "7.4"), ("Avg Stress", "4.8")],
            (147, 112, 219),
        ),
    ]

    gif_path = ASSETS / "dashboard-demo-pro.gif"
    slides[0].save(
        gif_path,
        save_all=True,
        append_images=slides[1:],
        duration=[1300, 1300, 1300],
        loop=0,
        optimize=True,
    )

    # Keep compatibility with current README references if needed.
    slides[0].save(ASSETS / "dashboard-frame-1.png")
    slides[1].save(ASSETS / "dashboard-frame-2.png")
    slides[2].save(ASSETS / "dashboard-frame-3.png")


if __name__ == "__main__":
    generate_banner()
    generate_gif()
    print("Generated professional assets:")
    print(f"- {ASSETS / 'banner-pro.png'}")
    print(f"- {ASSETS / 'dashboard-demo-pro.gif'}")
