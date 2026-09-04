"""
Build a print-ready PDF of STUDY_GUIDE.md using:
  markdown  (MD -> HTML)
  xhtml2pdf (HTML + CSS -> PDF)

Why this approach:
  - Real CSS, real tables, real typography
  - @page rules for Letter size, margins, page numbers
  - @page :first for cover (no header/footer)
  - Table styling that doesn't break across pages
  - Inline <a name="..."> anchors for clickable navigation
"""
import re
import sys
from pathlib import Path

import markdown

# Monkey-patch: xhtml2pdf imports pyhanko unconditionally but we don't sign PDFs.
# Stub out the signs module so the import doesn't fail.
import sys
import types
_stub = types.ModuleType("xhtml2pdf.builders.signs")
class _Noop:
    @staticmethod
    def sign(*a, **kw): return False
_stub.PDFSignature = _Noop
sys.modules["xhtml2pdf.builders.signs"] = _stub

from xhtml2pdf import pisa

SRC = Path("/Users/harshith/Documents/ChipPlacer/STUDY_GUIDE.md")
DST = Path("/Users/harshith/Documents/ChipPlacer/STUDY_GUIDE.pdf")
TMP_HTML = Path("/tmp/study_guide.html")


# ---------- Unicode cleanup for Helvetica-only PDF font ----------
UNICODE_MAP = {
    "\u2014": "--",  "\u2013": "-",
    "\u2018": "'",   "\u2019": "'",
    "\u201c": '"',   "\u201d": '"',
    "\u2026": "...",
    "\u2192": "->",  "\u2190": "<-",
    "\u2264": "<=",  "\u2265": ">=",
    "\u00b1": "+/-", "\u03bc": "u",   "\u00b5": "u",
    "\u00b0": "deg", "\u00d7": "x",   "\u00f7": "/",
    "\u2208": "in",  "\u2282": "in",  "\u2286": "sub",
    "\u2283": "sup", "\u2287": "sup",
    "\u2113": "l",   "\u2200": "for all", "\u2203": "exists",
    "\u2295": "(+)", "\u2297": "(x)",
    "\u00a9": "(c)", "\u00ae": "(R)",
    "\u2022": "*",   "\u00a7": "sec", "\u00b6": "P",
    "\u2207": "grad", "\u2202": "d",  "\u2211": "sum",
    "\u2229": "n",   "\u222a": "u",
    "\u03a3": "sum", "\u03bb": "lambda",
    "\u00bd": "1/2", "\u00bc": "1/4", "\u00be": "3/4",
    "\u2032": "'",   "\u2033": "''",
    "\u221e": "inf", "\u2248": "~=", "\u2260": "!=",
    "\u2261": "===",
    "\u22c5": "*",   "\u2194": "<->",
    "\u21d2": "=>",  "\u21d0": "<=",  "\u21d4": "<=>",
    "\u00a0": " ",   "\u2009": " ",   "\u200b": "",
    "\u2705": "[x]", "\u274c": "[ ]", "\u2713": "[x]", "\u2717": "[ ]",
}


def clean_text(s: str) -> str:
    for k, v in UNICODE_MAP.items():
        s = s.replace(k, v)
    # Drop any remaining non-ASCII (math symbols, etc.)
    s = re.sub(r"[^\x00-\x7f]", "?", s)
    return s


def clean_html(html: str) -> str:
    """Strip any non-ASCII chars after markdown rendering (math symbols etc.)."""
    # Walk text nodes only - keep tags intact
    def repl(m):
        return clean_text(m.group(0))
    # Match content of all text nodes (between > and <)
    return re.sub(r">([^<]+)<", lambda m: ">" + clean_text(m.group(1)) + "<", html)


# ---------- Add anchors to section headers for clickable TOC ----------
def add_anchors(html: str) -> str:
    counter = {"h1": 0, "h2": 0, "h3": 0}
    def repl(m):
        level = m.group(1)
        text = m.group(2)
        if level == "h1":
            counter["h1"] += 1
            counter["h2"] = 0
            anchor = f"sec_{counter['h1']}"
            # Mark "PART X" headings as page-break-before
            cls = ' class="part"' if counter["h1"] >= 1 else ""
        elif level == "h2":
            counter["h2"] += 1
            counter["h3"] = 0
            anchor = f"sec_{counter['h1']}_{counter['h2']}"
            cls = ""
        else:
            counter["h3"] += 1
            anchor = f"sec_{counter['h1']}_{counter['h2']}_{counter['h3']}"
            cls = ""
        return f'<{level}{cls} id="{anchor}">{text}</{level}>'
    # But we don't want page-break on the first h1 (the title) - apply only to PARTs
    # Re-process: only add class="part" to h1s that start with "PART"
    def add_part_class(html: str) -> str:
        return re.sub(r"<(h1) id=\"(sec_\d+)\">(PART [^<]+)</\1>",
                      r'<\1 class="part" id="\2">\3</\1>', html)
    html = re.sub(r"<(h[123])>(.+?)</\1>", repl, html, flags=re.DOTALL)
    html = add_part_class(html)
    return html


