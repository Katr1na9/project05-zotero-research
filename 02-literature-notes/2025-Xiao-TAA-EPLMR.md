# TAA-EPLMR: Threat Actor Attribution via Evidence Path-Enhanced Large Language Model Reasoning

## 1. 基本信息

- 英文题名：TAA-EPLMR: Threat Actor Attribution via Evidence Path-Enhanced Large Language Model Reasoning
- 中文译名：TAA-EPLMR：基于证据路径增强大语言模型推理的威胁行为体归因方法
- 作者：Nan Xiao, Bo Lang, Yikai Chen, Shuxin Zhao, Yuhao Yan
- 年份：2025
- Venue：IEEE International Conference on Big Data 2025
- DOI / URL：https://doi.org/10.1109/BIGDATA66926.2025.11402113
- PDF 来源：`C:/Users/35393/Downloads/TAA-EPLMR_Threat_Actor_Attribution_via_Evidence_Path-Enhanced_Large_Language_Model_Reasoning(科研通-ablesci.com) (1).pdf`
- 本地归档：`../07-zotero-exports/pdfs_20260705_round4/TAA_EPLMR_2025.pdf`
- Zotero key：待补
- 阅读日期：2026-07-08
- 阅读优先级：必读 / 红线精读
- 所属主题：LLM-based APT attribution / CTI-KG / Evidence path retrieval / Attribution explanation / Confidence score
- 阅读状态：正文 PDF 已获取并完成 Project05 新主线复核；由原“高风险撞题笔记”升级为规范精读笔记

## 2. 一句话总结

TAA-EPLMR 是当前最强的撞题论文之一：它将 IOC-based CTI-KG 中的证据路径检索、攻击者区分度剪枝、候选攻击者证据子图聚合与 LLM evidence-aware CoT 推理结合起来，输出 APT group、自然语言归因解释和 confidence score，并在完整、不完整、噪声三类数据集上验证。它基本堵住了“CTI-KG evidence path + LLM reasoning + APT actor attribution explanation”的旧方向。

## 3. 研究问题

- APT threat actor attribution 需要在多源 CTI 中整合 IOC、恶意软件、域名、IP、漏洞、文件名等证据关联。
- 传统 CTI-based attribution 方法依赖 TF-IDF、embedding、HIN/GNN 或多模态特征融合，训练数据规模通常只有几百到几千篇 CTI 报告，先验知识和语义推理能力有限。
- LLM 有更强的语义理解和 in-context learning 能力，但直接让 LLM 根据 IOC 归因会出现领域知识缺口、IOC 时效性不足和 hallucination。
- Vanilla RAG 能补充外部知识，但难以利用 CTI-KG 中的多跳、异构、带语义优先级的证据路径。
- 论文要解决的问题是：如何利用 CTI-KG 中的 evidence paths 为 LLM 提供可解释、可检索、可比较的归因上下文，从而提高闭集 APT actor attribution 的准确性、解释性和可信度。

这篇论文的任务边界很明确：它做的是给定 IOC 和历史 CTI-KG 的 closed-set actor attribution，不是证据不足时的拒答/降级，不是 open-set unknown actor，也不是主动取证规划。

## 4. 核心贡献

1. 提出 CTI-KG-enhanced LLM reasoning 的 APT 归因范式，将 CTI knowledge graph 与 LLM 结合，用结构化证据路径增强 LLM 推理。
2. 设计 IOC attribution graph schema，并基于该 schema 定义 19 类 evidence path patterns，用于刻画从输入 IOC 到带 actor 标签的历史 APT report 的多层证据关联。
3. 提出 evidence path retrieval augmentation：先按 EPP 检索候选路径，再按 attacker discriminability 做 IOC subpath-level 和 evidence path pattern-level 两级剪枝，最后按 attacker 聚合成 evidence subgraph。
4. 设计 evidence-aware attribution logic 的 CoT prompt 和 progressively challenging few-shot demonstrations，引导 LLM 从证据数量、关联报告数、路径类型多样性和路径语义优先级四个方面比较候选 actor。
5. 在 Dataset-Full、Dataset-Incomplete、Dataset-Noise 三个 IOC-based attribution 数据集上对比 14 个 baseline，并展示 APT32/OceanLotus 案例的解释和 confidence score。

