"""
Generate featured.png (1200×630) and comparison.png (1200×800) for golden-article-001.

Requires: Pillow>=9.0  (pip install Pillow)
Japanese font: NotoSansCJK or similar (see FONT_SEARCH_PATHS below)
  Ubuntu/Debian: sudo apt-get install fonts-noto-cjk
  macOS:         brew install font-noto-sans-cjk-jp

Run from repo root:
  python3 content-samples/golden-article-001/gen_images.py
"""
import os
import struct
import zlib

BASE    = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "images")
os.makedirs(IMG_DIR, exist_ok=True)

# ── PIL import ─────────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("WARNING: Pillow not found. Falling back to stdlib-only (no text).")
    print("  pip install Pillow")

# ── Japanese font search ────────────────────────────────────────────────────
FONT_SEARCH_PATHS = [
    # Linux (Noto CJK)
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    # macOS
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/NotoSansCJKjp-Regular.otf",
    # Windows
    "C:/Windows/Fonts/YuGothR.ttc",
    "C:/Windows/Fonts/meiryo.ttc",
]


def find_jp_font():
    for p in FONT_SEARCH_PATHS:
        if os.path.exists(p):
            return p
    # Try fc-list
    try:
        import subprocess
        out = subprocess.check_output(
            ["fc-list", ":lang=ja", "--format=%{file}\n"],
            stderr=subprocess.DEVNULL, timeout=3
        ).decode()
        for line in out.splitlines():
            line = line.strip()
            if line and os.path.exists(line):
                return line
    except Exception:
        pass
    return None


# ── Brand colors ────────────────────────────────────────────────────────────
BG      = (246, 251, 250)   # #F6FBFA
WATER   = (221, 244, 240)   # #DDF4F0
PRIMARY = ( 40, 119, 122)   # #28777A
TEXT    = ( 23,  63,  66)   # #173F42
MUTED   = ( 89, 116, 119)   # #597477
ACCENT  = (215, 180, 106)   # #D7B46A
WHITE   = (255, 255, 255)


