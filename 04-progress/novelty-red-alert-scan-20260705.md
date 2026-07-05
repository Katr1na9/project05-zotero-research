# Project05 新颖性红线扫描 - 2026-07-05

## 这份文档的作用

在最终确定 Project05 的专利/论文选题之前，必须先做直接撞题扫描。原来的宽泛想法：

> 多源证据融合 + 大语言模型辅助 APT 归因解释

现在已经属于高风险表述。它太宽，已经被多篇论文和多个专利从不同角度覆盖。

## 红线结论

本轮新增两个决策辅助文档：

- `chinese-patent-claims-redline-20260705.md`：中文专利权利要求红线分析。
- `collision-matrix-20260705.md`：Project05 撞题矩阵。

### 0. 当前已纳入精读/红线笔记的新增材料

本轮扫描后，已经新增到 Project05 精读或红线笔记中的材料包括：

- `2026-Meng-Uncovering-Vulnerabilities-LLM-Assisted-CTI.md`
- `2026-Saha-Kitten-or-Panda-Group-Profile-Specificity.md`
- `2024-Huang-Cascade-APT-Campaign-Attribution-Logs.md`
- `2024-Huang-SAGA-Synthetic-Audit-Log-Generation-APT.md`
- `2025-Boge-Unveiling-Cyber-Threat-Actors.md`
- `2025-Basnet-APT-Attribution-DRL.md`
- `2026-APTA2D-Attention-Pruning-2D-Convolutional-Reasoning.md`
- `2025-Cai-APT-ATT-High-Risk-Related.md`
- `2021-US20210281585A1-Confidence-Level-Cyber-Campaign-Attribution.md`
- `2025-US12368730B2-Multiple-Evidence-Threat-Actor-Attribution-Patent.md`
- `2024-CN118646607A-APT-KG-LLM-Enhancement-Patent.md`
- `2025-CN120110776B-Attack-Pattern-Clustering-Attribution-Patent.md`

即时判断：Project05 的专利空间比之前想象得窄很多。以下表达都已经有现有技术或近似现有技术：

- confidence-aware attribution；
- information gap；
- multiple evidence；
- TTP/tool matching；
- APT KG + LLM；
- LLM/RAG/KG/TTP attack-tree attribution。

### 1. US12368730B2 - Automatic threat actor attribution based on multiple evidence

- 来源：https://patents.google.com/patent/US12368730B2/en
- 申请人：Forescout Technologies Inc.
- 授权/公开日期：2025-07-22
- 优先权日期：2022-08-17
- 发明人包括：Koen Teuwen 等

为什么危险：

- 题名直接覆盖 `automatic threat actor attribution based on multiple evidence`。
- 专利使用 IoC attributor 和 TTP attributor。
- 每个 attributor 输出 probability function / PMF。
- attribution aggregator 使用 opinion pools 融合概率函数。
- 明确提到 minimum confidence threshold 和候选 actor 概率接近时的歧义。

对 Project05 的影响：

Project05 不能再把宽泛的 “多源证据融合威胁行为体归因” 当作专利新颖性。这个大框架已经被堵住。

### 2. TAA-EPLMR - Threat Actor Attribution via Evidence Path-Enhanced Large Language Model Reasoning

- 来源：https://ieeexplore.ieee.org/document/11402113/
- DOI：10.1109/BigData66926.2025.11402113
- 会议：IEEE BigData 2025
- 作者：Nan Xiao, Bo Lang, Yikai Chen, Shuxin Zhao, Yuhao Yan
- 本地全文：`../07-zotero-exports/pdfs_20260705_round4/TAA_EPLMR_2025.pdf`

为什么危险：

- 它已经实现 `CTI-KG + evidence path retrieval + attacker-discriminability pruning + LLM CoT reasoning + attribution explanation + confidence score`。
- 它定义 19 类 evidence path patterns，用 IOC 到 APT report / actor 的多级关联构建证据路径。
- 它在 Dataset-Full、Dataset-Incomplete、Dataset-Noise 三个数据集上实验，明确测试 incomplete / noisy information。
- 它输出 actor、自然语言归因解释和 confidence score。
- 案例研究中已经讨论 evidence quantity、report diversity、path priority、limiting factors 和 data incompleteness。

