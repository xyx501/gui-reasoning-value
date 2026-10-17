# 面向 GUI 智能体的推理价值校准

## 1. Idea Overview

### 暂定题目

**面向 GUI 智能体的额外观测与推理价值估计**

英文：

**Estimating the Value of Additional Observation and Reasoning for GUI Agents**

### 一句话概括

在 GUI Agent 执行动作前，判断当前状态下是应该直接执行，还是值得花费额外成本进行补充观测或追加推理，并预测这些额外投入相对于直接执行的实际增量收益。

### 核心研究问题

现有 GUI Agent 通常在获得截图后直接生成并执行动作。但在复杂界面中，模型可能遇到：

- 目标控件较小；
- 多个候选控件相似；
- 当前截图信息不完整；
- 页面仍在加载或发生变化；
- 输入焦点或窗口状态不明确；
- 多次动作预测不一致；
- 模型置信度过高但动作实际错误。

此时，系统可以选择：

```text
直接执行
补充观测后再决策
追加推理后再决策
等待相同时间后执行
```

问题在于：

> 额外观测或追加推理并不总是有用，同时会增加延迟、模型调用和交互成本。系统需要判断当前状态下这些额外投入是否值得。

## 2. 研究范围

### 第一阶段范围

- 以 `CLICK` 为主要动作；
- `TYPE` 或 `HOTKEY` 作为后续扩展；
- 任务以单步或短程、可自动判断结果的 GUI 任务为主；
- Actor 固定，不从收益预测器反向学习；
- 暂不把人工协助、滚动、拖拽和长任务价值预测纳入主实验。

### 四条决策路径

#### Direct

当前截图和任务输入 Actor，直接执行其动作。

#### Observe More

补充局部截图、放大区域、OCR 或其他结构信息后，再让 Actor 决策。第一阶段建议固定为以初始预测位置为中心进行局部 crop 或高分辨率 crop。

#### Reason More

不增加新的视觉信息，只让 Actor 对当前动作重新检查一次。第一阶段建议固定为一次 self-reflection 或候选动作复核。

#### Wait Control

等待与追加推理相同的时间，但不进行追加推理，用于排除页面自然加载或界面变化造成的收益。

## 3. 核心假设

### H1

额外观测和追加推理的收益具有状态依赖性，并不是对所有 GUI 状态都有效。

### H2

空间歧义、语义歧义、信息缺失、界面时效性和当前动作可执行性等运行时证据，可以预测额外观测或追加推理是否有正收益。

### H3

基于校准收益预测的自适应路径选择，相比固定 direct、always-observe、always-reason 或简单置信度阈值策略，可以在相同成本下获得更高成功率，或在相同成功率下降低成本。

### H4

wait-control 是必要对照。若不控制等待时间，就无法判断提升来自额外推理，还是来自 GUI 页面自然变化。

## 4. 方法框架

```text
任务指令 + 当前截图 + 操作历史
                    ↓
              固定 Actor
                    ↓
            生成初始候选动作
                    ↓
          提取运行时证据和成本
                    ↓
      预测 observe / reason 的增量收益
                    ↓
       计算收益 - 额外成本
                    ↓
  direct / observe-more / reason-more
                    ↓
                 执行
                    ↓
         记录实际结果与资源消耗
```

### 4.1 固定 Actor

Actor 只负责生成动作，不在第一阶段训练或更新。

输入：

```text
当前截图 + 用户任务 + 操作历史
```

输出：

```json
{
  "action": "CLICK",
  "position": [x, y],
  "target": "目标控件"
}
```

### 4.2 运行时证据

#### 空间证据

- 多次预测坐标的离散程度；
- 预测坐标是否形成多个聚类；
- 点击点到目标边界的安全边距；
- 全图和局部 crop 下的预测是否一致；
- 目标控件尺寸；
- 目标周围的视觉 clutter。

#### 语义证据

- 非等价候选动作数量；
- Top-1 与 Top-2 候选分数差距；
- 候选动作概率分布熵；
- 多次推理生成的动作是否一致；
- 用户指令是否存在歧义。

#### 可执行性证据

- 目标是否可见；
- 控件是否启用；
- 输入框是否获得焦点；
- 当前窗口是否正确；
- 目标是否被遮挡；
- 动作类型是否与目标兼容。

#### 观测时效性证据

- 当前截图距决策时刻的时间；
- 页面是否正在加载；
- UI 是否发生变化；
- 是否存在动画、弹窗或异步更新；
- 当前状态是否可能已经过期。

#### 成本证据

- 额外观测耗时；
- 追加推理耗时；
- 模型调用次数；
- token 或 API 成本；
- OCR、DOM 或 Accessibility Tree 调用成本。

## 5. 增量收益定义

设当前 GUI 状态为 $s$，用户任务为 $g$，操作历史为 $h$。

四条路径执行后得到结果分数：

$$
R_{\text{direct}},\quad
R_{\text{obs}},\quad
R_{\text{reason}},\quad
R_{\text{wait}}
$$

第一阶段可以使用二值结果：

$$
R =
\begin{cases}
1, & \text{动作成功或进入预期状态}\\
0, & \text{动作失败}
\end{cases}
$$

额外观测的增量收益：

$$
\Delta_{\text{obs}} =
R_{\text{obs}}-R_{\text{direct}}
$$

追加推理的增量收益：

$$
\Delta_{\text{reason}} =
R_{\text{reason}}-R_{\text{direct}}
$$

扣除等待影响后的净收益：

$$
\Delta_{\text{obs-net}} =
R_{\text{obs}}-R_{\text{wait}}
$$

$$
\Delta_{\text{reason-net}} =
R_{\text{reason}}-R_{\text{wait}}
$$

## 6. 价值预测与自适应执行

