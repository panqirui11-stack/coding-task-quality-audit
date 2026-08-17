import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from task_quality_audit.audit import audit_task


GOOD_SPEC = {
    "title": "修复缓存失效逻辑",
    "objective": "使过期缓存不会返回旧值。",
    "constraints": ["Python 3.10+", "不修改公共 API"],
    "acceptance_criteria": ["过期条目重新计算", "现有测试通过"],
    "metadata": {"difficulty": "medium", "tags": ["python", "bugfix"]},
    "execution": {"timeout_seconds": 5, "random_seed": 42},
}


class AuditTests(unittest.TestCase):
    def make_good_task(self, root: Path) -> None:
        (root / "task.json").write_text(json.dumps(GOOD_SPEC, ensure_ascii=False), encoding="utf-8")
        (root / "requirements.lock").write_text("# no external dependencies\n", encoding="utf-8")
        tests = root / "tests"
        tests.mkdir()
        for name in ("test_basic.py", "test_edge_cases.py", "test_invalid_input.py"):
            (tests / name).write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")

    def test_good_task_scores_a(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_good_task(root)
            report = audit_task(root)
        self.assertEqual(report.score, 100)
        self.assertEqual(report.grade, "A")

    def test_missing_spec_is_critical(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = audit_task(temp_dir)
        self.assertLess(report.score, 80)
        self.assertEqual(report.findings[0].rule_id, "SPEC001")

    def test_leakage_is_detected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.make_good_task(root)
            spec = dict(GOOD_SPEC)
            spec["objective"] = "See reference_solution.py"
            (root / "task.json").write_text(json.dumps(spec), encoding="utf-8")
            report = audit_task(root)
        self.assertIn("LEAK001", {item.rule_id for item in report.findings})


if __name__ == "__main__":
    unittest.main()
