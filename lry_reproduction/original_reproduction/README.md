# WBF 原项目复现记录

本目录仅记录原项目运行情况，属于环境搭建与基线复现，不属于自主设计的测试成果。官方测试指当前项目已有的 `tests/test_bbox.py`，本次未联网比对上游版本。

## 运行结果

- 环境：Windows，Python 3.10.16，独立虚拟环境 `.venv`。
- `python examples/example.py`：退出码 0，完成双模型 WBF、单模型 WBF、NMS、Soft-NMS 四个示例，保存 8 张原生图像窗口截图。
- `python tests/test_bbox.py -v`：原有 6 个测试全部通过，输出 `Ran 6 tests in 2.344s`、`OK`，退出码 0。
- `python -m pip check`：`No broken requirements found.`
- 算法包、示例脚本和官方测试的运行前后 SHA256 一致，未修改原源码。见 `source_hashes_before.csv` 和 `source_hashes_after.csv`。

## 依赖兼容性说明

首先按根目录 `requirements.txt` 安装全部依赖，并以 editable 模式安装本地算法包。
原列表中的 NumPy 2.0.2 会使示例在 `np.unique(labels_list)` 处出现不等长嵌套列表的 `ValueError`，首次失败日志保存在 `example_numpy2_failure.log`。

为保持原源码不变，仅将虚拟环境的 NumPy 调整为 1.23.5，其余直接依赖保持原列表版本。调整后示例完成运行，但保留 `VisibleDeprecationWarning`。因此本次证明的是原项目在记录的兼容环境中可以运行，不能表述为当前根目录依赖列表可直接无误运行。

完整安装版本见 `environment_freeze.txt`；可移植依赖快照见 `requirements.compat.txt`。根目录 `requirements.txt` 未改动。

## 再次运行

在项目根目录使用 PowerShell：

```powershell
# 已创建的环境可直接执行以下两条命令
.\.venv\Scripts\python.exe examples/example.py
.\.venv\Scripts\python.exe tests/test_bbox.py -v
```

示例每次显示图像后按空格继续，共 8 个窗口。重新创建环境时：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r lry_reproduction/original_reproduction/requirements.compat.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```

## 保存的证据

| 文件 | 内容 |
| --- | --- |
| `01_wbf_two_models_before.png` / `02_wbf_two_models_after.png` | 双模型 WBF 融合前后窗口截图 |
| `03_wbf_one_model_before.png` / `04_wbf_one_model_after.png` | 单模型 WBF 融合前后窗口截图 |
| `05_nms_before.png` / `06_nms_after.png` | NMS 处理前后窗口截图 |
| `07_soft_nms_before.png` / `08_soft_nms_after.png` | Soft-NMS 处理前后窗口截图 |
| `09_official_tests.png` | 官方测试原始日志在日志查看窗口中的截图 |
| `10_example_output.png` | 示例原始日志在日志查看窗口中的截图 |
| `example.log` / `official_tests.log` | 完整运行输出与退出码 |
| `install.log` / `install_project.log` / `install_numpy_compat.log` | 依赖安装、本地包安装及兼容性调整日志 |
| `pip_check.log` | 依赖一致性检查 |

`capture_example.py` 通过子进程直接运行原示例，仅截取其窗口并发送空格键；`capture_logs.py` 展示保存的原始日志后截屏。两者都是证据采集辅助脚本，不是新增测试用例。
