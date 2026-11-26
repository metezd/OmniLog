"""Turn software-design-report.md into HTML for render-pdf.sh, which prints it to PDF with Chromium."""
import pathlib
import re
import sys

import markdown

src = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
# GitHub starts a list right after a paragraph line, Python-Markdown needs an empty line first
LIST = re.compile(r"^\s*([-*+]|\d+\.)\s")
lines, fenced = [], False
for line in src.read_text(encoding="utf-8").splitlines():
    if line.lstrip().startswith("```"):
        fenced = not fenced
    if not fenced and LIST.match(line) and lines and lines[-1].strip() and not LIST.match(lines[-1]) \
            and not lines[-1].startswith(("  ", "\t", "|")):
        lines.append("")
    lines.append(line)
body = markdown.markdown(
    "\n".join(lines),
    extensions=["tables", "fenced_code", "toc", "sane_lists"],
)
css = """
@page { size: A4; margin: 16mm 14mm; }
body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #1f2328; }
h1 { font-size: 20pt; border-bottom: 1px solid #d0d7de; padding-bottom: 4px; }
h2 { font-size: 15pt; border-bottom: 1px solid #d0d7de; padding-bottom: 3px; margin-top: 22px; page-break-after: avoid; }
h3 { font-size: 12pt; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 9pt; }
tr { page-break-inside: avoid; }
th, td { border: 1px solid #d0d7de; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #f6f8fa; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 8.5pt; background: #f6f8fa; padding: 0 2px; word-break: break-word; }
pre { background: #f6f8fa; padding: 8px; white-space: pre-wrap; }
pre code { background: none; }
img { max-width: 100%; page-break-inside: avoid; }
hr { border: 0; border-top: 1px solid #d0d7de; }
"""
out.write_text(
    '<!doctype html><html lang="en"><head><meta charset="utf-8"><base href="file:///design/">'
    f"<title>OmniLog Software Design Report</title><style>{css}</style></head><body>{body}</body></html>",
    encoding="utf-8",
)
