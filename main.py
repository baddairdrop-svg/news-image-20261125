#!/usr/bin/env python3
"""news-image-20261125: draw one image summing up the world news of
Wednesday 25 November 2026 and write it to /output/entry.png.

Pure Python 3 standard library only (struct, zlib, os, sys): no network,
no fonts on disk, no randomness, no clock. The picture is a newspaper
front page: a header naming the day, six panels (one per main story),
each with a drawn scene, a headline, one big figure and one short
sub-line, plus a footer strip with three smaller stories. Every fact
comes from the research brief for this day; no quotes, numbers or faces
are invented, and no real person is drawn.

Run it the way the grader does:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
The output is a deterministic 1024x1024 PNG under 1 MiB: running it
twice writes the same bytes.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

# --- palette (newspaper front page) -------------------------------------
PAPER = (246, 241, 227)
INK = (27, 42, 65)
NAVY = (20, 38, 63)
NAVY_DARK = (13, 27, 46)
RED = (180, 35, 24)
BLUE = (29, 78, 137)
GOLD = (201, 162, 39)
GREEN = (30, 122, 52)
TEAL = (15, 118, 110)
ORANGE = (217, 119, 6)
PURPLE = (107, 33, 168)
GREY = (107, 114, 128)
LIGHT_GREY = (203, 213, 225)
WHITE = (255, 255, 255)
SKY = (135, 206, 235)
SKY_DARK = (30, 58, 95)
SAND = (222, 184, 135)
DUSK = (232, 121, 71)


# --- PNG writer (stdlib only) -------------------------------------------
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, pixels, width, height):
    """pixels: bytes of RGB rows, width*3 per row, top to bottom."""
    raw = b"".join(b"\x00" + pixels[y * width * 3:(y + 1) * width * 3]
                   for y in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(raw, 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# --- canvas ---------------------------------------------------------------
class Canvas:
    def __init__(self, width, height, bg):
        self.w = width
        self.h = height
        self.px = bytearray(bg * (width * height))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w + max(0, x)) * 3
            for xx in range(max(0, x), min(self.w, x + w)):
                self.px[base:base + 3] = bytes(color)
                base += 3

    def border(self, x, y, w, h, color, t=3):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x0 + a, y0 + b, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color, t=3):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d <= r * r:
                    self.set(xx, yy, color)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        ymin = min(y0, y1, y2)
        ymax = max(y0, y1, y2)
        for yy in range(ymin, ymax + 1):
            xs = []
            for (ax, ay, bx, by) in ((x0, y0, x1, y1),
                                     (x1, y1, x2, y2),
                                     (x2, y2, x0, y0)):
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by):
                    xs.append(ax + (yy - ay) * (bx - ax) // (by - ay))
            if len(xs) >= 2:
                for xx in range(min(xs), max(xs) + 1):
                    self.set(xx, yy, color)


# --- 5x7 bitmap font ------------------------------------------------------
# Each glyph is 7 rows of 5 pixels, "#" on, "." off. Uppercase text only.
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
}
FONT.update({
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    "-": ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "?": ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    ";": ["00000", "01100", "01100", "00000", "01100", "00100", "01000"],
    "*": ["00000", "10101", "01110", "10101", "00000", "00000", "00000"],
})

CHAR_W = 6  # 5 pixels + 1 spacing, times scale


def text_width(text, scale):
    return len(text) * CHAR_W * scale - scale


def draw_text(c, x, y, text, scale, color):
    for ci, ch in enumerate(text):
        glyph = FONT.get(ch, FONT["?"])
        gx = x + ci * CHAR_W * scale
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    c.rect(gx + col * scale, y + row * scale,
                           scale, scale, color)


def draw_text_center(c, cx, y, text, scale, color):
    draw_text(c, cx - text_width(text, scale) // 2, y, text, scale, color)


def wrap_text(text, max_chars):
    """Greedy word wrap; returns a list of lines, each <= max_chars."""
    lines = []
    for para in text.split("\n"):
        line = ""
        for word in para.split(" "):
            if not line:
                line = word
            elif len(line) + 1 + len(word) <= max_chars:
                line += " " + word
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def draw_block(c, x, y, width, text, scale, color, align="left"):
    """Wrapped text block; returns the y just below the last line."""
    max_chars = max(1, width // (CHAR_W * scale))
    line_h = 9 * scale
    yy = y
    for line in wrap_text(text, max_chars):
        if align == "center":
            draw_text_center(c, x + width // 2, yy, line, scale, color)
        else:
            draw_text(c, x, yy, line, scale, color)
        yy += line_h
    return yy


# --- scenes (one drawn picture per story, no faces) ------------------------
def scene_space(c, ox, oy, w, h):
    c.rect(ox, oy, w, h, SKY_DARK)
    for sx, sy in ((20, 15), (60, 40), (100, 12), (240, 20), (280, 50),
                   (300, 90), (40, 90), (90, 70), (200, 8), (130, 55)):
        c.rect(ox + sx, oy + sy, 3, 3, WHITE)
    # space station, top right
    c.rect(ox + 240, oy + 22, 56, 14, LIGHT_GREY)
    c.rect(ox + 212, oy + 24, 26, 10, BLUE)
    c.rect(ox + 298, oy + 24, 26, 10, BLUE)
    c.rect(ox + 264, oy + 14, 8, 8, GOLD)
    # rocket, centre
    c.rect(ox + 150, oy + 18, 28, 72, WHITE)
    c.triangle(ox + 150, oy + 18, ox + 178, oy + 18, ox + 164, oy + 2, RED)
    c.circle(ox + 164, oy + 48, 7, BLUE)
    c.triangle(ox + 150, oy + 90, ox + 138, oy + 112, ox + 150, oy + 78, RED)
    c.triangle(ox + 178, oy + 90, ox + 190, oy + 112, ox + 178, oy + 78, RED)
    c.triangle(ox + 154, oy + 90, ox + 174, oy + 90, ox + 164, oy + 128, ORANGE)
    c.triangle(ox + 158, oy + 90, ox + 170, oy + 90, ox + 164, oy + 116, GOLD)
    for cx, cy, r in ((150, 132, 8), (178, 136, 7), (164, 142, 9)):
        c.circle(ox + cx, oy + cy, r, LIGHT_GREY)
    # flags on the ground: Pakistan (green) and China (red)
    c.rect(ox, oy + h - 8, w, 8, NAVY_DARK)
    c.rect(ox + 20, oy + 128, 34, 20, GREEN)
    c.rect(ox + 20, oy + 128, 8, 20, WHITE)
    c.rect(ox + 62, oy + 128, 34, 20, RED)
    for dx, dy in ((6, 4), (14, 4), (10, 9), (16, 9), (8, 13)):
        c.rect(ox + 62 + dx, oy + 128 + dy, 3, 3, GOLD)


def scene_sea(c, ox, oy, w, h):
    c.rect(ox, oy, w, 62, (226, 232, 240))
    c.rect(ox, oy + 62, w, h - 62, (58, 110, 165))
    c.rect(ox + 30, oy + 14, 60, 12, WHITE)
    c.rect(ox + 210, oy + 26, 70, 12, WHITE)
    # drone, top right
    c.rect(ox + 236, oy + 30, 24, 10, INK)
    for dx, dy in ((232, 26), (260, 26), (232, 40), (260, 40)):
        c.circle(ox + dx, oy + dy, 5, GREY)
    c.line(ox + 248, oy + 40, ox + 230, oy + 62, INK, 2)
    # cargo ship
    for i, col in enumerate((RED, GOLD, GREEN, BLUE)):
        c.rect(ox + 64 + i * 34, oy + 64, 30, 24, col)
    c.rect(ox + 200, oy + 56, 34, 32, WHITE)
    c.rect(ox + 60, oy + 88, 200, 26, NAVY_DARK)
    c.rect(ox + 60, oy + 88, 200, 5, RED)
    # waves and map pins
    for wx in (20, 90, 160, 240, 290):
        c.line(ox + wx, oy + 128, ox + wx + 22, oy + 128, WHITE, 2)
    for px, py in ((36, 122), (292, 126)):
        c.circle(ox + px, oy + py, 8, RED)
        c.triangle(ox + px - 6, oy + py + 4, ox + px + 6, oy + py + 4,
                   ox + px, oy + py + 16, RED)
        c.circle(ox + px, oy + py, 3, WHITE)


def scene_markets(c, ox, oy, w, h):
    c.rect(ox, oy, w, h, (238, 238, 230))
    # falling bars, left to right
    heights = (108, 92, 68, 82, 44, 28)
    tops = []
    for i, bh in enumerate(heights):
        bx = ox + 24 + i * 46
        c.rect(bx, oy + 138 - bh, 32, bh, RED)
        tops.append((bx + 16, oy + 138 - bh))
    for (x0, y0), (x1, y1) in zip(tops, tops[1:]):
        c.line(x0, y0, x1, y1, INK, 3)
    # big down arrow, right
    c.line(ox + 296, oy + 18, ox + 296, oy + 66, RED, 6)
    c.triangle(ox + 280, oy + 58, ox + 312, oy + 58, ox + 296, oy + 88, RED)
    # tariff tag
    c.rect(ox + 16, oy + 12, 116, 28, RED)
    draw_text(c, ox + 26, oy + 19, "TARIFFS", 2, WHITE)
    # axis, bottom left
    c.line(ox + 12, oy + 138, ox + 316, oy + 138, INK, 2)


def scene_gaza(c, ox, oy, w, h):
    c.rect(ox, oy, w, 52, DUSK)
    c.rect(ox, oy + 52, w, 48, PURPLE)
    c.rect(ox, oy + 100, w, h - 100, NAVY_DARK)
    # skyline silhouettes
    for bx, bw, bh in ((0, 44, 52), (48, 30, 70), (82, 52, 44),
                       (138, 34, 64), (176, 46, 50), (226, 36, 74),
                       (266, 62, 58)):
        c.rect(ox + bx, oy + 158 - bh, bw, bh, INK)
    for wx, wy in ((12, 122), (58, 104), (96, 128), (148, 108),
                   (190, 124), (240, 100), (282, 116)):
        c.rect(ox + wx, oy + wy, 4, 4, GOLD)
    # smoke column rising from one building
    c.circle(ox + 208, oy + 96, 10, ORANGE)
    c.circle(ox + 208, oy + 82, 13, GREY)
    c.circle(ox + 204, oy + 64, 12, LIGHT_GREY)
    c.circle(ox + 210, oy + 46, 10, GREY)
    c.circle(ox + 206, oy + 30, 8, LIGHT_GREY)


def scene_yemen(c, ox, oy, w, h):
    c.rect(ox, oy, w, h, SAND)
    c.circle(ox + 44, oy + 26, 18, GOLD)
    # telecom tower, right
    c.line(ox + 268, oy + 148, ox + 288, oy + 40, INK, 3)
    c.line(ox + 308, oy + 148, ox + 288, oy + 40, INK, 3)
    for yy in (120, 96, 72):
        c.line(ox + 274, oy + yy, ox + 302, oy + yy, INK, 2)
    c.line(ox + 288, oy + 40, ox + 288, oy + 22, INK, 3)
    c.circle(ox + 288, oy + 18, 4, RED)
    # road, diagonal
    c.line(ox, oy + 148, ox + 240, oy + 108, (90, 90, 96), 16)
    # bus and truck on the road
    c.rect(ox + 60, oy + 108, 58, 22, WHITE)
    c.rect(ox + 66, oy + 112, 46, 8, BLUE)
    c.rect(ox + 150, oy + 100, 44, 22, (120, 72, 20))
    c.rect(ox + 194, oy + 108, 20, 14, INK)
    for wx in (70, 100, 160, 185, 205):
        c.circle(ox + wx, oy + 132, 5, INK)
    # dunes
    c.triangle(ox, oy + h, ox + 120, oy + h, ox + 60, oy + h - 22, (198, 158, 105))
    c.triangle(ox + 180, oy + h, ox + 328, oy + h, ox + 260, oy + h - 18,
               (198, 158, 105))


def scene_nepal(c, ox, oy, w, h):
    c.rect(ox, oy, w, 96, SKY)
    c.circle(ox + 282, oy + 24, 16, GOLD)
    # back mountain, front mountain with snow cap
    c.triangle(ox + 10, oy + 128, ox + 150, oy + 128, ox + 80, oy + 34,
               LIGHT_GREY)
    c.triangle(ox + 120, oy + 128, ox + 320, oy + 128, ox + 220, oy + 18, INK)
    c.triangle(ox + 198, oy + 42, ox + 242, oy + 42, ox + 220, oy + 18, WHITE)
    c.triangle(ox + 66, oy + 48, ox + 94, oy + 48, ox + 80, oy + 34, WHITE)
    # cracked ground
    c.rect(ox, oy + 128, w, 30, (120, 96, 64))
    c.line(ox + 40, oy + 128, ox + 70, oy + 142, INK, 3)
    c.line(ox + 70, oy + 142, ox + 52, oy + 156, INK, 3)
    c.line(ox + 200, oy + 128, ox + 230, oy + 140, INK, 3)
    c.line(ox + 230, oy + 140, ox + 214, oy + 158, INK, 3)
    # seismograph strip
    c.rect(ox + 16, oy + 96, 296, 26, WHITE)
    pts = [(16, 109), (40, 109), (52, 100), (64, 118), (76, 104),
           (88, 114), (110, 109), (140, 109), (152, 98), (164, 120),
           (176, 104), (188, 114), (210, 109), (250, 109), (262, 100),
           (274, 118), (286, 109), (312, 109)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        c.line(ox + x0, oy + y0, ox + x1, oy + y1, RED, 2)


SCENES = {
    "space": scene_space,
    "sea": scene_sea,
    "markets": scene_markets,
    "gaza": scene_gaza,
    "yemen": scene_yemen,
    "nepal": scene_nepal,
}

# kicker, colour, scene, headline, big figure, sub-line
PANELS = [
    ("SPACE", BLUE, "space", "PAKISTAN REACHES SPACE", "1ST",
     "PAKISTANI IN ORBIT ABOARD SHENZHOU-24 TO TIANGONG"),
    ("UKRAINE", TEAL, "sea", "ZELENSKYY CONFIRMS SEA STRIKES", "2 SHIPS",
     "GULF OF FINLAND HIT, WARSHIP SUNK OFF BENGHAZI"),
    ("MARKETS", RED, "markets", "AI STOCKS TUMBLE ON TARIFF FEARS", "-6%",
     "NVIDIA -6%, MICRON -11%, NASDAQ -1.5%"),
    ("GAZA", PURPLE, "gaza", "ISRAELI STRIKE KILLS HAMAS SECURITY CHIEF",
     "GAZA CITY", "NAEEM ABU NAHEL KILLED IN WESTERN GAZA CITY"),
    ("YEMEN", ORANGE, "yemen", "AIRSTRIKES KILL DOZENS IN YEMEN", "17 + 26",
     "KILLED IN HODEIDA AND LAHJ, HOUTHIS NEAR ADEN"),
    ("NEPAL", GREEN, "nepal", "EARTHQUAKE SHAKES EASTERN NEPAL", "5.6",
     "MAGNITUDE QUAKE IN KOSHI, NEAR TIBET, AT 07:17"),
]

FOOTER = [
    (TEAL, "ROHINGYA",
     "MALAYSIA TO RETURN 6,500+ REFUGEES TO MYANMAR"),
    (RED, "HEALTH",
     "AIDS DEATHS AT 570,000, LOWEST IN 20+ YEARS"),
    (GOLD, "USA",
     "TRUMP AWARDS MEDAL OF FREEDOM TO GIULIANI"),
]


def draw_panel(c, px, py, panel):
    kicker, color, scene, headline, stat, sub = panel
    w, h = 328, 384
    c.rect(px, py, w, h, WHITE)
    c.border(px, py, w, h, INK, 3)
    c.rect(px + 3, py + 3, w - 6, 30, color)
    draw_text_center(c, px + w // 2, py + 11, kicker, 2, WHITE)
    SCENES[scene](c, px + 3, py + 33, w - 6, 158)
    draw_block(c, px + 12, py + 198, w - 24, headline, 3, INK)
    draw_text(c, px + 12, py + 286, stat, 4, color)
    draw_block(c, px + 12, py + 322, w - 24, sub, 2, GREY)
    c.rect(px + 3, py + h - 7, w - 6, 4, color)


def draw():
    c = Canvas(WIDTH, HEIGHT, PAPER)
    # header
    c.rect(0, 0, WIDTH, 104, NAVY)
    draw_text_center(c, WIDTH // 2, 16, "WORLD NEWS IN ONE IMAGE", 4, WHITE)
    draw_text_center(c, WIDTH // 2, 58, "WEDNESDAY 25 NOVEMBER 2026", 3, GOLD)
    c.rect(0, 100, WIDTH, 4, RED)
    # six panels, 2 rows x 3 columns
    for i, panel in enumerate(PANELS):
        px = 8 + (i % 3) * 336
        py = 112 + (i // 3) * 392
        draw_panel(c, px, py, panel)
    # footer strip
    fy = 896
    c.rect(0, fy, WIDTH, 4, RED)
    c.rect(0, fy + 4, WIDTH, HEIGHT - fy - 4, WHITE)
    for i, (color, label, text) in enumerate(FOOTER):
        fx = 8 + i * 336
        c.rect(fx + 4, fy + 20, 16, 16, color)
        draw_text(c, fx + 28, fy + 21, label, 2, INK)
        draw_block(c, fx + 4, fy + 46, 320, text, 2, INK)
    draw_text_center(c, WIDTH // 2, 992, "SOURCES: REUTERS, AP, EURONEWS",
                     2, GREY)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    canvas = draw()
    write_png(path, bytes(canvas.px), WIDTH, HEIGHT)
    print("wrote %s (%d bytes)" % (path, os.path.getsize(path)))


if __name__ == "__main__":
    main()
