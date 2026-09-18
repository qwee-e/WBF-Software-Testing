# AI-WBF-016 执行记录

- 状态：FAIL / 需阅读原始日志
- UTC 开始时间：2026-09-18T01:03:27.653797+00:00
- pytest 退出码：1
- 实际计数：`{"candidates": 3000, "exploratory_candidates": 300, "mutation:model_count": 300, "accepted": 3000, "exploratory_accepted": 300, "seed:20260918016:accepted": 600, "source_examples": 3000, "wbf_calls": 3324, "candidate_calls": 3000, "exploratory_warning_inputs": 299, "exploratory_violating_inputs": 299, "exploratory:nonfinite": 299, "main_candidates": 2700, "mutation:duplicate_detection": 300, "main_accepted": 2700, "mutation:dense_overlap": 300, "mutation:empty_model": 300, "mutation:label_bijection": 300, "mutation:permutation": 300, "mutation:near_threshold": 300, "mutation:numeric_scale": 300, "mutation:filter_and_mode": 300, "mutation:box_count": 300, "main_violating_inputs": 11, "main:score_upper": 11, "seed:20260918017:accepted": 600, "seed:20260918018:accepted": 600, "seed:20260918019:accepted": 600, "seed:20260918020:accepted": 600, "shrink_calls": 306, "shrink_attempts": 306, "replay_calls": 18}`
- 原始输出：`pytest.log`；机器结果：`pytest.xml`；环境与命令：`run.json`；输入及性质比较：`evidence.json`。
- 生成输入次数不等于 pytest 用例条数；调用计数包含基准、变换、重放及缩减（如有）。
