# Experiment Tracker

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| R001 | M0 | 验证环境 reset 和结果检查器 | direct / observe / reason / wait | 5-10 pilot states | state match, label validity | MUST | TODO | 先不训练 |
| R002 | M1 | 检查路径收益是否存在 | 四路径，每状态 3 repeats | 50 CLICK states | success, delta gain, latency | MUST | TODO | 决定是否继续 |
| R003 | M2 | 建立固定策略基线 | direct-only | pilot split | success, cost | MUST | TODO | 主 baseline |
| R004 | M2 | 建立固定额外观测基线 | always-observe | pilot split | success, cost | MUST | TODO | 固定 observe protocol |
| R005 | M2 | 建立固定追加推理基线 | always-reason | pilot split | success, cost | MUST | TODO | 固定 reason protocol |
| R006 | M2 | 排除等待造成的提升 | wait-control | pilot split | success, latency | MUST | TODO | 时间匹配 |
| R007 | M3 | 预测 observe 增量收益 | rule/linear/MLP | train/val/test by layout | AUROC, ECE, MAE | MUST | TODO | 先特征模型 |
| R008 | M3 | 预测 reason 增量收益 | rule/linear/MLP | train/val/test by layout | AUROC, ECE, MAE | MUST | TODO | 与 R007 分开 |
| R009 | M3 | 对比现有简单信号 | Actor confidence / self-consistency | same test | AUROC, ECE, Brier | MUST | TODO | 不用大模型先 |
| R010 | M4 | 自适应路径选择 | value - lambda * cost | new test states | success-cost, budget-success | MUST | TODO | 多个 lambda |
| R011 | M4 | 检验是否退化为固定策略 | adaptive policy vs fixed policies | new test states | route mix, utility | MUST | TODO | 必须报告选择比例 |
| R012 | M5 | 新布局泛化 | full predictor | held-out layouts | AUROC, ECE | NICE | TODO | 主结论后再做 |
| R013 | M5 | 特征消融 | no spatial / no semantic / no freshness | held-out layouts | gain prediction, calibration | NICE | TODO | 支撑机制解释 |
| R014 | M5 | TYPE 扩展 | direct / observe / reason / wait | short input tasks | success-cost | NICE | TODO | 不影响主结果 |
| R015 | M5 | HOTKEY 扩展 | direct / observe / reason / wait | short shortcut tasks | success-cost | NICE | TODO | 需要焦点日志 |

## Run Notes

- 当前尚未指定具体环境、Actor、GPU 和模型 API，因此成本栏先采用相对等级，不虚构 GPU-hour。
- 第一批实际运行只启动 R001；R002 的结果决定是否进入预测器训练。
