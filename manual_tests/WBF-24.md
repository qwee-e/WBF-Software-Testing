# 测试24框与类别数量不一致异常

被测对象：`ensemble_boxes/ensemble_boxes_wbf.py` 的 `weighted_boxes_fusion()`。设计来源：WBF 模块1人工测试设计框架2.0第24项。

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
    ]
  ],
  "scores_list": [
    [
      0.9
    ]
  ],
  "labels_list": [
    []
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

建议接口契约：无效输入应抛出可由调用方处理的ValueError，不能直接终止宿主进程。此契约尚待评审，实际退出行为单独记录。

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

**FAIL**。实际为SystemExit(None)，错误信息打印到stdout；直接运行的进程可能以成功状态退出。与23、30按exit调用同类根因归并，接口契约待评审。

```json
{"case_id": "WBF-24", "warnings": [], "exception": "SystemExit", "exception_message": "None"}
```

## 证据与复现

使用已有wbf-test环境，在仓库根目录执行：

```bash
conda activate wbf-test
python -m pytest manual_tests/test_wbf_24.py -v -s
```

- [固定输入与预期](../test_data/WBF-24.json)
- [完整运行日志](results/WBF-24/pytest.log)
- [时间、环境、源码版本及哈希](results/WBF-24/execution.json)

处理状态：已复现；本轮为原版测试记录，未修改算法，修复提交与修改版回归结果待后续修复后补充。