## 5. 方法框架

### 输入

- 待归因 APT campaign report 中抽取出的 IOCs。
- IOC 类型包括 malware、vulnerability、IP、domain、URL、filename、filepath、registry、email。
- 历史 CTI-KG：由训练集 CTI reports、APT report 标签、IOC 节点和 IOC 关系构建。
- LLM prompt 中的任务说明、I/O 规格、evidence-aware CoT guidance 和 few-shot demonstrations。

### 输出

- `APT_Group`：最可能的 APT group。
- `Explanations`：基于证据路径和 CoT 的自然语言归因解释。
- `Confidence`：0.00-1.00 的归因置信度。

### 关键模块

| 模块 | 作用 | 对 Project05 的意义 |
|---|---|---|
| IOC attribution graph schema | 规定 APT report、IOC 节点和 IOC 关系类型 | CTI-KG 证据建模已被做实，不能作为宽泛创新 |
| Evidence Path Pattern Construction | 定义 19 类从输入 IOC 到 actor-labeled report 的路径模式 | “证据路径增强归因”被强覆盖 |
| Candidate Evidence Path Retrieval | 在 CTI-KG 中按 EPP 检索候选路径 | 可作为 Project05 baseline 或上游证据源 |
| Two-level Pruning | 按 attacker discriminability 过滤低区分度路径 | 已有证据剪枝/证据增强机制 |
| Attacker-wise Aggregation | 将保留路径按候选 actor 聚合为 evidence subgraph | 提供候选 actor 证据对比结构 |
| LLM Attribution Reasoning | 用 evidence-aware CoT 和 examples 引导 LLM 输出 actor、解释、置信度 | LLM 归因解释/置信度已不是安全创新点 |

### 方法流程

```text
input IOCs from campaign report
  -> IOC attribution graph schema
  -> 19 evidence path patterns
  -> CTI-KG candidate evidence path retrieval
  -> IOC subpath-level pruning
  -> evidence path pattern-level pruning
  -> attacker-wise evidence path aggregation
  -> evidence subgraphs for candidate attackers
  -> LLM prompt with task instructions, CoT guidance, demos, IOCs, evidence subgraphs
  -> APT group + explanation + confidence score
```

## 6. 方法细节精读

### 6.1 IOC attribution graph schema

论文把 APT report 作为核心节点，report 节点带有 attributed attacker label。IOC 节点包括 9 类：malware、vulnerability、IP、domain、URL、filename、filepath、registry、email。关系包括 report 包含 IOC 的 inclusion relation，以及 IOC 之间的关系：

- IP-domain resolution；
- IP-malware association；
- domain-malware association；
- malware homology。

这个 schema 的意义是把原来散落在 CTI 报告中的 IOC 转成可检索图结构，使“某个输入 IOC 是否与某个历史 actor-labeled report 通过路径相连”成为可以计算的问题。

### 6.2 Evidence Path Pattern

作者定义 EPP 为从输入报告中的 IOC 节点出发，经过若干 IOC 关系，最终到达带 attacker label 的历史 APT report 的路径模式。论文共定义 19 类 EPP。

其中 first-order evidence path 直接把输入 IOC 连到 actor-labeled report，例如：

- malware -> APT report；
- domain -> APT report；
- IP -> APT report；
- URL / email / registry / filepath / filename / vulnerability -> APT report。

higher-order evidence path 通过多层 IOC 关系连接，例如：

- IP -> malware -> APT report；
- domain -> malware -> APT report；
- malware -> domain -> malware -> APT report；
- IP -> domain -> IP -> APT report。

论文借用了 Pyramid of Pain 的直觉：malware、domain 等更高层、更难更换的 IOC 通常有更高归因价值；first-order path 一般比长路径更强，因为长路径容易出现 semantic drift 和稀疏性问题。

### 6.3 Evidence path retrieval and pruning

对每个待归因报告 `x`，系统按 19 类 EPP 从 CTI-KG 中检索候选 evidence paths，得到 `EP = {EP_i}`。

问题在于，有些 IOC 被多个 group 共用，例如商用 malware、公共云 C2 IP、常见基础设施。直接把这些路径交给 LLM 会导致上下文过长、噪声增多和误归因。因此作者提出 attacker-discriminability pruning。

两级剪枝：

