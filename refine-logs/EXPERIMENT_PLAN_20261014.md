# Experiment Plan

**Problem**: 面向 GUI Agent 的额外观测与追加推理价值估计和成本感知执行
**Method Thesis**: 在同一可重置 GUI 状态下比较 direct、observe-more、reason-more 和 wait-control，利用运行时证据预测额外路径相对直接执行的增量收益，并根据收益与成本选择执行路径。
**Date**: 2026-10-14

## Scope and Assumptions

- 第一阶段以 `CLICK` 为主，`TYPE` 或 `HOTKEY` 作为扩展；不把滚动、拖拽和人工协助纳入主结果。
- Actor 固定，不从收益预测器反向学习；实验研究的是路径价值估计和自适应路由。
- 结果标签优先采用短程、可自动判定的单步或短链任务；完整长任务价值预测列为后续方向。
- 如果没有可重置的真实 GUI 环境，先在受控网页/桌面任务上构造 pilot，不把不可复现的在线页面作为主数据源。

## Claim Map

| Claim | Why It Matters | Minimum Convincing Evidence | Linked Blocks |
|---|---|---|---|
| C1: 运行时证据可以预测额外观测或追加推理相对 direct 的增量收益，并且预测可校准。 | 这是方法的核心机制；若不能预测收益，自适应执行没有基础。 | 在完全未参与训练的任务/布局上，收益预测优于 Actor 自身置信度、简单 self-consistency 和固定策略；ECE/Brier 与区分能力同时改善。 | B1, B2 |
| C2: 基于校准收益的路径选择可以在相近成功率下减少无效观测/推理成本，或在相同成本下提高成功率。 | 证明方法不只是离线预测，而能改变实际执行决策。 | 在 direct、always-observe、always-reason、置信阈值策略和 wait-control 之上，adaptive policy 取得更好的 Success-Cost 或 Budget-Success 曲线。 | B3, B4 |

## Paper Storyline

- **Main paper must prove**:
  - 同一初始状态下，额外观测和追加推理的收益不是固定的，且 wait-control 能排除单纯等待造成的提升。
  - 运行时证据能够预测何时 observe/reason 有价值。
  - 经过校准的价值预测能带来更好的成本-成功率权衡。
- **Appendix can support**:
  - TYPE/HOTKEY 扩展；
  - 更细的空间特征、语义特征和可执行性特征；
  - 不同阈值、不同重复次数和不同路径成本设置；
  - 长任务或人工协助的初步结果。
- **Experiments intentionally cut**:
  - 第一阶段不训练 Actor；
  - 不同时覆盖所有 GUI 动作；
  - 不把结果状态价值、人工协助和长程规划全部塞进主方法；
  - 不使用没有可靠 reset 或自动判定的动态网页作为核心证据。

## Experiment Blocks

### Block 1: Counterfactual Path Dataset and Metric Sanity

- **Claim tested**: 多路径对照能够稳定产生可学习的增量收益标签。
- **Why this block exists**: 没有稳定的 direct/observe/reason/wait 标签，后续预测器和自适应策略都没有意义。
- **Dataset / split / task**:
  - 先构造 50-100 个短程、可重置任务状态，优先 CLICK；
  - 任务覆盖视觉歧义、小目标、相似控件、遮挡/加载、动作候选分歧；
  - 每个状态运行四条路径：`direct`、`observe-more`、`reason-more`、`wait-control`；
  - 每条路径至少重复 3 次；固定 Actor、温度和最大步骤；
  - 以任务状态检查器或元素命中规则产生成功标签。
- **Compared systems**:
  - Direct baseline；
  - Observe-more protocol；
  - Reason-more protocol；
  - Wait-control；
  - 不同随机种子/重复 rollout 作为方差估计。
- **Metrics**:
  - 路径成功率；
  - \(\Delta_{\text{obs}} = R_{\text{obs}}-R_{\text{direct}}\)；
  - \(\Delta_{\text{reason}} = R_{\text{reason}}-R_{\text{direct}}\)；
  - wait-adjusted gain；
  - 标签重复一致性；
  - 平均延迟和调用成本。
