# Coding Task Quality Audit

面向 AI Coding 训练数据的静态质量审计工具。它在任务进入标注、训练或评测流程之前，检查任务说明、测试设计、可复现性和答案泄漏风险，并输出 0-100 分质量报告。

## 审计维度

1. **任务定义**：标题、目标、约束、验收标准是否完整；
2. **元数据**：难度、标签、预期语言是否明确；
3. **可复现性**：是否设置超时、随机种子和依赖锁定信息；
4. **测试质量**：是否包含足够测试、边界场景和失败场景；
5. **泄漏风险**：公开说明中是否出现标准答案路径或完整解法提示。

## 快速开始

```bash
python -m pip install -e .
python -m task_quality_audit.cli examples/good_task
python -m unittest discover -s tests -v
```

输出示例：

```json
{
  "score": 100,
  "grade": "A",
  "findings": []
}
```

## 任务目录约定

```text
task/
├── task.json
├── requirements.lock
└── tests/
    ├── test_basic.py
    ├── test_edge_cases.py
    └── test_invalid_input.py
```

该工具不尝试判断题目本身是否“有价值”，而是提供一套可解释、可自动化的准入检查。实际生产流程还应叠加人工复核、去重检测、难度校准和多模型验证。

## 仓库标签建议

`ai-coding` `data-quality` `static-analysis` `benchmark` `qa` `python`

## License

MIT
