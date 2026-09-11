# WBF-Software-Testing

## 测试工作目录

```text
WBF-Software-Testing/
├── ensemble_boxes/          官方被测代码
├── tests/                   官方自带测试
├── manual_tests/            模块1人工测试
├── test_data/               测试数据
├── defects/                 缺陷材料
└── docs/                    需求分析、报告材料
```

- `ensemble_boxes/`：保留官方算法实现，被测入口为 `weighted_boxes_fusion()`。
- `tests/`：保留官方自带测试，与自行设计的人工测试区分。
- [manual_tests/](manual_tests/README.md)：模块1人工设计的测试用例、测试脚本与执行记录。
- [test_data/](test_data/README.md)：测试输入和预期结果数据。
- [defects/](defects/README.md)：缺陷复现步骤、证据和分析材料。
- [docs/](docs/README.md)：需求分析、测试计划及报告材料。

以上为测试工作的主要目录；已有 `examples/`、`benchmark_*/`、`lry_reproduction/`、`zjw_test/` 等目录继续保留。

## 原项目复现基线

冻结标签为 `reproduction-success`。运行环境及恢复方法见 [基线说明](lry_reproduction/original_reproduction/BASELINE.md)。成功复现使用 NumPy 1.23.5，重建环境应使用记录的兼容依赖快照。

原示例与官方测试的成功运行属于基线复现，不属于自行设计的测试成果。
