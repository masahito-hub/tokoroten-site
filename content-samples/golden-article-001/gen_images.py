"""
Generate featured.png and comparison.png for golden-article-001.
Uses only Python standard library (struct, zlib) — no external packages.
Run from repo root: python3 content-samples/golden-article-001/gen_images.py
"""
import struct
import zlib
import os

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "images")
os.makedirs(IMG_DIR, exist_ok=True)

# Brand colors (R, G, B)
BG        = (246, 251, 250)   # #F6FBFA
WATER     = (221, 244, 240)   # #DDF4F0
PRIMARY   = (40,  119, 122)   # #28777A
TEXT      = (23,   63,  66)   # #173F42
MUTED     = (89,  116, 119)   # #597477
ACCENT    = (215, 180, 106)   # #D7B46A
WHITE     = (255, 255, 255)   # #FFFFFF


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    length = struct.pack(">I", len(data))
    crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return length + chunk_type + data + crc


def encode_png(pixels: list[list[tuple[int, int, int]]], width: int, height: int) -> bytes:
    """pixels[y][x] = (R, G, B)"""
    raw_rows = []
    for row in pixels:
        raw = b"\x00"  # filter type: None
        for r, g, b in row:
            raw += bytes([r, g, b])
        raw_rows.append(raw)
    raw_data = b"".join(raw_rows)
    compressed = zlib.compress(raw_data, 9)

    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    chunks = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr_data)
        + png_chunk(b"IDAT", compressed)
        + png_chunk(b"IEND", b"")
    )
    return chunks


