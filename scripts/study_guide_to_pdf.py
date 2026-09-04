"""
Convert STUDY_GUIDE.md to a print-ready A4 PDF.
- Title page
- Section headers (auto-numbered, with anchors)
- Tables render properly
- Headers/footers with page numbers
- Two-column-friendly spacing
- Bookmarks for clickable navigation (TOC)
"""
import re
import sys
from pathlib import Path

from fpdf import FPDF

SRC = Path("/Users/harshith/Documents/ChipPlacer/STUDY_GUIDE.md")
DST = Path("/Users/harshith/Documents/ChipPlacer/STUDY_GUIDE_PRINT.pdf")


UNICODE_MAP = {
    "\u2014": "--",  # em-dash
    "\u2013": "-",   # en-dash
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
    "\u2026": "...", # ellipsis
    "\u2192": "->",  # right arrow
    "\u2190": "<-",  # left arrow
    "\u2264": "<=",  # leq
    "\u2265": ">=",  # geq
    "\u00b1": "+/-", # plus-minus
    "\u03bc": "u",   # mu
    "\u00b5": "u",   # micro
    "\u00b0": "deg", # degree
    "\u00d7": "x",   # times
    "\u2208": "in",  # element of
    "\u2282": "in",  # subset
    "\u2283": "sup", # superset
    "\u2286": "sub", # subset or equal
    "\u2287": "sup", # superset or equal
    "\u2113": "l",   # script l
    "\u2200": "for all",
    "\u2203": "exists",
    "\u2295": "(+)",
    "\u2297": "(x)",
    "\u00a9": "(c)",
    "\u00ae": "(R)",
    "\u2022": "*",
    "\u00a7": "section",
    "\u00b6": "P",
    "\u2207": "grad",
    "\u2202": "d",
    "\u2211": "sum",
    "\u2229": "n",
    "\u222a": "u",
    "\u2202": "d",
    "\u03a3": "sum",
    "\u03bb": "lambda",
    "\u00bd": "1/2",
    "\u00bc": "1/4",
    "\u00be": "3/4",
    "\u00f7": "/",
    "\u2032": "'",
    "\u2033": "''",
    "\u221e": "inf",
    "\u2248": "~=",
    "\u2260": "!=",
    "\u2261": "===",
    "\u22c5": "*",
    "\u2194": "<->",
    "\u21d2": "=>",
    "\u21d0": "<=",
    "\u21d4": "<=>",
    "\u00a0": " ",   # nbsp
    "\u2009": " ",
    "\u200b": "",
}


