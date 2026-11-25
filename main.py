#!/usr/bin/env python3
"""news-image-20261125 v2: draw one image summing up the world news of
Wednesday 25 November 2026 and write it to /output/entry.png.

Pure Python 3 standard library only (struct, zlib, os, sys): no network,
no fonts on disk, no randomness, no clock. Concept: "THE WORLD IN 24
HOURS" - the page is one day running midnight to midnight. A black
masthead, a region-count strip, a four-block timeline spine (00-06 /
06-12 / 12-18 / 18-24 UTC) with a red dot at each hero's real hour, three
chronological hero cards with drawn scenes, a five-number stat strip, a
ten-card grid (numbered 4-13, continuing the heroes), a dotted world map
with numbered pins, and a red DATE CHECK box listing the big stories
that were EXCLUDED because they happened on 24 November, not the 25th.

Every story on the page was verified against a source dated 25 November
2026 (Reuters, WSJ, Yonhap, NATO, European Council, Kremlin, ABC News,
European Parliament, PM of Australia, UN Women, PIB, OHCHR). No quotes,
numbers or faces are invented, and no real person is drawn. All text on
the page is English.

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

# --- palette ------------------------------------------------------------
PAPER = (246, 241, 227)
INK = (27, 42, 65)
NAVY = (20, 38, 63)
NAVY_DARK = (13, 27, 46)
BLACK = (10, 10, 12)
RED = (180, 35, 24)
RED_LIGHT = (253, 235, 232)
BLUE = (29, 78, 137)
GOLD = (201, 162, 39)
GREEN = (30, 122, 52)
TEAL = (15, 118, 110)
ORANGE = (217, 119, 6)
PURPLE = (107, 33, 168)
GREY = (107, 114, 128)
LIGHT_GREY = (203, 213, 225)
MAP_DOT = (90, 110, 140)
WHITE = (255, 255, 255)
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


def draw_text_right(c, rx, y, text, scale, color):
    draw_text(c, rx - text_width(text, scale), y, text, scale, color)


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


# --- hero scenes (one drawn picture per hero, no faces) -------------------
# One consistent style: flat vector shapes, deep colours, one light source
# (sun / moon / tower light), tiny human silhouettes only for scale.

def scene_markets(c, ox, oy, w, h):
    """Seoul at dawn: skyline with N Seoul Tower, red bars falling."""
    c.rect(ox, oy, w, h, NAVY_DARK)
    # first light on the horizon
    c.rect(ox, oy + 96, w, 6, (120, 60, 40))
    c.rect(ox, oy + 102, w, 4, (160, 90, 50))
    # N Seoul Tower, left
    c.line(ox + 42, oy + 118, ox + 42, oy + 34, LIGHT_GREY, 3)
    c.circle(ox + 42, oy + 30, 10, LIGHT_GREY)
    c.circle(ox + 42, oy + 30, 4, GOLD)
    # skyline silhouettes
    for bx, bw, bh in ((0, 34, 34), (58, 26, 48), (88, 40, 30),
                       (132, 30, 56), (166, 44, 38), (214, 28, 52),
                       (246, 38, 32), (288, 37, 46)):
        c.rect(ox + bx, oy + h - bh, bw, bh, BLACK)
    for wx, wy in ((8, 128), (66, 118), (140, 108), (176, 122),
                   (222, 112), (256, 126), (296, 116)):
        c.rect(ox + wx, oy + wy, 4, 5, GOLD)
    # falling red bars
    heights = (86, 74, 58, 66, 40, 24)
    tops = []
    for i, bh in enumerate(heights):
        bx = ox + 14 + i * 48
        c.rect(bx, oy + 108 - bh, 30, bh, RED)
        tops.append((bx + 15, oy + 108 - bh))
    for (x0, y0), (x1, y1) in zip(tops, tops[1:]):
        c.line(x0, y0, x1, y1, WHITE, 3)
    # big down arrow, right
    c.line(ox + 296, oy + 14, ox + 296, oy + 52, RED, 6)
    c.triangle(ox + 280, oy + 44, ox + 312, oy + 44, ox + 296, oy + 72, RED)


def scene_space(c, ox, oy, w, h):
    """Shenzhou-24 lifts off for Tiangong; Pakistan and China flags."""
    c.rect(ox, oy, w, h, SKY_DARK)
    for sx, sy in ((20, 15), (60, 40), (100, 12), (240, 20), (280, 50),
                   (300, 90), (40, 90), (90, 70), (200, 8), (130, 55)):
        c.rect(ox + sx, oy + sy, 3, 3, WHITE)
    # space station, top right (kept clear of the UTC chip at top right)
    c.rect(ox + 206, oy + 22, 56, 14, LIGHT_GREY)
    c.rect(ox + 178, oy + 24, 26, 10, BLUE)
    c.rect(ox + 264, oy + 24, 26, 10, BLUE)
    c.rect(ox + 230, oy + 14, 8, 8, GOLD)
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


def scene_summit(c, ox, oy, w, h):
    """Mar-a-Lago at dusk: warm sky, white villa, palms, two flags."""
    c.rect(ox, oy, w, 52, DUSK)
    c.rect(ox, oy + 52, w, 46, PURPLE)
    c.rect(ox, oy + 98, w, h - 98, NAVY_DARK)
    # low sun
    c.circle(ox + 282, oy + 46, 16, GOLD)
    c.circle(ox + 282, oy + 46, 10, (250, 220, 130))
    # palm trees
    for px, lean in ((36, -1), (296, 1)):
        c.line(ox + px, oy + 148, ox + px + lean * 10, oy + 78, (60, 40, 20), 4)
        for dx, dy in ((-26, -14), (-14, -24), (0, -28), (14, -24), (26, -14)):
            c.line(ox + px + lean * 10, oy + 78,
                   ox + px + lean * 10 + dx, oy + 78 + dy, GREEN, 3)
    # white villa
    c.rect(ox + 108, oy + 92, 110, 56, WHITE)
    c.triangle(ox + 100, oy + 92, ox + 226, oy + 92, ox + 163, oy + 66, RED)
    c.rect(ox + 156, oy + 52, 14, 16, WHITE)
    c.triangle(ox + 152, oy + 52, ox + 174, oy + 52, ox + 163, oy + 40, RED)
    for wx in (118, 140, 162, 184, 206):
        c.rect(ox + wx, oy + 104, 10, 18, NAVY)
        c.circle(ox + wx + 5, oy + 104, 5, NAVY)
    c.rect(ox + 158, oy + 122, 10, 26, INK)
    # two flags on poles in front of the villa
    for fx, flag in ((96, "us"), (232, "nato")):
        c.line(ox + fx, oy + 148, ox + fx, oy + 82, INK, 2)
        if flag == "us":
            for i in range(7):
                c.rect(ox + fx + 2, oy + 84 + i * 4, 26,
                       2, RED if i % 2 == 0 else WHITE)
            c.rect(ox + fx + 2, oy + 84, 12, 12, BLUE)
        else:
            c.rect(ox + fx + 2, oy + 84, 26, 28, BLUE)
            c.triangle(ox + fx + 15, oy + 88, ox + fx + 15, oy + 108,
                       ox + fx + 10, oy + 98, WHITE)
            c.triangle(ox + fx + 5, oy + 98, ox + fx + 25, oy + 98,
                       ox + fx + 15, oy + 93, WHITE)
    # two small suited figures for scale, no faces
    for fx in (146, 172):
        c.circle(ox + fx + 4, oy + 130, 4, INK)
        c.rect(ox + fx, oy + 134, 8, 14, INK)


SCENES = {
    "markets": scene_markets,
    "space": scene_space,
    "summit": scene_summit,
}


# --- grid pictograms (26x26, one per grid card) ---------------------------
def icon_building(c, x, y, color):
    c.rect(x + 5, y + 6, 16, 20, color)
    for wy in (10, 16, 22):
        for wx in (9, 15, 21):
            c.rect(x + wx, y + wy, 2, 2, WHITE)


def icon_train(c, x, y, color):
    c.rect(x + 4, y + 4, 18, 16, color)
    c.rect(x + 7, y + 7, 12, 6, WHITE)
    c.circle(x + 9, y + 22, 3, INK)
    c.circle(x + 17, y + 22, 3, INK)
    c.line(x, y + 24, x + 26, y + 24, INK, 2)


def icon_flags(c, x, y, color):
    c.line(x + 6, y + 24, x + 6, y + 4, INK, 2)
    c.line(x + 19, y + 24, x + 19, y + 4, INK, 2)
    c.rect(x + 8, y + 4, 10, 8, BLUE)
    c.rect(x + 11, y + 7, 2, 2, GOLD)
    c.rect(x + 21, y + 4, 10, 8, color)
    c.rect(x + 24, y + 7, 2, 2, WHITE)


def icon_dome(c, x, y, color):
    c.rect(x + 4, y + 16, 18, 10, color)
    c.triangle(x + 4, y + 16, x + 22, y + 16, x + 13, y + 4, color)
    c.circle(x + 13, y + 4, 2, GOLD)
    c.rect(x + 8, y + 20, 3, 6, WHITE)
    c.rect(x + 15, y + 20, 3, 6, WHITE)


def icon_flame(c, x, y, color):
    c.triangle(x + 13, y + 2, x + 24, y + 22, x + 2, y + 22, color)
    c.triangle(x + 13, y + 12, x + 19, y + 24, x + 7, y + 24, GOLD)


def icon_bank(c, x, y, color):
    c.triangle(x + 2, y + 10, x + 24, y + 10, x + 13, y + 2, color)
    for cx in (5, 11, 17):
        c.rect(x + cx, y + 12, 3, 10, color)
    c.rect(x + 2, y + 22, 22, 3, color)


def icon_shield(c, x, y, color):
    c.rect(x + 5, y + 3, 16, 12, color)
    c.triangle(x + 5, y + 15, x + 21, y + 15, x + 13, y + 25, color)
    c.line(x + 9, y + 10, x + 12, y + 13, WHITE, 2)
    c.line(x + 12, y + 13, x + 18, y + 6, WHITE, 2)


def icon_megaphone(c, x, y, color):
    c.triangle(x + 4, y + 10, x + 4, y + 18, x + 22, y + 24, color)
    c.triangle(x + 4, y + 10, x + 22, y + 24, x + 22, y + 4, color)
    c.rect(x + 2, y + 10, 3, 8, INK)
    c.rect(x + 8, y + 18, 4, 7, INK)


def icon_sprout(c, x, y, color):
    c.line(x + 13, y + 24, x + 13, y + 12, color, 3)
    c.triangle(x + 13, y + 12, x + 1, y + 4, x + 13, y + 3, color)
    c.triangle(x + 13, y + 12, x + 25, y + 4, x + 13, y + 3, color)


def icon_globe(c, x, y, color):
    c.circle(x + 13, y + 13, 10, color)
    c.circle(x + 13, y + 13, 6, WHITE)
    c.line(x + 3, y + 13, x + 23, y + 13, WHITE, 1)
    c.line(x + 13, y + 3, x + 13, y + 23, WHITE, 1)


ICONS = {
    "building": icon_building,
    "train": icon_train,
    "flags": icon_flags,
    "dome": icon_dome,
    "flame": icon_flame,
    "bank": icon_bank,
    "shield": icon_shield,
    "megaphone": icon_megaphone,
    "sprout": icon_sprout,
    "globe": icon_globe,
}


# --- story data (all verified against a source dated 25 Nov 2026) --------
# Heroes: (number, scene, tag, headline line 1, headline line 2,
#          summary line 1, summary line 2, source, UTC chip, UTC hour)
HEROES = [
    (1, "markets", "SEOUL / MARKETS",
     "ASIA STOCKS SLIDE", "KOSPI FALLS 4.7%",
     "SAMSUNG -8.0%, SK HYNIX -7.5%,", "NIKKEI -3.15%, TAIEX -8.2%.",
     "WSJ / YONHAP", "00:00 UTC", 0.0),
    (2, "space", "JIUQUAN / SPACE",
     "PAKISTAN IN ORBIT", "FIRST ABOARD TIANGONG",
     "SHENZHOU-24 LIFTS OFF AT 00:18,", "MUHAMMAD ZEESHAN ALI, 40, ABOARD.",
     "REUTERS", "00:18 UTC", 0.3),
    (3, "summit", "FLORIDA / DIPLOMACY",
     "TRUMP MEETS NATO CHIEF", "AT MAR-A-LAGO TODAY",
     "PRESIDENT TRUMP HOSTS MARK RUTTE", "IN LATE-AFTERNOON TALKS TODAY.",
     "NATO", "21:00 UTC", 21.0),
]

# Stat strip: (big number, label) - hard news numbers only.
STATS = [
    ("-4.7%", "KOSPI SLIDE"),
    ("1ST", "PAKISTANI IN ORBIT"),
    ("30.4BN", "EUROS SOUGHT IN FUNDS"),
    ("2,212", "SEOUL METRO JOBS SAVED"),
    ("4TH", "POLITBURO MEMBER PROBED"),
]

# Grid cards 4-13: (number, icon, accent, tag, headline,
#                   summary line 1, summary line 2, source)
GRID = [
    (4, "building", BLUE, "SHANGHAI / POLITICS",
     "SHANGHAI PLEDGES LOYALTY",
     "4TH POLITBURO MEMBER PROBED", "SINCE 2025 - CHEN JINING, 62",
     "REUTERS"),
    (5, "train", TEAL, "SEOUL / LABOUR",
     "SEOUL METRO STRIKE OFF",
     "2,212 JOB CUTS SHELVED, 500", "NEW HIRES, WAGES UP 3.5%",
     "YONHAP"),
    (6, "flags", GOLD, "BRUSSELS / DIPLOMACY",
     "EU-BALKANS SUMMIT",
     "5 LEADERS MEET IN BRUSSELS,", "SERBIA ABSENT, PLENARY 17:00",
     "EUROPEAN COUNCIL"),
    (7, "dome", PURPLE, "MOSCOW / DIPLOMACY",
     "PUTIN MEETS BRUNEI SULTAN",
     "STATE VISIT IN MOSCOW, DAY 2", "SULTAN ON 24-25 NOV VISIT",
     "KREMLIN"),
    (8, "flame", ORANGE, "TASMANIA / WILDFIRE",
     "FLINDERS FIRE WARNING",
     "TOO LATE TO LEAVE, FIRE AT", "3,000-4,000 HA, LIGHTNING",
     "ABC NEWS"),
    (9, "bank", BLUE, "STRASBOURG / EU",
     "EU SEEKS 30.4BN IN FUNDS",
     "MIGRATION FUNDS BRIEF, 10:00", "ASYLUM 13.31, BORDERS 17.12",
     "EUROPEAN PARLIAMENT"),
    (10, "shield", GREEN, "CANBERRA / SECURITY",
     "SOLOMONS SIGN SECURITY PACT",
     "AUSTRALIA TOP SECURITY PARTNER", "CHINA PACT FACES PHASE-OUT",
     "PM OF AUSTRALIA"),
    (11, "megaphone", RED, "GLOBAL / CAMPAIGN",
     "16 DAYS OF ACTIVISM",
     "UN CAMPAIGN STARTS TODAY,", "RUNS TO 10 DEC, END IMPUNITY",
     "UN WOMEN"),
    (12, "sprout", PURPLE, "NEW DELHI / CAMPAIGN",
     "NAYI CHETNA 5.0 LAUNCHES",
     "INDIA GENDER DRIVE STARTS,", "RUNS TO 23 DEC, 15 MINISTRIES",
     "PIB"),
    (13, "globe", TEAL, "GENEVA / RIGHTS",
     "UN RIGHTS FORUM CLOSES",
     "BUSINESS FORUM ENDS AFTER", "3 DAYS, CLOSING PLENARY TODAY",
     "OHCHR"),
]

# Date-check box: stories excluded because they are 24 Nov, not 25 Nov.
DATE_CHECK = [
    "ZELENSKYY SHIP CLAIM - 24 NOV",
    "NEPAL QUAKE - 24 NOV",
    "GAZA HAMAS CHIEF - 24 NOV",
    "GIULIANI MEDAL - 24 NOV",
    "COP31 NO DEAL - 24 NOV",
    "CIA BREACH - 24 NOV",
]

REGION_STRIP = "13 STORIES - ASIA 5 - OCEANIA 2 - EUROPE 4 - AMERICAS 1 - GLOBAL 1"

REGION_ROWS = [
    ("ASIA", 5, RED),
    ("OCEANIA", 2, TEAL),
    ("EUROPE", 4, BLUE),
    ("AMERICAS", 1, GOLD),
    ("GLOBAL", 1, PURPLE),
]

TIMELINE_BLOCKS = [
    "00-06 ASIA WAKES",
    "06-12 EUROPE AND ASIA",
    "12-18 THE AMERICAS",
    "18-24 NIGHT",
]

# Coarse land mask: (lon_min, lon_max, lat_min, lat_max) rectangles.
LAND = [
    (-168, -95, 50, 72), (-125, -66, 30, 50), (-105, -80, 14, 30),
    (-58, -20, 60, 78),
    (-78, -50, -5, 10), (-72, -42, -35, -5), (-70, -52, -55, -35),
    (-17, 32, 8, 35), (-10, 40, -35, 8), (43, 50, -25, -12),
    (-10, 40, 36, 70), (40, 180, 45, 75), (35, 60, 12, 42),
    (68, 90, 8, 35), (95, 110, 5, 28), (75, 135, 20, 53),
    (95, 141, -10, 6), (113, 154, -39, -11), (145, 149, -44, -40),
    (166, 178, -47, -34), (129, 146, 31, 45), (-5, 2, 50, 59),
    (-22, -14, 63, 67),
]

# Map pins: (story number, lon, lat, offset_x, offset_y) - offsets keep
# crowded pins apart; a thin leader line joins pin to its true spot.
PINS = [
    (1, 127.0, 37.5, 0, 0),       # Seoul - Asia stocks
    (2, 98.5, 41.0, 0, 0),        # Jiuquan - Pakistan launch
    (3, -80.0, 27.0, 0, 0),       # Florida - Trump / Rutte
    (4, 121.5, 31.0, -12, 8),     # Shanghai
    (5, 127.0, 37.5, 14, -10),    # Seoul - metro strike
    (6, 4.4, 50.8, 0, 0),         # Brussels
    (7, 37.6, 55.8, 0, 0),        # Moscow
    (8, 148.0, -40.0, 0, 0),      # Flinders Island
    (9, 7.8, 48.6, 14, 10),       # Strasbourg
    (10, 149.1, -35.3, 14, -10),  # Canberra
    (12, 77.2, 28.6, 0, 0),       # New Delhi
    (13, 6.1, 46.2, -14, 12),     # Geneva
]

FOOTER_SOURCES = ("SOURCES: REUTERS, WSJ, YONHAP, NATO, EUROPEAN COUNCIL, "
                  "KREMLIN, ABC NEWS, EUROPEAN PARLIAMENT, PM OF AUSTRALIA, "
                  "UN WOMEN, PIB, OHCHR")


def _all_strings():
    out = [REGION_STRIP, FOOTER_SOURCES]
    out += TIMELINE_BLOCKS + DATE_CHECK
    for h in HEROES:
        out += [h[2], h[3], h[4], h[5], h[6], h[7], h[8]]
    for num, label in STATS:
        out += [num, label]
    for g in GRID:
        out += [g[3], g[4], g[5], g[6], g[7]]
    for name, _n, _c in REGION_ROWS:
        out.append(name)
    out += ["THE WORLD IN ", "24", " HOURS", "ONE DAY - ONE PAGE",
            "WEDNESDAY", "25 NOVEMBER 2026", "ALL TIMES UTC",
            "DATE CHECK - EXCLUDED AS THE WRONG DAY",
            "WHERE IT HAPPENED",
            "EVERY STORY ABOVE HAPPENED OR WAS FIRST REPORTED ON "
            "WEDNESDAY 25 NOVEMBER 2026,",
            "AS THE NAMED OUTLETS REPORTED IT. MAP AND DRAWINGS ARE "
            "ORIGINAL VECTOR ART."]
    return out


def _validate():
    """Fail loudly (before drawing) on any character the font lacks,
    any truncation marker, or any line that would overflow its box."""
    for s in _all_strings():
        if "..." in s:
            raise ValueError("truncated text: %r" % s)
        for ch in s:
            if ch not in FONT:
                raise ValueError("no glyph for %r in %r" % (ch, s))
    for _n, _s, tag, h1, h2, _a, _b, _src in [
            (g[0], g[1], g[3], g[4], None, None, None, None)
            for g in GRID]:
        if text_width(tag, 1) > 130:
            raise ValueError("tag too wide: %r" % tag)
        if text_width(h1, 1) > 180:
            raise ValueError("headline too wide: %r" % h1)
    for _n, _sc, _t, h1, h2, _a, _b, _src, _chip, _h in HEROES:
        if text_width(h1, 2) > 301 or text_width(h2, 2) > 301:
            raise ValueError("hero headline too wide: %r / %r" % (h1, h2))


# --- layout -----------------------------------------------------------------
MX = 16            # side margin
CW = 992           # content width


def draw_masthead(c):
    c.rect(0, 0, WIDTH, 92, BLACK)
    # title: "THE WORLD IN " white + "24" red + " HOURS" white, scale 4
    x = MX
    for text, color in (("THE WORLD IN ", WHITE), ("24", RED),
                        (" HOURS", WHITE)):
        draw_text(c, x, 18, text, 4, color)
        x += text_width(text, 4)
    draw_text(c, MX, 58, "ONE DAY - ONE PAGE", 2, WHITE)
    draw_text_right(c, WIDTH - MX, 14, "WEDNESDAY", 2, WHITE)
    draw_text_right(c, WIDTH - MX, 34, "25 NOVEMBER 2026", 3, GOLD)
    draw_text_right(c, WIDTH - MX, 62, "ALL TIMES UTC", 1, WHITE)
    c.rect(0, 92, WIDTH, 4, RED)


def draw_region_strip(c):
    draw_text_center(c, WIDTH // 2, 102, REGION_STRIP, 1, INK)


def draw_timeline(c):
    y = 124
    block_w = CW // 4
    for i, label in enumerate(TIMELINE_BLOCKS):
        cx = MX + i * block_w + block_w // 2
        draw_text_center(c, cx, y + 4, label, 1, INK)
    # hour ticks every 3 hours
    for h in range(0, 25, 3):
        tx = MX + h * CW // 24
        c.line(tx, y + 22, tx, y + 30, GREY, 1)
    # red progress line
    c.rect(MX, y + 25, CW, 3, RED)
    # hero dots at their real UTC hour
    for _n, _sc, _t, _a, _b, _s1, _s2, _src, _chip, hour in HEROES:
        dx = MX + int(hour * CW / 24)
        c.circle(dx, y + 26, 4, RED)
        c.circle(dx, y + 26, 1, WHITE)


def draw_hero(c, x, w, hero):
    num, scene, tag, h1, h2, s1, s2, source, chip, _hour = hero
    y0 = 164
    h = 272
    c.rect(x, y0, w, h, WHITE)
    c.border(x, y0, w, h, INK, 2)
    SCENES[scene](c, x + 2, y0 + 2, w - 4, 148)
    # number badge
    c.circle(x + 20, y0 + 20, 13, RED)
    draw_text(c, x + 14, y0 + 13, str(num), 2, WHITE)
    # UTC chip, top right of the scene
    c.rect(x + w - 72, y0 + 8, 64, 16, RED)
    draw_text(c, x + w - 67, y0 + 10, chip, 1, WHITE)
    # tag, headlines, summary, source
    draw_text(c, x + 12, y0 + 158, tag, 1, RED)
    draw_text(c, x + 12, y0 + 172, h1, 2, INK)
    draw_text(c, x + 12, y0 + 190, h2, 2, INK)
    draw_text(c, x + 12, y0 + 212, s1, 1, GREY)
    draw_text(c, x + 12, y0 + 221, s2, 1, GREY)
    draw_text(c, x + 12, y0 + 240, source, 1, INK)
    c.rect(x, y0 + h - 4, w, 4, RED)


def draw_stats(c):
    y0 = 442
    h = 64
    c.rect(MX, y0, CW, h, WHITE)
    c.border(MX, y0, CW, h, INK, 2)
    for i, (num, label) in enumerate(STATS):
        x0 = MX + (i * CW) // 5
        x1 = MX + ((i + 1) * CW) // 5
        if i:
            c.line(x0, y0 + 8, x0, y0 + h - 8, LIGHT_GREY, 1)
        cx = (x0 + x1) // 2
        draw_text_center(c, cx, y0 + 10, num, 3, RED)
        draw_text_center(c, cx, y0 + 38, label, 1, INK)


def draw_grid(c):
    for i, g in enumerate(GRID):
        num, icon, accent, tag, headline, s1, s2, source = g
        col, row = i % 5, i // 5
        x = MX + col * 200
        y = 512 + row * 106
        w, h = 192, 98
        c.rect(x, y, w, h, WHITE)
        c.border(x, y, w, h, INK, 2)
        # number badge
        c.rect(x + 6, y + 6, 14, 14, RED)
        num_w = text_width(str(num), 1)
        draw_text(c, x + 6 + (14 - num_w) // 2, y + 8, str(num), 1, WHITE)
        # pictogram + tag
        ICONS[icon](c, x + 26, y + 4, accent)
        draw_text(c, x + 56, y + 11, tag, 1, RED)
        # headline, summary, source
        draw_text(c, x + 6, y + 38, headline, 1, INK)
        draw_text(c, x + 6, y + 52, s1, 1, GREY)
        draw_text(c, x + 6, y + 63, s2, 1, GREY)
        draw_text(c, x + 6, y + 80, source, 1, INK)
        c.rect(x + 2, y + h - 5, w - 4, 3, accent)


def _is_land(lon, lat):
    for lo0, lo1, la0, la1 in LAND:
        if lo0 <= lon <= lo1 and la0 <= lat <= la1:
            return True
    return False


def draw_map(c):
    y0 = 722
    h = 124
    c.rect(MX, y0, CW, h, WHITE)
    c.border(MX, y0, CW, h, INK, 2)
    map_x, map_y, map_w, map_h = 24, 730, 636, 112

    def px(lon):
        return map_x + int((lon + 180) * map_w / 360)

    def py(lat):
        return map_y + int((78 - lat) * map_h / 136)

    # dotted land (dense sampling so continents read at strip height)
    lon = -178
    while lon <= 178:
        lat = 75
        while lat >= -57:
            if _is_land(lon, lat):
                c.rect(px(lon) - 1, py(lat) - 1, 2, 2, MAP_DOT)
            lat -= 5
        lon += 3
    # numbered pins (leader line first, then the pin)
    for num, lon, lat, dx, dy in PINS:
        tx, ty = px(lon), py(lat)
        cx, cy = tx + dx, ty + dy
        if dx or dy:
            c.line(tx, ty, cx, cy, GREY, 1)
        c.circle(cx, cy, 8, RED)
        num_w = text_width(str(num), 1)
        draw_text(c, cx - num_w // 2, cy - 3, str(num), 1, WHITE)
    # divider + region counts on the right
    c.line(668, y0 + 8, 668, y0 + h - 8, LIGHT_GREY, 1)
    draw_text(c, 676, y0 + 6, "WHERE IT HAPPENED", 2, INK)
    for i, (name, n, color) in enumerate(REGION_ROWS):
        ry = y0 + 28 + i * 19
        c.rect(676, ry + 1, 12, 12, color)
        draw_text(c, 694, ry, "%s %d" % (name, n), 2, INK)


def draw_date_check(c):
    y0 = 852
    h = 160
    c.rect(MX, y0, CW, h, RED_LIGHT)
    c.border(MX, y0, CW, h, RED, 3)
    draw_text(c, MX + 16, y0 + 12,
              "DATE CHECK - EXCLUDED AS THE WRONG DAY", 2, RED)
    for i, item in enumerate(DATE_CHECK):
        col, row = i % 2, i // 2
        x = MX + 16 + col * 504
        y = y0 + 40 + row * 16
        draw_text(c, x, y, "X", 1, RED)
        draw_text(c, x + 12, y, item, 1, INK)
    draw_text(c, MX + 16, y0 + 98,
              "EVERY STORY ABOVE HAPPENED OR WAS FIRST REPORTED ON "
              "WEDNESDAY 25 NOVEMBER 2026,", 1, INK)
    draw_text(c, MX + 16, y0 + 111,
              "AS THE NAMED OUTLETS REPORTED IT. MAP AND DRAWINGS ARE "
              "ORIGINAL VECTOR ART.", 1, INK)
    draw_text(c, MX + 16, y0 + 130, FOOTER_SOURCES, 1, GREY)


def draw():
    _validate()
    c = Canvas(WIDTH, HEIGHT, PAPER)
    draw_masthead(c)
    draw_region_strip(c)
    draw_timeline(c)
    hero_xs = [MX, 349, 682]
    hero_ws = [325, 325, 326]
    for x, w, hero in zip(hero_xs, hero_ws, HEROES):
        draw_hero(c, x, w, hero)
    draw_stats(c)
    draw_grid(c)
    draw_map(c)
    draw_date_check(c)
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
