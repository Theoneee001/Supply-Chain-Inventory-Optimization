from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_artifacts import require_complete_policy_grid  # noqa: E402


class ArtifactVerifierTests(unittest.TestCase):
    def test_each_scenario_must_contain_the_complete_unique_policy_grid(self) -> None:
        baseline = pd.DataFrame({"s": [1, 1, 2], "S": [3, 4, 4]})
        complete = pd.concat(
            [baseline.assign(scenario="baseline"), baseline.assign(scenario="steady")],
            ignore_index=True,
        )
        require_complete_policy_grid(complete, {"baseline", "steady"}, baseline)

        incomplete = complete.copy()
        incomplete.loc[incomplete.index[-1], ["s", "S"]] = [1, 3]
        with self.assertRaisesRegex(RuntimeError, "complete unique policy grid"):
            require_complete_policy_grid(incomplete, {"baseline", "steady"}, baseline)


if __name__ == "__main__":
    unittest.main(verbosity=2)
