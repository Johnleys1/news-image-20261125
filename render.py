#!/usr/bin/env python3
"""Render THE WORLD - Wednesday 25 November 2026 as a 1024x1024 PNG.

Pure standard library: a small framebuffer, a 5x7 bitmap font, vector scenes
and a zlib PNG writer. Deterministic: identical bytes on every run.
"""
import struct
import zlib

W, H = 1024, 1024

PAPER = (250, 247, 238)
INK = (22, 22, 24)
RED = (178, 34, 34)
NAVY = (24, 64, 110)
GREEN = (46, 125, 50)
NGREEN = (96, 170, 40)
GOLD = (198, 150, 40)
GREY = (200, 196, 186)
PANEL = (232, 238, 244)
WARM = (245, 238, 225)
SKY = (214, 228, 240)
SEA = (36, 98, 140)
WHITE = (255, 255, 255)
DARK = (16, 28, 44)


class Canvas:
    def __init__(self):
        self.buf = bytearray(W * H * 3)
        self.fill_rect(0, 0, W, H, PAPER)

    def px(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def fill_rect(self, x, y, w, h, color):
        x0 = max(x, 0)
        y0 = max(y, 0)
        x1 = min(x + w, W)
        y1 = min(y + h, H)
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * W + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = r
                self.buf[i + 1] = g
                self.buf[i + 2] = b

    def hline(self, x1, x2, y, color):
        if y < 0 or y >= H:
            return
        a, b = min(x1, x2), max(x1, x2)
        self.fill_rect(a, y, b - a + 1, 1, color)

    def vline(self, x, y1, y2, color):
        if x < 0 or x >= W:
            return
        a, b = min(y1, y2), max(y1, y2)
        self.fill_rect(x, a, 1, b - a + 1, color)

    def rect(self, x, y, w, h, color, t=1):
        for k in range(t):
            self.hline(x, x + w - 1, y + k, color)
            self.hline(x, x + w - 1, y + h - 1 - k, color)
            self.vline(x + k, y, y + h - 1, color)
            self.vline(x + w - 1 - k, y, y + h - 1, color)

    def line(self, x1, y1, x2, y2, color):
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        x, y = x1, y1
        while True:
            self.px(x, y, color)
            if x == x2 and y == y2:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.hline(cx - dx, cx + dx, cy + dy, color)

    def circle(self, cx, cy, r, color):
        steps = max(24, r * 6)
        import math
        prev = None
        for k in range(steps + 1):
            a = 2 * math.pi * k / steps
            p = (cx + int(r * math.cos(a)), cy + int(r * math.sin(a)))
            if prev is not None:
                self.line(prev[0], prev[1], p[0], p[1], color)
            prev = p

    def poly(self, pts, color):
        ys = [p[1] for p in pts]
        for y in range(max(min(ys), 0), min(max(ys), H - 1) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(int(xs[i]), int(xs[i + 1]), y, color)

    def tri(self, x1, y1, x2, y2, x3, y3, color):
        self.poly([(x1, y1), (x2, y2), (x3, y3)], color)


def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def save_png(path, cv):
    raw = b"".join(b"\x00" + bytes(cv.buf[y * W * 3:(y + 1) * W * 3]) for y in range(H))
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(raw, 9)) + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


# 5x7 bitmap font, uppercase + digits + punctuation. '#' = on, '.' = off.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", "#....", "#...."),
    "$": ("..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    ">": (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
}


def text_w(s, scale):
    return len(s.upper()) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color, align="l"):
    s = s.upper()
    w = text_w(s, scale)
    if align == "c":
        x -= w // 2
    elif align == "r":
        x -= w
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[" "])
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == "#":
                    cv.fill_rect(cx + c * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return w


def wrap(s, max_chars):
    words = s.upper().split(" ")
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def text_block(cv, x, y, s, scale, color, max_chars, lh=None, align="l"):
    lines = wrap(s, max_chars)
    if lh is None:
        lh = 9 * scale
    for ln in lines:
        draw_text(cv, x, y, ln, scale, color, align)
        y += lh
    return y


FONT["\u2022"] = (".....", ".....", ".###.", ".###.", ".###.", ".....", ".....")


def _norm(s):
    return s.replace("\u2014", "-").replace("\u2013", "-").replace("\u2019", "'")


def draw_text2(cv, x, y, s, scale, color, align="l"):
    return draw_text(cv, x, y, _norm(s), scale, color, align)


def scene_nvidia(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, DARK)
    # rising chart bars
    bars = [0.22, 0.38, 0.30, 0.55, 0.48, 0.78, 1.0]
    bw = w // 9
    for i, f in enumerate(bars):
        bh = int(h * 0.55 * f)
        cv.fill_rect(x + 12 + i * bw, y + h - 14 - bh, bw - 6, bh, (70, 90, 120))
    # chip
    cx, cy = x + w // 2, y + h // 2 - 18
    s = 74
    cv.fill_rect(cx - s // 2 - 8, cy - s // 2, 8, s, NGREEN)
    cv.fill_rect(cx + s // 2, cy - s // 2, 8, s, NGREEN)
    cv.fill_rect(cx - s // 2, cy - s // 2 - 8, s, 8, NGREEN)
    cv.fill_rect(cx - s // 2, cy + s // 2, s, 8, NGREEN)
    cv.fill_rect(cx - s // 2, cy - s // 2, s, s, NGREEN)
    draw_text2(cv, cx, cy - 10, "NVDA", 3, WHITE, "c")
    # rising arrow
    pts = [(x + 16, y + h - 30), (x + w // 3, y + h - 78), (x + w // 2, y + h - 58),
           (x + 2 * w // 3, y + h - 108), (x + w - 24, y + 26)]
    for k in range(len(pts) - 1):
        for t in range(4):
            cv.line(pts[k][0], pts[k][1] + t, pts[k + 1][0], pts[k + 1][1] + t, GOLD)
    ex, ey = pts[-1]
    cv.tri(ex - 16, ey + 2, ex - 2, ey - 12, ex + 6, ey + 8, GOLD)


def scene_poland(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, SKY)
    cx, cy = x + w - 46, y + h // 2
    for r in (52, 38, 24):
        cv.circle(cx, cy, r, NAVY)
    cv.disc(cx, cy, 4, RED)
    cv.line(cx, cy, x + 18, y + 16, NAVY)
    # missile streaks
    for i, yy in enumerate((y + 26, y + 58, y + 92)):
        x0 = x + 14 + i * 8
        for t in range(3):
            cv.line(x0, yy + t, x0 + 74, yy - 18 + t, RED)
        cv.disc(x0 + 78, yy - 20, 3, INK)
    # jets
    for jx, jy in ((x + 30, y + h - 26), (x + 66, y + h - 44)):
        cv.tri(jx, jy - 8, jx - 12, jy + 8, jx + 12, jy + 8, INK)


def scene_hormuz(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (168, 200, 222))
    cv.fill_rect(x, y + h * 2 // 5, w, h * 3 // 5, SEA)
    for wy in range(y + h * 2 // 5 + 12, y + h - 6, 16):
        for wx in range(x + 6, x + w - 10, 26):
            cv.hline(wx, wx + 14, wy, WHITE)
    # tankers
    for tx, tw, th in ((x + 12, 62, 20), (x + w // 2 - 30, 74, 24), (x + w - 88, 56, 18)):
        ty = y + h - 34
        cv.fill_rect(tx, ty - th, tw, th, INK)
        cv.fill_rect(tx + tw - 18, ty - th - 12, 10, 12, RED)
        cv.fill_rect(tx + 6, ty - th - 8, tw - 28, 8, (120, 130, 140))
    # mines
    for mx, my in ((x + w - 30, y + h // 2 + 6), (x + 34, y + h // 2 + 22)):
        cv.disc(mx, my, 5, INK)
        cv.line(mx - 8, my, mx + 8, my, INK)
        cv.line(mx, my - 8, mx, my + 8, INK)
    # warning triangle
    cv.tri(x + 12, y + 12, x + 34, y + 12, x + 23, y + 32, RED)
    draw_text2(cv, x + 23, y + 16, "!", 2, WHITE, "c")


def _icon_box(cv, x, y, s):
    cv.fill_rect(x, y, s, s, PANEL)
    cv.rect(x, y, s, s, GREY, 1)


def icon_ship(cv, x, y, s):
    _icon_box(cv, x, y, s)
    cv.fill_rect(x + 8, y + 10, 10, 8, RED)
    cv.fill_rect(x + 19, y + 10, 10, 8, NAVY)
    cv.fill_rect(x + 8, y + 19, 21, 5, NAVY)
    cv.poly([(x + 5, y + 25), (x + 33, y + 25), (x + 29, y + 33), (x + 9, y + 33)], INK)
    cv.hline(x + 4, x + 34, y + 36, NAVY)


def icon_chart_down(cv, x, y, s):
    _icon_box(cv, x, y, s)
    cv.vline(x + 7, y + 6, y + 32, INK)
    cv.hline(x + 7, x + 33, y + 32, INK)
    pts = [(x + 9, y + 10), (x + 16, y + 16), (x + 23, y + 15), (x + 31, y + 27)]
    for k in range(len(pts) - 1):
        for t in range(3):
            cv.line(pts[k][0], pts[k][1] + t, pts[k + 1][0], pts[k + 1][1] + t, RED)
    cv.tri(pts[-1][0] - 5, pts[-1][1] - 2, pts[-1][0] + 4, pts[-1][1] - 2, pts[-1][0], pts[-1][1] + 6, RED)


def icon_chip(cv, x, y, s):
    _icon_box(cv, x, y, s)
    cv.fill_rect(x + 12, y + 12, 16, 16, NAVY)
    cv.rect(x + 16, y + 16, 8, 8, WHITE, 1)
    for px in (x + 15, x + 19, x + 23):
        cv.fill_rect(px, y + 7, 2, 5, INK)
        cv.fill_rect(px, y + 28, 2, 5, INK)
    for py in (y + 15, y + 19, y + 23):
        cv.fill_rect(x + 7, py, 5, 2, INK)
        cv.fill_rect(x + 28, py, 5, 2, INK)


def icon_branch(cv, x, y, s):
    _icon_box(cv, x, y, s)
    cv.line(x + 8, y + 32, x + 30, y + 8, GREEN)
    for lx, ly in ((x + 12, y + 24), (x + 18, y + 18), (x + 24, y + 12)):
        cv.disc(lx, ly, 5, GREEN)
        cv.disc(lx + 7, ly + 5, 4, NGREEN)


def icon_globe(cv, x, y, s):
    _icon_box(cv, x, y, s)
    cv.circle(x + 20, y + 20, 13, NAVY)
    cv.circle(x + 20, y + 20, 7, NAVY)
    cv.hline(x + 7, x + 33, y + 20, NAVY)
    cv.vline(x + 20, y + 7, y + 33, NAVY)


def icon_gamepad(cv, x, y, s):
    _icon_box(cv, x, y, s)
    cv.fill_rect(x + 7, y + 13, 26, 14, INK)
    cv.disc(x + 7, y + 20, 7, INK)
    cv.disc(x + 33, y + 20, 7, INK)
    cv.fill_rect(x + 12, y + 17, 3, 7, WHITE)
    cv.fill_rect(x + 10, y + 19, 7, 3, WHITE)
    cv.disc(x + 27, y + 18, 2, RED)
    cv.disc(x + 31, y + 22, 2, GOLD)


def icon_parliament(cv, x, y, s):
    _icon_box(cv, x, y, s)
    cv.tri(x + 6, y + 16, x + 34, y + 16, x + 20, y + 7, NAVY)
    for cx in (x + 10, x + 18, x + 26):
        cv.fill_rect(cx, y + 17, 4, 12, INK)
    cv.fill_rect(x + 6, y + 30, 28, 3, INK)


def icon_mountains(cv, x, y, s):
    _icon_box(cv, x, y, s)
    cv.disc(x + 30, y + 10, 4, GOLD)
    cv.tri(x + 4, y + 33, x + 16, y + 33, x + 12, y + 14, NAVY)
    cv.tri(x + 14, y + 33, x + 34, y + 33, x + 27, y + 10, INK)
    cv.tri(x + 10, y + 17, x + 14, y + 17, x + 12, y + 14, WHITE)
    cv.tri(x + 24, y + 15, x + 30, y + 15, x + 27, y + 10, WHITE)


def icon_derrick(cv, x, y, s):
    _icon_box(cv, x, y, s)
    cv.line(x + 12, y + 33, x + 18, y + 8, INK)
    cv.line(x + 28, y + 33, x + 22, y + 8, INK)
    cv.hline(x + 14, x + 26, y + 26, INK)
    cv.hline(x + 16, x + 24, y + 18, INK)
    cv.fill_rect(x + 8, y + 33, 24, 3, INK)
    cv.disc(x + 31, y + 12, 4, RED)


def icon_mic(cv, x, y, s):
    _icon_box(cv, x, y, s)
    cv.disc(x + 20, y + 14, 7, RED)
    cv.fill_rect(x + 14, y + 20, 12, 4, INK)
    cv.vline(x + 20, y + 24, y + 32, INK)
    cv.hline(x + 13, x + 27, y + 33, INK)


GRID = [
    (4, "TRUMP TARIFF WAVE", icon_ship),
    (5, "ANTHROPIC SLIDES", icon_chart_down),
    (6, "HUAWEI GUILTY", icon_chip),
    (7, "GAZA CRISIS DEEPENS", icon_branch),
    (8, "COP31 COLLAPSES", icon_globe),
    (9, "GTA 6 LAUNCHES", icon_gamepad),
    (10, "BJP-SAD REUNITE", icon_parliament),
    (11, "NEPAL QUAKE 5.6", icon_mountains),
    (12, "IRAQ OIL FIGHT", icon_derrick),
    (13, "IRAN: 74 LASHES", icon_mic),
]

RAIL = [
    "GIULIANI GETS MEDAL OF FREEDOM",
    "2 HELD OVER WILLIAM HOME BREAK-IN",
    "DENMARK UPHOLDS GHETTO EVICTIONS",
    "ISRAEL ARMY SUICIDES AT 16-YR HIGH",
    "RIYADH TOWER BLAST CONDEMNED",
    "ZIMBABWEAN JAILED OVER UKRAINE BID",
    "US CONSUMER CONFIDENCE IN FOCUS",
    "SENSEX -1,484; NIFTY BELOW 25,400",
    "ENGLAND BEAT AUSTRALIA IN T20I",
    "SOORYAVANSHI: FASTEST LIST-A 100",
    "NZ HOLD INDIA TO DRAW IN 1ST TEST",
    "PRIYANSH ARYA HITS 181 IN T20",
    "VERA RUBIN'S FIRST IMAGES WOW",
    "DIDYMOS ECLIPSE STUNS SKYGAZERS",
    "IMPOSSIBLE STAR SYSTEM FOUND",
    "GREAT BARRIER REEF CORALS REVIVED",
    "END VIOLENCE AGAINST WOMEN DAY",
    "12,000 EVACUATED OVER GAS ALARM",
    "MODI-MERZ TALK STRATEGIC TIES",
    "INDIA SPACE ECONOMY TO $45B",
    "US-QATAR STRATEGIC TALKS",
]


def build():
    cv = Canvas()
    # Masthead
    draw_text2(cv, 512, 14, "THE WORLD", 13, INK, "c")
    draw_text2(cv, 512, 112, "WEDNESDAY 25 NOVEMBER 2026 \u2022 34 STORIES \u2022 9 REGIONS",
               2, INK, "c")
    cv.fill_rect(24, 134, 976, 4, RED)
    # Stat strip
    stats = ["+31.5% NVIDIA", "+$952B IN ONE DAY", "3 MISSILES \u2022 3 TANKERS"]
    for i, s in enumerate(stats):
        bx = 24 + i * 320
        cv.fill_rect(bx, 142, 312, 32, WARM)
        cv.rect(bx, 142, 312, 32, GREY, 1)
        draw_text2(cv, bx + 156, 150, s, 2, INK, "c")
    # Hero 1: NVIDIA
    scene_nvidia(cv, 24, 182, 416, 246)
    draw_text2(cv, 456, 192, "MARKETS \u2022 MONDAY 23 NOV", 2, RED)
    draw_text2(cv, 456, 220, "HUANG IS BACK", 5, INK)
    draw_text2(cv, 456, 272, "NVIDIA +31.5% IN A DAY", 3, NAVY)
    deck = ["JENSEN HUANG RETURNS AS CEO,",
            "10 DAYS AFTER QUITTING AMID",
            "SPY PROBE. MARKET CAP +$952B,",
            "A RECORD DAY. STILL -32%",
            "FROM OCTOBER PEAK."]
    yy = 306
    for ln in deck:
        draw_text2(cv, 456, yy, ln, 2, INK)
        yy += 18
    draw_text2(cv, 456, 404, "+31.5%  \u2022  +$952B  \u2022  $165", 3, GREEN)
    cv.hline(24, 1000, 436, GREY)
    # Wings
    scene_poland(cv, 24, 444, 150, 134)
    draw_text2(cv, 182, 450, "NATO \u2022 25 NOV", 1, RED)
    yy = text_block(cv, 182, 466, "3 MISSILES OVER POLAND", 3, INK, 17, lh=27)
    text_block(cv, 182, yy + 4, "RUSSIA BREACHES NATO AIRSPACE; ALLIANCE SCRAMBLES JETS.",
               2, INK, 26, lh=18)
    scene_hormuz(cv, 516, 444, 150, 134)
    draw_text2(cv, 674, 450, "HORMUZ \u2022 25 NOV", 1, RED)
    yy = text_block(cv, 674, 466, "MINES HIT 3 TANKERS", 3, INK, 17, lh=27)
    text_block(cv, 674, yy + 4, "IRAN'S GUARDS: BLASTS IN THE STRAIT. OIL ROUTE ON EDGE.",
               2, INK, 26, lh=18)
    cv.hline(24, 1000, 586, GREY)
    # Grid 10
    for i, (num, title, icon) in enumerate(GRID):
        cx = 24 + (i % 5) * 196
        cy = 594 + (i // 5) * 94
        cv.fill_rect(cx, cy, 188, 86, PANEL)
        cv.rect(cx, cy, 188, 86, GREY, 1)
        draw_text2(cv, cx + 5, cy + 4, "%02d" % num, 1, RED)
        icon(cv, cx + 76, cy + 12, 36)
        text_block(cv, cx + 94, cy + 52, title, 2, INK, 15, lh=17, align="c")
    cv.hline(24, 1000, 784, GREY)
    # Rail 21 (stories 14-34), two columns x eleven rows
    for i, headline in enumerate(RAIL):
        col = i // 11
        row = i % 11
        x = 24 + col * 488
        y = 792 + row * 18
        draw_text2(cv, x, y + 2, "%02d" % (14 + i), 2, RED)
        draw_text2(cv, x + 30, y + 2, headline, 2, INK)
    draw_text2(cv, 512 + 30, 974, "END OF 34 STORIES", 2, GREY)
    cv.hline(24, 1000, 994, GREY)
    return cv


def main():
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    cv = build()
    save_png(os.path.join(here, "entry.png"), cv)


if __name__ == "__main__":
    main()
