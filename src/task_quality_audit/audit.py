from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    deduction: int
    message: str
    suggestion: str


@dataclass(frozen=True)
class AuditReport:
    score: int
    grade: str
    findings: tuple[Finding, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "grade": self.grade,
            "findings": [asdict(item) for item in self.findings],
        }


def _finding(rule_id: str, severity: str, deduction: int, message: str, suggestion: str) -> Finding:
    return Finding(rule_id, severity, deduction, message, suggestion)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("task.json must contain a JSON object")
    return value


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def audit_task(task_dir: str | Path) -> AuditReport:
    root = Path(task_dir)
    findings: list[Finding] = []
    spec_path = root / "task.json"
    if not spec_path.is_file():
        findings.append(
            _finding("SPEC001", "critical", 35, "缺少 task.json。", "添加结构化任务规范。")
        )
        score = 100 - sum(item.deduction for item in findings)
        return AuditReport(score=max(score, 0), grade=_grade(max(score, 0)), findings=tuple(findings))

    spec = _load_json(spec_path)
    required_text = {
        "title": ("SPEC002", 8, "补充简洁、可区分的任务标题。"),
        "objective": ("SPEC003", 12, "明确待实现或待修复的行为。"),
        "constraints": ("SPEC004", 8, "列出语言、性能或兼容性约束。"),
        "acceptance_criteria": ("SPEC005", 12, "把完成条件写成可验证的验收标准。"),
    }
    for field, (rule, deduction, suggestion) in required_text.items():
        value = spec.get(field)
        if not isinstance(value, (str, list)) or not value:
            findings.append(
                _finding(rule, "high", deduction, f"缺少或未填写 {field}。", suggestion)
            )

    metadata = spec.get("metadata", {})
    if not isinstance(metadata, dict) or not metadata.get("difficulty"):
        findings.append(
            _finding("META001", "medium", 5, "缺少难度标记。", "使用 easy/medium/hard 或团队统一等级。")
        )
    if not isinstance(metadata, dict) or not metadata.get("tags"):
        findings.append(
            _finding("META002", "low", 3, "缺少任务标签。", "添加语言、领域和任务类型标签。")
        )

    execution = spec.get("execution", {})
    if not isinstance(execution, dict) or not execution.get("timeout_seconds"):
        findings.append(
            _finding("REPRO001", "high", 8, "未设置执行超时。", "为评测命令设置合理超时。")
        )
    if not isinstance(execution, dict) or "random_seed" not in execution:
        findings.append(
            _finding("REPRO002", "medium", 4, "未声明随机种子。", "即使任务不使用随机性，也明确填写 null 或固定值。")
        )
    if not (root / "requirements.lock").is_file():
        findings.append(
            _finding("REPRO003", "medium", 6, "缺少依赖锁定文件。", "提交 requirements.lock 或等价锁文件。")
        )

    tests_dir = root / "tests"
    test_files = sorted(tests_dir.glob("test_*.py")) if tests_dir.is_dir() else []
    if len(test_files) < 3:
        findings.append(
            _finding("TEST001", "high", 12, f"仅发现 {len(test_files)} 个测试文件。", "至少覆盖基础、边界和失败场景。")
        )
    names = " ".join(path.name.lower() for path in test_files)
    if not re.search(r"edge|boundary|empty|limit", names):
        findings.append(
            _finding("TEST002", "medium", 6, "未识别到边界测试。", "增加 edge/boundary/empty/limit 场景。")
        )
    if not re.search(r"invalid|error|failure|negative", names):
        findings.append(
            _finding("TEST003", "medium", 6, "未识别到失败场景测试。", "增加非法输入或预期失败场景。")
        )

    public_text = json.dumps(spec, ensure_ascii=False).lower()
    leakage_terms = ("gold_solution", "reference_solution.py", "完整答案如下", "copy this solution")
    if any(term in public_text for term in leakage_terms):
        findings.append(
            _finding("LEAK001", "critical", 25, "任务说明可能暴露标准答案。", "移除答案路径、完整实现或可直接复制的解法。")
        )

    score = max(0, 100 - sum(item.deduction for item in findings))
    return AuditReport(score=score, grade=_grade(score), findings=tuple(findings))
