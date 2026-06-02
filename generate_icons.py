from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

base_dir = Path("frontend/assets/icons")
base_dir.mkdir(parents=True, exist_ok=True)

def create_icon(size):
    img = Image.new("RGB", (size, size), "#0f172a")
    draw = ImageDraw.Draw(img)

    margin = int(size * 0.10)
    radius = int(size * 0.18)

    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill="#2563eb"
    )

    circle_size = int(size * 0.38)
    draw.ellipse(
        [
            size - margin - circle_size,
            margin,
            size - margin,
            margin + circle_size
        ],
        fill="#22c55e"
    )

    text = "CIQ"

    try:
        font = ImageFont.truetype("arialbd.ttf", int(size * 0.23))
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    draw.text(
        ((size - text_w) / 2, (size - text_h) / 2),
        text,
        fill="white",
        font=font
    )

    img.save(base_dir / f"icon-{size}.png")

create_icon(192)
create_icon(512)

print("Icone PWA create in frontend/assets/icons/")