# AI-WBF-016 执行记录

- 状态：FAIL / 需阅读原始日志
- UTC 开始时间：2026-09-18T01:03:25.071060+00:00
- pytest 退出码：1
- 实际计数：`{"candidates": 150, "main_candidates": 135, "mutation:model_count": 15, "accepted": 150, "main_accepted": 135, "seed:20260918016:accepted": 30, "source_examples": 150, "wbf_calls": 496, "candidate_calls": 150, "mutation:duplicate_detection": 15, "mutation:dense_overlap": 15, "mutation:empty_model": 15, "mutation:label_bijection": 15, "mutation:permutation": 15, "mutation:near_threshold": 15, "mutation:numeric_scale": 15, "mutation:filter_and_mode": 15, "exploratory_candidates": 15, "mutation:box_count": 15, "exploratory_accepted": 15, "exploratory_warning_inputs": 15, "exploratory_violating_inputs": 15, "exploratory:nonfinite": 15, "main_violating_inputs": 1, "main:score_upper": 1, "seed:20260918017:accepted": 30, "seed:20260918018:accepted": 30, "seed:20260918019:accepted": 30, "seed:20260918020:accepted": 30, "shrink_calls": 330, "shrink_attempts": 330, "replay_calls": 16}`
- 原始输出：`pytest.log`；机器结果：`pytest.xml`；环境与命令：`run.json`；输入及性质比较：`evidence.json`。
- 生成输入次数不等于 pytest 用例条数；调用计数包含基准、变换、重放及缩减（如有）。