1. IOC subpath-level pruning
   如果某个 IOC subpath 关联多个 APT group，则认为区分度低。实际设置 `theta_SP = 1`，只保留与单一 group 关联的高区分度 subpath；如果某个 group 占该 subpath 路径数量的 50% 以上，则通过 degradation mechanism 保留该 group 的路径，避免过剪枝。

2. Evidence path pattern-level pruning
   对每个 EPP 类型，如果其关联 group 数量超过阈值，则认为该 pattern 在当前样本中区分度不足。实际设置 `theta_P = 5`。若剪枝后路径集为空，则用 degradation mechanism 保留关联 IOC subpath 数最多的 actor 路径。

这个模块本质上已经做了“证据增强/证据筛选”：不是所有 evidence path 都给 LLM，而是优先保留能区分 actor 的路径。

### 6.4 Attacker-wise evidence path aggregation

剪枝后，系统将路径按候选 attacker 聚合，再按 EPP 类型、输入 IOC、历史 report 组合统计。最终生成一个嵌套字典形式的 evidence subgraph，例如：

```text
APT32
  -> EPP_10 domain first-order path
  -> EPP_11 IP first-order path
  -> EPP_4 malware homology path

APT34
  -> EPP_4 malware homology path
```

这个表示让 LLM 可以比较不同候选 actor 的证据数量、证据类型、路径优先级和关联报告数。

### 6.5 LLM attribution reasoning

LLM prompt 包含四部分：

- 任务说明和输入输出格式；
- evidence-aware attribution logic 的 CoT guidance；
- progressively challenging demonstrations；
- 当前样本的 IOCs 和候选 attacker evidence subgraphs。

CoT guidance 明确要求 LLM 五步推理：

1. 提取关键 attack indicators，如 malware、domain。
2. 解释 evidence path patterns 并分析 evidence subgraphs。
3. 从 evidence path 数量、associated reports 数量、path pattern diversity、semantic priority 四个方面评价候选 actor。
4. 推断最可能的 threat actor。
5. 根据 evidence priority 和 sufficiency 给出 0.00-1.00 confidence score。

重要红线：论文不仅让 LLM “解释一下”，而是已经把证据路径的数量、多样性、优先级和报告数写进了推理步骤。因此 Project05 不能再把“LLM 根据证据路径解释归因并给置信度”作为核心创新。

## 7. 数据集与实验

- 基础数据集：APT-MMF 使用的 IOC-based threat actor attribution dataset。
- 数据来源：APTNotes、安全厂商 CTI 报告、CVE、MITRE ATT&CK、VirusTotal 等。
- 规模：
  - 1,300 篇 CTI reports；
  - 21 个 APT groups；
  - 137 篇 test reports；
  - CTI-KG 包含 23,615 nodes 和 38,626 relations。
- 划分：每个 group 报告按 9:1 划分，训练部分构建 CTI-KG，测试部分用于归因。

### 三个数据集

| 数据集 | 构造方式 | 含义 |
|---|---|---|
| Dataset-Full | 原始完整 IOC-based attribution dataset | 正常闭集 actor attribution |
| Dataset-Incomplete | 删除 vulnerability、filename、registry、email 四类 IOC | 模拟缺少部分 IOC 类型 |
| Dataset-Noise | 向每个 report 加入 unrelated malware、domain、URL、filepath、IP，共 640 个 noisy entities | 模拟噪声 IOC |

注意：Dataset-Incomplete 只是删除若干 IOC 类型后继续做 actor classification，并没有判断“证据是否不足以归因”。这点对 Project05 非常关键。

### Baselines

传统 ML：

- Naive Bayes；
- KNN；
- Decision Tree；
- SVM；
- Random Forest；
- XGBoost；
- MLP。

GNN / 图方法：

- GCN；
- GAT；
- HAN；
- HGNN-AC；
- APT-MMF。

LLM 方法：

- Direct：只给任务说明和 IOCs，不给外部知识；
- Vanilla RAG：基于输入 IOCs 从已知报告检索单跳 CTI 信息；
- TAA-EPLMR：证据路径检索增强 + LLM reasoning。

LLM backbone：

- Qwen3-Plus；
- QwQ-Plus；
- DeepSeek-V3；
- DeepSeek-R1。

### 指标

