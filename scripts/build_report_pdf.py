"""Build the formal PDF edition of the inventory optimisation report."""

from __future__ import annotations

import re
from functools import partial
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents
from svglib.svglib import svg2rlg


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "report" / "final_report.md"
OUTPUT = ROOT / "report" / "final_report.pdf"

NAVY = colors.HexColor("#243044")
TEAL = colors.HexColor("#117C75")
GOLD = colors.HexColor("#D7A43B")
CORAL = colors.HexColor("#D95D4F")
MID = colors.HexColor("#607086")
PALE = colors.HexColor("#EEF2F5")
WHITE = colors.white


class ReportDocument(BaseDocTemplate):
    """Document template with numbered headings, footer, and table of contents."""

    def __init__(self, filename: str) -> None:
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=22 * mm,
            rightMargin=22 * mm,
            topMargin=21 * mm,
            bottomMargin=19 * mm,
            title="Stochastic Inventory Optimisation for Ecommerce",
            author="Jialiang Gong",
            subject="Finite Markov-chain and Monte Carlo inventory policy study",
        )
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="body")
        self.addPageTemplates(PageTemplate(id="report", frames=[frame], onPage=self.draw_page))

    @staticmethod
    def draw_page(canvas, document) -> None:
        canvas.saveState()
        if document.page > 1:
            canvas.setStrokeColor(colors.HexColor("#D8DEE6"))
            canvas.line(22 * mm, 15 * mm, A4[0] - 22 * mm, 15 * mm)
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(MID)
            canvas.drawString(22 * mm, 10.5 * mm, "Stochastic Inventory Optimisation | Jialiang Gong")
            canvas.drawRightString(A4[0] - 22 * mm, 10.5 * mm, f"Page {document.page}")
        canvas.restoreState()

    def afterFlowable(self, flowable) -> None:
        if isinstance(flowable, Paragraph):
            style_name = flowable.style.name
            if style_name in {"ReportHeading1", "ReportHeading2"}:
                level = 0 if style_name == "ReportHeading1" else 1
                text = flowable.getPlainText()
                bookmark = f"heading-{self.seq.nextf('heading')}"
                self.canv.bookmarkPage(bookmark)
                self.canv.addOutlineEntry(text, bookmark, level=level, closed=False)
                self.notify("TOCEntry", (level, text, self.page, bookmark))


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "ReportBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=13.7,
            textColor=NAVY,
            spaceAfter=7,
            alignment=TA_LEFT,
            allowWidows=0,
            allowOrphans=0,
        ),
        "h1": ParagraphStyle(
            "ReportHeading1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=NAVY,
            spaceBefore=13,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "ReportHeading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=TEAL,
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "meta": ParagraphStyle(
            "ReportMeta",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=MID,
            spaceAfter=3,
        ),
        "caption": ParagraphStyle(
            "ReportCaption",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=8.2,
            leading=11,
            textColor=MID,
            alignment=TA_CENTER,
            spaceBefore=3,
            spaceAfter=9,
        ),
        "reference": ParagraphStyle(
            "ReportReference",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.3,
            leading=11.2,
            textColor=NAVY,
            leftIndent=10,
            firstLineIndent=-10,
            spaceAfter=4,
        ),
        "code": ParagraphStyle(
            "ReportCode",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.8,
            leading=10.5,
            textColor=NAVY,
            backColor=PALE,
            borderPadding=7,
            spaceBefore=4,
            spaceAfter=9,
        ),
        "toc_title": ParagraphStyle(
            "ContentsTitle",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=NAVY,
            spaceAfter=14,
        ),
    }


def inline_markup(text: str) -> str:
    safe = escape(text, quote=False)
    safe = re.sub(r"\[([^]]+)]\(([^)]+)\)", r'<link href="\2" color="#117C75">\1</link>', safe)
    safe = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', safe)
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", safe)
    return safe


