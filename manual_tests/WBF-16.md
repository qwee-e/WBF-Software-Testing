# 测试16负坐标裁剪

被测对象：`ensemble_boxes/ensemble_boxes_wbf.py` 的 `weighted_boxes_fusion()`。设计来源：WBF 模块1人工测试设计框架2.0第16项。

## 固定输入

```json
{
  "boxes_list": [
    [
      [
        -0.1,
        -0.2,
        0.5,
        0.5
      ]
    ]
  ],
  "scores_list": [
    [
      0.9
    ]
  ],
  "labels_list": [
    [
      1
    ]
  ],
  "weights": [
    1
  ],
  "iou_thr": 0.55,
  "skip_box_thr": 0.0,
  "conf_type": "avg",
  "allows_overflow": false
}
```

## 执行前预期与依据

x1和y1小于0，分别裁剪为0并告警，修正后仍为正面积框。

```json
{
  "boxes": [
    [
      0,
      0,
      0.5,
      0.5
    ]
  ],
  "scores": [
    0.9
  ],
  "labels": [
    1
  ],
  "warnings": [
    "X1 < 0 in box. Set it to 0.",
    "Y1 < 0 in box. Set it to 0."
  ],
  "contract": null
}
```

数值比较使用rtol=0、atol=1e-6，类别精确比较；异常契约用例不将当前错误行为改写为通过预期。

## 实际结果

**PASS**。输出形状、数值、类别及警告全部符合预期。

```json
{"case_id": "WBF-16", "warnings": ["X1 < 0 in box. Set it to 0.", "Y1 < 0 in box. Set it to 0."], "exception": null, "exception_message": null, "boxes": [[0.0, 0.0, 0.5, 0.5]], "scores": [0.9], "labels": [1.0], "shapes": [[1, 4], [1], [1]]}
```

## 证据与复现

使用已有wbf-test环境，在仓库根目录执行：

```bash
conda activate wbf-test
python -m pytest manual_tests/test_wbf_16.py -v -s
```

- [固定输入与预期](../test_data/WBF-16.json)
- [完整运行日志](results/WBF-16/pytest.log)
- [时间、环境、源码版本及哈希](results/WBF-16/execution.json)

