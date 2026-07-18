# Paper B Phase 1 train-null 修订选项 v0.1

状态：`decision_required`（仅供审阅，尚未修改权威设计或授权实施）

日期：2026-07-16

## 1. 触发原因

Task 6 完成许可检查、规范化、标签串硬化与冻结 payload exclusion 后，
清洁作者提案队列包含：

| split | observation | null |
|---|---:|---:|
| train | 2,394 | 2 |
| training-validation | 483 | 517 |

现行 Task 7 要求 train 与 training-validation 的 positive/null 比例均处于
40%–60%。即使现有提案全部通过作者审核，train 侧也不可能过 Gate。因此
Task 7 当前状态必须记为 `pre-failed_pending_amendment`，不得下载 tokenizer、
安装运行时、下载 Qwen 权重、训练或推理。

## 2. null 的不可放宽定义

训练 null 是编译器的弃权样本：packet 中不存在作者可接受的目标 SPO
observation，target 必须严格为：

```json
{"status":"abstain","candidate_claims":[]}
```

以下情况均不能单独证明 null：

- 日志被描述为良性、噪声或正常；
- 行中没有攻击标签、TTP 或告警；
- 记录位于某个 benign/scenario 目录；
- frozen extractor 没有自动抽出 candidate；
- 记录不属于攻击窗口。

只要可见字段仍支持一个符合合同的 process/file/network/system SPO，就不能
把它标成 null。任何 null 都需要逐项作者确认；训练标签不是 G2，也不能称为
人类共识 gold。

## 3. 选项

### A. 接受 `smoke_only`

- 不新增来源、不改变 Task 6 队列；
- adapter 只可用于管线可运行性 smoke，不进入 Paper B 核心条件；
- Paper B 回退为 Rule/General/structured/direct 的接口或负结果 pilot；
- 保留未来补充数据后重新开启 adapter Gate 的可能。

优点是科学边界最干净、无需新增人工和数据治理。代价是本轮不能检验正式
task-adapted QLoRA 增益。

### B. 新批独立的 train-null 来源族（推荐）

新增一个与 C07–C12、E3 及现有六族独立的、许可明确的 routine/status
日志来源，重新走 V3-B 子闸门。最低要求：

1. 固定发布者、版本/commit、许可证据、字节数和下载范围；
2. 不使用 PCAP、告警标签、attack/benign 路径或场景名作为监督；
3. 先以规则提出至少 300 个 null 候选，目标是在作者审核与 1024-token
   过滤后仍保留不少于 240 个；
4. 每项必须由可见来源片段证明“无可接受目标 SPO”，不能仅因 extractor
   无输出而准入；
5. 通过 blocked-family、exact、5-gram exclusion 与许可证/nested-notice
   检查；
6. Task 7 只从审核通过的样本中确定性下采样约 200 positive + 200 null，
   然后重新计算 4+2 家族、40%–60%、干扰覆盖和 token Gate。

该选项不把新来源宣称为 APT 领域数据；对外仍只能称
`task/schema-adapted observation-compiler`。

### C. 已批 train 族内建立“无目标 SPO 时间窗”协议（备选）

该选项只能作为新的 Task 6 子协议，不能静默修改现有 normalizer：

1. CAM-LDS 继续绝对禁止用于 null；
2. 不得把现有 observation 候选重新标成 null；
3. 只能从 Atomic/Splunk/SOCBED 尚未进入队列的原始记录构造固定窗口；
4. 窗口规则必须在查看候选结果前冻结，只依赖时间、记录顺序和可见字段，
   不依赖路径、scenario、run、attack/benign 或告警标签；
5. 每个窗口须经作者确认其中不存在任何可接受目标 SPO；
6. 先做不超过 50 项的 feasibility audit。若接受率不足以投影到至少 240
   个最终 train null，则立即否决 C，不得反复改规则追数量；
7. 若 feasibility 通过，再对新增候选重跑完整 normalization、label-value
   gate、payload exclusion 和作者审核。

C 的主要风险是：主机事件通常本身就支持 process/file/system observation，
“良性”不等于“无可编译 observation”。因此它只有在小规模语义审计证明
null 定义可稳定满足时才可采用。

### D. 放宽 CAM-LDS 或把缺少攻击行当 null

`rejected`。该做法违反已经批准的来源条件，并把“未检测到攻击”偷换为
“无可接受 observation”，会制造标签而不是补充证据。

## 4. 建议决策顺序

1. 先完成 50 行 `batch-001-quality-probe`，估计现有 Loghub null 与
   Atomic/SOCBED observation 的作者接受率；
2. 若仍希望 adapter 成为 Paper B 正式条件，优先选择 B；
3. 只有在不新增来源且愿意承担语义审计风险时才试 C 的 50 项 feasibility；
4. 若不愿扩展来源或人工工作量，选择 A，并在论文中诚实降级。

## 5. 当前硬停

本文件不授权任何来源下载、现有语料重标、Task 7 packet 构建、tokenizer
获取、运行时安装、Qwen 权重下载、训练或推理。只有用户明确选择 A/B/C 并
批准相应实施补丁后，才能修改权威设计与实施计划。