def table_from_lines(lines: list[str], styles: dict[str, ParagraphStyle]) -> Table:
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines]
    rows = [rows[0], *rows[2:]]
    column_count = len(rows[0])
    available_width = A4[0] - 44 * mm
    column_widths = [available_width / column_count] * column_count
    data = [
        [Paragraph(inline_markup(cell), styles["body"]) for cell in row]
        for row in rows
    ]
    table = Table(data, colWidths=column_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD4DE")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def figure_flowable(relative_path: str, caption: str, styles: dict[str, ParagraphStyle]):
    drawing = svg2rlg(str((SOURCE.parent / relative_path).resolve()))
    max_width = A4[0] - 48 * mm
    max_height = 112 * mm
    scale = min(max_width / drawing.width, max_height / drawing.height, 1.0)
    drawing.width *= scale
    drawing.height *= scale
    drawing.scale(scale, scale)
    return KeepTogether(
        [
            Spacer(1, 4),
            drawing,
            Paragraph(escape(caption), styles["caption"]),
        ]
    )


def parse_markdown(styles: dict[str, ParagraphStyle]) -> list:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story: list = []
    paragraph_lines: list[str] = []
    figure_number = 0
    in_references = False

    def flush_paragraph() -> None:
        if paragraph_lines:
            text = " ".join(line.strip() for line in paragraph_lines)
            style = styles["meta"] if text.startswith("**Project type:**") else styles["body"]
            story.append(Paragraph(inline_markup(text), style))
            paragraph_lines.clear()

    index = 0
    in_code = False
    code_lines: list[str] = []
    while index < len(lines):
        line = lines[index]
        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["code"] ))
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            index += 1
            continue
        if in_code:
            code_lines.append(line)
            index += 1
            continue
        if line.startswith("| ") and index + 1 < len(lines) and lines[index + 1].startswith("| ---"):
            flush_paragraph()
            table_lines = [line, lines[index + 1]]
            index += 2
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            story.append(table_from_lines(table_lines, styles))
            story.append(Spacer(1, 8))
            continue
        image_match = re.fullmatch(r"!\[([^]]+)]\(([^)]+)\)", line.strip())
        if image_match:
            flush_paragraph()
            figure_number += 1
            story.append(
                figure_flowable(
                    image_match.group(2),
                    f"Figure {figure_number}. {image_match.group(1)}",
                    styles,
                )
            )
            index += 1
            continue
        if line.startswith("## "):
            flush_paragraph()
            heading = line[3:].strip()
            if heading.startswith("An (s, S)") or heading.startswith("A Markov-Chain"):
                index += 1
                continue
            story.append(Paragraph(inline_markup(heading), styles["h1"]))
            in_references = heading == "References"
        elif line.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[4:].strip()), styles["h2"]))
        elif line.startswith("# "):
            flush_paragraph()
        elif re.match(r"^\d+\. ", line):
            flush_paragraph()
            number, text = line.split(". ", 1)
            style = styles["reference"] if in_references else styles["body"]
            story.append(Paragraph(inline_markup(text), style, bulletText=f"{number}."))
        elif line.startswith("- "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[2:]), styles["body"], bulletText="•"))
        elif not line.strip():
            flush_paragraph()
        else:
            paragraph_lines.append(line)
        index += 1

    flush_paragraph()
    return story


def title_page(styles: dict[str, ParagraphStyle]) -> list:
    title_style = ParagraphStyle(
        "TitlePageTitle",
        parent=styles["h1"],
        fontSize=29,
        leading=34,
        alignment=TA_LEFT,
        textColor=NAVY,
        spaceAfter=16,
    )
    subtitle_style = ParagraphStyle(
        "TitlePageSubtitle",
        parent=styles["body"],
        fontSize=15,
        leading=21,
        textColor=TEAL,
        spaceAfter=22,
    )
    label_style = ParagraphStyle(
        "TitlePageLabel",
        parent=styles["body"],
        fontSize=10,
        leading=15,
        textColor=MID,
    )
    metric_style = ParagraphStyle(
        "TitlePageMetric",
        parent=styles["body"],
        fontSize=13,
        leading=18,
        textColor=NAVY,
    )
    metrics = Table(
        [
            [Paragraph("COST OPTIMUM", label_style), Paragraph("97% SERVICE CHOICE", label_style)],
            [Paragraph("(s, S) = (1, 12)<br/><b>19.66 per day</b>", metric_style), Paragraph("(s, S) = (2, 12)<br/><b>97.09% fill rate</b>", metric_style)],
        ],
        colWidths=[78 * mm, 78 * mm],
    )
    metrics.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), PALE),
                ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#E7F2F0")),
                ("BOX", (0, 0), (0, -1), 0.8, GOLD),
                ("BOX", (1, 0), (1, -1), 0.8, TEAL),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return [
        Spacer(1, 31 * mm),
        Table([["", ""]], colWidths=[34 * mm, 122 * mm], rowHeights=[3 * mm], style=TableStyle([("BACKGROUND", (0, 0), (0, 0), GOLD), ("BACKGROUND", (1, 0), (1, 0), TEAL)])),
        Spacer(1, 13 * mm),
        Paragraph("Stochastic Inventory<br/>Optimisation for Ecommerce", title_style),
        Paragraph("A Markov-chain and Monte Carlo study of one USB-C charging cable SKU", subtitle_style),
        Spacer(1, 6 * mm),
        metrics,
        Spacer(1, 22 * mm),
        Paragraph("ACADEMIC PORTFOLIO REPORT", label_style),
        Paragraph("Jialiang Gong", metric_style),
        Paragraph("Python | finite Markov chains | Monte Carlo | constrained optimisation | responsible AI", label_style),
        PageBreak(),
    ]


def build_pdf() -> None:
    styles = make_styles()
    contents = TableOfContents()
    contents.levelStyles = [
        ParagraphStyle("TOC1", fontName="Helvetica", fontSize=10, leading=15, leftIndent=0, textColor=NAVY),
        ParagraphStyle("TOC2", fontName="Helvetica", fontSize=9, leading=13, leftIndent=14, textColor=TEAL),
    ]
    story = title_page(styles)
    story.extend([Paragraph("Contents", styles["toc_title"]), contents, PageBreak()])
    story.extend(parse_markdown(styles))
    document = ReportDocument(str(OUTPUT))
    document.multiBuild(story, canvasmaker=partial(canvas.Canvas, invariant=1))
    print(f"PDF written to {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
