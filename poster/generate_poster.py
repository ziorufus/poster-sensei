#!/usr/bin/env python3
"""
Generate the SENSEI conference poster (A0, portrait) as a single SVG file.

Usage:
    .venv/bin/python3 poster/prepare_assets.py     # once, to rasterize figures
    .venv/bin/python3 poster/generate_poster.py    # writes poster/poster.svg

The script builds the SVG programmatically (plain strings, no heavy
dependencies beyond Pillow for text-metrics/image-size lookups) so the
output stays a clean, readable, hand-editable vector file: open it in
Inkscape / Illustrator / any text editor to tweak copy, colors or layout.
"""
import base64
import itertools
import os
from xml.sax.saxutils import escape

from PIL import Image, ImageFont

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "poster", "assets")
OUT_SVG = os.path.join(ROOT, "poster", "poster.svg")

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
FONT_OBLIQUE = os.path.join(FONT_DIR, "DejaVuSans-Oblique.ttf")
FONT_FAMILY = "DejaVu Sans, Verdana, Arial, sans-serif"

# --------------------------------------------------------------------------
# Page geometry (A0 portrait, millimetres used directly as SVG user units)
# --------------------------------------------------------------------------
PAGE_W, PAGE_H = 841.0, 1189.0
MARGIN = 25.0
GUTTER = 18.0
N_COLS = 3
COL_W = (PAGE_W - 2 * MARGIN - (N_COLS - 1) * GUTTER) / N_COLS
COL_X = [MARGIN + i * (COL_W + GUTTER) for i in range(N_COLS)]

HEADER_H = 165.0
FOOTER_H = 88.0

# --------------------------------------------------------------------------
# Palette (accents sampled from the paper's own architecture diagram, so the
# poster visually rhymes with Figure 1 / Figure 3)
# --------------------------------------------------------------------------
INK = "#1B1730"
INDIGO = "#2B1863"
INDIGO_DARK = "#1B0F42"
LAVENDER = "#EDE9F8"
LAVENDER_SOFT = "#F5F3FA"
PURPLE = "#4B2094"
GREEN = "#1F6B33"
NAVY = "#1A1E8C"
OLIVE = "#8A6D2F"
BODY_TEXT = "#2B2740"
MUTED = "#6B6580"
# RULE = "#D9D4E8"
RULE = ""
FBK_BLUE = "#1568B8"
UNITN_RED = "#A6192E"
WHITE = "#FFFFFF"
PAPER_BG = "#FFFFFF"
TABLE_ZEBRA = "#F7F6FB"

ACCENTS = [PURPLE, GREEN, NAVY, OLIVE]

# --------------------------------------------------------------------------
# Text metrics helpers (measured against the real font so wrapping matches
# what actually renders)
# --------------------------------------------------------------------------
_MEASURE = 1000
_font_cache = {}


def _font(bold=False, italic=False):
    key = (bold, italic)
    if key not in _font_cache:
        path = FONT_BOLD if bold else (FONT_OBLIQUE if italic else FONT_REGULAR)
        _font_cache[key] = ImageFont.truetype(path, _MEASURE)
    return _font_cache[key]


def text_width(text, size, bold=False, italic=False):
    return _font(bold, italic).getlength(text) * (size / _MEASURE)


def wrap_words(words, width, size, bold=False):
    """Greedy word-wrap of a pre-split word list into lines <= width."""
    lines, cur = [], []
    for w in words:
        trial = cur + [w]
        if text_width(" ".join(trial), size, bold) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = [w]
    if cur:
        lines.append(cur)
    return lines


def wrap_text(text, width, size, bold=False):
    return [" ".join(l) for l in wrap_words(text.split(), width, size, bold)]


# --------------------------------------------------------------------------
# SVG document builder
# --------------------------------------------------------------------------
class Doc:
    def __init__(self):
        self.parts = []
        self._ids = itertools.count(1)

    def add(self, s):
        self.parts.append(s)

    def uid(self, prefix):
        return f"{prefix}{next(self._ids)}"

    def render(self):
        body = "".join(self.parts)
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{PAGE_W}mm" height="{PAGE_H}mm" viewBox="0 0 {PAGE_W} {PAGE_H}"
     font-family="{FONT_FAMILY}">
