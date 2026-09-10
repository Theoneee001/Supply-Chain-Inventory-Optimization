"""Regression tests for the formal PDF builder."""

from __future__ import annotations

import sys
import tempfile
import unittest
import csv
from pathlib import Path

from reportlab.lib import colors


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_report_pdf  # noqa: E402
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

    def test_title_metrics_are_loaded_from_generated_decisions(self) -> None:
        load_metrics = getattr(build_report_pdf, "load_title_metrics", None)
        self.assertIsNotNone(load_metrics, "PDF title metrics must come from generated decisions")
        if load_metrics is None:
            return
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "decisions.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["minimum_fill_rate", "s", "S", "average_daily_cost", "fill_rate"],
                )
                writer.writeheader()
                writer.writerows(
                    [
                        {"minimum_fill_rate": 0, "s": 0, "S": 14, "average_daily_cost": 19.4352, "fill_rate": 0.906},
                        {"minimum_fill_rate": 0.97, "s": 2, "S": 15, "average_daily_cost": 19.7937, "fill_rate": 0.977},
                    ]
                )
            self.assertEqual(load_metrics(path), ((0, 14, 19.4352), (2, 15, 0.977)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
