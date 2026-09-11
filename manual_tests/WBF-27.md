# 测试27禁止溢出时分数上界

被测对象：`ensemble_boxes/ensemble_boxes_wbf.py` 的 `weighted_boxes_fusion()`。设计来源：WBF 模块1人工测试设计框架2.0第27项。

## 固定输入

```json
{
  "boxes_list": [
    [
      [
        0.1,
        0.1,
        0.5,
        0.5
      ],
      [
        0.1,
        0.1,
        0.5,
        0.5
      ]
    ],
    []
  ],
  "scores_list": [
    [
      0.9,
      0.9
    ],
    []
  ],
  "labels_list": [
    [
      1,
      1
    ],
    []
  ],
  "weights": [
    2,
    1
  ],
  "iou_thr": 0.55,
  "skip_box_thr": 0.0,
  "conf_type": "avg",
  "allows_overflow": false
}
```

## 执行前预期与依据

allows_overflow参数文档明确False时分数不超过1；输入分数0.9合法，因此所有输出应有限且在[0,1]内。

```json
{
  "boxes": null,
  "scores": null,
  "labels": null,
  "warnings": [],
  "contract": "bounded"
}
```

数值比较使用rtol=0、atol=1e-6，类别精确比较；异常契约用例不将当前错误行为改写为通过预期。

## 实际结果

**FAIL**。实际分数约1.2，超过参数文档承诺的上限1。重复框贡献加权分数1.8，当前重标定乘2/3得到1.2，未真正限制分数上界。

```json
{"case_id": "WBF-27", "warnings": [], "exception": null, "exception_message": null, "boxes": [[0.10000000149011612, 0.10000000149011612, 0.5, 0.5]], "scores": [1.1999999682108562], "labels": [1.0], "shapes": [[1, 4], [1], [1]]}
```

## 证据与复现

使用已有wbf-test环境，在仓库根目录执行：

```bash
conda activate wbf-test
python -m pytest manual_tests/test_wbf_27.py -v -s
```

- [固定输入与预期](../test_data/WBF-27.json)
- [完整运行日志](results/WBF-27/pytest.log)
- [时间、环境、源码版本及哈希](results/WBF-27/execution.json)

处理状态：已复现；本轮为原版测试记录，未修改算法，修复提交与修改版回归结果待后续修复后补充。

相同输入与断言再次执行仍为FAIL（退出码1），见[重复执行日志](results/WBF-27/repeat.log)。
