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

