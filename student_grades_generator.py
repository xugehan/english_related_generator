# -*- coding: utf-8 -*-
"""
Make student header strips (cards) PDF from an Excel sheet.
- The first row of the Excel is treated as the header.
- Each student's row becomes one "card" with key:value items from the header.
- Cards are arranged in a neat grid per page.

Dependencies:
    pip install pandas reportlab openpyxl

Example:
    python make_strips.py --excel input.xlsx --pdf output.pdf --font /path/to/SimHei.ttf --cols 2 --rows 4
"""

import argparse
import math
import os
from typing import List, Tuple

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def try_register_font(font_path: str, font_name: str = "CNFont") -> str:
    """
    Try to register a TrueType font for Chinese text.
    If the file is missing or invalid, fall back to Helvetica (ASCII only).
    """
    if font_path and os.path.isfile(font_path):
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            return font_name
        except Exception as e:
            print(f"[Warn] Failed to register font '{font_path}': {e}")
    print("[Info] Using fallback 'Helvetica' (may not render Chinese).")
    return "Helvetica"


def format_value(v):
    """
    Pretty-print cell values:
    - Convert floats like 4.0 -> 4
    - Keep strings as-is
    - Replace NaN with '-'
    """
    if pd.isna(v):
        return "-"
    if isinstance(v, float):
        if abs(v - int(v)) < 1e-9:
            return str(int(v))
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return str(v)


def split_columns_evenly(keys: List[str], values: List[str], max_items_each_col: int) -> Tuple[List[Tuple[str,str]], List[Tuple[str,str]], List[Tuple[str,str]]]:
    """
    Split key/value pairs into two columns to keep cards compact.
    """
    pairs = list(zip(keys, values))
    left = pairs[:max_items_each_col]
    middle = pairs[max_items_each_col: 2 * max_items_each_col]
    right = pairs[2 * max_items_each_col:]
    return left, middle, right


def draw_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    name: str,
    class_: str,
    code: str,
    kv_left: List[Tuple[str, str]],
    kv_middle: List[Tuple[str, str]],
    kv_right: List[Tuple[str, str]],
    font: str,
    title_font_size: int = 14,
    body_font_size: int = 10,
    corner_radius: int = 10,
):
    """
    Draw a single rounded-rectangle card with a title and two-column key:value body.
    (0,0) is the bottom-left of the page. Card's anchor point is bottom-left at (x, y).
    """
    # Card background
    c.saveState()
    c.setLineWidth(1)
    c.setStrokeColorRGB(0.25, 0.35, 0.55)
    c.setFillColorRGB(0.97, 0.98, 1.0)
    # Rounded rectangle path
    c.roundRect(x, y, w, h, corner_radius, stroke=1, fill=1)

    inner_margin = 10
    title_y = y + h - inner_margin - title_font_size

    # Title (student name, clsss and code)
    c.setFont(font, title_font_size)
    c.setFillColorRGB(0.12, 0.18, 0.35)
    c.drawString(x + inner_margin, title_y, f"{name} {code}")

    # Divider line under title
    c.setStrokeColorRGB(0.75, 0.8, 0.95)
    c.line(x + inner_margin, title_y - 4, x + w - inner_margin, title_y - 4)

    # Body text
    c.setFont(font, body_font_size)
    c.setFillColorRGB(0.1, 0.1, 0.1)

    # Two columns area
    body_top = title_y - 20
    line_height = body_font_size + 4
    col_gap = 8
    col_w = (w - inner_margin * 2 - col_gap * 2) / 3

    # Left column
    cur_y = body_top
    for k, v in kv_left:
        text = f"{k}: {v}"
        c.drawString(x + inner_margin, cur_y, text)
        cur_y -= line_height


    # Middle column
    cur_y = body_top
    right_x = x + inner_margin + col_w + col_gap
    for k, v in kv_middle:
        text = f"{k}: {v}"
        c.drawString(right_x, cur_y, text)
        cur_y -= line_height

    # Right column
    cur_y = body_top
    right_x = right_x + col_w + col_gap
    for k, v in kv_right:
        text = f"{k}: {v}"
        c.drawString(right_x, cur_y, text)
        cur_y -= line_height

    c.restoreState()


