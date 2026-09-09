"""Regression tests for the formal PDF builder."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from reportlab.lib import colors


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_report_pdf import ReportDocument, make_styles, table_from_lines  # noqa: E402


class ReportBuilderTests(unittest.TestCase):
    def test_pdf_template_uses_invariant_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            document = ReportDocument(str(Path(temporary_directory) / "report.pdf"))
        self.assertEqual(document.invariant, 1)

    def test_markdown_table_headers_use_visible_white_bold_text(self) -> None:
        styles = make_styles()
        table = table_from_lines(
            [
                "| Column A | Column B |",
                "| --- | --- |",
                "| value | value |",
            ],
            styles,
        )

        for paragraph in table._cellvalues[0]:
            self.assertEqual(paragraph.style.textColor, colors.white)
            self.assertEqual(paragraph.style.fontName, "Helvetica-Bold")


if __name__ == "__main__":
    unittest.main(verbosity=2)
