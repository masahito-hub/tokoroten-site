/**
 * Generate featured.png (1200x630) and comparison.png (1200x800)
 * for golden-article-001. Uses only Node.js built-in modules (zlib, fs, path).
 * Run: node content-samples/golden-article-001/gen_images.js
 */

'use strict';
const zlib = require('zlib');
const fs   = require('fs');
const path = require('path');

const BASE    = path.dirname(path.resolve(__filename));
const IMG_DIR = path.join(BASE, 'images');
fs.mkdirSync(IMG_DIR, { recursive: true });

// Brand colors [R, G, B]
const BG      = [246, 251, 250];  // #F6FBFA
const WATER   = [221, 244, 240];  // #DDF4F0
const PRIMARY = [ 40, 119, 122];  // #28777A
const TEXT    = [ 23,  63,  66];  // #173F42
const MUTED   = [ 89, 116, 119];  // #597477
const ACCENT  = [215, 180, 106];  // #D7B46A
const WHITE   = [255, 255, 255];  // #FFFFFF

// ── PNG encoder ──────────────────────────────────────────────────────────────

function crc32(buf) {
  const table = (() => {
    const t = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = (c & 1) ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
      t[n] = c;
    }
    return t;
  })();
  let c = 0xFFFFFFFF;
  for (let i = 0; i < buf.length; i++) c = table[(c ^ buf[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

function pngChunk(type, data) {
  const len = Buffer.allocUnsafe(4);
  len.writeUInt32BE(data.length, 0);
  const typeAndData = Buffer.concat([Buffer.from(type), data]);
  const crc = Buffer.allocUnsafe(4);
  crc.writeUInt32BE(crc32(typeAndData), 0);
  return Buffer.concat([len, typeAndData, crc]);
}

function encodePng(pixels, W, H) {
  // Build raw scanline data
  const rawRows = [];
  for (let y = 0; y < H; y++) {
    const row = Buffer.allocUnsafe(1 + W * 3);
    row[0] = 0; // filter: None
    for (let x = 0; x < W; x++) {
      const [r, g, b] = pixels[y][x];
      row[1 + x * 3]     = r;
      row[1 + x * 3 + 1] = g;
      row[1 + x * 3 + 2] = b;
    }
    rawRows.push(row);
  }
  const raw       = Buffer.concat(rawRows);
  const compressed = zlib.deflateSync(raw, { level: 9 });

  const ihdrData = Buffer.allocUnsafe(13);
  ihdrData.writeUInt32BE(W, 0);
  ihdrData.writeUInt32BE(H, 4);
  ihdrData[8]  = 8;  // bit depth
  ihdrData[9]  = 2;  // color type: RGB
  ihdrData[10] = 0;  // compression
  ihdrData[11] = 0;  // filter
  ihdrData[12] = 0;  // interlace

  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),
    pngChunk('IHDR', ihdrData),
    pngChunk('IDAT', compressed),
    pngChunk('IEND', Buffer.alloc(0)),
  ]);
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function blend(c1, c2, t) {
  return [
    Math.round(c1[0] + (c2[0] - c1[0]) * t),
    Math.round(c1[1] + (c2[1] - c1[1]) * t),
    Math.round(c1[2] + (c2[2] - c1[2]) * t),
  ];
}

function fillRect(pixels, x0, y0, x1, y1, color) {
  for (let y = y0; y < y1; y++)
    for (let x = x0; x < x1; x++)
      pixels[y][x] = color;
}

function drawCircle(pixels, W, H, cx, cy, r, color, alpha) {
  for (let y = Math.max(0, cy - r); y < Math.min(H, cy + r + 1); y++) {
    for (let x = Math.max(0, cx - r); x < Math.min(W, cx + r + 1); x++) {
      const dist = Math.hypot(x - cx, y - cy);
      if (dist <= r) {
        const a = alpha * (1 - dist / r * 0.4);
        pixels[y][x] = blend(pixels[y][x], color, a);
      }
    }
  }
}

function makePixels(W, H, fillColor) {
  return Array.from({ length: H }, () => Array.from({ length: W }, () => [...fillColor]));
}

// ── featured.png 1200 × 630 ──────────────────────────────────────────────────

function makeFeatured() {
  const W = 1200, H = 630;
  const pixels = makePixels(W, H, BG);

  // Water-tone gradient top section
  for (let y = 0; y < Math.floor(H * 0.45); y++) {
    const t = y / (H * 0.45);
    const c = blend(WATER, BG, t);
    for (let x = 0; x < W; x++) pixels[y][x] = c;
  }

  // Bottom primary stripe
  fillRect(pixels, 0, H - 12, W, H, PRIMARY);
  // Gold accent stripe
  fillRect(pixels, 0, H - 22, W, H - 12, ACCENT);

  // Wave lines
  const waves = [
    { yPct: 0.40, amp: 18, col: PRIMARY, bw: 4 },
    { yPct: 0.43, amp: 14, col: WATER,   bw: 3 },
    { yPct: 0.46, amp: 10, col: MUTED,   bw: 2 },
  ];
  waves.forEach(({ yPct, amp, col, bw }, wn) => {
    const yC = Math.floor(H * yPct);
    for (let x = 0; x < W; x++) {
      const waveY = Math.round(amp * Math.sin(x * 2 * Math.PI / 320 + wn * 1.2));
      for (let dy = -bw; dy <= bw; dy++) {
        const y = yC + waveY + dy;
        if (y >= 0 && y < H) {
          const a = (1 - Math.abs(dy) / (bw + 1)) * 0.55;
          pixels[y][x] = blend(pixels[y][x], col, a);
        }
      }
    }
  });

  // Center card
  const cx = W >> 1, cy = Math.floor(H * 0.62);
  const cw = 820, ch = 140;
  const x0 = cx - (cw >> 1), y0 = cy - (ch >> 1);
  // Shadow
  for (let y = y0 + 4; y < y0 + ch + 4; y++)
    for (let x = x0 + 4; x < x0 + cw + 4; x++)
      if (y >= 0 && y < H && x >= 0 && x < W)
        pixels[y][x] = blend(pixels[y][x], MUTED, 0.2);
  fillRect(pixels, x0, y0, x0 + cw, y0 + ch, WHITE);
  fillRect(pixels, x0, y0, x0 + cw, y0 + 6,  PRIMARY);
  fillRect(pixels, x0, y0, x0 + 8,  y0 + ch, ACCENT);

  // Decorative circles
  [
    [120, 100, 60, WATER, 0.7],
    [80,  150, 35, PRIMARY, 0.3],
    [1080, 90, 75, WATER, 0.6],
    [1110, 160, 40, PRIMARY, 0.25],
    [600,  80, 90, WATER, 0.4],
  ].forEach(([x, y, r, col, a]) => drawCircle(pixels, W, H, x, y, r, col, a));

  // Small accent dots
  [
    [200, 300, 8,  ACCENT],
    [950, 340, 6,  ACCENT],
    [350, 420, 5,  PRIMARY],
    [820, 400, 7,  PRIMARY],
  ].forEach(([x, y, r, col]) => drawCircle(pixels, W, H, x, y, r, col, 0.85));

  const outPath = path.join(IMG_DIR, 'featured.png');
  fs.writeFileSync(outPath, encodePng(pixels, W, H));
  console.log(`Created ${outPath} (${W}x${H})`);
}

// ── comparison.png 1200 × 800 ────────────────────────────────────────────────

function makeComparison() {
  const W = 1200, H = 800;
  const MID = W >> 1;
  const pixels = makePixels(W, H, BG);

  // Left panel (ところてん) — cool water tones
  for (let y = 0; y < H; y++)
    for (let x = 0; x < MID; x++)
      pixels[y][x] = blend(WATER, BG, (x / MID) * 0.18);

  // Right panel (寒天) — warm off-white
  const WARM_BG = [240, 245, 235];
  for (let y = 0; y < H; y++)
    for (let x = MID; x < W; x++)
      pixels[y][x] = blend(BG, WARM_BG, ((x - MID) / (W - MID)) * 0.18);

  // Center divider
  for (let y = 60; y < H - 60; y++) {
    pixels[y][MID - 1] = MUTED;
    pixels[y][MID]     = MUTED;
    pixels[y][MID + 1] = MUTED;
  }

  // Header bar
  fillRect(pixels, 0, 0, W, 56, PRIMARY);
  fillRect(pixels, 0, 56, W, 64, ACCENT);

  // Center badge (shared origin)
  drawCircle(pixels, W, H, MID, 64, 36, WHITE,   0.95);
  drawCircle(pixels, W, H, MID, 64, 30, ACCENT,  0.75);
  drawCircle(pixels, W, H, MID, 64, 20, PRIMARY, 0.95);

  // Left header block
  fillRect(pixels, 60,      90,  MID - 20, 150, PRIMARY);
  fillRect(pixels, 60,      150, MID - 20, 156, ACCENT);

  // Right header block
  fillRect(pixels, MID + 20, 90,  W - 60, 150, MUTED);
  fillRect(pixels, MID + 20, 150, W - 60, 156, ACCENT);

  // Info boxes — left
  [
    [90,  180, 460, 270],
    [90,  285, 460, 420],
    [90,  435, 460, 540],
    [90,  555, 460, 650],
    [90,  665, 460, 760],
  ].forEach(([bx0, by0, bx1, by1]) => {
    // shadow
    for (let y = by1; y < Math.min(H, by1 + 3); y++)
      for (let x = bx0; x < bx1; x++)
        pixels[y][x] = blend(pixels[y][x], MUTED, 0.2);
    fillRect(pixels, bx0, by0, bx1, by1, WHITE);
    fillRect(pixels, bx0, by0, bx0 + 6, by1, PRIMARY);
  });

  // Info boxes — right
  [
    [MID + 40, 180, W - 90, 270],
    [MID + 40, 285, W - 90, 420],
    [MID + 40, 435, W - 90, 540],
    [MID + 40, 555, W - 90, 650],
    [MID + 40, 665, W - 90, 760],
  ].forEach(([bx0, by0, bx1, by1]) => {
    for (let y = by1; y < Math.min(H, by1 + 3); y++)
      for (let x = bx0; x < bx1; x++)
        pixels[y][x] = blend(pixels[y][x], MUTED, 0.2);
    fillRect(pixels, bx0, by0, bx1, by1, WHITE);
    fillRect(pixels, bx0, by0, bx0 + 6, by1, MUTED);
  });

  // Bottom accent wave
  for (let y = H - 80; y < H - 20; y++) {
    const waveX = Math.round(12 * Math.sin(y * 2 * Math.PI / 60));
    for (let dx = -3; dx <= 3; dx++) {
      const px = MID + waveX + dx;
      if (px >= 0 && px < W) pixels[y][px] = ACCENT;
    }
  }

  // Bottom bar
  fillRect(pixels, 0, H - 16, W, H, PRIMARY);

  const outPath = path.join(IMG_DIR, 'comparison.png');
  fs.writeFileSync(outPath, encodePng(pixels, W, H));
  console.log(`Created ${outPath} (${W}x${H})`);
}

makeFeatured();
makeComparison();
console.log('Done.');