# ---------- CSS ----------
CSS = r"""
body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.4;
    color: #1a1a1a;
}

h1 {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 22pt;
    font-weight: bold;
    color: #1a2a4a;
    margin-top: 0;
    margin-bottom: 8pt;
    padding-bottom: 6pt;
    border-bottom: 2pt solid #3a4a6a;
}

h1.part {
    page-break-before: always;
}

h2 {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 16pt;
    font-weight: bold;
    color: #1a2a4a;
    margin-top: 16pt;
    margin-bottom: 6pt;
    padding-bottom: 3pt;
    border-bottom: 0.5pt solid #999;
}

h3 {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 12pt;
    font-weight: bold;
    color: #2a3a5a;
    margin-top: 12pt;
    margin-bottom: 4pt;
}

h4 {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 11pt;
    font-weight: bold;
    font-style: italic;
    color: #3a3a3a;
    margin-top: 8pt;
    margin-bottom: 3pt;
}

p {
    margin: 4pt 0 4pt 0;
    text-align: left;
}

ul, ol {
    margin: 4pt 0 4pt 18pt;
    padding-left: 6pt;
}

li {
    margin: 2pt 0;
}

strong { font-weight: bold; }
em { font-style: italic; }

code {
    font-family: Courier, monospace;
    font-size: 9pt;
    background: #f0f0f4;
    padding: 1pt 2pt;
}

pre {
    font-family: Courier, monospace;
    font-size: 8.5pt;
    background: #f5f5f8;
    border: 0.5pt solid #c0c0c8;
    padding: 6pt 8pt;
    white-space: pre-wrap;
    word-wrap: break-word;
    margin: 6pt 0;
}

blockquote {
    margin: 6pt 12pt;
    padding: 4pt 10pt;
    border-left: 3pt solid #4a5a8a;
    background: #f5f5fa;
    color: #2a2a3a;
    font-style: italic;
}

hr {
    border: none;
    border-top: 0.5pt solid #c0c0c8;
    margin: 12pt 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 6pt 0 10pt 0;
    font-size: 9pt;
}

th {
    background: #2a3a5a;
    color: #ffffff;
    font-weight: bold;
    text-align: left;
    padding: 4pt 6pt;
    border: 0.5pt solid #1a2a4a;
}

td {
    padding: 3pt 6pt;
    border: 0.5pt solid #c0c0c8;
    vertical-align: top;
}

a {
    color: #1a4a8a;
    text-decoration: none;
}

.cover {
    text-align: center;
    padding-top: 0.5in;
}

.cover-title {
    font-size: 36pt;
    font-weight: bold;
    color: #1a2a4a;
    margin: 0 0 4pt 0;
}

.cover-subtitle {
    font-size: 18pt;
    color: #2a3a5a;
    margin: 0 0 16pt 0;
}

.cover-fair {
    font-size: 14pt;
    font-style: italic;
    color: #3a3a3a;
    margin: 0 0 20pt 0;
}

.cover-line {
    width: 3in;
    margin: 12pt auto;
    border-top: 1pt solid #555;
}

.cover-tagline {
    font-size: 11pt;
    color: #2a2a2a;
    margin: 3pt 0;
}

.cover-name {
    font-size: 16pt;
    font-weight: bold;
    color: #1a2a4a;
    margin-top: 24pt;
}

.cover-school {
    font-size: 10pt;
    color: #2a2a2a;
    margin: 1pt 0;
}

.cover-note {
    font-size: 8.5pt;
    font-style: italic;
    color: #666;
    margin-top: 28pt;
}

table.toc-table {
    border: none;
    margin: 12pt auto;
    width: 80%;
}

table.toc-table td {
    border: none;
    padding: 4pt 8pt;
    background: transparent;
    font-size: 11pt;
}

table.toc-table td.toc-tag {
    font-weight: bold;
    color: #1a2a4a;
    width: 1.4in;
}

table.toc-table tr {
    border-bottom: 0.3pt dotted #888;
}

.header-text {
    color: #666;
    font-size: 8pt;
    font-style: italic;
    text-align: left;
}

.footer-text {
    color: #666;
    font-size: 8pt;
    font-style: italic;
    text-align: center;
}

.qa-question {
    font-weight: bold;
    color: #1a2a4a;
    margin-top: 8pt;
}

.numbers-table td.num {
    width: 1.2in;
    font-weight: bold;
    color: #1a2a4a;
    font-size: 11pt;
    text-align: center;
}
"""