- **Setup details**:
  - `observe-more` 必须固定操作定义，例如局部 crop 或高分辨率 crop，不能每个任务自由选择；
  - `reason-more` 固定为一次候选动作复核或 self-reflection，不允许无限追加推理；
  - `wait-control` 等待时间匹配 reason-more 的平均耗时；
  - 所有路径从同一 reset 状态开始。
- **Success criterion**:
  - direct/observe/reason 的差异可重复；
  - wait-control 能解释并排除一部分由等待造成的提升；
  - \(\Delta\) 标签不是完全由随机噪声主导。
- **Failure interpretation**:
  - 若不同路径结果差异不可重复，说明环境或协议不稳定，应先收缩任务；
  - 若 observe/reason 几乎从不带来收益，当前任务集不适合研究推理价值；
  - 若 wait-control 与 reason-more 等价，追加推理的独立价值尚未被证明。
- **Table / figure target**: 主文 Table 1（路径成功率、延迟、成本）和 Figure 1（同一状态多路径示例）。
- **Priority**: MUST-RUN

### Block 2: Incremental Value Prediction and Calibration

- **Claim tested**: 运行时证据可以预测 observe/reason 的正收益及收益大小。
- **Why this block exists**: 直接验证 C1，并区分“预测额外收益”和“仅预测 Actor 当前动作是否正确”。
- **Dataset / split / task**:
  - 使用 Block 1 产生的状态-路径记录；
  - 按任务和界面布局划分 train/validation/test，避免同一布局泄漏；
  - test 至少包含留出的新任务和新布局。
- **Compared systems**:
  - Actor 自身置信度；
  - 多次动作 self-consistency；
  - 规则/线性模型；
  - 轻量 MLP 或小型多模态 Critic；
  - 目标预测分别为：正收益分类、连续增量收益回归。
- **Runtime features**:
  - 空间：多次坐标离散程度、坐标聚类、目标边界安全边距、crop 间一致性；
  - 语义：候选动作数量、Top-1/Top-2 margin、候选熵、动作重复率；
  - 可执行性：控件可见/启用、焦点、遮挡、窗口状态；
  - 时效性：截图年龄、页面加载状态、界面变化；
  - 成本：额外观测/推理预计耗时和调用次数。
- **Metrics**:
  - 正收益识别：AUROC、AUPRC、F1；
  - 增量收益预测：MAE、RMSE、Spearman correlation；
  - 校准：ECE、Brier Score、reliability diagram；
  - 分动作、分困难类型报告结果。
- **Setup details**:
  - 预测器不访问执行后的结果，只使用执行前证据；
  - observe 和 reason 分别训练或使用 action/path-conditioned head；
  - 训练集只使用 reset 后独立记录，避免同一 rollout 的时间泄漏；
  - 先做特征模型，再做多模态模型，避免把收益简单归因于更大模型。
- **Success criterion**:
  - 价值预测器在留出任务/布局上优于 Actor confidence 和 self-consistency baseline；
  - calibration 改善与 AUROC 改善同时存在；
  - 模型能识别正收益状态，而不是只识别原始动作是否正确。
- **Failure interpretation**:
  - 若能预测动作正确性但不能预测额外收益，说明原有 Critic 不能直接替代价值预测器；
  - 若训练集好、跨布局差，说明特征学习了界面模板而非价值机制；
  - 若校准差但排序好，可保留排序能力并重新做温度缩放或 isotonic calibration。
- **Table / figure target**: 主文 Table 2（收益预测与校准）和 Figure 2（reliability diagram / gain prediction）。
- **Priority**: MUST-RUN

### Block 3: Cost-Aware Adaptive Path Selection

- **Claim tested**: 校准后的收益预测能够改进实际路径选择。
- **Why this block exists**: 证明方法对执行决策有实际价值，而非只在离线指标上有效。
- **Dataset / split / task**:
  - 使用全新 test 状态和布局；
  - 每个状态只允许策略选择一次路径，避免策略利用未来信息；
  - 先做单步/短链，再决定是否扩展。
