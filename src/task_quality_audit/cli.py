from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import audit_task


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit an AI coding task package.")
    parser.add_argument("task_dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = audit_task(args.task_dir)
    rendered = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    print(rendered)
    if args.report:
        args.report.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report.score >= 80 else 1


if __name__ == "__main__":
    raise SystemExit(main())