对 Project05 的影响：

不能使用 “evidence path-enhanced LLM attribution” 作为题名或核心创新。TAA-EPLMR 基本堵住了 “CTI-KG evidence path + LLM reasoning + APT actor attribution explanation” 这条宽路线。

它尚未完全覆盖的空间主要是：refusal/abstention、open-set/unknown actor、分层降级归因、confidence calibration 指标、false flag/mimicry 系统评估、CTI 与 provenance/log evidence 对齐。

### 3. LLM-Based Advanced Persistent Threat Attribution: A Novel Framework for Enhanced Cyber Threat Intelligence

- 来源：https://ieeexplore.ieee.org/abstract/document/11532806/
- 会议：MENACOMM 2026
- 作者：Adel Alshamrani
- DBLP：https://dblp.org/rec/conf/menacomm/Alshamrani26
- 本地全文：`../07-zotero-exports/pdfs_20260705_round4/LLMAPT_2026.pdf`

为什么危险：

- 这是 2026 年题名级撞题论文。
- 它会撞掉任何宽泛的 “LLM-based APT attribution framework” 题名。
- 它提出 LLMAPT，覆盖 multi-source intelligence integration、LLM semantic analysis、structured attribution reasoning、calibrated confidence quantification、explainable attribution interface。
- 它还声称包括 false flag robustness、temporal evolution modeling、multi-level explainability、confidence thresholds 和 ECE。

对 Project05 的影响：

Project05 不能直接叫 “基于大语言模型的 APT 归因框架”，也不能写成大而全的 multi-source + calibrated confidence + explainability 框架。LLMAPT 相对更概念化、实验规模较小，但题名和框架覆盖面很宽。

### 4. CN120110776B - 一种针对攻击模式的攻击手法聚类与归因方法

- 来源：https://patents.google.com/patent/CN120110776B/zh

为什么危险：

- 使用 LLM 从威胁情报中抽取攻击信息。
- 使用 RAG 生成三元组。
- 将三元组与网络安全知识图谱融合，得到 TTP 数据。
- 对 TTP 数据进行聚类。
- 构建攻击树。
- 使用 attention 分配权重。
- 通过攻击树匹配完成归因。

对 Project05 的影响：

这堵住了一个中文专利方向：

> LLM + RAG + KG + TTP + attack tree + attribution

Project05 不能沿着 “大模型抽 TTP、构攻击树、聚类归因” 直接写。

### 5. CN118646607A - 一种基于 APT 知识图谱关联数据的大语言模型增强方法

- 来源：https://patents.google.com/patent/CN118646607A/zh

为什么危险：

- 覆盖 APT 知识图谱构建。
- 覆盖根据用户问题查询 APT 知识图谱。
- 覆盖使用图谱查询片段生成增强提示。
- 覆盖大语言模型基于图谱增强提示生成回答。

对 Project05 的影响：

宽泛的 “APT KG + LLM enhanced analysis” 已经不能作为专利核心。Project05 如果使用知识图谱，只能把它作为证据通道之一，而不是创新终点。

### 6. Uncovering Vulnerabilities of LLM-Assisted Cyber Threat Intelligence

- 来源：https://arxiv.org/html/2509.23573

为什么危险：

- 讨论 LLM-assisted CTI 的失败模式，包括 attribution reasoning 过拟合。
- 明确建议使用 evidence-sufficiency gate：如果归因没有显式证据支持，就降低置信度或 abstain。
- 这与 Project05 当前的 `evidence sufficiency / abstain` 表述存在重叠。

但要注意：

它主要是失败模式分析和防御建议，不是完整的 APT 归因方法。因此它不是完全堵死 Project05，而是提醒我们不能把 “证据充分性门控” 写得太泛。

### 7. Kitten or Panda? / From IOCs to Group Profiles

- 来源：https://arxiv.org/abs/2506.10645
- Asia CCS 2026 版本：https://doi.org/10.1145/3779208.3786258

