# WBF-UT-023：数量不一致时触发 SystemExit

- 状态：异常行为已复现；是否按项目缺陷验收，待接口契约评审；未修复。
- 类型：输入校验与库函数异常处理的候选改进。
- 对应测试：`test_023__mismatched_scores_raise_value_error`。
- 输入：同一模型有2个框、1个分数、2个类别，权重为 `[1]`；完整数据见 [用例输入](../../test_data/member_a/WBF-UT-023.json)。
- 预期：显式 `ValueError` 并说明数量不一致，调用者可通过普通异常处理捕获。这是建议健壮性契约，不是原项目已承诺的异常类型。
- 实际：打印 `Error. Length of boxes arrays not equal to length of scores array: 2 != 1`，随后抛出 `SystemExit(None)`，没有返回结果。
- 判定：NG。不能将捕获到异常本身当作符合预期。

复现命令（项目根目录）：

```powershell
.\.venv\Scripts\python.exe -m pytest manual_tests/member_a/test_wbf_member_a.py::test_023__mismatched_scores_raise_value_error -v
```

证据：[批次06日志](../../manual_tests/member_a/results/batch_06/pytest.log)、[原始JSON及堆栈](../../manual_tests/member_a/results/batch_06/results.json)。执行时间、源码提交、SHA256和环境版本在 JSON 中记录；被测 WBF 源码与冻结基线一致。

原因定位：`ensemble_boxes/ensemble_boxes_wbf.py` 的 `prefilter_boxes()` 在第15—17行检查数量后调用 `exit()`。`SystemExit` 不属于 `Exception` 的子类，可能绕过调用者常规的 `except Exception`。本次记录器显式捕获了它，因此测试进程仍能继续；未将“测试进程已终止”描述为实际发生的结果。

建议：由项目确认严格输入校验契约后，改为带说明的 `ValueError`。本阶段只保留证据，不修改源码。
