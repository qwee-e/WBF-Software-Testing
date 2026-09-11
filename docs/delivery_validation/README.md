# 自动化测试工程交付与验证记录

## 本次完成的工作

- 同步远程提交 `05f30e7`，整合双方已完成的30个用例编号。
- 新增 `run_tests.py`，统一执行全部模块1用例，记录控制台日志、JUnit、JSON及Markdown结果；核对编号齐全，并区分断言失败与环境/收集错误。
- 新增 `run_tests.bat`，在Windows下自动创建独立 `.venv-test` 环境、安装 `requirements-test.txt` 依赖并运行测试。
- 修正原记录插件从父目录执行时读取未注册可选参数的问题；仅调整测试运行支持代码，没有修改被测算法或原用例断言。
- 补充运行README及 `tools/package_delivery.py`，生成可独立解压运行的源码ZIP和SHA256校验文件。

## 实际验证结果

1. 使用原成功复现环境运行统一入口，收集并执行31个pytest实例，覆盖30个用例编号。
2. 执行Windows一键脚本，实际创建独立环境、安装依赖并再次运行全部用例。
3. 将交付ZIP解压到仓库之外的新目录，逐文件核对134项SHA256；从工程目录之外启动，且PATH中不提供Git，验证独立运行。

三次运行结果一致：**30个编号中23通过、7失败；31个实例中24通过、7失败**。08包含两个参数化场景，因此实例数比编号数多1。

失败编号为 **23、24、25、26、27、28、30**。23、24、25、30涉及建议的ValueError异常契约；26返回NaN坐标；27分数超过1；28全零权重返回非有限数值且未满足当前ValueError预期。详细预期依据见各缺陷材料和工程README，不能把所有契约建议直接当作上游已承诺行为。

所有用例执行完毕，无缺失、跳过或基础设施错误。运行入口与pytest均保留退出码 **1**，表示真实断言失败；没有使用xfail或修改算法使其通过。官方自带6条测试不计入本轮30条。

## 验证环境与证据

Windows，Python 3.10.16，NumPy 1.23.5、Numba 0.60.0、llvmlite 0.43.0、pandas 2.3.3、pytest 9.0.3。其他平台未在本次实测。

- [summary.md](summary.md)：从ZIP独立运行后的30条结果。
- [summary.json](summary.json)：实际环境、时间、源码SHA256、编号与实例统计。
- [pytest.log](pytest.log)：实际命令、输出及失败断言。
- [junit.xml](junit.xml)：可供测试工具读取的运行报告。
- [package_check.json](package_check.json)：ZIP哈希、文件核对数量和独立解压运行检查。

交付文件：[WBF_module1_自动化测试工程.zip](../../deliverables/WBF_module1_自动化测试工程.zip)。SHA256：

```text
2ff62f2fffa0bba43edd837e85e7e77528409517b64991e083a4fcff04990bce
```

ZIP中的 `verification/` 是独立环境首次统一运行证据；本目录保留的是解压交付ZIP后再次验证的证据，所以执行时间和本地路径不同，结果一致。

## 使用与重新打包

接收者安装Python 3.10后，完整解压ZIP并双击根目录的 `run_tests.bat`。详细步骤见 [工程README](../自动化测试工程_README.md)。环境和测试输出目录不上传GitHub，正式ZIP及校验文件随本次提交保存。

源码或测试改动后，先执行统一入口，再用新的结果目录重新打包：

```powershell
.\.venv-test\Scripts\python.exe run_tests.py
.\.venv-test\Scripts\python.exe tools/package_delivery.py --verification test_results/实际生成的时间戳目录
```

此处的时间戳目录需替换为真实输出路径。重新生成ZIP后应重新做解压运行验证，并更新记录和校验值。
