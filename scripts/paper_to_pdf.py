"""
Render the arXiv preprint as a clean Letter-size academic-paper PDF.
Uses markdown + xhtml2pdf with proper LaTeX-flavored CSS.
"""
import re
import sys
import types
from pathlib import Path

# Monkey-patch for xhtml2pdf signing module BEFORE xhtml2pdf is imported
_stub = types.ModuleType("xhtml2pdf.builders.signs")
class _Noop:
    @staticmethod
    def sign(*a, **kw): return False
_stub.PDFSignature = _Noop
sys.modules["xhtml2pdf.builders.signs"] = _stub

import markdown
from xhtml2pdf import pisa

SRC = Path("/Users/harshith/Documents/ChipPlacer/paper/arxiv_preprint.md")
DST = Path("/Users/harshith/Documents/ChipPlacer/paper/arxiv_preprint.pdf")
TMP = Path("/tmp/arxiv_paper.html")


# Replace LaTeX math with simple text (xhtml2pdf doesn't render math)
def clean_math(text):
    text = re.sub(r"\$([^$]+)\$", r"\1", text)
    text = re.sub(r"\\mathcal\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\sum_\{([^}]+)\}", r"sum over \1", text)
    text = re.sub(r"\\text\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\operatorname\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\approx", "≈", text)
    text = re.sub(r"\\times", "×", text)
    text = re.sub(r"\\to", "->", text)
    text = re.sub(r"\\le", "≤", text)
    text = re.sub(r"\\ge", "≥", text)
    text = re.sub(r"\\lambda", "λ", text)
    text = re.sub(r"\\sigma", "σ", text)
    text = re.sub(r"\\alpha", "α", text)
    text = re.sub(r"\\$\|?", "", text)
    return text


CSS = r"""
@page {
    size: Letter;
    margin: 0.85in 0.85in 1.0in 0.85in;
}
body {
    font-family: Times, "Times New Roman", serif;
    font-size: 10.5pt;
    line-height: 1.32;
    color: #111;
    text-align: justify;
}

h1 {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 16pt;
    font-weight: bold;
    color: #1a2a4a;
    margin: 18pt 0 8pt 0;
    padding-bottom: 4pt;
    border-bottom: 1.5pt solid #2a3a5a;
    text-align: left;
    page-break-before: always;
}
h1:first-of-type { page-break-before: avoid; }

h2 {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 12pt;
    font-weight: bold;
    color: #1a2a4a;
    margin: 14pt 0 4pt 0;
    text-align: left;
}

h3 {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 11pt;
    font-weight: bold;
    color: #2a3a5a;
    margin: 10pt 0 3pt 0;
    text-align: left;
}

h4 {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
    font-weight: bold;
    font-style: italic;
    color: #3a3a3a;
    margin: 8pt 0 2pt 0;
    text-align: left;
}

p {
    margin: 4pt 0 4pt 0;
    text-align: justify;
}

ul, ol {
    margin: 4pt 0 4pt 22pt;
}

li {
    margin: 1pt 0;
}

strong { font-weight: bold; }
em { font-style: italic; }

table {
    width: 100%;
    border-collapse: collapse;
    margin: 6pt 0 8pt 0;
    font-size: 9.5pt;
}

th {
    background: #2a3a5a;
    color: #ffffff;
    font-weight: bold;
    text-align: left;
    padding: 3pt 5pt;
    border: 0.5pt solid #1a2a4a;
    font-family: Helvetica, Arial, sans-serif;
}

td {
    padding: 2pt 5pt;
    border: 0.5pt solid #b0b0b8;
    vertical-align: top;
}

tr:nth-child(even) td {
    background: #f5f5fa;
}

code {
    font-family: Courier, monospace;
    font-size: 9.5pt;
    background: #f0f0f4;
    padding: 0pt 2pt;
}

pre {
    font-family: Courier, monospace;
    font-size: 9pt;
    background: #f5f5f8;
    border: 0.5pt solid #c0c0c8;
    padding: 6pt 8pt;
    white-space: pre-wrap;
    margin: 4pt 0;
}

hr {
    border: none;
    border-top: 0.5pt solid #c0c0c8;
    margin: 12pt 0;
}

.title {
    text-align: center;
    font-size: 17pt;
    font-weight: bold;
    margin: 8pt 0 6pt 0;
    color: #1a2a4a;
}

.authors {
    text-align: center;
    font-size: 11pt;
    margin: 4pt 0 2pt 0;
}

.affiliation {
    text-align: center;
    font-size: 9.5pt;
    color: #555;
    margin: 0 0 4pt 0;
    font-style: italic;
}

.date {
    text-align: center;
    font-size: 9.5pt;
    color: #555;
    margin: 2pt 0 16pt 0;
}

.abstract {
    background: #f8f9fc;
    border-left: 3pt solid #2a3a5a;
    padding: 6pt 10pt;
    margin: 10pt 18pt 12pt 18pt;
    font-size: 10pt;
}
"""


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>SmallChip AI: Real-Time Interactive Chip Placement</title>
<style>
__CSS__
</style>
</head>
<body>
__BODY__
</body>
</html>
"""


def main():
    md = SRC.read_text(encoding="utf-8")
    md = clean_math(md)
    # Render with tables + fenced code
    body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    # Find the title (first # line) and reformat as a centered title
    import re
    m = re.search(r"<h1[^>]*>([^<]+)</h1>", body)
    if m:
        title = m.group(1)
        # Replace the first h1 with a centered title block
        body = re.sub(r"<h1[^>]*>[^<]+</h1>", "", body, count=1)
        title_html = f"""
<div class="title">{title}</div>
<div class="authors"><b>Harshith Nelabhotla</b></div>
<div class="affiliation">Strongsville High School, Strongsville OH 44136, USA<br>hnelabhotla@students.strongsville.k12.oh.us</div>
<div class="affiliation"><b>Faculty sponsor:</b> Mrs. DiGioia, Strongsville High School Science Research Program</div>
<div class="date">September 4, 2026</div>
<hr>
"""
        body = title_html + body
    full = HTML_TEMPLATE.replace("__CSS__", CSS).replace("__BODY__", body)
    TMP.write_text(full, encoding="utf-8")
    DST.parent.mkdir(parents=True, exist_ok=True)
    with DST.open("wb") as f:
        result = pisa.CreatePDF(full, dest=f, encoding="utf-8")
    if result.err:
        sys.exit(f"PDF error: {result.err}")
    print(f"Wrote {DST} ({DST.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
