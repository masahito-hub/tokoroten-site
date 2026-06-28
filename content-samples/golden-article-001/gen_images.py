"""
Generate featured.png (1200x630) and comparison.png (1200x800) for golden-article-001.

Uses ONLY Python standard library (struct, zlib, math, os) — no external packages.
Issue #5 constraint: no new dependencies added.

Run from repo root:
  python3 content-samples/golden-article-001/gen_images.py

Output directory: content-samples/golden-article-001/images/
"""
import math
import os
import struct
import zlib

BASE    = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "images")
os.makedirs(IMG_DIR, exist_ok=True)

# ── Brand colors (R, G, B) ──────────────────────────────────────────────────
BG      = (246, 251, 250)   # #F6FBFA  site background
WATER   = (221, 244, 240)   # #DDF4F0  light teal
PRIMARY = ( 40, 119, 122)   # #28777A  heading / teal
TEXT    = ( 23,  63,  66)   # #173F42  body text
MUTED   = ( 89, 116, 119)   # #597477  subdued
ACCENT  = (215, 180, 106)   # #D7B46A  gold accent
WHITE   = (255, 255, 255)   # #FFFFFF


# ── Pure stdlib PNG encoder ─────────────────────────────────────────────────
def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def encode_png(pixels: list, width: int, height: int) -> bytes:
    """Encode a list-of-rows (each row is a list of (R,G,B) tuples) as PNG."""
    raw_rows = []
    for row in pixels:
        raw = b"\x00"  # filter type None
        for r, g, b in row:
            raw += bytes([r, g, b])
        raw_rows.append(raw)
    compressed = zlib.compress(b"".join(raw_rows), 9)
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr_data)
        + _png_chunk(b"IDAT", compressed)
        + _png_chunk(b"IEND", b"")
    )


def blend(c1: tuple, c2: tuple, t: float) -> tuple:
    return tuple(max(0, min(255, int(c1[i] + (c2[i] - c1[i]) * t))) for i in range(3))


def fill_rect(pixels: list, x0: int, y0: int, x1: int, y1: int, color: tuple):
    for y in range(max(0, y0), min(len(pixels), y1)):
        for x in range(max(0, x0), min(len(pixels[0]), x1)):
            pixels[y][x] = color


def draw_circle(pixels: list, cx: int, cy: int, r: int, color: tuple, alpha: float = 0.6):
    H, W = len(pixels), len(pixels[0])
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        for x in range(max(0, cx - r), min(W, cx + r + 1)):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist <= r:
                a = alpha * max(0.0, 1.0 - dist / r * 0.3)
                pixels[y][x] = blend(pixels[y][x], color, a)


# ── featured.png (1200×630) ─────────────────────────────────────────────────
def make_featured() -> str:
    W, H = 1200, 630
    pixels = [[BG] * W for _ in range(H)]

    # Gradient top section (WATER → BG)
    for y in range(int(H * 0.45)):
        t = y / (H * 0.45)
        row_color = blend(WATER, BG, t)
        for x in range(W):
            pixels[y][x] = row_color

    # Bottom stripe
    fill_rect(pixels, 0, H - 20, W, H - 12, ACCENT)
    fill_rect(pixels, 0, H - 12, W, H, PRIMARY)

    # Decorative wave lines
    for wave_n, (y_pct, amp, col, bw) in enumerate([
        (0.40, 18, PRIMARY, 4),
        (0.43, 14, WATER,   3),
        (0.46, 10, MUTED,   2),
    ]):
        y_c = int(H * y_pct)
        for x in range(W):
            phase = wave_n * 1.2
            wy = int(amp * math.sin(x * 2 * math.pi / 320 + phase))
            for dy in range(-bw, bw + 1):
                py = y_c + wy + dy
                if 0 <= py < H:
                    a = (1.0 - abs(dy) / (bw + 1)) * 0.55
                    pixels[py][x] = blend(pixels[py][x], col, a)

    # Decorative circles
    draw_circle(pixels,  120, 100,  60, WATER, 0.7)
    draw_circle(pixels, 1080,  90,  75, WATER, 0.6)
    draw_circle(pixels,  600,  80,  90, WATER, 0.4)

    # Title card
    cx, cy = W // 2, int(H * 0.62)
    cw, ch = 820, 160
    x0, y0 = cx - cw // 2, cy - ch // 2
    # Shadow
    for y in range(y0 + 4, y0 + ch + 4):
        for x in range(x0 + 4, x0 + cw + 4):
            if 0 <= y < H and 0 <= x < W:
                pixels[y][x] = blend(pixels[y][x], MUTED, 0.25)
    fill_rect(pixels, x0,     y0,     x0 + cw, y0 + ch, WHITE)
    fill_rect(pixels, x0,     y0,     x0 + cw, y0 + 6,  PRIMARY)
    fill_rect(pixels, x0,     y0,     x0 + 8,  y0 + ch, ACCENT)

    # Label band: カテゴリー識別色帯
    fill_rect(pixels, x0 + 8, y0 + 14, x0 + 200, y0 + 40, WATER)
    fill_rect(pixels, x0 + 8, y0 + 50, x0 + cw - 8, y0 + 54, MUTED)

    # Heading area indicator (colored bar mimicking text block)
    fill_rect(pixels, x0 + 8, y0 + 62, x0 + cw - 40, y0 + 82, blend(TEXT, WHITE, 0.85))
    fill_rect(pixels, x0 + 8, y0 + 88, x0 + cw - 120, y0 + 104, blend(MUTED, WHITE, 0.7))

    path = os.path.join(IMG_DIR, "featured.png")
    with open(path, "wb") as f:
        f.write(encode_png(pixels, W, H))
    print(f"Created {path} ({W}x{H})")
    return path


