# WBF 模块1自动化测试工程

这是“自动化测试脚本（源代码工程）”交付件。包含被测源码、30条用例对应的测试脚本、测试数据、固定版本依赖和一键运行入口。测试使用 pytest，预期值和断言沿用双方已完成的用例，没有为使报告全绿而修改算法或放宽断言。

## 快速运行（Windows）

1. 安装 **Python 3.10**；建议使用64位版本，并确保 `py -3.10` 或 `python` 能找到该版本。
2. 将 ZIP **完整解压**到普通目录，不能直接在压缩包中双击脚本。
3. 双击根目录的 **`run_tests.bat`**。

脚本会创建独立的 `.venv-test` 环境，按 `requirements-test.txt` 安装依赖，然后自动运行全部用例。首次安装需要网络，之后仍会检查依赖是否已满足。结束时窗口保留，结果保存在 `test_results/时间戳/`。

运行不需要 Git、GitHub 登录、Conda、Excel、IDE 或图形显示。已有 Python 和依赖环境时，也可直接执行：

```powershell
python run_tests.py
```

指定一个尚不存在的结果目录：

```powershell
python run_tests.py --output test_results/my_run
```

入口会固定工作目录并开启 UTF-8，避免从其他目录启动或 Windows 默认编码导致读不到中文 JSON。每次生成新目录，保留以前的运行证据。

## 手动配置环境

Windows PowerShell：

```powershell
py -3.10 -m venv .venv-test
.\.venv-test\Scripts\python.exe -m pip install -r requirements-test.txt
.\.venv-test\Scripts\python.exe run_tests.py
```

若Python 3.10通过 `python` 提供，可将第一条中的 `py -3.10` 替换为 `python`。

macOS / Linux 可按下列方式运行；本交付实际验证的平台为 Windows / Python 3.10.16，其他平台未在本次实测：

```bash
python3.10 -m venv .venv-test
.venv-test/bin/python -m pip install -r requirements-test.txt
.venv-test/bin/python run_tests.py
```

无需先 `pip install -e .`：统一入口使用交付包内的本地源码。`requirements-test.txt` 只包含测试所需依赖，不需要安装绘图和示例所用的OpenCV、Matplotlib。

## 目录与运行范围

```text
WBF-module1-tests/
├── README.md                   本说明
├── run_tests.bat                Windows一键配置环境并运行
├── run_tests.py                 跨平台统一测试入口
├── requirements-test.txt        已验证的测试依赖版本
├── ensemble_boxes/             被测算法源码
├── manual_tests/               30个编号的测试脚本和原执行证据
├── test_data/                  输入数据与独立预期
├── defects/                    已发现问题的复现材料
├── tests/                      官方自带测试（单独运行）
├── verification/               交付前的统一运行证据
└── MANIFEST.json               打包时各文件的SHA256
```

`run_tests.py` 只运行 `manual_tests/`，覆盖 **WBF-UT-001至WBF-UT-030**。08使用了两个参数化场景，所以 pytest 显示 **31个实例**；按用例编号汇总仍然是30条，没有多算或漏算。

官方自带的6条测试不计入这30条。需要单独复核时执行：

```powershell
.\.venv-test\Scripts\python.exe -X utf8 -m pytest tests/test_bbox.py -v
```

只运行某条已知失败的测试，例如26：

```powershell
.\.venv-test\Scripts\python.exe -X utf8 -m pytest manual_tests/member_a/test_wbf_member_a.py::test_026__zero_scores_must_not_produce_nan -v
```

## 结果与退出码

交付前统一执行结果：**30个用例编号中23通过、7失败；31个pytest实例中24通过、7失败**。失败编号为 **23、24、25、26、27、28、30**。

| 文件 | 内容 |
| --- | --- |
| `pytest.log` | 本次命令、测试结果、失败断言、捕获的控制台输出及退出码 |
| `junit.xml` | 可由测试工具读取的JUnit报告，包含通过/失败信息和捕获输出 |
| `summary.json` | 按30个用例与31个实例分别统计，保存环境及被测文件哈希 |
| `summary.md` | 可直接阅读的30条结果清单 |

- 退出码 **0**：本次全部断言通过。
- 退出码 **1**：用例已执行，但存在真实断言失败。当前源码预期出现上述7项失败，不能将其写成全部通过。
- 其他非零退出码：环境、收集、运行中断、缺少用例等问题，先查看日志；不能笼统解释成已知缺陷。

脚本不会遇到第一项失败就停止，也没有用 `xfail` 隐藏失败。它会核对30个编号是否齐全，并将跳过、收集错误等单独标为运行异常。

## 失败项的含义

| 编号 | 已观察到的行为 | 预期依据 |
| --- | --- | --- |
| 23 | 框与分数数量不一致时触发SystemExit | 建议抛出ValueError的接口健壮性契约，定性待评审 |
| 24 | 框与类别数量不一致时触发SystemExit | 同上 |
| 25 | 三坐标框触发IndexError | 建议显式检查维度并抛出ValueError，定性待评审 |
| 26 | 零分重合框返回NaN坐标 | 输出应有限有效，数值问题已复现 |
| 27 | allows_overflow=False仍返回约1.2的分数 | 分数上界检查失败，已复现 |
| 28 | 全零权重返回NaN坐标/分数 | 当前用例采用ValueError契约；同时实际存在非有限输出 |
| 30 | 非法conf_type触发SystemExit | 建议ValueError契约，定性待评审 |

详细复现步骤见 `defects/`，原始按批执行的日志也保留在 `manual_tests/` 中。本工程只是把既有测试整合为交付入口，尚未修复上述被测代码问题。

07保留清单原输入，并额外验证精确等值及相邻浮点阈值；原输入计算出的IoU略小于0.55，这一点不作为精确等值的唯一证据。

## 交付边界

此ZIP是源代码工程，不包含虚拟环境、Git历史和图形示例。Excel清单和独立测试报告属于其他交付材料，按要求另外提交。包内README、源码、数据足够运行本轮全部30条用例；历史日志仅用于佐证，不能替代接收者自己的执行结果。

测试输入、预期与执行由工具辅助整理，应由提交者复核。官方基线复现和本轮模块测试分别记录。