- Micro-F1；
- Macro-F1；
- LLM 输出 actor 名称后，用 ATT&CK Groups、Threat Group Cards、Malpedia Actors 做 alias 对齐；
- 无法匹配测试集 actor 的输出统一记为 `off-list`。

`off-list` 只是评价时处理 LLM 输出不匹配标签的机制，不是 open-set attribution 或 unknown actor 机制。

## 8. 主要结果

### 8.1 Comparative experiment

TAA-EPLMR 在所有数据集和四个 LLM backbone 上都优于 Direct 和 Vanilla RAG。代表性结果：

| Backbone | Dataset-Full Micro-F1 | Dataset-Incomplete Micro-F1 | Dataset-Noise Micro-F1 |
|---|---:|---:|---:|
| Qwen3-Plus + TAA-EPLMR | 0.854 | 0.832 | 0.847 |
| QwQ-Plus + TAA-EPLMR | 0.854 | 0.847 | 0.854 |
| DeepSeek-V3 + TAA-EPLMR | 0.861 | 0.839 | 0.847 |
| DeepSeek-R1 + TAA-EPLMR | 0.861 | 0.839 | 0.861 |

与 APT-MMF 相比，作者报告平均 Micro-F1 提升约 4.63%，Macro-F1 提升约 4.33%。与 Vanilla RAG 相比，平均 Micro-F1 提升约 3.14%，Macro-F1 提升约 3.76%。

Direct LLM 表现很差，例如 DeepSeek-R1 在 Dataset-Full 上 Micro-F1 只有 0.117，说明 LLM 内部知识不足以完成 IOC-driven APT attribution。

### 8.2 Incomplete / noisy robustness

Dataset-Incomplete 和 Dataset-Noise 会降低所有方法表现，但 TAA-EPLMR 仍保持优势。作者据此说明 evidence path retrieval、剪枝和 LLM reasoning 对不完整/噪声 IOC 有鲁棒性。

对 Project05 的解读：这已经覆盖了“缺少部分 IOC 后仍做归因”的实验。因此我们不能只做 evidence deletion 然后比较 actor F1；必须进一步比较是否正确降级、拒答、停止或选择下一步证据动作。

### 8.3 Ablation study

消融以 DeepSeek-R1 为 backbone，从 Direct 开始逐步加入：

- `ep-r`：EPP-based candidate evidence path retrieval；
- `prun.&aggr.`：pruning and aggregation；
- `cot-eva`：evidence-aware CoT；
- `pc-demos`：progressively challenging demonstrations。

Dataset-Full 上：

- Direct：Micro-F1 0.117，Macro-F1 0.128；
- 加入 evidence path retrieval 后：Micro-F1 0.832，Macro-F1 0.716；
- 完整 TAA-EPLMR：Micro-F1 0.861，Macro-F1 0.742。

最大增益来自 evidence path retrieval，说明外部 CTI-KG evidence paths 是核心；剪枝聚合、CoT guidance 和 demonstrations 提供进一步提升。

## 9. Case Study：APT32 / OceanLotus

输入 IOC 包括：

- malware：`eb2b52ed27346962c4b7b26df51ebafa`；
- domain：`eoneorbin.com`、`maerferd.com`、`harinarach.com`、`ad.jqueryclick.com`；
- IP：`45.32.105.45`。

系统检索并聚合后，候选证据主要包括：

- APT32：
  - `EPP_10`：domain `ad.jqueryclick.com` 直接出现在 APT32/OceanLotus 相关报告；
  - `EPP_11`：IP `45.32.105.45` 直接出现在同一 APT32 报告；
  - `EPP_4`：malware homology 连接到疑似海莲花相关报告。
- APT34：
  - 主要只有 `EPP_4` malware homology，且相关报告标题是 `Unknown threat actor`，证据较弱。

LLM 输出 APT32，confidence 为 0.85。解释中比较了：

- evidence path 数量；
- associated reports 数量；
- path pattern diversity；
- path priority；
- APT34 噪声标签与其典型行为不一致。

这个案例说明 TAA-EPLMR 已经能让 LLM 基于证据路径生成较完整的归因解释，还能识别部分噪声标签的不一致性。但它仍然在最后输出 actor，而没有说“当前证据只能到 campaign/technique”或“需要继续取证”。

## 10. 关键知识点

