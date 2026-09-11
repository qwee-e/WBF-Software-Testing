# 模块1人工测试

本目录存放人工设计的测试用例、测试脚本和执行记录，被测函数为 `ensemble_boxes/ensemble_boxes_wbf.py` 中的 `weighted_boxes_fusion()`。

- 测试用例应说明编号、测试目的、输入、预期结果及预期结果的依据。
- 执行记录应区分预期结果与实际结果，并标注执行环境和对应代码版本。
- 共用输入数据放在 `../test_data/`，缺陷证据放在 `../defects/`。
- 官方自带测试保留在 `../tests/`；原项目复现材料保留在 `../lry_reproduction/`，不计作人工设计的测试成果。

成员一用例及执行方式见 [member_a/README.md](member_a/README.md)；实际进度以 [执行记录](../docs/member_a/执行记录.md) 为准。

测试 02（双模型完全相同且同类别的框）已执行通过，设计、手算预期与执行证据见 [WBF-02.md](WBF-02.md)，脚本为 `test_wbf_02.py`。该用例采用 AI 辅助编写与执行，需本人复核。

测试 04（同坐标不同类别隔离）和 06（同类别低 IoU 不融合）已执行通过，设计与执行证据见 [WBF-04-06.md](WBF-04-06.md)，脚本为 `test_wbf_04_06.py`，固定输入与手算预期位于 `test_data/WBF-04.json`、`test_data/WBF-06.json`。