为什么重要：

- 只有约 34% 的 ATT&CK groups 具有 group-specific techniques。
- 合并多个来源后，很多 group 仍然缺少 group-specific behavior。
- 这强力支持 evidence distinctiveness / sufficiency 的必要性。

对 Project05 的影响：

这篇支持我们做 “证据区分度 / 证据充分性 / 证据不足时拒答”，但也意味着 Project05 不能过度声称 TTP-based actor attribution 的可靠性。

### 8. 2026 年网络威胁归因综述与框架

已发现的相关综述/框架包括：

- Cyber Threat Actor Attribution: A Systematic Review and Evolutionary Perspective, IJISS 2026。
- A survey of cyber threat attribution: Challenges, techniques, and future directions, Computers & Security 2025。
- Trend Micro attribution framework discussion, 2026。

为什么重要：

- 该领域正在主动把归因重构为 evidence-integrated、confidence-qualified、multi-dimensional 的问题。
- 因此，普通的 “confidence-aware attribution” 题名已经不够新。

### 9. US20210281585A1 - System and method for determining the confidence level in attributing a cyber campaign to an activity group

- 来源：https://patents.google.com/patent/US20210281585A1/en

为什么危险：

- Claim 1 覆盖：收集 intrusion set data、提取 tools/TTPs、与 activity group data 比较，并确定 attribution 及 associated confidence level。
- Claim 2 覆盖：基于 unique techniques threshold 输出 high / moderate / low confidence。
- Claim 2 还覆盖：当 confidence 为 moderate 或 low 时确定 information gap。
- 说明书还包括：向用户推荐 unique techniques 供 hunting，用户更新后重新计算 confidence。

对 Project05 的影响：

这直接堵住了宽泛的：

> confidence scoring + information gap + hunting recommendation

如果 Project05 专利要写“缺失证据”和“补充取证建议”，必须设计得比这个专利更具体，不能只停留在 information gap 层面。

### 10. 行为、日志、恶意软件归因基线比预期更宽

本轮新增的相关工作包括：

- SFM cascade log campaign attribution：`Technique hunting + subgraph matching`。
- SAGA synthetic audit logs for APT campaigns。
- Unveiling Cyber Threat Actors：基于命令序列的 soft attribution。
- DRL APT malware attribution。
- APTA2D：attention-guided pruning + 2-D convolutional KG reasoning。
- APT-ATT：heterogeneous threat intelligence representation + CTGAN + APT attribution。

对 Project05 的影响：

Project05 不能安全地声称以下宽泛方向：

- behavior-based APT attribution；
- log-based APT attribution；
- malware-based APT attribution；
- KG-based APT attribution；
- heterogeneous-intelligence-based APT attribution。

真正可能留下的空间不是 “再做一个归因模型”，而是一个 decision layer：

> 判断每个证据通道是否充分、是否冲突、是否过于 generic、是否可被 mimicry、是否属于 out-of-scope。

## 当前相对安全的方向

经过这轮扫描后，Project05 应避免主张：

- 泛泛的 multi-source evidence attribution；
- 泛泛的 LLM-based APT attribution；
- 泛泛的 KG/RAG/GraphRAG-based attribution；
- 泛泛的 evidence-path LLM reasoning；
- 泛泛的 confidence score；
- 泛泛的 information gap。

更可防守的缺口是：

> 证据可用性诊断 + 缺失证据感知的归因门控 + 自适应归因粒度 + open-set / mimicry 场景下的拒答或暂缓归因。

题名应强调：

> 什么时候不能归因

而不只是：

> 怎么归因

## 最终定题前仍需继续补查

1. 继续寻找并精读 APT-ATT 全文。
2. 详细阅读 US12368730B2 的 claims。
3. 继续细读 CN120110776B 和 CN118646607A 的权利要求。
4. 继续用以下关键词检索论文和专利：
   - evidence sufficiency gate；
   - abstention；
   - open-set；
   - unknown actor；
   - false flag；
   - mimicry；
   - attribution refusal；
   - missing evidence attribution。
