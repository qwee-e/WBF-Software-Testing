# WBF-UT-025：三坐标框触发底层 IndexError

- 状态：异常行为已复现；建议健壮性契约是否作为缺陷验收依据，待评审；未修复。
- 类型：输入维度校验的候选改进。
- 输入：`boxes_list=[[[0.1,0.1,0.5]]]`，`scores_list=[[0.9]]`，`labels_list=[[1]]`，`weights=[1]`。
- 预期：明确拒绝不是4个坐标的框，抛出说明维度问题的 `ValueError`。这是本次建议契约，非上游已经保证的异常类型。
- 实际：`IndexError: list index out of range`，没有返回结果。
- 判定：NG；保留原始失败，不标记为预期失败或通过。

复现命令：

```powershell
.\.venv\Scripts\python.exe -m pytest manual_tests/member_a/test_wbf_member_a.py::test_025__three_coordinates_raise_value_error -v
```

证据：[批次07日志](../../manual_tests/member_a/results/batch_07/pytest.log)、[JSON及异常堆栈](../../manual_tests/member_a/results/batch_07/results.json)、[执行前预期](../../test_data/member_a/WBF-UT-025.json)。JSON 包含执行时间、环境、源码提交和 SHA256。

原因定位：`ensemble_boxes/ensemble_boxes_wbf.py` 第32行读取 `box_part[3]` 前没有检查框长度。建议在入口验证维度并给出明确错误；当前尚未修改被测源码。
