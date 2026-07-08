# 2025 - TAA-EPLMR

## 基本信息

- 题名：TAA-EPLMR: Threat Actor Attribution via Evidence Path-Enhanced Large Language Model Reasoning
- 作者：Nan Xiao, Bo Lang, Yikai Chen, Shuxin Zhao, Yuhao Yan
- 年份：2025
- 来源：IEEE BigData 2025
- DOI：10.1109/BigData66926.2025.11402113
- 本地文件：`../07-zotero-exports/pdfs_20260705_round4/TAA_EPLMR_2025.pdf`

## 一句话总结

TAA-EPLMR 是 Project05 当前最强撞题论文：它已经做了 `CTI-KG + evidence path retrieval + attacker-discriminability pruning + LLM CoT reasoning + attribution explanation + confidence score`，并在 incomplete/noisy 数据集上实验。因此 Project05 不能再主张泛泛的 “证据路径增强 LLM APT 归因解释”。

## 研究问题

作者认为 threat actor attribution 需要多源情报融合和语义推理。传统方法依赖小规模标注数据、embedding/GNN/ML 模型，难以捕捉复杂 IOC 关联和深层语义。LLM 有语义理解和 in-context learning 能力，但缺少最新 IOC 知识，容易幻觉。因此论文提出用 CTI knowledge graph 提供 evidence path，再让 LLM 进行归因推理。

## 方法框架

TAA-EPLMR 包含三个核心模块：

1. Evidence Path Pattern Construction  
   基于 IOC attribution graph schema 定义 19 类 evidence path patterns。节点类型包括 malware、vulnerability、IP、domain、URL、filename、filepath、registry、email、APT Report 等。

2. Evidence Path Retrieval Augmentation  
   使用 EPP 在 CTI-KG 中检索候选 evidence paths，然后进行 attacker-discriminability-based two-level pruning：
   - IOC subpath-level pruning；
   - evidence path pattern-level pruning；
   - attacker-wise aggregation。

3. LLM Attribution Reasoning  
   Prompt 中包含任务说明、I/O 格式、evidence-aware attribution logic、progressively challenging few-shot demonstrations、输入 IOCs 和 evidence subgraphs。LLM 输出：
   - 最可能的 APT group；
   - attribution explanation；
   - confidence score。

## 数据与实验

基础数据集来自 APT-MMF 的 IOC-based threat actor attribution dataset：

- 1,300 篇 CTI reports；
- 21 个 APT groups；
- 137 篇 test reports；
- CTI-KG 包含 23,615 nodes 和 38,626 relations；
- 数据来源包括 APTNotes、安全厂商报告、CVE、ATT&CK、VirusTotal 等。

作者构造了三个实验集：

- Dataset-Full；
- Dataset-Incomplete：删除 vulnerability、filename、registry、email 四类 IOC；
- Dataset-Noise：向报告中加入无关 malware、domain、URL、filepath、IP 等 noisy IOCs。

评价指标：

- Micro-F1；
- Macro-F1；
- LLM 输出 actor 名称时，用 ATT&CK Groups、Threat Group Cards、Malpedia Actors 做 alias 对齐；
- 无法匹配测试集 actor 的输出统一为 off-list。

## 结果

TAA-EPLMR 对比 14 个 baseline，包括传统 ML、GNN、APT-MMF、Direct LLM、Vanilla RAG。

关键结果：

- 相比 APT-MMF，平均 Micro-F1 提升约 4.63%，Macro-F1 提升约 4.33%；
- 在四个 LLM backbone 上均优于 Direct 和 Vanilla RAG；
- Dataset-Incomplete 和 Dataset-Noise 会降低所有方法性能，但 TAA-EPLMR 仍保持优势；
- 消融显示 evidence path retrieval 是最大增益来源，pruning/aggregation、CoT evidence-aware logic、progressively challenging demos 也有贡献。

## 案例研究

作者用 APT32/OceanLotus 案例展示模型输出。输入 IOCs 包括 malware、domain、IP。模型比较 APT32 与 APT34 的 evidence paths：

- APT32 有 first-order domain/IP evidence path；
- APT34 主要依赖 malware homology；
- APT32 关联报告数量更多、路径类型更多、路径优先级更高；
- 模型输出 APT32，confidence 0.85；
- 模型还指出部分 IOCs 未出现在 evidence 中，可能存在 data incompleteness。

## 它已经覆盖了什么

这篇已经覆盖：

- evidence path；
- CTI-KG；
- LLM reasoning；
- attribution explanation；
- confidence score；
- incomplete/noisy information robustness；
- attacker-discriminability pruning；
- candidate attacker evidence subgraph；
- IOC evidence priority / diversity / quantity reasoning。

## 它没有完全覆盖什么

仍未看到它系统处理：

- refusal / abstention；
- open-set / unknown actor；
- 证据不足时不输出 actor；
- actor / campaign / intent / technique 分层降级；
- confidence calibration 指标，如 ECE / Brier；
- false flag / mimicry 的系统评估；
- CTI evidence 与 provenance/log evidence 对齐；
- 真实组织内部证据缺失画像。

它有 off-list 评估标签，但这只是处理 LLM 输出无法匹配测试集 actor 的情况，不等于开放集归因机制。

## 对 Project05 的影响

这篇基本堵住旧题：

> 基于证据路径增强与大语言模型推理的 APT 行为体归因解释方法

Project05 必须进一步收窄到：

