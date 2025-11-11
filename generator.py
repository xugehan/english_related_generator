# -*- coding: utf-8 -*-
"""
Compact 2x3 "默写纸" worksheet PDF generator (SimSun + Times-Roman).

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
import io

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

# Optional imports for preview generation
try:
    import fitz  # PyMuPDF
    from PIL import Image
    HAS_PREVIEW_SUPPORT = True
except ImportError:
    HAS_PREVIEW_SUPPORT = False

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
        "{date} {scope} Name________ Class___"

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
            return f"{date_str} {scope} Name{nu}Class{cu}"
        return f"{date_str} {scope} Name{nu} Class{cu}"

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

def make_chongmo_pdf(date_str: str, scope: str, items: list, output_path: str,
                     cols: int = 2, rows: int = 3, font_size: float = 11, padding: float = 3) -> str:
    """
    Generate a compact A4 worksheet:
    - Flexible grid (default 2 x 3)
    - NO gutters between rows/columns
    - Small outer margin and inner padding
    - Customizable font size (default 11pt)
    - Bold, single-line header in each cell

    Args:
        date_str: Date string for header
        scope: Scope string for header
        items: List of items to display (any number)
        output_path: Path to save the PDF
        cols: Number of columns (default 2)
        rows: Number of rows (default 3)
        font_size: Font size in points (default 11)
        padding: Cell inner padding in mm (default 3)
    """
    if len(items) == 0:
        raise ValueError("Need at least 1 item.")

    PAGE_W, PAGE_H = A4
    margin = 8 * mm    # outer margin
    pad = padding * mm       # inner padding (per cell)

    # No gutters between columns/rows
    cell_w = (PAGE_W - 2 * margin) / cols
    cell_h = (PAGE_H - 2 * margin) / rows

    # Typography
    size = font_size
    leading = size * 1.23  # Proportional leading

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

# --------------------------- Preview generator ---------------------------

def generate_preview_image(date_str: str, scope: str, items: list,
                          cols: int = 2, rows: int = 3, font_size: float = 11,
                          padding: float = 3, dpi: int = 150) -> bytes:
    """
    Generate a PNG preview image of the first page of the PDF.

    Args:
        date_str: Date string for the header
        scope: Scope string for the header
        items: List of items (any number)
        cols: Number of columns (default 2)
        rows: Number of rows (default 3)
        font_size: Font size in points (default 11)
        padding: Cell inner padding in mm (default 3)
        dpi: DPI for the preview image (default 150)

    Returns:
        bytes: PNG image data

    Raises:
        RuntimeError: If PyMuPDF or PIL is not available
        ValueError: If items list is empty
    """
    if not HAS_PREVIEW_SUPPORT:
        raise RuntimeError("Preview generation requires PyMuPDF and Pillow. Please install: pip install PyMuPDF pillow")

    if len(items) == 0:
        raise ValueError("Need at least 1 item.")

    # Generate PDF in memory
    pdf_buffer = io.BytesIO()

    # Temporarily generate PDF with in-memory buffer approach
    # Since make_chongmo_pdf requires a file path, we'll use a different approach
    PAGE_W, PAGE_H = A4
    margin = 8 * mm
    pad = padding * mm

    cell_w = (PAGE_W - 2 * margin) / cols
    cell_h = (PAGE_H - 2 * margin) / rows

    size = font_size
    leading = size * 1.23

    header_style = ParagraphStyle(
        "hdr",
        fontName=ZH_FONT,
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

    c = canvas.Canvas(pdf_buffer, pagesize=A4)

    inner_w = cell_w - 2 * pad
    header_plain = build_header_one_line(
        date_str, scope, inner_w, font_size=size,
        en_font_for_width=EN_FONT_BOLD, zh_font_for_width=ZH_FONT
    )
    header_rich = "<b>" + wrap_mixed(header_plain, en_font=EN_FONT_BOLD, zh_font=ZH_FONT) + "</b>"

    flows = [Paragraph(header_rich, header_style)]
    for i, t in enumerate(items, 1):
        line = f"{i}. {t}"
        flows.append(Paragraph(wrap_mixed(line, en_font=EN_FONT, zh_font=ZH_FONT), body_style))

    for r in range(rows):
        for col in range(cols):
            x = margin + col * cell_w
            y = PAGE_H - margin - (r + 1) * cell_h
            c.rect(x, y, cell_w, cell_h, stroke=1, fill=0)
            Frame(x + pad, y + pad, inner_w, cell_h - 2 * pad, showBoundary=0).addFromList(list(flows), c)

    c.showPage()
    c.save()

    # Convert PDF to image
    pdf_buffer.seek(0)
    pdf_bytes = pdf_buffer.getvalue()

    # Open with PyMuPDF
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = pdf_doc[0]  # First page

    # Render to pixmap
    mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 is the default DPI
    pix = page.get_pixmap(matrix=mat)

    # Convert to PIL Image and then to PNG bytes
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    pdf_doc.close()

    return img_buffer.getvalue()

# --------------------------- Demo ---------------------------

if __name__ == "__main__":
    # Replace with your real 10 words + 5 phrases (total 15 items)
    demo_items =   [
    "n. 鹰",
    "n. 耳朵",
    "v. 赢得；挣得；搏得",
    "n. 地震",
    "adj. 东方的；东部的",
    "n. 生态学",
    "n. 经济",
    "n. 边缘；刀刃；优势",
    "n. 编辑；审校者；剪辑师",
    "adj. 高效的",
    "放心好了，别着急",
    "赢得好名声",
    "在地球上",
    "紧张，不安",
    "起作用，生效"
]


    date = '1111'
    scope = 'eager-effort'
    out_path = os.path.abspath(f"{date}-{scope}.pdf")
    if os.path.exists(out_path):
        indication = input("File exist, replace? [y]")
    else:
        indication = "y"
    if indication == "y":
        make_chongmo_pdf(date, scope, demo_items, out_path)
        print("PDF saved to:", out_path)