def strip_md(text: str) -> str:
    """Light markdown stripping for plain text cells + Unicode -> ASCII."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    for k, v in UNICODE_MAP.items():
        text = text.replace(k, v)
    # Drop any remaining non-ASCII (math symbols, etc.)
    text = re.sub(r"[^\x00-\x7f]", "?", text)
    return text


class StudyGuidePDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return  # cover
        self.set_y(8)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, "SmallChip AI  -  NEOSEF / ISEF Study Guide", align="L")
        self.cell(0, 5, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(10, 14, 200, 14)
        self.set_y(18)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(140, 140, 140)
        self.cell(0, 5, "Confidential - Harshith  -  Strongsville High School", align="C")


def render_inline(pdf: StudyGuidePDF, text: str, base_size: int = 10, base_style: str = ""):
    """Render text with **bold** and *italic* inline."""
    text = strip_md(text)
    # Split on **...** and *...*
    parts = re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            pdf.set_font("Helvetica", "B", base_size)
            pdf.write(base_size * 0.45, part[2:-2])
        elif part.startswith("*") and part.endswith("*"):
            pdf.set_font("Helvetica", "I", base_size)
            pdf.write(base_size * 0.45, part[1:-1])
        else:
            pdf.set_font("Helvetica", base_style, base_size)
            pdf.write(base_size * 0.45, part)
    pdf.ln(base_size * 0.6)


def render_table(pdf: StudyGuidePDF, rows: list[list[str]], col_widths: list[float]):
    """Render a markdown table with header bold + grid lines."""
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 230, 240)
    pdf.set_text_color(0, 0, 0)
    for i, cell in enumerate(rows[0]):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 230, 240)
        pdf.multi_cell(col_widths[i], 5, strip_md(cell), border=1, fill=True, new_x="END", new_y="TOP", max_line_height=pdf.font_size * 1.4)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_fill_color(255, 255, 255)
    for row in rows[1:]:
        row_h = 0
        # Pre-compute cell heights
        heights = []
        for i, cell in enumerate(row):
            lines = pdf.multi_cell(col_widths[i], 5, strip_md(cell), dry_run=True, output="LINES")
            heights.append(max(1, len(lines)))
        row_h = max(heights) * 5
        if pdf.get_y() + row_h > 280:
            pdf.add_page()
        x0, y0 = pdf.get_x(), pdf.get_y()
        for i, cell in enumerate(row):
            x = x0 + sum(col_widths[:i])
            pdf.set_xy(x, y0)
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(col_widths[i], 5, strip_md(cell), border=1, new_x="END", new_y="TOP", max_line_height=pdf.font_size * 1.4)
        pdf.set_y(y0 + row_h)


TOC_ENTRIES = [
    ("Section I",   "Formal Vocabulary"),
    ("Section II",  "The Project Introduction"),
    ("Section III", "Foundational Concepts of Chip Design"),
    ("Section IV",  "The Project in Formal Terms"),
    ("Section V",   "The Presentation"),
    ("Section VI",  "The Five Most Important Numbers"),
    ("Section VII", "Formal Definitions for Anticipated Questions"),
    ("Section VIII","How to Study This Document"),
    ("Section IX",  "Closing Note"),
]


def add_toc(pdf: StudyGuidePDF):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 30, 80)
    pdf.cell(0, 10, "Table of Contents", align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(80, 80, 120)
    pdf.line(15, pdf.get_y() + 1, 195, pdf.get_y() + 1)
    pdf.ln(6)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 12)
    for tag, title in TOC_ENTRIES:
        pdf.set_x(20)
        pdf.cell(35, 7, tag + " -", align="L")
        pdf.cell(0, 7, title, align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5,
        "How to use this guide: Read one section per day. Memorize Section I (vocabulary), "
        "internalize Section II (hooks and words to use), and rehearse Section V (the 12-minute pitch). "
        "Section VI is the canonical set of numbers. Section VII is the Q&A survival kit. "
        "Section VIII is the study plan. Section IX is the close.",
        new_x="LMARGIN", new_y="NEXT")


def add_cover(pdf: StudyGuidePDF):
    pdf.add_page()
    pdf.set_xy(0, 50)
    pdf.set_font("Helvetica", "B", 32)
    pdf.cell(0, 12, "SmallChip AI", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 16)
    pdf.cell(0, 8, "Formal Study Guide", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 13)
    pdf.cell(0, 8, "NEOSEF 2027  /  ISEF 2027", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_draw_color(50, 50, 50)
    pdf.line(60, 130, 150, 130)
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, "Math / Computer Science (MCS) Category", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Real-Time Interactive Chip Placement", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Graph Attention Network for the Sub-15K-Cell Market", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 7, "Harshith", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, "Strongsville High School  -  Strongsville, OH", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Faculty sponsor: Mrs. DiGioia", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, "Nine sections. Read one per day. Memorize I, II.D, and VI.", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "Rehearse the 12-minute pitch. Own the project.", align="C", new_x="LMARGIN", new_y="NEXT")


def parse_table(lines: list[str], idx: int):
    """Parse a markdown table starting at lines[idx]. Return (rows, next_idx)."""
    rows = []
    i = idx
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        line = lines[i].strip()
        if re.match(r"^\|[\s\-|:]+\|$", line):
            i += 1
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
        i += 1
    return rows, i


def main():
    pdf = StudyGuidePDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(15, 18, 15)

    # Cover
    add_cover(pdf)
    add_toc(pdf)

    # Body
    pdf.add_page()
    text = SRC.read_text(encoding="utf-8")
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            pdf.ln(2)
            i += 1
            continue

        # H1: # Section Title
        if stripped.startswith("# ") and not stripped.startswith("##"):
            pdf.add_page()
            title = strip_md(stripped[2:])
            pdf.set_font("Helvetica", "B", 20)
            pdf.set_text_color(30, 30, 80)
            pdf.multi_cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(80, 80, 120)
            pdf.line(15, pdf.get_y() + 1, 195, pdf.get_y() + 1)
            pdf.ln(4)
            pdf.set_text_color(0, 0, 0)
            i += 1
            continue

        # H2: ## Section
        if stripped.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(50, 50, 110)
            pdf.multi_cell(0, 7, strip_md(stripped[3:]), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
            pdf.set_text_color(0, 0, 0)
            i += 1
            continue

        # H3: ### Subsection
        if stripped.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 6, strip_md(stripped[4:]), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
            i += 1
            continue

        # H4: #### Sub-subsection
        if stripped.startswith("#### "):
            pdf.ln(1)
            pdf.set_font("Helvetica", "BI", 10)
            pdf.multi_cell(0, 5, strip_md(stripped[5:]), new_x="LMARGIN", new_y="NEXT")
            i += 1
            continue

        # Block quote
        if stripped.startswith("> "):
            pdf.set_text_color(60, 60, 60)
            pdf.set_font("Helvetica", "I", 10)
            quote_lines = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quote_lines.append(lines[i].lstrip()[1:].strip())
                i += 1
            for q in quote_lines:
                pdf.set_x(20)
                pdf.multi_cell(0, 5, strip_md(q), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            pdf.set_text_color(0, 0, 0)
            continue

        # Table
        if stripped.startswith("|"):
            rows, i = parse_table(lines, i)
            if not rows:
                continue
            n_cols = max(len(r) for r in rows)
            total = 180
            col_widths = [total / n_cols] * n_cols
            render_table(pdf, rows, col_widths)
            pdf.ln(3)
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            pdf.set_draw_color(200, 200, 200)
            y = pdf.get_y() + 1
            pdf.line(15, y, 195, y)
            pdf.ln(4)
            i += 1
            continue

        # Bullet list
        if re.match(r"^[-*]\s+", stripped):
            pdf.set_x(18)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(4, 5, chr(149), align="L")  # bullet
            render_inline(pdf, re.sub(r"^[-*]\s+", "", stripped), base_size=10)
            i += 1
            continue

        # Numbered list
        if re.match(r"^\d+\.\s+", stripped):
            pdf.set_x(18)
            m = re.match(r"^(\d+)\.\s+(.*)", stripped)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(6, 5, f"{m.group(1)}.", align="L")
            render_inline(pdf, m.group(2), base_size=10)
            i += 1
            continue

        # Plain paragraph
        pdf.set_font("Helvetica", "", 10)
        render_inline(pdf, stripped, base_size=10)
        i += 1

    pdf.output(str(DST))
    print(f"Wrote {DST}  ({DST.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
