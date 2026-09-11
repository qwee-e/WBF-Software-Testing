# WBF 复现成功基线

冻结日期：2026-09-11。Git 标签：`reproduction-success`。

本基线保存原项目源码、原示例运行证据、官方测试结果及兼容依赖快照，作为后续 Bug 分析和源码修改的对照，不属于自主测试成果，也不代表算法不存在 Bug。

## 冻结前确认

- Python 3.10.16；当前环境的 25 项依赖版本与 `requirements.compat.txt` 全部一致。
- `python -m pip check`：`No broken requirements found.`
- 重新运行 `python tests/test_bbox.py -v`：6 项官方测试全部通过，输出 `Ran 6 tests in 2.365s` 和 `OK`。
- 算法包中的 7 个 Python 文件、`examples/example.py` 和 `tests/test_bbox.py` 共 9 个文件的 SHA256 与已保存的复现记录全部一致。
- 原示例成功记录沿用 `example.log`、`example_capture.json` 和 8 张图像窗口截图；冻结时未重新运行 GUI 示例。
- 原项目源码未修改；本次新增项目协作约定 `AGENTS.md` 和本基线说明。

## 环境限制

成功复现依赖 NumPy 1.23.5。根目录 `requirements.txt` 中的 NumPy 2.0.2 会导致原示例报错，因此重建环境必须使用本目录的 `requirements.compat.txt`。详细经过见 `README.md` 和 `example_numpy2_failure.log`。

## 在独立目录取出基线

在项目根目录执行以下命令，保留当前工作目录用于后续开发：

```powershell
git worktree add --detach ../WBF-reproduction-success reproduction-success
cd ../WBF-reproduction-success
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r lry_reproduction/original_reproduction/requirements.compat.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe examples/example.py
.\.venv\Scripts\python.exe tests/test_bbox.py -v
```

示例图像窗口每次按空格继续。后续可通过 `git diff reproduction-success -- ensemble_boxes tests examples` 查看源码和测试相对本基线的变化。保持此标签不变，后续修改使用新的提交。