<title>SENSEI -- CLiC-it 2026 poster</title>
<rect x="0" y="0" width="{PAGE_W}" height="{PAGE_H}" fill="{PAPER_BG}"/>
{body}
</svg>
'''


doc = Doc()


# --------------------------------------------------------------------------
# Drawing primitives
# --------------------------------------------------------------------------
def text(x, y, s, size, weight="400", color=BODY_TEXT, anchor="start",
         italic=False, family=FONT_FAMILY, spacing=None, opacity=None):
    style = f' font-style="italic"' if italic else ""
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    op = f' opacity="{opacity}"' if opacity is not None else ""
    doc.add(
        f'<text x="{x:.2f}" y="{y:.2f}" font-family="{family}" font-size="{size:.2f}" '
        f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{style}{sp}{op}>'
        f'{escape(s)}</text>'
    )


def rich_line(x, y, spans, size, family=FONT_FAMILY):
    """spans: list of (text, weight, color) rendered as one baseline row."""
    inner = "".join(
        f'<tspan font-weight="{w}" fill="{c}">{escape(t)}</tspan>' for t, w, c in spans
    )
    doc.add(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{family}" font-size="{size:.2f}">{inner}</text>')


def paragraph(x, y, width, s, size=8.2, line_h=None, color=BODY_TEXT, weight="400",
              italic=False, anchor="start"):
    line_h = line_h or size * 1.42
    for line in wrap_text(s, width, size, bold=(weight == "700")):
        lx = x + width if anchor == "end" else (x + width / 2 if anchor == "middle" else x)
        text(lx, y, line, size, weight=weight, color=color, italic=italic, anchor=anchor)
        y += line_h
    return y


def hrule(x, y, width, color=RULE, w=0.7, opacity=1.0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    doc.add(f'<line x1="{x:.2f}" y1="{y:.2f}" x2="{x+width:.2f}" y2="{y:.2f}" '
             f'stroke="{color}" stroke-width="{w}" opacity="{opacity}"{d}/>')


def section_header(x, y, width, number, title, accent):
    y += 7.0  # breathing room above every section title, regardless of caller
    avail = width - 19.5
    size = 13.6
    up = title.upper()
    tw = text_width(up, size, bold=True)
    if tw > avail:
        size = max(10.5, size * avail / tw)

    # Center the number badge on the title's own cap-height box (title has
    # no descenders, being all-caps), instead of assuming a fixed offset —
    # keeps the two aligned even when the title font shrinks to fit.
    cap = size * 0.729
    title_mid = y - cap / 2
    badge = 12.5
    doc.add(f'<rect x="{x:.2f}" y="{title_mid-badge/2:.2f}" width="{badge:.2f}" height="{badge:.2f}" '
             f'rx="2.8" fill="{accent}"/>')
    num_size = 7.2
    num_cap = num_size * 0.729
    text(x + badge / 2, title_mid + num_cap / 2, f"{number}", num_size, weight="700",
         color=WHITE, anchor="middle")

    text(x + 19.5, y, up, size, weight="700", color=INK, spacing="0.3")
    y += 6.8
    hrule(x, y, width, color=accent, w=1.3, opacity=0.30)
    y += 14.5
    return y


def bullets(x, y, width, items, size=8.1, line_h=None, gap=7.5, bullet_color=PURPLE,
            text_color=BODY_TEXT, lead_color=None, indent=8.2):
    """items: list of (lead_or_None, rest) or plain strings."""
    line_h = line_h or size * 1.42
    lead_color = lead_color or INK
    for item in items:
        lead, rest = item if isinstance(item, tuple) else (None, item)
        lead_words = lead.split() if lead else []
        n_lead = len(lead_words)
        words = lead_words + rest.split()
        avail = width - indent
        lines = wrap_words(words, avail, size, bold=False)
        doc.add(f'<rect x="{x:.2f}" y="{y-size*0.62:.2f}" width="{size*0.34:.2f}" '
                 f'height="{size*0.34:.2f}" rx="0.7" fill="{bullet_color}"/>')
        idx = 0
        for line_words in lines:
            spans = []
            seg, seg_bold = [], (idx < n_lead)
            for w in line_words:
                is_bold = idx < n_lead
                if is_bold != seg_bold and seg:
                    spans.append((" ".join(seg) + " ", "700" if seg_bold else "400",
                                  lead_color if seg_bold else text_color))
                    seg = []
                seg_bold = is_bold
                seg.append(w)
                idx += 1
            if seg:
                spans.append((" ".join(seg), "700" if seg_bold else "400",
                              lead_color if seg_bold else text_color))
            rich_line(x + indent, y, spans, size)
            y += line_h
        y += gap
    return y - gap + gap * 0.15


def embed_image(x, y, width, path, max_height=None, radius=0.0, shadow=False,
                 border=RULE, fit="cover", target_h=None):
    im = Image.open(path)
    iw, ih = im.size
    ar = iw / ih
    if target_h is not None:
        h = target_h
        w = width
    else:
        h = width / ar
        w = width
        if max_height and h > max_height:
            h = max_height
            w = h * ar
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    cx = x + (width - w) / 2
    clip_id = doc.uid("clip")
    if shadow:
        doc.add(f'<rect x="{cx+1.6:.2f}" y="{y+2.8:.2f}" width="{w:.2f}" height="{h:.2f}" '
                 f'rx="{radius}" fill="#000000" opacity="0.16"/>')
    doc.add(f'<clipPath id="{clip_id}"><rect x="{cx:.2f}" y="{y:.2f}" width="{w:.2f}" '
             f'height="{h:.2f}" rx="{radius}"/></clipPath>')
    doc.add(f'<image xlink:href="data:image/png;base64,{b64}" x="{cx:.2f}" y="{y:.2f}" '
             f'width="{w:.2f}" height="{h:.2f}" clip-path="url(#{clip_id})" '
             f'preserveAspectRatio="xMidYMid slice"/>')
    if border:
        doc.add(f'<rect x="{cx:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{radius}" '
                 f'fill="none" stroke="{border}" stroke-width="0.8"/>')
    return y + h, w, h


def pill(x, y, w, h, fill, text_str=None, size=6.6, color=WHITE, weight="600", stroke=None):
    st = f' stroke="{stroke}" stroke-width="0.7"' if stroke else ""
    doc.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{h/2:.2f}" fill="{fill}"{st}/>')
    if text_str:
        text(x + w / 2, y + h / 2 + size * 0.34, text_str, size, weight=weight, color=color, anchor="middle")


def stat_tile(x, y, w, h, number, label, color):
    doc.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="4.5" fill="{LAVENDER_SOFT}"/>')
    doc.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="4" height="{h:.2f}" rx="2" fill="{color}"/>')
    text(x + w / 2 + 2, y + h * 0.42, number, 21.0, weight="700", color=color, anchor="middle")
    lines = wrap_text(label, w - 14, 7.4, bold=True)
    ly = y + h * 0.66
    for line in lines:
        text(x + w / 2 + 2, ly, line, 7.4, weight="700", color=INK, anchor="middle")
        ly += 8.6


def checkmark(cx, cy, r, color):
    doc.add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{color}" opacity="0.14"/>')
    p = (f"M {cx-r*0.5:.2f} {cy+0.05:.2f} L {cx-r*0.12:.2f} {cy+r*0.42:.2f} "
         f"L {cx+r*0.55:.2f} {cy-r*0.45:.2f}")
    doc.add(f'<path d="{p}" fill="none" stroke="{color}" stroke-width="{r*0.34:.2f}" '
             f'stroke-linecap="round" stroke-linejoin="round"/>')


def emptybox(cx, cy, r, color):
    doc.add(f'<rect x="{cx-r*0.55:.2f}" y="{cy-r*0.55:.2f}" width="{r*1.1:.2f}" height="{r*1.1:.2f}" '
             f'rx="1" fill="none" stroke="{color}" stroke-width="{r*0.22:.2f}" opacity="0.55"/>')


# --------------------------------------------------------------------------
# Compact, icon-driven building blocks (used to replace long bullet lists
# with something more visual/poster-like and much lower in word count)
# --------------------------------------------------------------------------
def mini_icon(kind, cx, cy, r, color):
    doc.add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{color}" opacity="0.13"/>')
    s = r * 0.55
    sw = r * 0.16
    if kind == "frontend":
        doc.add(f'<rect x="{cx-s:.2f}" y="{cy-s*0.75:.2f}" width="{2*s:.2f}" height="{1.5*s:.2f}" '
                 f'rx="{0.2*s:.2f}" fill="none" stroke="{color}" stroke-width="{sw:.2f}"/>')
        doc.add(f'<line x1="{cx-s:.2f}" y1="{cy-s*0.12:.2f}" x2="{cx+s:.2f}" y2="{cy-s*0.12:.2f}" '
                 f'stroke="{color}" stroke-width="{sw*0.85:.2f}"/>')
    elif kind == "database":
        ew, eh = s * 1.05, s * 0.4
        doc.add(f'<ellipse cx="{cx:.2f}" cy="{cy-s*0.55:.2f}" rx="{ew:.2f}" ry="{eh:.2f}" '
                 f'fill="none" stroke="{color}" stroke-width="{sw:.2f}"/>')
        doc.add(f'<line x1="{cx-ew:.2f}" y1="{cy-s*0.55:.2f}" x2="{cx-ew:.2f}" y2="{cy+s*0.55:.2f}" '
                 f'stroke="{color}" stroke-width="{sw:.2f}"/>')
        doc.add(f'<line x1="{cx+ew:.2f}" y1="{cy-s*0.55:.2f}" x2="{cx+ew:.2f}" y2="{cy+s*0.55:.2f}" '
                 f'stroke="{color}" stroke-width="{sw:.2f}"/>')
        doc.add(f'<path d="M {cx-ew:.2f} {cy+s*0.55:.2f} A {ew:.2f} {eh:.2f} 0 0 0 {cx+ew:.2f} {cy+s*0.55:.2f}" '
                 f'fill="none" stroke="{color}" stroke-width="{sw:.2f}"/>')
    elif kind == "cascade":
        for dx in (-s * 0.4, s * 0.4):
            doc.add(f'<path d="M {cx+dx-s*0.3:.2f} {cy-s*0.5:.2f} L {cx+dx+s*0.3:.2f} {cy:.2f} '
                     f'L {cx+dx-s*0.3:.2f} {cy+s*0.5:.2f}" fill="none" stroke="{color}" '
                     f'stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round"/>')
    elif kind == "loop":
        doc.add(f'<path d="M {cx-s*0.65:.2f} {cy-s*0.15:.2f} A {s*0.68:.2f} {s*0.68:.2f} 0 1 1 {cx+s*0.1:.2f} {cy+s*0.67:.2f}" '
                 f'fill="none" stroke="{color}" stroke-width="{sw:.2f}" stroke-linecap="round"/>')
        doc.add(f'<path d="M {cx+s*0.1:.2f} {cy+s*0.67:.2f} L {cx-s*0.05:.2f} {cy+s*0.28:.2f} '
                 f'M {cx+s*0.1:.2f} {cy+s*0.67:.2f} L {cx+s*0.48:.2f} {cy+s*0.55:.2f}" '
                 f'stroke="{color}" stroke-width="{sw:.2f}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    elif kind == "play":
        doc.add(f'<path d="M {cx-s*0.4:.2f} {cy-s*0.58:.2f} L {cx-s*0.4:.2f} {cy+s*0.58:.2f} '
                 f'L {cx+s*0.62:.2f} {cy:.2f} Z" fill="{color}"/>')
    elif kind == "editor":
        for i, dy in enumerate((-0.34, 0.0, 0.34)):
            wf = 1.0 if i < 2 else 0.58
            doc.add(f'<line x1="{cx-s*wf:.2f}" y1="{cy+s*dy:.2f}" x2="{cx+s*wf:.2f}" y2="{cy+s*dy:.2f}" '
                     f'stroke="{color}" stroke-width="{sw*0.9:.2f}" stroke-linecap="round"/>')
    elif kind == "wave":
        heights = [0.32, 0.75, 1.0, 0.5, 0.85, 0.38]
        n = len(heights)
        bw = (2 * s) / (n * 1.55)
        for i, hf in enumerate(heights):
            bx = cx - s + i * (bw * 1.55)
            bh = s * hf
            doc.add(f'<rect x="{bx:.2f}" y="{cy-bh/2:.2f}" width="{bw:.2f}" height="{bh:.2f}" '
                     f'rx="{bw/2:.2f}" fill="{color}"/>')
    elif kind == "export":
        doc.add(f'<line x1="{cx:.2f}" y1="{cy-s*0.6:.2f}" x2="{cx:.2f}" y2="{cy+s*0.12:.2f}" '
                 f'stroke="{color}" stroke-width="{sw:.2f}" stroke-linecap="round"/>')
        doc.add(f'<path d="M {cx-s*0.32:.2f} {cy-s*0.14:.2f} L {cx:.2f} {cy+s*0.24:.2f} L {cx+s*0.32:.2f} {cy-s*0.14:.2f}" '
                 f'fill="none" stroke="{color}" stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round"/>')
        doc.add(f'<line x1="{cx-s*0.55:.2f}" y1="{cy+s*0.6:.2f}" x2="{cx+s*0.55:.2f}" y2="{cy+s*0.6:.2f}" '
                 f'stroke="{color}" stroke-width="{sw:.2f}" stroke-linecap="round"/>')
    elif kind == "speed":
        doc.add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{s*0.75:.2f}" fill="none" stroke="{color}" stroke-width="{sw:.2f}"/>')
        doc.add(f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{cx+s*0.5:.2f}" y2="{cy-s*0.38:.2f}" '
                 f'stroke="{color}" stroke-width="{sw:.2f}" stroke-linecap="round"/>')
        doc.add(f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{cx:.2f}" y2="{cy-s*0.6:.2f}" '
                 f'stroke="{color}" stroke-width="{sw*0.7:.2f}" stroke-linecap="round"/>')
    elif kind == "ruler":
        doc.add(f'<rect x="{cx-s*0.85:.2f}" y="{cy-s*0.32:.2f}" width="{s*1.7:.2f}" height="{s*0.64:.2f}" '
                 f'rx="{s*0.12:.2f}" fill="none" stroke="{color}" stroke-width="{sw:.2f}"/>')
        for i in range(4):
            tx = cx - s * 0.6 + i * s * 0.4
            doc.add(f'<line x1="{tx:.2f}" y1="{cy-s*0.32:.2f}" x2="{tx:.2f}" y2="{cy:.2f}" '
                     f'stroke="{color}" stroke-width="{sw*0.75:.2f}"/>')
    elif kind == "clock":
        doc.add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{s*0.75:.2f}" fill="none" stroke="{color}" stroke-width="{sw:.2f}"/>')
        doc.add(f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{cx:.2f}" y2="{cy-s*0.5:.2f}" '
                 f'stroke="{color}" stroke-width="{sw*0.8:.2f}" stroke-linecap="round"/>')
        doc.add(f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{cx+s*0.38:.2f}" y2="{cy+s*0.12:.2f}" '
                 f'stroke="{color}" stroke-width="{sw*0.8:.2f}" stroke-linecap="round"/>')


def feature_card(x, y, w, h, kind, color, label, desc, desc_size=7.3):
    doc.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="3.8" fill="{LAVENDER_SOFT}"/>')
    icon_r = 9.0
    icx, icy = x + 14.5, y + 16.5
    mini_icon(kind, icx, icy, icon_r, color)
    label_lines = wrap_text(label, w - 31, 8.6, bold=True)[:1]
    text(x + 27, y + 19.5, label_lines[0] if label_lines else label, 8.6, weight="700", color=INK)
    ty = y + 35.5
    for line in wrap_text(desc, w - 9, desc_size)[:3]:
        text(x + 5, ty, line, desc_size, color=MUTED)
        ty += desc_size * 1.4


def feature_grid(x, y, w, items, cols=2, gap=9.0, card_h=50.0):
    """items: list of (icon_kind, color, label, desc)"""
    card_w = (w - gap * (cols - 1)) / cols
    for i, (kind, color, label, desc) in enumerate(items):
        r, c = divmod(i, cols)
        feature_card(x + c * (card_w + gap), y + r * (card_h + gap), card_w, card_h,
                     kind, color, label, desc)
    rows = -(-len(items) // cols)
    return y + rows * card_h + (rows - 1) * gap


def pill_row(x, y, w, items, color=NAVY, size=7.8, h=14.5, gap=6.0, row_gap=7.0):
    cx, cy = x, y
    max_x = x + w
    for label in items:
        pw = text_width(label, size, bold=True) + 15
        if cx + pw > max_x and cx > x:
            cx = x
            cy += h + row_gap
        doc.add(f'<rect x="{cx:.2f}" y="{cy:.2f}" width="{pw:.2f}" height="{h:.2f}" '
                 f'rx="{h/2:.2f}" fill="{LAVENDER_SOFT}" stroke="{color}" stroke-width="0.8" opacity="0.95"/>')
        text(cx + pw / 2, cy + h / 2 + size * 0.34, label, size, weight="700", color=INK, anchor="middle")
        cx += pw + gap
    return cy + h


# ==========================================================================
# HEADER
# ==========================================================================
def build_header():
    doc.add(f'<rect x="0" y="0" width="{PAGE_W}" height="{HEADER_H}" fill="{INDIGO}"/>')
    doc.add(f'<rect x="0" y="0" width="{PAGE_W}" height="{HEADER_H}" fill="url(#hdrgrad)"/>')
    doc.add(f'''<defs>
      <linearGradient id="hdrgrad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#3A2178"/>
        <stop offset="1" stop-color="{INDIGO_DARK}"/>
      </linearGradient>
    </defs>''')
    # thin decorative "subtitle timeline" motif along the very top
    bar_y = 6.0
    bx = MARGIN
    import random
    rng = random.Random(7)
    while bx < PAGE_W - MARGIN:
        bw = rng.uniform(10, 34)
        doc.add(f'<rect x="{bx:.2f}" y="{bar_y:.2f}" width="{bw:.2f}" height="2.2" rx="1.1" '
                 f'fill="#FFFFFF" opacity="0.16"/>')
        bx += bw + rng.uniform(4, 10)

    # Conference badge, top-right (the only "meta" line — no keyword chips)
    badge_w = 320.0
    bx0 = PAGE_W - MARGIN - badge_w
    text(bx0 + badge_w, 20.0, "12th Italian Conference on Computational Linguistics", 7.6,
         weight="600", color="#D9D0F2", anchor="end")
    text(bx0 + badge_w, 30.5, "CLiC-it 2026  ·  September 14–16, 2026  ·  Palermo, Italy", 8.6,
         weight="700", color=WHITE, anchor="end")

    # Title — the sole identity mark of the header (no duplicate wordmark above it)
    title_lines = ["SENSEI: A Simple, Elegant, and Nimble", "Subtitle Editing Interface"]
    ty = 70.0
    for line in title_lines:
        text(MARGIN, ty, line, 30.5, weight="700", color=WHITE, spacing="0.1")
        ty += 33.0

    # Authors
    ay = ty
    author_spans = [
        ("Mauro Cettolo", "700", WHITE), ("¹†, ", "400", "#CFC3EE"),
        ("Elia Soliman", "700", WHITE), ("²†, ", "400", "#CFC3EE"),
        ("Roldano Cattoni", "700", WHITE), ("¹, ", "400", "#CFC3EE"),
        ("Matteo Negri", "700", WHITE), ("¹, ", "400", "#CFC3EE"),
        ("Luisa Bentivogli", "700", WHITE), ("¹ and ", "400", "#CFC3EE"),
        ("Alessio Palmero Aprosio", "700", WHITE), ("²*", "400", "#CFC3EE"),
    ]
    rich_line(MARGIN, ay, author_spans, 12.5)

    # Affiliations + footnote markers, collapsed onto a single line
    afy = ay + 10.0
    text(MARGIN, afy, "¹ Fondazione Bruno Kessler, Trento   ·   ² University of Trento   —   "
                       "† Equal contribution   * Corresponding author",
         7.6, weight="400", color="#C2B6E6", italic=True)

    # bottom hairline
    hrule(0, HEADER_H, PAGE_W, color="#FFFFFF", w=0.6, opacity=0.14)


# ==========================================================================
# COLUMN 1 -- Motivation / Contributions / Architecture
# ==========================================================================
def build_column1(y0):
    x, w = COL_X[0], COL_W
    y = y0

    y = section_header(x, y, w, 1, "Motivation", PURPLE)
    y = paragraph(x, y, w,
        "Automatic subtitling keeps improving, but broadcast-ready output still "
        "needs human validation against reading speed, line length, "
        "lines-per-block, and text accuracy. Existing editors are either generic and free, or "
        "polished and closed. SENSEI closes that gap.",
        size=9.4, color=BODY_TEXT)
    y += 22

    y = section_header(x, y, w, 2, "Key contributions", GREEN)
    y = bullets(x, y, w, [
        ("Open by design.", "Apache-2.0, self-hostable, web-based — no local "
         "install, usable from any browser."),
        ("Natively bilingual.", "source and target are first-class, "
         "reactively synchronized tracks."),
        ("Compliance built in.", "live, per-block, user-configurable "
         "monitoring of every formatting constraint."),
    ], bullet_color=GREEN, size=9.2)
    y += 18

    y = section_header(x, y, w, 3, "System architecture", NAVY)
    y, iw, ih = embed_image(x, y, w, os.path.join(ASSETS, "diagram.png"))
    y += 11.0
    y = paragraph(x, y, w, "Figure 1. Overall architecture of the SENSEI ecosystem.",
                  size=7.3, color=MUTED, italic=True)
    y += 14
    y = feature_grid(x, y, w, [
        ("frontend", PURPLE, "Frontend", "Vue.js video preview, block editor & timeline."),
        ("database", GREEN, "Management DB", "users, projects, files & permissions."),
        ("cascade", NAVY, "Subtitling engine", "the two-stage ASR–MT cascade (§6)."),
        ("loop", OLIVE, "HITL loop", "edits & compliance checks close to SRT."),
    ], cols=2, card_h=60.0)
    return y


# ==========================================================================
# COLUMN 2 -- Interface screenshot + workspace + compliance
# ==========================================================================
def build_column2(y0):
    x, w = COL_X[1], COL_W
    y = y0

    y = section_header(x, y, w, 4, "The editing interface", PURPLE)
    # y, iw, ih = embed_image(x, y, w, os.path.join(ASSETS, "screenshot.png"))
    # y += 11.0
    # y = paragraph(x, y, w, "Figure 3. The SENSEI workspace, fully synchronized live.",
    #               size=7.3, color=MUTED, italic=True)
    # y += 14

    y = feature_grid(x, y, w, [
        ("export", PURPLE, "Top bar", "Undo (50 steps), Save, SRT export."),
        ("play", NAVY, "Video preview", "playback & full-screen inspection."),
        ("editor", GREEN, "Block editor", "Edit · Add · Delete · Duplicate · Merge"),
        ("wave", OLIVE, "Timeline", "waveform, drag-and-drop timing."),
    ], cols=2, card_h=60.0)
    y += 36

    y = section_header(x, y, w, 5, "Compliance at a glance", OLIVE)
    # formula card
    card_h = 32
    doc.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{card_h:.2f}" rx="3.4" fill="{LAVENDER_SOFT}"/>')
    text(x + w / 2, y + 14.5, "CPS = C ⁄ (t_out − t_in)", 15.0, weight="700",
         color=INK, anchor="middle")
    text(x + w / 2, y + 25.0, "reading speed, in characters per second", 7.4,
         color=MUTED, anchor="middle", italic=True)
    y += card_h + 14
    y = feature_grid(x, y, w, [
        ("speed", OLIVE, "Reading", "21 cps default (9 ZH, 4 JA)."),
        ("ruler", PURPLE, "Block", "max lines (d. 2) & chars per line (d. 42, 16 ZH, 13 JA)"),
        ("clock", NAVY, "Timing", "min/max on-screen duration"),
    ], cols=3, card_h=75.0, gap=6.0)
    y += 9
    y = paragraph(x, y, w, "All thresholds are user-editable; violations are flagged live.",
                  size=7.3, color=MUTED, italic=True)
    y += 15

    # text(x, y, "SENSEI BY THE NUMBERS", 8.6, weight="700", color=MUTED, spacing="0.4")
    # y += 10
    # stats = [
    #     # ("2", "cascade stages: baseline + refinement", PURPLE),
    #     ("5", "block operators", GREEN),
    #     # ("400+", "languages via MADLAD-400", NAVY),
    #     ("50", "steps in the Undo buffer", OLIVE),
    # ]
    # tile_gap = 10.0
    # tile_w = (w - tile_gap) / 2
    # tile_h = 52.0
    # for i, (num, label, col) in enumerate(stats):
    #     tx = x + (i % 2) * (tile_w + tile_gap)
    #     ty = y + (i // 2) * (tile_h + tile_gap)
    #     stat_tile(tx, ty, tile_w, tile_h, num, label, col)
    # y += 2 * tile_h + tile_gap
    return y


# ==========================================================================
# COLUMN 3 -- Pipeline / models / evaluation / open source / future work
# ==========================================================================
def build_column3(y0):
    x, w = COL_X[2], COL_W
    y = y0

    y = section_header(x, y, w, 6, "Subtitling pipeline", NAVY)
    y = paragraph(x, y, w,
        "A two-stage ASR–MT cascade, built entirely from freely available components.",
        size=9.2, color=BODY_TEXT)
    y += 12

    # mini pipeline strip: stage 1
    def stage_strip(y, label, steps, color):
        text(x, y, label, 8.6, weight="700", color=color, spacing="0.2")
        y += 14.0
        n = len(steps)
        gap = 5.0
        bw = (w - gap * (n - 1)) / n
        bh = 26.0
        for i, s in enumerate(steps):
            bx = x + i * (bw + gap)
            doc.add(f'<rect x="{bx:.2f}" y="{y:.2f}" width="{bw:.2f}" height="{bh:.2f}" rx="2.8" '
                     f'fill="{LAVENDER_SOFT}" stroke="{color}" stroke-width="0.8" opacity="0.95"/>')
            lines = wrap_text(s, bw - 5, 6.6, bold=True)[:3]
            ly = y + bh / 2 - (len(lines) - 1) * 3.9
            for line in lines:
                text(bx + bw / 2, ly, line, 6.6, weight="700", color=INK, anchor="middle")
                ly += 7.8
            if i < n - 1:
                ax = bx + bw + gap / 2
                doc.add(f'<path d="M {ax-1.9:.2f} {y+bh/2:.2f} L {ax+1.9:.2f} {y+bh/2:.2f} '
                         f'M {ax:.2f} {y+bh/2-2.1:.2f} L {ax+2.1:.2f} {y+bh/2:.2f} '
                         f'L {ax:.2f} {y+bh/2+2.1:.2f}" stroke="{color}" stroke-width="1.0" '
                         f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        return y + bh + 20

    y = stage_strip(y, "STAGE 1 — BASELINE",
                     ["SB-VAD\nsegmentation", "Whisper\nlarge-v3 ASR", "MADLAD\nMT per subtitle"], NAVY)
    y = stage_strip(y, "STAGE 2 — SENTENCE-AWARE REFINEMENT",
                     ["Aggregate\nVAD segments", "Voxtral\nASR", "Sentence\nMADLAD MT", "mwerAlign\nre-alignment"], PURPLE)

    # y = paragraph(x, y, w,
    #     "Post-processing enforces reading-speed/line-length compliance and "
    #     "filters hallucinated repetitions on both stages.",
    #     size=8.0, color=MUTED, italic=True)
    # y += 22

    # text(x, y, "MODELS", 8.6, weight="700", color=MUTED, spacing="0.4")
    # y += 12
    # y = pill_row(x, y, w, [
    #     "SpeechBrain VAD", "Whisper large-v3", "Voxtral-Mini-3B", "MADLAD-400-10B",
    # ], color=NAVY)
    # y += 32

    y += 10
    y = section_header(x, y, w, 7, "Evaluation highlights", GREEN)
    y = bullets(x, y, w, [
        (None, "IWSLT 2026 Subtitling task, 3 domains, up to 5 languages: the "
               "sentence-aware cascade consistently beats the baseline on "
               "BLEU, ChrF and BLEURT."),
        (None, "On ITV test2023: competitive with AppTek's commercial system, "
               "ahead of all previous FBK submissions (SubER)."),
    ], bullet_color=GREEN, size=9.4, gap=10.0)
    y += 20

    # y = section_header(x, y, w, 8, "Open source & what's next", OLIVE)
    # y = bullets(x, y, w, [
    #     (None, "Interface + pipeline + models, all Apache-2.0 — "
    #            "github.com/hlt-mt/sensei & /subtitler."),
    #     # (None, "Next: user studies with professional subtitlers, and more "
    #     #        "robust multi-speaker alignment."),
    # ], bullet_color=OLIVE, size=9.4, gap=10.0)
    return y


# ==========================================================================
# COMPARISON TABLE (full width band)
# ==========================================================================
TABLE_COLS = ["SENSEI", "MateSub", "HappyScribe", "Aegisub", "Subtitle Edit"]
TABLE_ROWS = [
    ("Automatic subtitle generation", [True, True, True, False, True]),
    ("Merge", [True, True, True, True, True]),
    ("Add", [True, True, True, True, True]),
    ("Delete", [True, True, True, True, True]),
    ("Duplicate", [True, False, False, True, False]),
    ("Edit text", [True, True, True, True, True]),
    ("Edit timestamp (keyboard)", [True, True, True, True, True]),
    ("Edit timestamp (mouse)", [True, True, True, False, True]),
    ("Fullscreen video", [True, False, True, False, True]),
    ("Resizeable interface", [True, "open/close sidebar only", "sidebar only", True, True]),
    ("Multi-language", [True, False, "separate environments", False, False]),
    ("Load SRT file", [True, True, True, True, True]),
    ("Playback of single subtitle", [True, True, False, True, "vertical sidebar only"]),
]


def build_comparison_table(y0):
    x, w = MARGIN, PAGE_W - 2 * MARGIN
    y = y0
    y = section_header(x, y, w, 8, "How does SENSEI compare?", OLIVE)
    y = paragraph(x, y, w,
        "The only environment combining automatic generation, bilingual tracks and "
        "compliance-aware editing under a fully open license:",
        size=9.4, color=BODY_TEXT)
    y += 9

    label_w = 225.0
    n_data = len(TABLE_COLS)
    data_w = w - label_w
    col_w = data_w / n_data
    header_h = 18.0
    row_h = 14.2

    table_top = y
    # header row
    doc.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{header_h:.2f}" fill="{INDIGO}"/>')
    text(x + 8, y + header_h / 2 + 3.0, "Functions", 8.6, weight="700", color=WHITE)
    for i, cname in enumerate(TABLE_COLS):
        cx = x + label_w + i * col_w
        highlight = (i == 0)
        if highlight:
            doc.add(f'<rect x="{cx:.2f}" y="{y:.2f}" width="{col_w:.2f}" height="{header_h:.2f}" fill="{PURPLE}"/>')
        text(cx + col_w / 2, y + header_h / 2 + 3.0, cname, 8.6, weight="700",
             color="#F2C94C" if highlight else WHITE, anchor="middle")
    y += header_h

    for ridx, (label, cells) in enumerate(TABLE_ROWS):
        if ridx % 2 == 1:
            doc.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{row_h:.2f}" fill="{TABLE_ZEBRA}"/>')
        doc.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{label_w:.2f}" height="{row_h:.2f}" '
                 f'fill="{LAVENDER}" opacity="0.55"/>')
        text(x + 8, y + row_h / 2 + 2.8, label, 8.0, weight="600", color=INK)
        for i, cell in enumerate(cells):
            cx = x + label_w + i * col_w
            if i == 0:
                doc.add(f'<rect x="{cx:.2f}" y="{y:.2f}" width="{col_w:.2f}" height="{row_h:.2f}" '
                         f'fill="{PURPLE}" opacity="0.07"/>')
            ccx, ccy = cx + col_w / 2, y + row_h / 2
            if cell is True:
                checkmark(ccx, ccy + 1.9, 4.3, GREEN if i > 0 else PURPLE)
            elif cell is False:
                emptybox(ccx, ccy + 1.2, 4.3, MUTED)
            else:
                lines = wrap_text(cell, col_w - 7, 6.3, bold=False)[:2]
                ly = ccy + 2.5 - (len(lines) - 1) * 3.4
                for line in lines:
                    text(ccx, ly, line, 6.3, color=MUTED, anchor="middle", italic=True)
                    ly += 6.8
        y += row_h

    # outer + column separators
    doc.add(f'<rect x="{x:.2f}" y="{table_top:.2f}" width="{w:.2f}" height="{y-table_top:.2f}" '
             f'fill="none" stroke="{RULE}" stroke-width="0.8"/>')
    doc.add(f'<line x1="{x+label_w:.2f}" y1="{table_top:.2f}" x2="{x+label_w:.2f}" y2="{y:.2f}" '
             f'stroke="{RULE}" stroke-width="0.8"/>')
    doc.add(f'<line x1="{x+label_w+col_w:.2f}" y1="{table_top:.2f}" x2="{x+label_w+col_w:.2f}" y2="{y:.2f}" '
             f'stroke="{PURPLE}" stroke-width="1.1" opacity="0.5"/>')
    for i in range(1, n_data):
        cx = x + label_w + i * col_w
        doc.add(f'<line x1="{cx:.2f}" y1="{table_top:.2f}" x2="{cx:.2f}" y2="{y:.2f}" '
                 f'stroke="{RULE}" stroke-width="0.6"/>')
    return y


# ==========================================================================
# FOOTER
# ==========================================================================
def build_footer():
    y0 = PAGE_H - FOOTER_H
    doc.add(f'<rect x="0" y="{y0:.2f}" width="{PAGE_W}" height="{FOOTER_H:.2f}" fill="{LAVENDER_SOFT}"/>')
    hrule(0, y0, PAGE_W, color=RULE, w=1.0)

    cy = y0 + FOOTER_H / 2

    # Logos, left
    lx = MARGIN
    _, lw, lh = embed_image(lx, y0 + 26, 95, os.path.join(ASSETS, "fbk-logo.png"),
                                max_height=40, shadow=False, border=None)
    lx += lw + 26
    _, lw2, lh2 = embed_image(lx, y0 + 20, 130, os.path.join(ASSETS, "marchio_unitrento_colore_it.png"),
                              max_height=48, shadow=False, border=None)

    # Funding + contact, middle
    mid_x = 330.0
    mid_w = 330.0
    text(mid_x, y0 + 28, "Funding", 7.4, weight="700", color=INK, spacing="0.3")
    text(mid_x, y0 + 37, "This work has received funding from the European Union's Horizon Europe programme",
         6.9, weight="400", color=MUTED)
    text(mid_x, y0 + 46.8, "under grant agreement No. 101213369 (DVPS).",
         6.9, weight="400", color=MUTED)
    # text(mid_x, y0 + 68, "cettolo@fbk.eu   ·   a.palmeroaprosio@unitn.it", 6.9,
    #      weight="400", color=MUTED)

    # QR codes + repo links, right — one QR per repository
    repos = [
        ("qr-sensei.png", "/sensei"),
        ("qr-subtitler.png", "/subtitler"),
    ]
    qr_size = 44.0
    qr_gap = 14.0
    block_w = qr_size * len(repos) + qr_gap * (len(repos) - 1)
    bx = PAGE_W - MARGIN - block_w
    qy = cy - qr_size / 2 - 3
    text(PAGE_W - MARGIN, qy - 8, "github.com/hlt-mt", 7.6, weight="700", color=INK, anchor="end")
    for i, (fname, label) in enumerate(repos):
        qx = bx + i * (qr_size + qr_gap)
        qr_path = os.path.join(ASSETS, fname)
        if os.path.exists(qr_path):
            embed_image(qx, qy, qr_size, qr_path, target_h=qr_size, border=RULE)
            text(qx + qr_size / 2, qy + qr_size + 8.5, label, 6.6, weight="400",
                 color=MUTED, anchor="middle")


# --------------------------------------------------------------------------
# Assemble
# --------------------------------------------------------------------------
def main():
    build_header()

    y_top = HEADER_H + 18

    x = COL_X[1]
    y = y_top + 10
    w = 2 * COL_W + GUTTER
    y, iw, ih = embed_image(x, y, w, os.path.join(ASSETS, "screenshot.png"))
    y += 11.0
    y = paragraph(x, y, w, "Figure 3. The SENSEI workspace, fully synchronized live.",
                  size=7.3, color=MUTED, italic=True)

    y_top += 20
    y1 = build_column1(y_top)
    y2 = build_column2(y_top + 280)
    y3 = build_column3(y_top + 280)
    y_table_start = max(y1, y2, y3)

    y_table_end = build_comparison_table(y_table_start)

    footer_top = PAGE_H - FOOTER_H
    if y_table_end > footer_top - 10:
        print(f"WARNING: content overflow, table ends at {y_table_end:.1f}, "
              f"footer starts at {footer_top:.1f}")

    build_footer()

    with open(OUT_SVG, "w", encoding="utf-8") as f:
        f.write(doc.render())
    print("wrote", OUT_SVG)
    print("column bottoms:", y1, y2, y3, "-> table starts", y_table_start, "ends", y_table_end)


if __name__ == "__main__":
    main()
