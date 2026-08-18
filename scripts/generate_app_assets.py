"""Generate high-resolution branding assets for Koota Match mobile app."""
import os
import math
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "mobile", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Editorial Color Palette
COLOR_IVORY = (250, 248, 245, 255)       # #FAF8F5
COLOR_TERRACOTTA = (139, 58, 43, 255)    # #8B3A2B
COLOR_TERRA_DARK = (107, 44, 32, 255)    # #6B2C20
COLOR_GOLD = (212, 175, 55, 255)         # #D4AF37
COLOR_GOLD_LIGHT = (235, 206, 110, 255)  # #EBCE6E
COLOR_TRANSPARENT = (0, 0, 0, 0)

def draw_koota_emblem(draw, center_x, center_y, radius):
    """Draw a refined geometric Koota harmony crest."""
    # Outer gold ring
    draw.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        outline=COLOR_GOLD,
        width=int(radius * 0.04),
    )
    
    # Inner terracotta solid circle
    r_inner = radius * 0.88
    draw.ellipse(
        [center_x - r_inner, center_y - r_inner, center_x + r_inner, center_y + r_inner],
        fill=COLOR_TERRACOTTA,
    )
    
    # Concentric 8-point geometric lotus/star
    points = []
    num_points = 16
    for i in range(num_points * 2):
        angle = i * (math.pi / num_points)
        r = (radius * 0.76) if i % 2 == 0 else (radius * 0.48)
        px = center_x + r * math.cos(angle)
        py = center_y + r * math.sin(angle)
        points.append((px, py))
    draw.polygon(points, fill=COLOR_TERRA_DARK, outline=COLOR_GOLD)
    
    # Center gold diamond / emblem
    r_core = radius * 0.30
    draw.ellipse(
        [center_x - r_core, center_y - r_core, center_x + r_core, center_y + r_core],
        fill=COLOR_GOLD,
    )
    
    # Core terracotta heart dot
    r_dot = radius * 0.12
    draw.ellipse(
        [center_x - r_dot, center_y - r_dot, center_x + r_dot, center_y + r_dot],
        fill=COLOR_TERRACOTTA,
    )

def generate_icon(size=1024):
    img = Image.new("RGBA", (size, size), COLOR_IVORY)
    draw = ImageDraw.Draw(img)
    draw_koota_emblem(draw, size // 2, size // 2, int(size * 0.38))
    icon_path = os.path.join(ASSETS_DIR, "icon.png")
    img.save(icon_path, "PNG")
    print(f"Generated {icon_path}")

def generate_adaptive_icon(size=1024):
    img = Image.new("RGBA", (size, size), COLOR_TRANSPARENT)
    draw = ImageDraw.Draw(img)
    draw_koota_emblem(draw, size // 2, size // 2, int(size * 0.34))
    icon_path = os.path.join(ASSETS_DIR, "adaptive-icon.png")
    img.save(icon_path, "PNG")
    print(f"Generated {icon_path}")

def generate_splash(width=2048, height=2048):
    img = Image.new("RGBA", (width, height), COLOR_IVORY)
    draw = ImageDraw.Draw(img)
    center_x = width // 2
    center_y = height // 2 - 120
    draw_koota_emblem(draw, center_x, center_y, 360)
    
    # Subtle accent lines below
    line_y = center_y + 440
    draw.line([center_x - 180, line_y, center_x + 180, line_y], fill=COLOR_GOLD, width=4)
    
    splash_path = os.path.join(ASSETS_DIR, "splash.png")
    img.save(splash_path, "PNG")
    print(f"Generated {splash_path}")

def generate_favicon(size=48):
    img = Image.new("RGBA", (size, size), COLOR_IVORY)
    draw = ImageDraw.Draw(img)
    draw_koota_emblem(draw, size // 2, size // 2, int(size * 0.44))
    favicon_path = os.path.join(ASSETS_DIR, "favicon.png")
    img.save(favicon_path, "PNG")
    print(f"Generated {favicon_path}")

if __name__ == "__main__":
    generate_icon()
    generate_adaptive_icon()
    generate_splash()
    generate_favicon()
    print("All branding assets generated successfully.")
