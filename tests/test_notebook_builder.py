"""Regression tests for deterministic notebook publication."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_notebook as notebook_builder  # noqa: E402


class NotebookBuilderTests(unittest.TestCase):
    @staticmethod
    def notebook_with_residual(value: str) -> nbformat.NotebookNode:
        notebook = nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_code_cell(
                    outputs=[
                        nbformat.v4.new_output(
                            output_type="stream",
                            name="stdout",
                            text=f"Stationary residual ||pi P - pi||_inf: {value}\n",
                        )
                    ]
                )
            ]
        )
        notebook.metadata["language_info"] = {"name": "python", "version": "3.12.14"}
        return notebook

    def test_publication_stabilises_python_patch_version(self) -> None:
        stabilise = getattr(notebook_builder, "stabilise_notebook", None)
        self.assertIsNotNone(stabilise, "Notebook publication needs a stabilisation step")
        notebook = self.notebook_with_residual("1.3072876114961218e-14")

        stabilise(notebook)

        self.assertEqual(notebook.metadata["language_info"]["version"], "3.12")

    def test_publication_rounds_insignificant_residual_noise(self) -> None:
        stabilise = getattr(notebook_builder, "stabilise_notebook", None)
        self.assertIsNotNone(stabilise, "Notebook publication needs a stabilisation step")
        first = self.notebook_with_residual("1.3100631690576847e-14")
        second = self.notebook_with_residual("1.3072876114961218e-14")

        stabilise(first)
        stabilise(second)

        self.assertEqual(first.cells[0].outputs[0].text, second.cells[0].outputs[0].text)
        self.assertEqual(
            first.cells[0].outputs[0].text,
            "Stationary residual ||pi P - pi||_inf: 1.31e-14\n",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