1. 当前证据是否足以归因；
2. 证据不足时是否拒答；
3. 是否从 actor 降级到 campaign / intent / technique；
4. unknown actor / out-of-scope / mimicry / false flag；
5. confidence 是否随缺失证据合理下降；
6. CTI evidence 与本地日志/provenance evidence 的对齐。

## 可用于 Project05 的定位句

TAA-EPLMR 解决的是：

```text
给定 IOC 与 CTI-KG evidence paths，如何增强 LLM 进行 closed-set actor attribution。
```

Project05 如果继续推进，应解决：

```text
给定不完整、冲突、可能被模仿、可能 open-set 的证据，如何判断能否归因、归因到哪一层、何时拒答，并解释缺失证据。
```

## 2026-07-08 新主线复核

复核目标：按 Project05 当前主线“对齐感知证据状态建模 + 主动取证规划”重新审计 TAA-EPLMR 是否已经覆盖核心创新。

### 覆盖度矩阵

| 能力点 | TAA-EPLMR 是否覆盖 | 复核判断 |
|---|---|---|
| CTI-KG evidence path 检索 | 是 | 19 类 evidence path pattern + CTI-KG 检索，是论文核心。 |
| 证据路径剪枝 / 聚合 | 是 | 做 attacker-discriminability pruning 和 attacker-wise aggregation。 |
| LLM evidence-aware CoT | 是 | prompt 中显式加入 evidence-aware attribution logic 与 progressive demonstrations。 |
| APT actor attribution | 是 | 输出最可能 APT group，评价 Micro-F1 / Macro-F1。 |
| attribution explanation | 是 | 输出归因解释。 |
| confidence score | 是 | 要求 LLM 输出 0-1 confidence score，案例中给出 0.85。 |
| confidence calibration | 否 | 未见 ECE、Brier、reliability diagram 或置信度校准实验。 |
| incomplete evidence robustness | 部分覆盖 | Dataset-Incomplete 删除 vulnerability、filename、registry、email 后继续闭集分类；这是鲁棒性实验，不是证据不足判定。 |
| noisy evidence robustness | 部分覆盖 | Dataset-Noise 加入 unrelated malware/domain/URL/filepath/IP 后继续闭集分类；未做反证、false flag 或 mimicry 机制。 |
| evidence weighting | 部分覆盖 | 通过路径数量、多样性、优先级、关联报告数量指导 LLM 判断，但不是可学习/可校准的证据权重模型。 |
| evidence enhancement | 部分覆盖 | 它的 enhancement 是 evidence path retrieval/pruning/aggregation，即检索增强；不是对缺失证据状态的主动增强或闭环补证。 |
| evidence sufficiency gate | 否 | 没有判断“当前证据是否足以支撑 actor-level 归因”。 |
| attribution granularity gate | 否 | 没有 technique / intent / campaign / actor 的层级降级机制，默认输出 actor。 |
| refusal / abstention | 否 | 没有证据不足时拒答或暂缓归因。 |
| open-set / unknown actor | 否 | off-list 只是评价时处理无法匹配标签的输出，不是开放集归因机制。 |
| active evidence acquisition | 否 | 没有候选取证动作、成本、动作价值估计、下一步证据规划。 |
| iterative re-alignment loop | 否 | 没有“对齐-评估-补证-再对齐”的闭环。 |
| CTI-local provenance/log alignment | 否 | 证据主要来自 IOC-based CTI-KG，不处理本地 provenance/log 证据与 CTI 行为图对齐。 |

### 复核结论

TAA-EPLMR 已经把旧方向中最危险的一段做实了：

```text
IOC / CTI-KG evidence paths
  -> evidence path retrieval and pruning
  -> LLM CoT attribution reasoning
  -> actor label + explanation + confidence
```

因此 Project05 不能再写成：

- evidence path-enhanced LLM APT attribution；
- CTI-KG + LLM reasoning + confidence score；
- incomplete/noisy IOC 下的鲁棒 actor classification；
- 让 LLM 根据 evidence path 输出归因解释。

但它没有覆盖当前新主线：

```text
alignment output / evidence state
  -> supportable attribution granularity
  -> next evidence acquisition action
  -> cost-aware planning
  -> re-alignment / stop / downgrade
```

也就是说，TAA-EPLMR 的终点是“证据路径增强后的闭集 actor 归因”；Project05 的起点应当是“已有归因/对齐证据状态是否足够，以及不够时下一步取什么证据最有价值”。

### 对实验设计的影响

TAA-EPLMR 应作为强 baseline 或红线参照，而不是被重复：

- baseline：`TAA-EPLMR-like CTI-KG evidence path + LLM actor attribution`；
- Project05 的对照任务：在相同证据被遮蔽时，不只比较 actor F1，还比较是否正确降级、拒答、选择下一步证据动作；
- 指标必须加入 over-attribution rate、correct downgrade / abstention、granularity selection accuracy、next-best-evidence ranking、cost-to-target-granularity；
- 如果只做 Dataset-Incomplete 风格删除 IOC 后继续分类，会落回 TAA-EPLMR 的实验边界。

### 对专利写法的红线

后续专利 v0.3 不应主张：

- “基于证据路径增强的大语言模型 APT 归因方法”；
- “构建 CTI-KG 并检索证据路径供 LLM 推理”；
- “根据证据路径数量、优先级、多样性生成归因解释与置信度”。

更安全的权利要求焦点应限定为：

- 对齐结果到证据状态的结构化建模；
- 归因粒度可支撑性判定；
- 面向归因粒度提升的候选取证动作价值估计；
- 成本约束下的主动取证规划；
- 预算终止或证据不足时的降级/停止/解释。
