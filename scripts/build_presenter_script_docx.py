"""
build_presenter_script_docx.py

Converts docs/deck/firn_ev_presenter_script.md into a clean Word document
docs/deck/firn_ev_presenter_script.docx for read-aloud during the interview.

Markdown features supported:
    - # / ## / ### / #### headings (H1-H4)
    - **bold** and *italic* inline
    - `inline code` as monospace
    - > blockquotes (rendered as indented italic paragraphs)
    - - bullet lists
    - 1. numbered lists
    - --- horizontal rules (rendered as a thin grey separator paragraph)
    - | table | rendering

Usage:
    python scripts/build_presenter_script_docx.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt, RGBColor

sys.stdout.reconfigure(encoding="utf-8")

# ----- Paths ------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_MD = REPO_ROOT / "docs" / "deck" / "firn_ev_presenter_script.md"
OUTPUT_DOCX = REPO_ROOT / "docs" / "deck" / "firn_ev_presenter_script.docx"

# ----- Theme colors -----------------------------------------------------------
COLOR_PRIMARY = RGBColor(0x2C, 0x5F, 0x7C)
COLOR_SECONDARY = RGBColor(0xD9, 0x77, 0x57)
COLOR_TEXT = RGBColor(0x1A, 0x1A, 0x1A)
COLOR_TEXT_MUTED = RGBColor(0x5C, 0x5C, 0x5C)
COLOR_DIVIDER = RGBColor(0xCC, 0xCC, 0xCC)


# ----- Inline-formatting parser ----------------------------------------------
INLINE_RE = re.compile(
    r"(\*\*[^*]+\*\*|"      # bold: **...**
    r"\*[^*\n]+\*|"          # italic: *...*  (single-line, no inner asterisks)
    r"`[^`\n]+`)"            # inline code: `...`
)


def add_inline_runs(paragraph, text: str, italic_default: bool = False) -> None:
    """Parse inline markdown (**bold**, *italic*, `code`) into formatted runs."""
    parts = INLINE_RE.split(text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) >= 4:
            run = paragraph.add_run(part[2:-2])
            run.bold = True
            run.italic = italic_default
        elif part.startswith("*") and part.endswith("*") and len(part) >= 2:
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        elif part.startswith("`") and part.endswith("`") and len(part) >= 2:
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
        else:
            run = paragraph.add_run(part)
            run.italic = italic_default


# ----- Horizontal-rule paragraph ---------------------------------------------
def add_horizontal_rule(doc: Document) -> None:
    """Add a thin horizontal-rule paragraph (bottom border on empty paragraph)."""
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "CCCCCC")
    pBdr.append(bottom)
    pPr.append(pBdr)


# ----- Table builder ----------------------------------------------------------
def add_md_table(doc: Document, table_lines: list[str]) -> None:
    """Render a markdown table into a docx table.

    Expects: [header row, separator row, ...data rows].
    """
    if len(table_lines) < 2:
        return
    headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
    data_rows = [
        [c.strip() for c in row.strip("|").split("|")]
        for row in table_lines[2:]
    ]

    n_cols = len(headers)
    t = doc.add_table(rows=1 + len(data_rows), cols=n_cols)
    t.style = "Light Grid Accent 1"

    # Header row
    hdr_cells = t.rows[0].cells
    for k, h in enumerate(headers):
        cell = hdr_cells[k]
        cell.text = ""
        p = cell.paragraphs[0]
        add_inline_runs(p, h)
        for r in p.runs:
            r.bold = True

    # Data rows
    for k, row in enumerate(data_rows):
        row_cells = t.rows[k + 1].cells
        for m in range(n_cols):
            cell = row_cells[m]
            cell.text = ""
            cell_md = row[m] if m < len(row) else ""
            p = cell.paragraphs[0]
            add_inline_runs(p, cell_md)

    # Small spacing after table
    doc.add_paragraph()


# ----- Document setup --------------------------------------------------------
def configure_styles(doc: Document) -> None:
    """Set default font + heading styles."""
    # Body default
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.font.color.rgb = COLOR_TEXT

    # Headings
    for name, size, color in [
        ("Heading 1", 24, COLOR_PRIMARY),
        ("Heading 2", 18, COLOR_PRIMARY),
        ("Heading 3", 14, COLOR_TEXT),
        ("Heading 4", 12, COLOR_TEXT),
    ]:
        s = doc.styles[name]
        s.font.name = "Calibri"
        s.font.size = Pt(size)
        s.font.color.rgb = color
        s.font.bold = True


def configure_margins(doc: Document) -> None:
    """Set 1-inch margins on US Letter."""
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)


# ----- Main parser-renderer --------------------------------------------------
def build_docx() -> None:
    if not SOURCE_MD.exists():
        raise FileNotFoundError(f"Source markdown missing: {SOURCE_MD}")

    md = SOURCE_MD.read_text(encoding="utf-8")
    doc = Document()
    configure_margins(doc)
    configure_styles(doc)

    lines = md.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # Horizontal rule
        if line.strip() == "---":
            add_horizontal_rule(doc)
            i += 1
            continue

        # Headings
        if line.startswith("#### "):
            doc.add_heading(line[5:].strip(), level=4)
            i += 1
            continue
        if line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
            i += 1
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
            i += 1
            continue
        if line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=1)
            i += 1
            continue

        # Tables
        if line.startswith("|") and i + 1 < len(lines) and "---" in lines[i + 1]:
            table_lines = [line]
            j = i + 1
            while j < len(lines) and lines[j].startswith("|"):
                table_lines.append(lines[j])
                j += 1
            add_md_table(doc, table_lines)
            i = j
            continue

        # Blockquote
        if line.startswith("> "):
            quote_text = line[2:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.4)
            p.paragraph_format.right_indent = Inches(0.4)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            add_inline_runs(p, quote_text)
            i += 1
            continue

        # Bullet list
        if line.startswith("- "):
            content = line[2:].strip()
            p = doc.add_paragraph(style="List Bullet")
            add_inline_runs(p, content)
            i += 1
            continue

        # Numbered list (single-digit and double-digit)
        m_num = re.match(r"^(\d+)\.\s+(.*)$", line)
        if m_num:
            content = m_num.group(2).strip()
            p = doc.add_paragraph(style="List Number")
            add_inline_runs(p, content)
            i += 1
            continue

        # Blank line → consume but don't add multiple empty paragraphs
        if line.strip() == "":
            i += 1
            continue

        # Default: regular paragraph
        p = doc.add_paragraph()
        add_inline_runs(p, line)
        i += 1

    OUTPUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT_DOCX)
    print(f"Saved: {OUTPUT_DOCX}")
    print(f"Size:  {OUTPUT_DOCX.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_docx()