def main():
    parser = argparse.ArgumentParser(description="Generate student strips (cards) PDF from Excel.")
    parser.add_argument("--excel", required=True, help="Path to input .xlsx file (first sheet used).")
    parser.add_argument("--pdf", required=True, help="Output PDF path.")
    parser.add_argument("--font", default="", help="Path to a TTF font that supports Chinese (e.g., SimHei/SourceHanSans).")
    parser.add_argument("--title", default="学生成绩小分条", help="Optional document title to place on the first page header.")
    parser.add_argument("--cols", type=int, default=2, help="Number of cards per row.")
    parser.add_argument("--rows", type=int, default=4, help="Number of card rows per page.")
    parser.add_argument("--portrait", action="store_true", help="Use portrait A4 (default is landscape).")
    parser.add_argument("--card_h", type=float, default=140, help="Card height in points.")
    parser.add_argument("--margin", type=float, default=36, help="Page margin in points (1/2 inch ≈ 36).")
    parser.add_argument("--gutter", type=float, default=16, help="Horizontal/vertical space between cards in points.")
    args = parser.parse_args()

    # Page size
    page_w, page_h = A4
    if args.portrait:
        page_w, page_h = portrait(A4)
    else:
        page_w, page_h = landscape(A4)

    # Register font
    font_name = try_register_font(args.font)

    # Read Excel
    df = pd.read_excel(args.excel, engine="openpyxl")
    if df.empty:
        raise ValueError("The Excel sheet is empty.")

    code_col_candidates = [c for c in df.columns if str(c).strip() in ("学号", "学号/Code", "code", "Code")]
    if code_col_candidates:
        code_col = code_col_candidates[0]
    else:
        code_col = df.columns[0]

    # Ensure there is a '姓名' column (or try to guess)
    name_col_candidates = [c for c in df.columns if str(c).strip() in ("姓名", "姓名/Name", "name", "Name")]
    if name_col_candidates:
        name_col = name_col_candidates[0]
    else:
        # Fallback to the first column
        name_col = df.columns[1]

    class_col_candidates = [c for c in df.columns if str(c).strip() in ("班级", "班级/Class", "class", "Class")]
    if class_col_candidates:
        class_col = class_col_candidates[0]
    else:
        class_col = df.columns[2]



    # Canvas
    c = canvas.Canvas(args.pdf, pagesize=(page_w, page_h))
    c.setTitle(args.title)

    # Pre-compute card width and positions
    usable_w = page_w - 2 * args.margin
    usable_h = page_h - 2 * args.margin

    card_w = (usable_w - (args.cols - 1) * args.gutter) / args.cols
    card_h = args.card_h

    # How many rows actually fit vertically if user-specified rows * card_h is too tall
    max_rows_fit = max(1, int((usable_h + args.gutter) // (card_h + args.gutter)))
    rows = min(args.rows, max_rows_fit)
    cards_per_page = args.cols * rows

    # Page header
    def draw_header(page_idx: int):
        c.saveState()
        c.setFont(font_name, 12)
        c.setFillColorRGB(0.15, 0.15, 0.15)
        header_y = page_h - args.margin + 10
        c.drawString(args.margin, header_y, f"{args.title}  —  Page {page_idx}")
        c.restoreState()

    page_idx = 1
    draw_header(page_idx)

    # Exclude the name column from detail list
    detail_cols = [cn for cn in df.columns if (not isinstance(cn, str)) or (cn != name_col and cn != code_col and cn != class_col)]

    # Estimate lines per column based on card height
    body_font_size = 8
    line_height = body_font_size + 4
    approx_lines_body = int((card_h - 36) // line_height)  # 36 ~ title+spacing
    max_each_col = max(1, approx_lines_body)

    card_count_on_page = 0
    for idx, row in df.iterrows():
        name = format_value(row[name_col])
        class_ = format_value(row[class_col])
        code = format_value(row[code_col])

        # Prepare left/right column key-values
        values = [format_value(row[col]) for col in detail_cols]
        left, middle, right = split_columns_evenly(detail_cols, values, max_each_col)

        # Compute card position
        pos_in_page = card_count_on_page % cards_per_page
        r = pos_in_page // args.cols
        c_in_row = pos_in_page % args.cols

        x = args.margin + c_in_row * (card_w + args.gutter)
        # From top to bottom: convert row index to y
        top_area = page_h - args.margin - card_h
        y = top_area - r * (card_h + args.gutter)

        draw_card(
            c,
            x,
            y,
            card_w,
            card_h,
            name=name,
            class_=class_,
            code=code,
            kv_left=left,
            kv_middle=middle,
            kv_right=right,
            font=font_name,
            title_font_size=10,
            body_font_size=body_font_size,
            corner_radius=10,
        )

        card_count_on_page += 1

        # New page if filled
        if (card_count_on_page % cards_per_page) == 0 and idx != len(df) - 1:
            c.showPage()
            page_idx += 1
            draw_header(page_idx)

    # Finish
    c.save()
    print(f"[OK] PDF saved to: {args.pdf}")


if __name__ == "__main__":
    main()