# ── comparison.png (1200×800) ───────────────────────────────────────────────
def make_comparison() -> str:
    W, H = 1200, 800
    MID = W // 2
    pixels = [[BG] * W for _ in range(H)]

    # Panel backgrounds
    for y in range(H):
        for x in range(MID):
            t = x / MID * 0.15
            pixels[y][x] = blend(WATER, BG, t)
        for x in range(MID, W):
            t = (x - MID) / (W - MID) * 0.15
            pixels[y][x] = blend(BG, (240, 245, 232), t)

    # Top header bar
    fill_rect(pixels, 0, 0, W, 60, PRIMARY)
    fill_rect(pixels, 0, 60, W, 68, ACCENT)

    # Header title indicator (white bar inside PRIMARY)
    fill_rect(pixels, 250, 14, 950, 46, blend(WHITE, PRIMARY, 0.3))

    # Centre divider
    for y in range(68, H - 60):
        pixels[y][MID - 1] = MUTED
        pixels[y][MID]     = MUTED
        pixels[y][MID + 1] = MUTED

    # Column headers — ところてん (left) / 寒天 (right)
    fill_rect(pixels, 60,       78, MID - 20,  148, PRIMARY)
    fill_rect(pixels, 60,      148, MID - 20,  154, ACCENT)
    fill_rect(pixels, MID + 20, 78, W - 60,   148, MUTED)
    fill_rect(pixels, MID + 20,148, W - 60,   154, ACCENT)

    # Header label bars (white text-placeholder inside column headers)
    fill_rect(pixels,  80, 94,  340, 130, blend(WHITE, PRIMARY, 0.25))
    fill_rect(pixels, MID + 40, 94, MID + 200, 130, blend(WHITE, MUTED, 0.35))

    # Comparison rows: (y_top, y_bot, label_color)
    ROWS = [
        (166, 246),   # 原料
        (256, 376),   # 製法
        (386, 476),   # 食感
        (486, 576),   # 主用途
        (586, 656),   # 共通
    ]
    label_colors = [PRIMARY, MUTED, PRIMARY, MUTED, ACCENT]

    for (y0b, y1b), lcol in zip(ROWS, label_colors):
        # White content boxes
        fill_rect(pixels, 60,       y0b, MID - 20, y1b, WHITE)
        fill_rect(pixels, MID + 20, y0b, W - 60,   y1b, WHITE)
        # Left accent bar
        fill_rect(pixels, 60,       y0b, 66,        y1b, PRIMARY)
        fill_rect(pixels, MID + 20, y0b, MID + 26,  y1b, MUTED)
        # Bottom shadow
        for y in range(y1b, min(H, y1b + 3)):
            for x in range(60, MID - 20):
                pixels[y][x] = blend(pixels[y][x], MUTED, 0.2)
            for x in range(MID + 20, W - 60):
                pixels[y][x] = blend(pixels[y][x], MUTED, 0.2)

        # Centre label badge
        lbl_w, lbl_h = 90, 32
        lbl_x = MID - lbl_w // 2
        lbl_y = y0b + (y1b - y0b) // 2 - lbl_h // 2
        fill_rect(pixels, lbl_x, lbl_y, lbl_x + lbl_w, lbl_y + lbl_h, lcol)

        # Content value placeholders (tinted bars to indicate text)
        bar_y = y0b + 14
        bar_h = min(20, (y1b - y0b) // 3)
        fill_rect(pixels, 90, bar_y, MID - 40, bar_y + bar_h,
                  blend(TEXT, WHITE, 0.82))
        fill_rect(pixels, MID + 50, bar_y, W - 80, bar_y + bar_h,
                  blend(TEXT, WHITE, 0.82))
        if (y1b - y0b) > 80:
            fill_rect(pixels, 90, bar_y + bar_h + 8, MID - 80, bar_y + bar_h * 2 + 8,
                      blend(MUTED, WHITE, 0.75))
            fill_rect(pixels, MID + 50, bar_y + bar_h + 8, W - 120, bar_y + bar_h * 2 + 8,
                      blend(MUTED, WHITE, 0.75))

    # Bottom bar
    fill_rect(pixels, 0, H - 18, W, H, PRIMARY)

    path = os.path.join(IMG_DIR, "comparison.png")
    with open(path, "wb") as f:
        f.write(encode_png(pixels, W, H))
    print(f"Created {path} ({W}x{H})")
    return path


if __name__ == "__main__":
    make_featured()
    make_comparison()
    print("Done.")