# ── PIL-based generation ────────────────────────────────────────────────────
def make_featured_pil(font_path):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Water-tone gradient top section
    for y in range(int(H * 0.45)):
        t = y / (H * 0.45)
        r = int(WATER[0] + (BG[0] - WATER[0]) * t)
        g = int(WATER[1] + (BG[1] - WATER[1]) * t)
        b = int(WATER[2] + (BG[2] - WATER[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Decorative wave lines
    import math
    for wave_n, (y_pct, amp, col) in enumerate([
        (0.40, 18, PRIMARY),
        (0.43, 14, WATER),
        (0.46, 10, MUTED),
    ]):
        y_c = int(H * y_pct)
        pts = []
        for x in range(0, W, 2):
            phase = wave_n * 1.2
            wy = int(amp * math.sin(x * 2 * math.pi / 320 + phase))
            pts.append((x, y_c + wy))
        if pts:
            draw.line(pts, fill=col, width=3)

    # Accent bottom stripe
    draw.rectangle([0, H - 20, W, H - 12], fill=ACCENT)
    draw.rectangle([0, H - 12, W, H], fill=PRIMARY)

    # Decorative circles
    for cx, cy, r, col in [
        (120, 100, 60, WATER),
        (1080, 90, 75, WATER),
        (600, 80, 90, WATER),
    ]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)

    # Title card background
    cx, cy = W // 2, int(H * 0.62)
    cw, ch = 820, 160
    x0, y0 = cx - cw // 2, cy - ch // 2
    # Shadow
    draw.rectangle([x0 + 4, y0 + 4, x0 + cw + 4, y0 + ch + 4], fill=MUTED)
    # White card
    draw.rectangle([x0, y0, x0 + cw, y0 + ch], fill=WHITE)
    # Top border
    draw.rectangle([x0, y0, x0 + cw, y0 + 6], fill=PRIMARY)
    # Left accent bar
    draw.rectangle([x0, y0, x0 + 8, y0 + ch], fill=ACCENT)

    # Text: article title
    try:
        font_title = ImageFont.truetype(font_path, 38) if font_path else ImageFont.load_default()
        font_sub   = ImageFont.truetype(font_path, 24) if font_path else ImageFont.load_default()
    except Exception:
        font_title = ImageFont.load_default()
        font_sub   = ImageFont.load_default()

    title_text = "ところてんと寒天は何が違う？"
    sub_text   = "原料・作り方・食感を比較"

    # Center text in card
    tx = x0 + 40
    ty = y0 + 28
    draw.text((tx, ty), title_text, font=font_title, fill=TEXT)
    draw.text((tx, ty + 58), sub_text, font=font_sub, fill=MUTED)

    path = os.path.join(IMG_DIR, "featured.png")
    img.save(path, "PNG")
    print(f"Created {path} ({W}x{H})")


def make_comparison_pil(font_path):
    W, H = 1200, 800
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    MID = W // 2

    # Left panel background (teal tint)
    for x in range(MID):
        t = x / MID * 0.12
        r = int(WATER[0] + (BG[0] - WATER[0]) * t)
        g = int(WATER[1] + (BG[1] - WATER[1]) * t)
        b = int(WATER[2] + (BG[2] - WATER[2]) * t)
        draw.line([(x, 0), (x, H)], fill=(r, g, b))

    # Right panel background (warm off-white)
    for x in range(MID, W):
        t = (x - MID) / (W - MID) * 0.12
        rv = int(BG[0] + (240 - BG[0]) * t)
        gv = int(BG[1] + (245 - BG[1]) * t)
        bv = int(BG[2] + (232 - BG[2]) * t)
        draw.line([(x, 0), (x, H)], fill=(rv, gv, bv))

    # Top header bar
    draw.rectangle([0, 0, W, 60], fill=PRIMARY)
    draw.rectangle([0, 60, W, 68], fill=ACCENT)

    # Center divider
    draw.rectangle([MID - 2, 68, MID + 2, H - 60], fill=MUTED)

    # Bottom bar
    draw.rectangle([0, H - 18, W, H], fill=PRIMARY)

    # ── Fonts ──────────────────────────────────────────────────────────────
    try:
        font_header_lg = ImageFont.truetype(font_path, 36) if font_path else ImageFont.load_default()
        font_header_sm = ImageFont.truetype(font_path, 30) if font_path else ImageFont.load_default()
        font_label     = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
        font_body      = ImageFont.truetype(font_path, 17) if font_path else ImageFont.load_default()
        font_top       = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
    except Exception:
        font_header_lg = font_header_sm = font_label = font_body = font_top = ImageFont.load_default()

    # Top header text
    top_text = "ところてんと寒天の違い"
    draw.text((W // 2 - 200, 14), top_text, font=font_top, fill=WHITE)

    # ── Left column header ──────────────────────────────────────────────
    draw.rectangle([60, 78, MID - 20, 148], fill=PRIMARY)
    draw.rectangle([60, 148, MID - 20, 154], fill=ACCENT)
    draw.text((120, 94), "ところてん", font=font_header_lg, fill=WHITE)

    # ── Right column header ─────────────────────────────────────────────
    draw.rectangle([MID + 20, 78, W - 60, 148], fill=MUTED)
    draw.rectangle([MID + 20, 148, W - 60, 154], fill=ACCENT)
    draw.text((MID + 80, 94), "寒天", font=font_header_lg, fill=WHITE)

    # ── Comparison rows ─────────────────────────────────────────────────
    # (label, left_value, right_value, y_top, y_bot)
    rows = [
        ("原料",
         "テングサ（主）",
         "テングサ・オゴノリ等",
         166, 246),
        ("製法",
         "煮出し→冷却固化のみ",
         "煮出し→冷却→凍結乾燥",
         256, 376),
        ("食感",
         "ぷるぷる・のど越しよい",
         "シャキッと歯切れよい",
         386, 476),
        ("主用途",
         "そのまま食べる",
         "羊羹・あんみつ等の凝固剤",
         486, 576),
        ("共通",
         "植物性 / 低カロリー / 食物繊維源",
         "植物性 / 低カロリー / 食物繊維源",
         586, 656),
    ]

    for label, left_val, right_val, y0, y1 in rows:
        # Left box
        draw.rectangle([60, y0, MID - 20, y1], fill=WHITE)
        draw.rectangle([60, y0, 66, y1], fill=PRIMARY)
        # Right box
        draw.rectangle([MID + 20, y0, W - 60, y1], fill=WHITE)
        draw.rectangle([MID + 20, y0, MID + 26, y1], fill=MUTED)
        # Box shadows
        draw.rectangle([60, y1, MID - 20, y1 + 3], fill=(200, 210, 210))
        draw.rectangle([MID + 20, y1, W - 60, y1 + 3], fill=(200, 210, 210))

        # Label bar (center)
        lbl_w = 90
        lbl_x = MID - lbl_w // 2
        lbl_y = y0 + (y1 - y0) // 2 - 16
        draw.rectangle([lbl_x, lbl_y, lbl_x + lbl_w, lbl_y + 32], fill=ACCENT)
        draw.text((lbl_x + 10, lbl_y + 6), label, font=font_label, fill=TEXT)

        # Row values
        row_text_y = y0 + 14
        draw.text((90, row_text_y), left_val, font=font_body, fill=TEXT)
        draw.text((MID + 50, row_text_y), right_val, font=font_body, fill=TEXT)

    path = os.path.join(IMG_DIR, "comparison.png")
    img.save(path, "PNG")
    print(f"Created {path} ({W}x{H})")


# ── stdlib PNG fallback ─────────────────────────────────────────────────────
def png_chunk(chunk_type, data):
    length = struct.pack(">I", len(data))
    crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return length + chunk_type + data + crc


def encode_png_raw(pixels, width, height):
    raw_rows = []
    for row in pixels:
        raw = b"\x00"
        for r, g, b in row:
            raw += bytes([r, g, b])
        raw_rows.append(raw)
    compressed = zlib.compress(b"".join(raw_rows), 9)
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr_data)
        + png_chunk(b"IDAT", compressed)
        + png_chunk(b"IEND", b"")
    )


def blend(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def fill_rect(pixels, x0, y0, x1, y1, color):
    for y in range(y0, y1):
        for x in range(x0, x1):
            pixels[y][x] = color


def make_featured_stdlib():
    import math
    W, H = 1200, 630
    pixels = [[BG] * W for _ in range(H)]

    for y in range(int(H * 0.45)):
        t = y / (H * 0.45)
        row_color = blend(WATER, BG, t)
        for x in range(W):
            pixels[y][x] = row_color

    for y in range(H - 12, H):
        fill_rect(pixels, 0, y, W, y + 1, PRIMARY)
    for y in range(H - 20, H - 12):
        fill_rect(pixels, 0, y, W, y + 1, ACCENT)

    for wave_n, (y_pct, amp, col, bw) in enumerate([
        (0.40, 18, PRIMARY, 4),
        (0.43, 14, WATER, 3),
        (0.46, 10, MUTED, 2),
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

    cx, cy = W // 2, int(H * 0.62)
    cw, ch = 820, 160
    x0, y0 = cx - cw // 2, cy - ch // 2
    for y in range(y0 + 4, y0 + ch + 4):
        for x in range(x0 + 4, x0 + cw + 4):
            if 0 <= y < H and 0 <= x < W:
                pixels[y][x] = blend(pixels[y][x], MUTED, 0.25)
    fill_rect(pixels, x0, y0, x0 + cw, y0 + ch, WHITE)
    fill_rect(pixels, x0, y0, x0 + cw, y0 + 6, PRIMARY)
    fill_rect(pixels, x0, y0, x0 + 8, y0 + ch, ACCENT)

    def draw_circle(ccx, ccy, r, color, alpha=0.6):
        for y in range(max(0, ccy - r), min(H, ccy + r + 1)):
            for x in range(max(0, ccx - r), min(W, ccx + r + 1)):
                dist = ((x - ccx) ** 2 + (y - ccy) ** 2) ** 0.5
                if dist <= r:
                    a = alpha * max(0, 1 - dist / r * 0.3)
                    pixels[y][x] = blend(pixels[y][x], color, a)

    draw_circle(120, 100, 60, WATER, 0.7)
    draw_circle(1080, 90, 75, WATER, 0.6)
    draw_circle(600, 80, 90, WATER, 0.4)

    path = os.path.join(IMG_DIR, "featured.png")
    with open(path, "wb") as f:
        f.write(encode_png_raw(pixels, W, H))
    print(f"Created {path} ({W}x{H}) [stdlib fallback — no text]")


def make_comparison_stdlib():
    import math
    W, H = 1200, 800
    pixels = [[BG] * W for _ in range(H)]
    MID = W // 2

    for y in range(H):
        for x in range(MID):
            t = x / MID * 0.15
            pixels[y][x] = blend(WATER, BG, t)
        for x in range(MID, W):
            t = (x - MID) / (W - MID) * 0.15
            pixels[y][x] = blend(BG, (240, 245, 232), t)

    for y in range(60, H - 60):
        pixels[y][MID - 1] = MUTED
        pixels[y][MID]     = MUTED
        pixels[y][MID + 1] = MUTED

    fill_rect(pixels, 0, 0, W, 56, PRIMARY)
    fill_rect(pixels, 0, 56, W, 64, ACCENT)

    fill_rect(pixels, 60, 90, MID - 20, 148, PRIMARY)
    fill_rect(pixels, 60, 148, MID - 20, 154, ACCENT)
    fill_rect(pixels, MID + 20, 90, W - 60, 148, MUTED)
    fill_rect(pixels, MID + 20, 148, W - 60, 154, ACCENT)

    row_bounds = [(166, 246), (256, 376), (386, 476), (486, 576), (586, 656)]
    for y0b, y1b in row_bounds:
        fill_rect(pixels, 60, y0b, MID - 20, y1b, WHITE)
        fill_rect(pixels, 60, y0b, 66, y1b, PRIMARY)
        fill_rect(pixels, MID + 20, y0b, W - 60, y1b, WHITE)
        fill_rect(pixels, MID + 20, y0b, MID + 26, y1b, MUTED)
        for y in range(y1b, min(H, y1b + 3)):
            for x in range(60, MID - 20):
                pixels[y][x] = blend(pixels[y][x], MUTED, 0.2)
            for x in range(MID + 20, W - 60):
                pixels[y][x] = blend(pixels[y][x], MUTED, 0.2)

    fill_rect(pixels, 0, H - 16, W, H, PRIMARY)

    path = os.path.join(IMG_DIR, "comparison.png")
    with open(path, "wb") as f:
        f.write(encode_png_raw(pixels, W, H))
    print(f"Created {path} ({W}x{H}) [stdlib fallback — no text]")


# ── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if HAS_PIL:
        font_path = find_jp_font()
        if font_path:
            print(f"Using font: {font_path}")
        else:
            print("WARNING: No Japanese font found. Text may not render correctly.")
            print("  Ubuntu: sudo apt-get install fonts-noto-cjk")
            print("  macOS:  brew install font-noto-sans-cjk-jp")
        make_featured_pil(font_path)
        make_comparison_pil(font_path)
    else:
        print("Using stdlib fallback (no text rendering).")
        make_featured_stdlib()
        make_comparison_stdlib()
    print("Done.")
