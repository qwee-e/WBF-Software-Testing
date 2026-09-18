# WBF-Software-Testing

## 模块二 AI 测试

本轮完成 AI-WBF-001、002、004、005、006、008、014、016，共 8 条；另外已同步远端新增的 003，保留其脚本及原有记录。
安装 `requirements-ai.txt` 后运行 `python run_ai_tests.py`，或用 `--case 001` 选择单条。
结果默认在 `ai_test_results/`；已提交的真实结果见 [模块二执行记录](docs/module2/执行记录.md)。
本轮负责的 8 条中 7 条通过，016 因复现已知分数越界问题而失败；桥接排列敏感性及极端权重风险单独记录，不冒充新缺陷。运行器默认扫描现有全部 AI 用例，含远端新增编号。
完整安装命令、测试前提和反例重放见 [AI 测试说明](ai_tests/README.md)。被测源码未修改。

## 自动化测试工程交付

双方30条用例已整合为统一入口。Windows安装Python 3.10后双击 **`run_tests.bat`**，即可自动配置测试环境并运行全部用例；已有测试环境可执行 **`python run_tests.py`**。

交付文件：[自动化测试源码工程ZIP](deliverables/WBF_module1_自动化测试工程.zip)；[交付与验证记录](docs/delivery_validation/README.md)。

完整说明见 [自动化测试工程README](docs/自动化测试工程_README.md)。结果写入 `test_results/时间戳/`，包含日志、JUnit、JSON和Markdown汇总。交付前统一运行：30个编号中23通过、7失败；08包含两个场景，因此pytest显示24通过、7失败，共31个实例。真实失败按原样保留。

此入口与下方历史基线复现独立，采用 `requirements-test.txt` 创建的环境，不要求队友机器上的Conda环境。

## 测试工作目录

```text
WBF-Software-Testing/
├── ensemble_boxes/          官方被测代码
├── tests/                   官方自带测试
├── manual_tests/            模块1人工测试
├── test_data/               测试数据
├── defects/                 缺陷材料
└── docs/                    需求分析、报告材料
```

- `ensemble_boxes/`：保留官方算法实现，被测入口为 `weighted_boxes_fusion()`。
- `tests/`：保留官方自带测试，与自行设计的人工测试区分。
- [manual_tests/](manual_tests/)：模块1人工设计的测试用例、测试脚本与执行记录。
- [test_data/](test_data/README.md)：测试输入和预期结果数据。
- [defects/](defects/README.md)：缺陷复现步骤、证据和分析材料。
- [docs/](docs/README.md)：需求分析、测试计划及报告材料。

以上为测试工作的主要目录；已有 `examples/`、`benchmark_*/`、`lry_reproduction/`、`zjw_test/` 等目录继续保留。

## 原项目复现基线

冻结标签为 `reproduction-success`。运行环境及恢复方法见 [基线说明](lry_reproduction/original_reproduction/BASELINE.md)。成功复现使用 NumPy 1.23.5，重建环境应使用记录的兼容依赖快照。

原示例与官方测试的成功运行属于基线复现，不属于自行设计的测试成果。

## 本次 WBF 基线复现

已在已有的 `wbf-test` Conda 环境中验证：现有 6 项测试全部通过，6 个示例全部运行成功，生成 12 张处理前后的图片。本次属于原项目基线复现，未运行数据集基准实验，也不作为自主设计的测试成果。

与此前保存的结果比较，6 份示例文本和 12 张图片逐字节一致，只有环境记录及测试耗时不同，无需为查看结果重复运行。

### 当前环境

使用 Python 3.11.15、NumPy 2.4.6、Numba 0.67.0、Matplotlib 3.9.4、opencv-python 4.11.0.86、pandas 3.0.5、pytest 9.1.1。已补齐 Matplotlib 和 OpenCV，保留其他已有依赖，临时 `.venv` 已删除。

当前环境与 `requirements.txt` 中的固定版本、上述冻结基线环境有所不同。各次运行的实际版本以对应的 `environment.txt` 为准，无需在已有环境中重新安装固定版本依赖。

### 结果文件

- `zjw_replicate_test/`：本次提交保存的首次复现结果，环境记录对应首次运行。
- `artifacts/`：`reproduce.py` 的实际输出目录，本地保存了 `wbf-test` 的验证结果，已被 Git 忽略。
- `tests.txt`：pytest 结果；`environment.txt`：Python 与直接依赖版本。
- 各示例 `.txt`：控制台输出；`*_before.png`、`*_after.png`：处理前后图片。

可查看 [测试结果](zjw_replicate_test/tests.txt)、[二维 WBF 输出](zjw_replicate_test/wbf_2d_two_models.txt) 和 [融合后图片](zjw_replicate_test/wbf_2d_two_models_after.png)。

### 运行方式

在项目根目录执行：

```bash
conda activate wbf-test
python reproduce.py
```

脚本先运行现有测试，通过后按原示例入口参数运行二维 WBF（单模型、双模型）、NMS、Soft-NMS、一维 WBF 和三维 WBF。绘图保存为 PNG，重新运行会覆盖 `artifacts/` 中同名文件。

仅运行官方自带测试（不含模块1的30条用例）：

```bash
conda activate wbf-test
python -m pytest tests/test_bbox.py -q
```

交互式绘图可在激活环境后运行 `python -m examples.example`、`python -m examples.example_1d` 或 `python -m examples.example_3d`。OpenCV 窗口按键后继续；三维示例使用 Matplotlib 窗口。IDE 中请选择 `wbf-test` 解释器。

### 修改说明

- 新增 `reproduce.py`，统一运行测试与示例，保存环境、日志和图片。
- 修复二维示例对不等长标签列表直接调用 `np.unique` 导致的 NumPy 2 报错：先展平标签再统计类别，仅修改绘图辅助代码，算法实现不变。
- 补充忽略规则，排除虚拟环境、缓存和本地生成结果。

成员二记录10起的测试内容、执行结果和证据见[执行汇总](manual_tests/member_b.md)。