# ---------- HTML page template ----------
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>SmallChip AI - Study Guide</title>
<style>
__CSS__
</style>
</head>
<body>

<div class="cover">
    <div class="cover-title">SmallChip AI</div>
    <div class="cover-subtitle">Study Guide</div>
    <div class="cover-fair">NEOSEF 2027 &nbsp;/&nbsp; ISEF 2027</div>
    <div class="cover-line"></div>
    <div class="cover-tagline">Math / Computer Science (MCS) Category</div>
    <div class="cover-tagline">Real-Time Interactive Chip Placement</div>
    <div class="cover-tagline">Graph Attention Network for the Sub-15K-Cell Market</div>
    <div class="cover-name">Harshith</div>
    <div class="cover-school">Strongsville High School &nbsp;-&nbsp; Strongsville, OH</div>
    <div class="cover-school">Faculty sponsor: Mrs. DiGioia</div>
    <div class="cover-note">
        Master glossary + 8-part study reference.<br>
        Read one section per day. Memorize Part I, IV, and VII.<br>
        Rehearse the 12-minute pitch. Own the project.
    </div>
</div>

__BODY__

</body>
</html>
"""


# ---------- TOC entries (auto-generated from headings) ----------
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


def build_toc(html: str) -> str:
    rows = []
    h1_seen = 0
    part_n = 0
    # Find all h1, h2 tags (handle class attribute)
    for m in re.finditer(r"<(h[12])(?:\s+class=\"[^\"]*\")?\s+id=\"([^\"]+)\">([^<]+)</\1>", html):
        level, anchor, text = m.group(1), m.group(2), m.group(3).strip()
        text = re.sub(r"<[^>]+>", "", text)  # strip inner HTML
        if level == "h1":
            h1_seen += 1
            # Skip ONLY the doc title h1 (the very first one).
            # PART I = h1_seen 2, PART II = h1_seen 3, ...
            if h1_seen == 1:
                continue
            part_n += 1
            tag = f"Part {ROMAN[part_n-1]}"
            rows.append(f'<tr><td class="toc-tag">{tag}</td><td><a href="#{anchor}">{text}</a></td></tr>')
        else:
            rows.append(f'<tr><td class="toc-tag">&nbsp;</td><td style="padding-left:18pt; font-size:10pt; color:#444;"><a href="#{anchor}">{text}</a></td></tr>')
    return (
        '<h1 id="toc">Table of Contents</h1>'
        '<table class="toc-table">'
        + "".join(rows)
        + "</table>"
    )


def main():
    md_text = SRC.read_text(encoding="utf-8")
    # Clean Unicode BEFORE markdown rendering
    md_text = clean_text(md_text)

    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists"],
    )
    html_body = add_anchors(html_body)
    # Insert TOC right after the first h1
    toc_html = build_toc(html_body)
    # Find the first h1 (after the leading "How to Use This Document" h1 if any)
    # The first h1 is the title; the second h1 is "Table of Contents" header we just generated.
    # Better: insert TOC right after the "## How to Use This Document" section.
    # The first h1 in the source is "# SmallChip AI -- Study Guide". Let's place TOC after that.
    match = re.search(r'(<h1 id="sec_1">.*?</h1>)', html_body, flags=re.DOTALL)
    if match:
        html_body = html_body[:match.end()] + toc_html + html_body[match.end():]
    else:
        # fallback: prepend
        html_body = toc_html + html_body

    # Build final HTML
    full_html = HTML_TEMPLATE.replace("__CSS__", CSS).replace("__BODY__", html_body)
    TMP_HTML.write_text(full_html, encoding="utf-8")

    with DST.open("wb") as out:
        result = pisa.CreatePDF(full_html, dest=out, encoding="utf-8")
    if result.err:
        sys.exit(f"PDF generation failed: {result.err}")
    print(f"Wrote {DST} ({DST.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