### 概念

- evidence path：从输入 IOC 到带 actor 标签历史 report 的图路径，是本文归因证据的基本单位。
- evidence path pattern：路径类型模板，类似 heterogeneous information network 中的 metapath。
- attacker discriminability：某条 IOC subpath 或 EPP 能否把候选 actor 区分开，关联 actor 越少，区分度越强。
- evidence subgraph：按候选 actor 聚合后的证据路径集合，用于 LLM 比较。
- evidence-aware CoT：把证据数量、报告数、多样性、路径优先级写进 LLM 推理步骤。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| evidence path | 证据路径 | 从 IOC 到 actor-labeled report 的路径 |
| evidence path pattern | 证据路径模式 | EPP，类似 metapath |
| attacker discriminability | 攻击者区分度 | 用于剪枝低区分度路径 |
| attacker-wise aggregation | 按攻击者聚合 | 将路径组织成候选 actor evidence subgraph |
| evidence-aware attribution logic | 证据感知归因逻辑 | LLM CoT guidance 的核心 |
| confidence score | 置信度分数 | 本文由 LLM 输出，未做校准评估 |

## 11. 优点

- 方法链条完整：schema、EPP、检索、剪枝、聚合、LLM reasoning、解释、置信度、实验都有。
- 和 Direct LLM / Vanilla RAG 对比清楚，证明“直接问 LLM”不可靠，结构化 CTI-KG evidence path 很关键。
- 三个数据集覆盖完整、不完整、噪声信息，已经考虑了真实 CTI 中常见的不完整和噪声问题。
- 消融清楚显示 evidence path retrieval 是主要增益来源。
- Case study 展示了 LLM 如何在证据路径层面对候选 actor 做可读解释。

## 12. 局限

- 闭集 actor attribution：默认测试样本属于 21 个已知 APT groups 之一。
- 没有 open-set / unknown actor 机制，`off-list` 只是评价标签处理。
- 没有 refusal / abstention：证据不足时仍要求输出最可能 APT group。
- 没有 attribution granularity gate：不支持 technique、intent、campaign、actor 的层级降级。
- confidence score 由 LLM 生成，但没有 ECE、Brier score、reliability diagram 等校准评估。
- incomplete/noisy 实验仍是分类鲁棒性实验，不是证据充分性判定实验。
- 证据来源主要是 CTI/IOC KG，不处理本地 EDR/provenance/log/network evidence 与 CTI 行为图的对齐状态。
- 没有候选取证动作、动作成本、动作收益估计，也没有主动补证闭环。

## 13. 对 Project05 的启发

- 强红线：不能再主张“证据路径增强 LLM APT 归因解释”。
- 强红线：不能把 `CTI-KG + evidence path retrieval + LLM CoT + confidence` 写成核心创新。
- 强红线：不能只做删除 IOC / 加噪声 IOC 后继续输出 actor label，这已经落在 TAA-EPLMR 的实验边界内。
- 可作为 baseline：TAA-EPLMR-like 方法可以作为 `CTI-KG evidence path + LLM actor attribution` 强 baseline。
- 可借鉴输入结构：candidate evidence subgraphs 可以作为 Project05 evidence state 的一部分。
- 可借鉴证据维度：path 数量、报告数、path diversity、path priority 可以转化为 evidence state feature。
- Project05 必须上移：从“更好地输出 actor”转到“当前证据能支撑哪一级归因，以及下一步取什么证据最有价值”。

## 14. 可转化的研究问题

1. 当 TAA-EPLMR 在 Dataset-Incomplete 中仍输出 actor 时，这些输出是否存在 over-attribution？Project05 能否识别哪些样本应降级或暂缓归因？
2. TAA-EPLMR 的 confidence score 是否经过校准？在证据遮蔽程度增加时，其 confidence 是否单调合理下降？
3. 将 TAA-EPLMR 的 evidence subgraph 转为 evidence state 后，能否规划下一步最值得获取的 IOC/provenance/log evidence？
4. 当 evidence paths 只支持某个 campaign 或 technique，而不足以区分 actor 时，系统应如何输出粒度受控结论？
5. TAA-EPLMR-like baseline 与 Project05 planner 在相同 evidence ablation 设置下，谁能以更低成本达到目标归因粒度？