- **Compared systems**:
  - Direct-only；
  - Always-observe；
  - Always-reason；
  - Actor-confidence threshold；
  - Self-consistency threshold；
  - Value-calibrated adaptive policy。
- **Decision rule**:
  \[
  p^*=\arg\max_{p\in\{\text{direct, observe, reason}\}}
  \left(\widehat{\Delta}_p-\lambda Cost(p)\right)
  \]
  - 在多个 \(\lambda\) 下形成不同资源预算；
  - 只允许一次额外观测或一次追加推理，控制策略复杂度。
- **Metrics**:
  - Success rate；
  - average latency；
  - average model calls；
  - extra observation/reasoning rate；
  - Success-Cost curve；
  - Budget-Success curve；
  - utility \(=Success-\lambda Cost\)；
  - wait-adjusted utility。
- **Success criterion**:
  - 在相同成本下，自适应策略成功率高于固定阈值策略；
  - 或在相同成功率下，自适应策略成本更低；
  - 自适应策略不是简单地趋向 always-observe 或 always-reason。
- **Failure interpretation**:
  - 若 adaptive policy 只选择 direct，说明额外路径收益不足或预测器过于保守；
  - 若 adaptive policy 退化成 always-reason，说明成本惩罚或校准不足；
  - 若成功率提高但成本增长过大，说明价值估计没有形成实际 utility 改善。
- **Table / figure target**: 主文 Table 3（策略比较）和 Figure 3（Success-Cost / Budget-Success）。
- **Priority**: MUST-RUN

### Block 4: Generalization and Failure Diagnosis

- **Claim tested**: 价值预测不是对固定任务模板的记忆，并能解释何时预测失败。
- **Why this block exists**: 回应跨场景适应性和机制可信度。
- **Dataset / split / task**:
  - 留出新任务；
  - 留出新界面布局；
  - 可选留出一种困难类型，例如小目标或页面加载；
  - TYPE/HOTKEY 只作为扩展，不影响主结果。
- **Compared systems**:
  - 完整价值预测器；
  - 去除空间特征；
  - 去除语义特征；
  - 去除时效性/成本特征；
  - 不做 wait adjustment 的版本。
- **Metrics**:
  - 跨布局 AUROC/ECE；
  - 不同困难类型的收益预测误差；
  - calibration drift；
  - 失败路径占比；
  - 成本和策略选择分布。
- **Success criterion**:
  - 在新布局上仍保持基本的收益排序和可接受校准；
  - 特征消融结果与理论预期一致；
  - wait-control 能显著影响动态加载类任务，但不应解释所有收益。
- **Failure interpretation**:
  - 跨布局完全失效，说明方法依赖模板，应重新定义任务或加入结构化归一化；
  - 去除任一特征均无影响，说明特征并未支撑方法，应简化模型；
  - wait adjustment 影响极大，说明当前任务集更像等待问题而非推理价值问题。
- **Table / figure target**: Appendix Table A1 和 Figure 4（错误案例与路径选择可视化）。
- **Priority**: NICE-TO-HAVE after B1-B3

## Main Paper vs Appendix

### Main paper must-run

- B1：多路径数据和标签稳定性；
- B2：收益预测和校准；
- B3：成本感知自适应执行。

### Appendix

- B4：跨布局泛化和特征诊断；
- TYPE/HOTKEY 扩展；
- 多次重复次数和阈值敏感性；
- 结果状态分数的替代定义；
- 初步人工协助路径。

## Run Order and Milestones

