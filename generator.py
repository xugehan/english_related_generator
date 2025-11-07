# -*- coding: utf-8 -*-
"""
Compact 2x3 "重默" worksheet PDF generator (SimSun + Times-Roman).

- Chinese font: SimSun from local "simsun.ttc" (same directory as this script).
- English fonts: Times-Roman (normal), Times-Bold (bold) — built-in in ReportLab.
- A4 portrait, 2 columns x 3 rows, NO gutters between rows/columns.
- Tight margins/padding to save space.
- 11pt for both header and body; header is forced to ONE line (auto-shrinks underlines).
- Header is bold (English truly bold; Chinese bold via <b> markup).

Run:
    python generator.py
"""

import os
import re
import sys

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

# --------------------------- Font setup ---------------------------

def register_simsun_from_local():
    """Register SimSun from a local 'simsun.ttc' placed next to this script."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    simsun_path = os.path.join(base_dir, "simsun.ttc")
    if os.path.isfile(simsun_path):
        try:
            pdfmetrics.registerFont(TTFont("SimSun", simsun_path))
            return "SimSun"
        except Exception as e:
            print("Failed to load local simsun.ttc, fallback to Helvetica:", e)
            return "Helvetica"
    else:
        print("simsun.ttc not found next to script, fallback to Helvetica.")
        return "Helvetica"

# Chinese (SimSun) & English (Times) font names used throughout
ZH_FONT = register_simsun_from_local()
EN_FONT = "Times-Roman"     # built-in
EN_FONT_BOLD = "Times-Bold" # built-in

# --------------------------- Mixed-text helpers ---------------------------

ASCII = set(range(32, 127))

def split_runs(s: str):
    """Split s into ASCII and non-ASCII runs (keeps order)."""
    return re.findall(r'[ -~]+|[^\x20-\x7E]+', s)

def wrap_mixed(s: str, en_font: str = EN_FONT, zh_font: str = ZH_FONT) -> str:
    """
    Wrap ASCII runs with <font name='en_font'>, others with <font name='zh_font'>,
    so a Paragraph may render mixed fonts correctly.
    """
    parts = []
    for tok in split_runs(s):
        if tok and all(ord(ch) in ASCII for ch in tok):
            parts.append(f"<font name='{en_font}'>{tok}</font>")
        else:
            parts.append(f"<font name='{zh_font}'>{tok}</font>")
    return "".join(parts)

def string_width_mixed(s: str, en_font: str = EN_FONT, zh_font: str = ZH_FONT, size: float = 11) -> float:
    """Measure width of mixed string by summing run widths with the given fonts."""
    width = 0.0
    for tok in split_runs(s):
        font = en_font if (tok and all(ord(ch) in ASCII for ch in tok)) else zh_font
        width += pdfmetrics.stringWidth(tok, font, size)
    return width

# --------------------------- Header builder ---------------------------

def build_header_one_line(date_str: str, scope: str, max_width: float, font_size: float = 11,
                          en_font_for_width: str = EN_FONT_BOLD, zh_font_for_width: str = ZH_FONT) -> str:
    """
    Make a one-line header that fits max_width at font_size.
    Uses bold EN font for width calculation to avoid wrap after bolding.

    Target format:
        "{date}重默 {scope} Name________ Class___"

    Strategy:
        reduce underline lengths (Name/Class) until fits; if needed, remove
        the space before 'Class' as last resort.
    """
    # Start with reasonably long underlines
    name_us = "________"
    class_us = "___"
    # Minimal underline lengths to keep visible lines
    min_name = "__"
    min_class = "_"

    def assemble(nu: str, cu: str, tight: bool = False) -> str:
        if tight:
            return f"{date_str}重默 {scope} Name{nu}Class{cu}"
        return f"{date_str}重默 {scope} Name{nu} Class{cu}"

    nu, cu = name_us, class_us
    header = assemble(nu, cu)

    # Slight safety margin to account for rendering quirks when bolding
    safety = 1.0 * mm
    while string_width_mixed(header, en_font_for_width, zh_font_for_width, font_size) > (max_width - safety):
        if len(nu) > len(min_name):
            nu = nu[:-1]
        elif len(cu) > len(min_class):
            cu = cu[:-1]
        else:
            # last resort: remove the space before "Class"
            header = assemble(nu, cu, tight=True)
            break
        header = assemble(nu, cu)
    return header

# --------------------------- PDF generator ---------------------------

def make_chongmo_pdf(date_str: str, scope: str, items: list, output_path: str) -> str:
    """
    Generate a compact A4 worksheet:
    - 2 x 3 grid
    - NO gutters between rows/columns
    - Small outer margin and inner padding
    - 11pt fonts
    - Bold, single-line header in each cell
    """
    if len(items) != 15:
        raise ValueError("Need exactly 15 items (10 words + 5 phrases).")

    PAGE_W, PAGE_H = A4
    margin = 8 * mm    # outer margin
    pad = 3 * mm       # inner padding (per cell)
    cols, rows = 2, 3

    # No gutters between columns/rows
    cell_w = (PAGE_W - 2 * margin) / cols
    cell_h = (PAGE_H - 2 * margin) / rows

    # Typography
    size = 11
    leading = 13.5

    # Styles (header bold via markup; English in header uses Times-Bold explicitly)
    header_style = ParagraphStyle(
        "hdr",
        fontName=ZH_FONT,   # base; actual runs are tagged inside
        fontSize=size,
        leading=leading,
        spaceAfter=2,
        alignment=TA_LEFT,
    )
    body_style = ParagraphStyle(
        "body",
        fontName=ZH_FONT,
        fontSize=size,
        leading=leading,
        spaceAfter=1,
        alignment=TA_LEFT,
    )

    c = canvas.Canvas(output_path, pagesize=A4)

    # Build bold header text that is guaranteed to fit one line
    inner_w = cell_w - 2 * pad
    header_plain = build_header_one_line(
        date_str, scope, inner_w, font_size=size,
        en_font_for_width=EN_FONT_BOLD, zh_font_for_width=ZH_FONT
    )
    # Use Times-Bold for ASCII runs in header; wrap entire header with <b> for Chinese bolding
    header_rich = "<b>" + wrap_mixed(header_plain, en_font=EN_FONT_BOLD, zh_font=ZH_FONT) + "</b>"

    # Prepare flowables for one cell
    flows = [Paragraph(header_rich, header_style)]
    for i, t in enumerate(items, 1):
        line = f"{i}. {t}"
        flows.append(Paragraph(wrap_mixed(line, en_font=EN_FONT, zh_font=ZH_FONT), body_style))

    # Draw 2x3 cells
    for r in range(rows):
        for col in range(cols):
            x = margin + col * cell_w
            y = PAGE_H - margin - (r + 1) * cell_h
            c.rect(x, y, cell_w, cell_h, stroke=1, fill=0)
            Frame(x + pad, y + pad, inner_w, cell_h - 2 * pad, showBoundary=0).addFromList(list(flows), c)

    c.showPage()
    c.save()
    return output_path

# --------------------------- Demo ---------------------------

if __name__ == "__main__":
    # Replace with your real 10 words + 5 phrases (total 15 items)
    demo_items =       [
    "adj. 动态的；精力充沛的",
    "v. 驾驶；驱动；逼迫",
    "n. 无人机；嗡嗡声",
    "v. 淹死；淹没",
    "n. 干旱",
    "adv. 适当地；如期地",
    "v. 排出；耗尽",
    "adj. 戏剧性的；引人注目的",
    "v. 画；拉；吸引",
    "v. 钻孔；训练",
    "使某人发疯",
    "退学",
    "梦想做某事",
    "抽签",
    "盛装打扮"
]


    date = '1030'
    scope = 'download-D结束'
    out_path = os.path.abspath(f"重默-{date}-{scope}.pdf")
    if os.path.exists(out_path):
        indication = input("File exist, replace? [y]")
    else:
        indication = "y"
    if indication == "y":
        make_chongmo_pdf(date, scope, demo_items, out_path)
        print("PDF saved to:", out_path)
