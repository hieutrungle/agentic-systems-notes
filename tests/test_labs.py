import unittest

from labs.autoresearch import run
from labs.tool_contract import Result, dispatch


class ToolContractTests(unittest.TestCase):
    def test_lookup(self):
        self.assertEqual(dispatch("lookup_run", {"run_id": "run-001"}), Result("ok", "baseline"))
        self.assertEqual(dispatch("lookup_run", {"run_id": "unknown"}), Result("not_found"))

    def test_unknown_tool_is_denied(self):
        self.assertEqual(dispatch("delete_run", {"run_id": "run-001"}), Result("unknown_tool"))

    def test_rejects_wrong_shape_and_type(self):
        for arguments in (None, [], {}, {"run_id": 1}, {"run_id": "run-001", "extra": True}):
            with self.subTest(arguments=arguments):
                self.assertEqual(dispatch("lookup_run", arguments), Result("invalid_arguments"))


class AutoResearchTests(unittest.TestCase):
    def test_strict_improvement_and_holdout(self):
        report = run(4)
        self.assertEqual([trial.accepted for trial in report.trials], [True, False, True, False])
        self.assertEqual([trial.incumbent for trial in report.trials], [2, 2, 3, 3])
        self.assertEqual(report.baseline_validation_mae, 3)
        self.assertEqual(report.winner_validation_mae, 0.5)
        self.assertEqual(report.holdout_mae, 1)

    def test_respects_budget(self):
        self.assertEqual(run(0).trials, ())
        self.assertEqual(run(0).winner, 0)
        self.assertEqual(len(run(1).trials), 1)
        self.assertEqual(run(1).winner, 2)

    def test_invalid_budget(self):
        for budget in (-1, 5):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                run(budget)
