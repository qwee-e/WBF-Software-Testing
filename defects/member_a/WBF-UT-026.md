# WBF-UT-026：两个零分重合框融合得到 NaN 坐标

- 状态：数值无效结果已复现；未修复。
- 类型：零加权分数下的除零/无效坐标。
- 输入：两个模型各提供一个 `[0.1,0.1,0.5,0.5]` 框，类别均为1，分数均为0，权重 `[1,1]`，`skip_box_thr=0`、`iou_thr=0.55`、`conf_type='avg'`。
- 预期：不得返回 NaN/Inf；可以显式 `ValueError` 拒绝，或给出有限合法结果，包括过滤后的空结果。未强行指定唯一的零分框处置政策。
- 实际：返回 `boxes=[[nan,nan,nan,nan]]`、`scores=[0.0]`、`labels=[1.0]`；伴随 `RuntimeWarning: invalid value encountered in divide`。
- 判定：NG。输入坐标、类别、权重均正常，分数0等于过滤阈值，当前实现没有拒绝输入却返回无效框。

复现命令：

```powershell
.\.venv\Scripts\python.exe -m pytest manual_tests/member_a/test_wbf_member_a.py::test_026__zero_scores_must_not_produce_nan -v
```

证据：[批次07日志](../../manual_tests/member_a/results/batch_07/pytest.log)、[原始调用记录](../../manual_tests/member_a/results/batch_07/results.json)、[执行前预期](../../test_data/member_a/WBF-UT-026.json)。JSON 为保持标准格式，将非有限浮点值序列化为字符串 `"nan"`；pytest 日志中的 `nan` 来自实际 NumPy 数组。

原因定位：原文件第25行只过滤 `score < thr`，所以两个零分框都保留；完全重合使它们进入同簇；`get_weighted_box()` 第107行用 `conf=0` 去除坐标加权和，发生 `0/0`，最终返回 NaN 坐标。

建议：先明确零分框策略，可选择忽略零贡献框或对零和簇做显式检查。尚未实施修复，也未验证某一种修复方案；后续应与 `reproduction-success` 对照。