def blend(c1: tuple, c2: tuple, t: float) -> tuple:
    """Linear blend between c1 (t=0) and c2 (t=1)."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def fill_rect(pixels, x0, y0, x1, y1, color):
    for y in range(y0, y1):
        for x in range(x0, x1):
            pixels[y][x] = color


def draw_wave_band(pixels, y_center, amplitude, width, color, band_width=6):
    """Draw a wavy horizontal band."""
    import math
    for x in range(width):
        wave = int(amplitude * math.sin(x * 2 * math.pi / (width / 3)))
        for dy in range(-band_width, band_width + 1):
            y = y_center + wave + dy
            if 0 <= y < len(pixels):
                alpha = 1.0 - abs(dy) / (band_width + 1)
                pixels[y][x] = blend(pixels[y][x], color, alpha * 0.7)


# ──────────────────────────────────────────────
#  featured.png  1200 × 630
# ──────────────────────────────────────────────
def make_featured():
    W, H = 1200, 630
    pixels = [[BG] * W for _ in range(H)]

    # Water-tone gradient top section
    for y in range(0, int(H * 0.45)):
        t = y / (H * 0.45)
        row_color = blend(WATER, BG, t)
        for x in range(W):
            pixels[y][x] = row_color

    # Accent stripe (bottom band)
    for y in range(H - 12, H):
        for x in range(W):
            pixels[y][x] = PRIMARY

    # Gold accent stripe above bottom
    for y in range(H - 20, H - 12):
        for x in range(W):
            pixels[y][x] = ACCENT

    # Decorative wave lines
    import math
    for wave_n, (y_pct, amp, col, bw) in enumerate([
        (0.40, 18, PRIMARY, 4),
        (0.43, 14, WATER,   3),
        (0.46, 10, MUTED,   2),
    ]):
        y_c = int(H * y_pct)
        for x in range(W):
            phase = wave_n * 1.2
            wave_y = int(amp * math.sin(x * 2 * math.pi / 320 + phase))
            for dy in range(-bw, bw + 1):
                y = y_c + wave_y + dy
                if 0 <= y < H:
                    alpha = 1.0 - abs(dy) / (bw + 1)
                    pixels[y][x] = blend(pixels[y][x], col, alpha * 0.55)

    # Center block — title background card
    cx, cy = W // 2, int(H * 0.62)
    cw, ch = 820, 140
    x0, y0 = cx - cw // 2, cy - ch // 2
    # White card with slight shadow
    for y in range(y0 + 4, y0 + ch + 4):
        for x in range(x0 + 4, x0 + cw + 4):
            if 0 <= y < H and 0 <= x < W:
                pixels[y][x] = blend(pixels[y][x], MUTED, 0.25)
    fill_rect(pixels, x0, y0, x0 + cw, y0 + ch, WHITE)
    # Card top border in primary
    fill_rect(pixels, x0, y0, x0 + cw, y0 + 6, PRIMARY)
    # Left accent mark
    fill_rect(pixels, x0, y0, x0 + 8, y0 + ch, ACCENT)

    # Decorative circles (water drops)
    def draw_circle(cx, cy, r, color, alpha=0.6):
        for y in range(max(0, cy - r), min(H, cy + r + 1)):
            for x in range(max(0, cx - r), min(W, cx + r + 1)):
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if dist <= r:
                    a = alpha * max(0, 1 - dist / r * 0.3)
                    pixels[y][x] = blend(pixels[y][x], color, a)

    draw_circle(120, 100, 60, WATER, 0.7)
    draw_circle(80,  150, 35, PRIMARY, 0.3)
    draw_circle(1080, 90, 75, WATER, 0.6)
    draw_circle(1110, 160, 40, PRIMARY, 0.25)
    draw_circle(600,  80, 90, WATER, 0.4)

    # Small dots
    for dx, dy, r, col in [
        (200, 300, 8, ACCENT),
        (950, 340, 6, ACCENT),
        (350, 420, 5, PRIMARY),
        (820, 400, 7, PRIMARY),
    ]:
        draw_circle(dx, dy, r, col, 0.8)

    path = os.path.join(IMG_DIR, "featured.png")
    with open(path, "wb") as f:
        f.write(encode_png(pixels, W, H))
    print(f"Created {path} ({W}x{H})")


# ──────────────────────────────────────────────
#  comparison.png  1200 × 800
# ──────────────────────────────────────────────
def make_comparison():
    import math
    W, H = 1200, 800
    pixels = [[BG] * W for _ in range(H)]

    MID = W // 2

    # Left panel (ところてん) — water/teal tones
    for y in range(H):
        for x in range(0, MID):
            t = x / MID * 0.15
            pixels[y][x] = blend(WATER, BG, t)

    # Right panel (寒天) — warmer muted tone
    for y in range(H):
        for x in range(MID, W):
            t = (x - MID) / (W - MID) * 0.15
            c = blend(BG, (240, 245, 232), t)
            pixels[y][x] = c

    # Center divider line
    for y in range(60, H - 60):
        pixels[y][MID - 1] = MUTED
        pixels[y][MID]     = MUTED
        pixels[y][MID + 1] = MUTED

    # Top header bar
    fill_rect(pixels, 0, 0, W, 56, PRIMARY)
    # Accent stripe below header
    fill_rect(pixels, 0, 56, W, 64, ACCENT)

    # Center circle at top — shared origin badge
    def draw_circle_soft(cx, cy, r, color, alpha=1.0):
        for y in range(max(0, cy - r), min(H, cy + r + 1)):
            for x in range(max(0, cx - r), min(W, cx + r + 1)):
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if dist <= r:
                    a = alpha * (1 - dist / r * 0.5)
                    pixels[y][x] = blend(pixels[y][x], color, a)

    draw_circle_soft(MID, 64, 36, WHITE, 0.95)
    draw_circle_soft(MID, 64, 30, ACCENT, 0.7)
    draw_circle_soft(MID, 64, 20, PRIMARY, 0.9)

    # Left panel header block
    fill_rect(pixels, 60, 90, MID - 20, 150, PRIMARY)
    # Left title accent bar
    fill_rect(pixels, 60, 150, MID - 20, 156, ACCENT)

    # Right panel header block
    fill_rect(pixels, MID + 20, 90, W - 60, 150, MUTED)
    # Right title accent bar
    fill_rect(pixels, MID + 20, 150, W - 60, 156, ACCENT)

    # Info boxes — left (ところてん)
    box_left_specs = [
        (90,  180, 460, 270,  PRIMARY),   # 原料ボックス
        (90,  285, 460, 420,  PRIMARY),   # 製法ボックス
        (90,  435, 460, 540,  PRIMARY),   # 食感ボックス
        (90,  555, 460, 650,  PRIMARY),   # 食べ方ボックス
        (90,  665, 460, 760,  PRIMARY),   # 栄養ボックス
    ]
    for (bx0, by0, bx1, by1, col) in box_left_specs:
        fill_rect(pixels, bx0, by0, bx1, by1, WHITE)
        fill_rect(pixels, bx0, by0, bx0 + 6, by1, col)
        # Subtle bottom shadow
        for y in range(by1, min(H, by1 + 3)):
            for x in range(bx0, bx1):
                pixels[y][x] = blend(pixels[y][x], MUTED, 0.2)

    # Info boxes — right (寒天)
    box_right_specs = [
        (MID + 40, 180, W - 90, 270,  MUTED),
        (MID + 40, 285, W - 90, 420,  MUTED),
        (MID + 40, 435, W - 90, 540,  MUTED),
        (MID + 40, 555, W - 90, 650,  MUTED),
        (MID + 40, 665, W - 90, 760,  MUTED),
    ]
    for (bx0, by0, bx1, by1, col) in box_right_specs:
        fill_rect(pixels, bx0, by0, bx1, by1, WHITE)
        fill_rect(pixels, bx0, by0, bx0 + 6, by1, col)
        for y in range(by1, min(H, by1 + 3)):
            for x in range(bx0, bx1):
                pixels[y][x] = blend(pixels[y][x], MUTED, 0.2)

    # Connecting arrow / wave between panels at center
    for y in range(H - 80, H - 20):
        wave = int(12 * math.sin(y * 2 * math.pi / 60))
        for dx in range(-3, 4):
            px = MID + wave + dx
            if 0 <= px < W:
                pixels[y][px] = ACCENT

    # Bottom bar
    fill_rect(pixels, 0, H - 16, W, H, PRIMARY)

    path = os.path.join(IMG_DIR, "comparison.png")
    with open(path, "wb") as f:
        f.write(encode_png(pixels, W, H))
    print(f"Created {path} ({W}x{H})")


if __name__ == "__main__":
    make_featured()
    make_comparison()
    print("Done.")