## 15. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| APT-MMF | TAA-EPLMR 的核心数据集和强 baseline 来源；APT-MMF 做 multimodal/multilevel feature fusion，TAA-EPLMR 用 CTI-KG evidence path + LLM 推理超过它 |
| AURA | 都是 LLM / KG / RAG 辅助 APT attribution；TAA-EPLMR 更具体、更可复现，撞题风险更高 |
| LLMAPT | 同属 LLM-based APT attribution；TAA-EPLMR 在 evidence path 和实验上更扎实 |
| APT-ATT | APT-ATT 是非 LLM 的异构 CTI 表示 + CTGAN + stacking 分类路线；TAA-EPLMR 是 LLM + CTI-KG evidence path 路线 |
| CTIConnect / Beyond RAG for CTI | 说明 vanilla RAG 不足，图/混合检索更适合 CTI 多跳关联 |
| POIROT / DeepHunter / MEGR-APT / CLIProv / APT-CGLP | 这些偏 CTI-local/provenance alignment 和 threat hunting；TAA-EPLMR 偏 CTI-KG actor attribution |
| Project05 | TAA-EPLMR 是必须避让的强 baseline；Project05 不重复 actor attribution，而做 evidence state、granularity gate、active evidence acquisition |

## 16. 论文写作可引用句式

- Recent work has shown that CTI knowledge graphs can provide evidence paths that substantially improve LLM-based closed-set threat actor attribution, yielding both attribution explanations and confidence scores.
- However, evidence path-enhanced attribution methods still assume that an actor-level decision should be produced, even under incomplete or noisy evidence, and do not model whether the current evidence state supports a given attribution granularity.
- Project05 therefore treats evidence-path attribution systems as upstream or baseline components, and focuses on evidence-state modeling and cost-aware acquisition planning under partial observation.

## 17. 我的批注与疑问

- 这篇是旧题的真正“红灯”：如果题目里还出现 evidence path-enhanced LLM attribution，基本会被它压死。
- 它的 confidence score 是最值得警惕的地方：看起来已经覆盖“置信度”，但其实没有校准，也没有证据不足时拒答。
- 它的 incomplete/noisy 实验不等于我们要做的 evidence insufficiency。作者是“删证据后继续分类”；Project05 要问“删到这种程度时是否还应该分类”。
- 它提示我们 MVP 不能只做 missing evidence list。必须把 missing evidence 转成 action value 和 cost-aware planning，否则还是像给 TAA-EPLMR 加一层解释。
- 如果后面写实验，TAA-EPLMR-like baseline 至少要有一个简化版：`evidence path retrieval + LLM actor output`，再对比我们的 `STOP / downgrade / acquire`。

## 18. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文红线价值：5/5
- 作为 Project05 baseline 价值：5/5
- 是否进入核心文献：是

## 19. 新主线复核：与 Project05 的覆盖边界

复核目标：按 Project05 当前主线“对齐感知证据状态建模 + 主动取证规划”审计 TAA-EPLMR 是否已经覆盖核心创新。

### 19.1 覆盖度矩阵

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

### 19.2 复核结论

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

### 19.3 对实验设计的影响

TAA-EPLMR 应作为强 baseline 或红线参照，而不是被重复：

- baseline：`TAA-EPLMR-like CTI-KG evidence path + LLM actor attribution`；
- Project05 的对照任务：在相同证据被遮蔽时，不只比较 actor F1，还比较是否正确降级、拒答、选择下一步证据动作；
- 指标必须加入 over-attribution rate、correct downgrade / abstention、granularity selection accuracy、next-best-evidence ranking、cost-to-target-granularity；
- 如果只做 Dataset-Incomplete 风格删除 IOC 后继续分类，会落回 TAA-EPLMR 的实验边界。

### 19.4 对专利写法的红线

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

## 20. 最终判断

TAA-EPLMR 对 Project05 的旧方向是红色警报，对当前新主线是可控红线。它已经覆盖 CTI-KG evidence path、LLM reasoning、explanation、confidence 和 incomplete/noisy IOC robustness，因此不能再做“证据路径增强 LLM 归因”。但它没有解决 evidence sufficiency、attribution granularity、active evidence acquisition 和 cost-aware planning，因此没有推翻当前“对齐感知证据状态建模 + 主动取证规划”主线。
