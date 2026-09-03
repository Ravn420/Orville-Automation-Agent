"""Generate a multi-resolution ICO icon for Orville Signal Room."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Brand colours
BG = (30, 40, 65)          # deep navy
ACCENT = (80, 180, 255)     # sky-blue ring / wave
LETTER = (220, 235, 255)   # near-white O

ICO_PATH = Path(__file__).parent / "icon.ico"
ARTWORK = Path(__file__).parent / "icon_artwork.png"

SIZES = [16, 32, 48, 64, 128, 256]

def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = size // 2
    cy = size // 2
    r = size // 2 - 1

    # filled circle background
    draw.ellipse((0, 0, size-1, size-1), fill=BG)

    # outer ring
    draw.ellipse((1, 1, size-2, size-2), outline=ACCENT, width=max(1, size // 16))

    # inner ring (signal zone)
    inner_r = int(r * 0.68)
    draw.ellipse((cx-inner_r, cy-inner_r, cx+inner_r, cy+inner_r),
                 outline=ACCENT, width=max(1, size // 20))

    # centre dot
    dot_r = max(1, size // 12)
    draw.ellipse((cx-dot_r, cy-dot_r, cx+dot_r, cy+dot_r), fill=ACCENT)

    # letter O — draw a pill shape
    pad_x = int(size * 0.28)
    pad_y = int(size * 0.22)
    o_left = cx - pad_x
    o_top  = cy - pad_y
    o_right = cx + pad_x
    o_bottom = cy + pad_y

    # outer O circle
    outer_r_px = pad_x
    draw.ellipse((o_left - outer_r_px, o_top - outer_r_px,
                  o_right + outer_r_px, o_bottom + outer_r_px),
                 fill=None, outline=LETTER, width=max(1, size // 14))
    # inner O hole
    inner_r_px = max(1, int(outer_r_px * 0.55))
    draw.ellipse((cx - inner_r_px, cy - inner_r_px,
                  cx + inner_r_px, cy + inner_r_px),
                 fill=BG, outline=BG, width=0)

    return img

def main():
    imgs = [draw_icon(s) for s in SIZES]
    # save artwork preview
    artwork = draw_icon(256)
    artwork.save(ARTWORK, "PNG")
    print(f"Artwork saved: {ARTWORK}")

    # ICO: PIL expects a list of (size, mode, data) tuples
    ico_img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    ico_img.paste(draw_icon(256), (0, 0))
    ico_img.save(ICO_PATH, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"ICO saved: {ICO_PATH}  ({len(SIZES)} sizes)")


if __name__ == "__main__":
    main()
