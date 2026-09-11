# 测试28全零模型权重异常

被测对象：`ensemble_boxes/ensemble_boxes_wbf.py` 的 `weighted_boxes_fusion()`。设计来源：WBF 模块1人工测试设计框架2.0第28项。

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
      ]
    ],
    [
      [
        0.1,
        0.1,
        0.5,
        0.5
      ]
    ]
  ],
  "scores_list": [
    [
      0.9
    ],
    [
      0.9
    ]
  ],
  "labels_list": [
    [
      1
    ],
    [
      1
    ]
  ],
  "weights": [
    0,
    0
  ],
  "iou_thr": 0.55,
  "skip_box_thr": 0.0,
  "conf_type": "avg",
  "allows_overflow": false
}
```

## 执行前预期与依据

权重和为0，归一化无定义；本测试采用明确抛出ValueError的建议契约，待评审。不得静默返回NaN或Inf。

```json
{
  "boxes": null,
  "scores": null,
  "labels": null,
  "warnings": [],
  "contract": "value_error"
}
```

数值比较使用rtol=0、atol=1e-6，类别精确比较；异常契约用例不将当前错误行为改写为通过预期。

## 实际结果

**FAIL**。实际返回NaN坐标和NaN分数，并有除零相关警告。坐标除以贡献和0，分数又除以权重和0，缺少无效权重保护。与26存在零贡献除零的共同路径。

```json
{"case_id": "WBF-28", "warnings": ["invalid value encountered in divide", "invalid value encountered in scalar divide"], "exception": null, "exception_message": null, "boxes": [[NaN, NaN, NaN, NaN]], "scores": [NaN], "labels": [1.0], "shapes": [[1, 4], [1], [1]]}
```

## 证据与复现

使用已有wbf-test环境，在仓库根目录执行：

```bash
conda activate wbf-test
python -m pytest manual_tests/test_wbf_28.py -v -s
```

- [固定输入与预期](../test_data/WBF-28.json)
- [完整运行日志](results/WBF-28/pytest.log)
- [时间、环境、源码版本及哈希](results/WBF-28/execution.json)

处理状态：已复现；本轮为原版测试记录，未修改算法，修复提交与修改版回归结果待后续修复后补充。

相同输入与断言再次执行仍为FAIL（退出码1），见[重复执行日志](results/WBF-28/repeat.log)。