| Milestone | Goal | Runs | Decision Gate | Cost | Risk |
|---|---|---|---|---|---|
| M0 Sanity | 验证 reset、状态检查器和四条路径正确 | 5-10 个状态，单次 rollout | 所有路径从同一初始状态开始，标签可自动读取 | Low | 环境 reset 或状态判定错误 |
| M1 Pilot | 判断是否存在可重复的路径收益差异 | 50 个 CLICK 状态，4 路径，3 次重复 | 若 \(\Delta_{\text{obs}}\)、\(\Delta_{\text{reason}}\) 近乎全为 0 或完全随机，暂停扩展 | Medium | 任务集没有信息价值差异 |
| M2 Baseline | 建立 direct、always-observe、always-reason、wait 结果 | 与 M1 相同 split | baseline 结果和成本记录完整 | Medium | 协议定义不公平 |
| M3 Predictor | 训练价值预测器并做校准 | 3 seeds；特征模型优先 | test 上预测优于 Actor confidence/self-consistency | Medium | 标签噪声或布局泄漏 |
| M4 Adaptive | 验证成本感知路径选择 | 3 seeds，多组 \(\lambda\) | Success-Cost 或 Budget-Success 优于 baseline | Medium-High | 策略退化为固定路径 |
| M5 Extension | TYPE/HOTKEY、新布局、误差分析 | 1-3 seeds，按资源选择 | 不影响主结论时进入 appendix | High | 动作协议扩展过快 |

## Compute and Data Budget

- **总预算**：当前硬件和模型访问条件未给出，因此不做虚假 GPU-hour 承诺。第一阶段按“可执行 pilot”预算：先运行 50 个状态、4 条路径、3 次重复，再根据方差决定是否扩充。
- **数据准备**：需要可重置 GUI 环境、任务初始状态、路径执行器、状态检查器、耗时/调用成本日志。
- **模型预算**：固定 Actor；预测器优先使用规则特征 + 轻量 MLP/校准器。只有在特征模型显示信号后，才尝试多模态 Critic。
- **人工评估**：主实验尽量自动判定。人工只用于检查功能等价、未知标签和少量错误案例。
- **最大瓶颈**：不是训练，而是四条路径的公平执行、可靠 reset 和结果标签。

## Risks and Mitigations

- **Risk**: observe-more 和 reason-more 的定义不稳定。
  - **Mitigation**: 第一阶段各固定一种实现，禁止按样本自由选择工具。
- **Risk**: wait-control 与 reason-more 时间不匹配。
  - **Mitigation**: 记录每次实际耗时；按 reason-more 的分位数设置等待时间，并在报告中给出时间匹配方式。
- **Risk**: 多路径结果方差过大。
  - **Mitigation**: 固定温度和随机种子；增加重复 rollout；先使用短程任务。
- **Risk**: 价值标签被原始动作正确率主导。
  - **Mitigation**: 单独报告“预测 direct 是否成功”和“预测额外路径是否带来正增量”两个任务。
- **Risk**: adaptive policy 只学习到 always-observe/reason。
  - **Mitigation**: 多个成本权重 \(\lambda\)；报告路径选择比例和 utility 曲线。
- **Risk**: 新布局泛化失败。
  - **Mitigation**: 训练/测试按布局隔离；先做结构化特征和简单模型，减少模板记忆。
- **Risk**: 人工协助扩展吞噬项目周期。
  - **Mitigation**: 第一阶段不做人工协助主实验，只记录为 future work。

## Stop / Go Rules

- **Stop 1**: M0 不能保证 reset 后初始状态一致，先不训练模型，修环境。
- **Stop 2**: M1 的四条路径差异不可重复，缩减任务为页面加载或小目标中的一种，并重新定义 observe/reason。
- **Go 1**: 若 M1 显示至少一类状态中 observe 或 reason 有稳定正增量，进入价值预测。
- **Go 2**: 若 M3 在留出布局上同时有较好的排序和校准，进入 adaptive policy。
- **Pivot**: 若预测器只能预测原始动作是否成功，不能预测额外路径增益，则将论文改为“基于运行时证据的路径选择/价值标签分析”，不继续声称通用推理价值预测。

## Final Checklist

- [ ] Main paper tables are covered
- [ ] 多路径收益标签经过 reset 和 wait-control 验证
- [ ] 增量收益预测与原始动作正确性预测分开
- [ ] Calibration 和 cost-aware execution 都有结果
- [ ] Success-Cost 或 Budget-Success 曲线已覆盖
- [ ] 新任务/新布局至少有一项泛化测试
- [ ] Nice-to-have runs 与 must-run runs 已分离
- [ ] 没有把人工协助、长任务和全部动作类型提前塞入主实验