训练轻量收益预测器：

$$
\hat{\Delta}_{p} =
f_{\phi}(s,g,h,a,p)
$$

其中：

- $a$：Actor 初始动作；
- $p$：候选路径；
- $\hat{\Delta}_{p}$：预测路径相对 direct 的增量收益。

也可以将问题转化为正收益分类：

$$
P(\Delta_{\text{obs}}>0),\qquad
P(\Delta_{\text{reason}}>0)
$$

最终根据收益和成本选择路径：

$$
p^* =
\arg\max_p
\left(
\hat{\Delta}_p-\lambda Cost(p)
\right)
$$

其中 $Cost(p)$ 是路径的额外时间、调用或交互成本，$\lambda$ 是成本权重。

## 7. 实验设计

### 7.1 最小实验设置

```text
动作：CLICK
状态：20-100 个真实或受控 GUI 状态
路径：direct / observe-more / reason-more
对照：wait-control
Actor：固定一个视觉语言模型
标签：动作是否成功
```

### 7.2 数据构造

每个状态保存：

```text
state_id
截图
任务指令
操作历史
Actor 初始动作
direct 结果
observe 结果
reason 结果
wait 结果
每条路径耗时
模型调用次数
额外成本
```

每个状态从同一个 reset 初始状态开始，避免不同路径之间的状态差异。

### 7.3 对比方法

1. `Direct-only`：永远直接执行；
2. `Always-observe`：永远补充观测；
3. `Always-reason`：永远追加推理；
4. `Actor-confidence threshold`：Actor 低置信时进行额外处理；
5. `Self-consistency threshold`：多次动作不一致时进行额外处理；
6. `Value-calibrated adaptive policy`：根据收益和成本选择路径。

### 7.4 评价指标

收益预测：

- AUROC；
- AUPRC；
- MAE；
- RMSE；
- Spearman correlation。

置信度校准：

- ECE；
- Brier Score；
- Reliability Diagram。

执行效果：

- Step Success；
- Task Success；
- 平均执行耗时；
- 平均模型调用次数；
- 额外观测次数；
- 追加推理次数。

成本收益：

$$
Utility = Success-\lambda Cost
$$

报告 Success-Cost Curve、Risk-Cost Curve、Budget-Success Curve 和 wait-adjusted utility。

## 8. 论文逻辑链

```text
GUI Agent 能够根据截图和任务生成操作
        ↓
复杂界面中存在视觉歧义、信息缺失和状态变化
        ↓
模型可能需要多看一眼或多想一步
        ↓
额外观测和追加推理会带来延迟和调用成本
        ↓
固定地增加观测或推理会产生无效开销
        ↓
仅使用模型自身置信度无法判断额外投入是否值得
        ↓
需要定义额外观测/追加推理相对于直接执行的增量收益
        ↓
在同一可重置状态下比较 direct / observe / reason / wait
        ↓
获得真实收益、等待影响和成本标签
        ↓
提取空间、语义、可执行性、时效性和成本证据
        ↓
训练并校准收益预测器
        ↓
根据预测收益减成本选择执行路径
        ↓
验证是否在相同成本下提高成功率
或在相同成功率下降低成本
```

## 9. 论文定位与预期贡献

### 论文定位

这是一个 **New Problem / Setting with a Companion Method**：

> 提出并验证 GUI Agent 中的额外观测与追加推理价值校准问题，同时给出轻量的收益预测和成本感知路径选择方法。

### 预期贡献

1. 定义 GUI Agent 中额外观测与追加推理的推理价值估计问题；
2. 提出同一可重置状态下的 direct / observe / reason / wait 多路径评估协议；
3. 利用多模态运行时证据预测额外路径的增量收益；
4. 提出成本感知的自适应执行策略；
5. 建立同时考虑收益预测、置信度校准和资源成本的评价框架。

## 10. 第一阶段执行计划

### M0：Sanity

- 5-10 个受控状态；
- 验证 reset、路径执行和结果判定；
- 确认四条路径可以从同一初始状态运行。

### M1：Pilot

- 20-50 个 CLICK 状态；
- 每个状态运行四条路径；
- 检查 observe/reason 是否存在可重复的正收益。

### M2：收益预测

- 先使用规则特征和轻量模型；
- 分别预测 observe 和 reason 的正收益；
- 计算 AUROC、ECE 和 Brier Score。

### M3：自适应执行

- 根据预测收益减成本选择路径；
- 对比 direct-only、always-observe、always-reason 和阈值策略；
- 绘制 Success-Cost Curve。

### 第一阶段暂不做

- Actor 反向学习；
- 人工协助；
- 滚动和拖拽；
- 长任务价值函数；
- 大规模强化学习；
- 多模型复杂协作。

## 11. 主要风险

### 收益标签噪声大

使用可重置环境、固定模型温度和随机种子、重复 rollout，并加入 wait-control。

### 追加推理没有独立收益

如果 reason 和 wait 的收益相同，说明提升可能来自等待而不是推理，需要重新定义 reason protocol。

### 收益预测器只学到任务模板

按任务和界面布局划分训练和测试，留出新任务和新布局，并报告跨场景校准结果。

### 额外成本抵消收益

同时报告成功率、总耗时、模型调用次数、额外观测次数和成本归一化成功率。

## 12. 当前状态

当前已完成：

- synthetic GUI CLICK 环境；
- direct / observe / reason / wait 四路径；
- rollout 日志；
- 增量收益统计；
- 轻量收益预测器；
- 初始实验计划和 tracker。

当前结果仅用于验证实验管线，不代表真实 GUI Agent 的最终实验结论。下一步是将 synthetic actor 替换为真实视觉语言模型，并在真实 GUI 截图或可重置 GUI 环境上运行 pilot。
