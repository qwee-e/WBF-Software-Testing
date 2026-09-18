# 最终核对记录

最终代码下重新执行 001、002、004、005、006、008、014：**7 passed in 22.64s**，见 [pytest 日志](seven_cases.log) 和 [JUnit](seven_cases.xml)。
016 的最终代码正式执行单独保留在 [016 记录](../results/AI-WBF-016/summary.md)：**1 failed**，失败原因是 11 个主验证域输入复现已知分数上界问题。
以上是两次执行的结果，未拼接成虚构的一次 pytest 输出；生成样本、变换调用、调试重跑不计作额外编号用例。

检查项目：

- 9 组 Fuzz 缩减代表以及 014 桥接见证，均经命令行工具独立重放成功：[JSON](replay.json)、[实际输出](replay.log)。
- 正式 Fuzz 轨迹恰为 3,000 条；完整失败输入为 310 条，其中主验证域 11 条、附加探索域 299 条，与统计一致。
- 比较器及分数范围判据的 7 个正/负对照通过：行序可变，坐标、标签、分数关联损坏被拒绝，avg+True 的合法溢出未误报，max 的上界仍检查，NaN 被识别。见 [检查结果](harness_checks.json)。
- `git diff reproduction-success -- ensemble_boxes` 无差异，所有官方算法实现保持冻结版本。
- 核心文件 SHA256：`a9663b421bc3adf4c42d74ccb572d1e2e149ee2a1c5aab2a6e88eec46c6b13b9`。
- `git diff --check` 通过；新的脚本、结果和提交说明不使用人员分工称呼。

正式环境为 Python 3.10.16、NumPy 1.23.5、Numba 0.60.0、pytest 9.0.3、Hypothesis 6.168.0，完整系统信息保存在各条 `run.json`。
为补齐失败输入保存字段，016 以相同种子重新执行过；正式目录保留最终执行，未将重跑包装为更多独立随机输入。
