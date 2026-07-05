# 威胁归因方向术语表 v0.1

## 2026-07-05 H1 补读新增术语

| 英文 | 建议译法 | 备注 |
|---|---|---|
| evidence-gated attribution | 证据门控归因 | 借鉴 OpenSec 的 evidence-gated action 思路，用于判断何时允许输出 actor |
| over-attribution rate | 过度归因率 | 证据不足时仍输出高置信 actor 的比例 |
| correct abstention rate | 正确暂缓归因率 | 不可归因/证据不足样本上正确拒答的比例 |
| selective accuracy | 选择性准确率 | 只在系统选择输出的样本上计算准确率 |
| coverage | 覆盖率 | 系统选择输出而非 abstain 的样本比例 |
| out-of-scope rejection rate | 范围外拒绝率 | OOS/未知 actor 样本被正确拒绝的比例 |
| open-set attribution | 开放集归因 | 测试样本不一定属于已知 actor 集合 |
| evidence availability profile | 证据可用性画像 | 描述当前案件有哪些证据、缺哪些证据、证据粒度和可靠性如何 |
| evidence sufficiency score | 证据充分性分数 | 判断证据足以支持 technique / intent / campaign / actor 哪一层结论 |
| adaptive attribution granularity | 自适应归因粒度 | 证据不足时从 actor 降级到 campaign / intent / technique |
| span localization | 证据片段定位 | TTPrint 中将 technique 候选锚定到原文证据窗口 |
| diverge-then-converge verification | 先发散后收敛验证 | 先召回候选，再用证据和定义过滤 |
| verifiable reward | 可验证奖励 | Minerva/RLVR 语境，使用确定性 verifier 评分 |
| reward sparsity | 奖励稀疏 | 可验证奖励只在部分输出上给出有效反馈 |
| time-decayed confidence | 时间衰减置信度 | ARCANE 中跨 campaign 累积证据时考虑时间衰减 |
| fingerprint separability ceiling | 指纹可分性上限 | 不同 actor 行为/遥测特征过于接近导致归因上限 |
| synthetic APT | 合成 APT | AI agent 按 APT profile 模仿出的攻击行为体 |
| TTP convergence | TTP 趋同 | 不同 actor/agent 独立产生相似 TTP 的现象 |

## 版本说明

- 版本：v0.1
- 更新日期：2026-07-04
- 来源文献：`A survey of cyber threat attribution`、`AttacKG`、`EXTRACTOR`、`KAIROS`、`TechniqueRAG`
- 用途：统一 Zotero 批注、论文精读笔记、开题报告和后续写作中的术语译法。

## 使用规则

- ATT&CK 专有名词尽量保留英文缩写，不强行翻译。
- `attribution` 统一译为“归因”，不译为“属性”。
- `campaign` 在安全语境中译为“攻击活动”，不优先译为“战役”。
- `provenance` 在系统安全语境中译为“溯源”，但注意它不是最终“威胁归因”，而是系统行为因果证据。
- `intent` 在当前选题语境中译为“攻击意图”，但后续需要单独定义标签体系。

## 1. 威胁归因与 APT

| 英文 | 建议译法 | 备注 |
|---|---|---|
| attribution | 归因 | 不译为属性 |
| cyber threat attribution | 网络威胁归因 | 核心术语 |
| threat attribution | 威胁归因 |  |
| APT attribution | APT 归因 |  |
| Advanced Persistent Threat | 高级持续性威胁 | APT |
| threat actor | 威胁行为体 | 也可称攻击行为体 |
| adversary | 对手 / 攻击者 | 视上下文 |
| attacker | 攻击者 |  |
| campaign | 攻击活动 | 不建议译为战役 |
| intrusion campaign | 入侵活动 |  |
| actor-level attribution | 威胁行为体级归因 | 归因到 APT/组织/团伙 |
| campaign-level attribution | 攻击活动级归因 | 介于单次事件和 actor 归因之间 |
| infrastructure-level attribution | 基础设施级归因 | IP、域名、C2、证书等 |
| campaign attribution | 攻击活动归因 | ADAPT it! 语境；把样本归入同一 campaign |
| group attribution | 组织级归因 / 行为体归因 | ADAPT it! 语境；把样本或 campaign 关联到 threat group |
| malware family | 恶意软件家族 |  |
| motive / motivation | 动机 | 高层归因或意图分析语境 |
| modus operandi | 作案方式 / 行为模式 | CTI 报告中常见 |
| ransomware attribution | 勒索软件归因 | `High Stakes, Low Certainty` 语境 |
| Ransomware-as-a-Service | 勒索软件即服务 | RaaS |
| ransomware threat actor | 勒索软件威胁行为体 | RTA |
| sanction screening | 制裁筛查 | 支付赎金前的合规检查 |
| relative attribution | 相对归因 | 关联到历史事件、活动簇或已知 actor cluster |
| absolute attribution | 绝对归因 | 声称识别真实幕后行为体，风险更高 |
| closed-set actor attribution | 封闭集行为体归因 | APT-MMF 语境；候选 actor 在训练集中已知 |
| unknown actor detection | 未知行为体检测 | 判断样本不属于任何已知 actor |
| false flag | 假旗行动 / 伪旗行动 | 攻击者故意伪装成其他 actor |
| linking feature | 关联特征 | ADAPT it! 中用于跨样本/跨文件类型连接 group 的特征 |
| Intra-Clustering | 域内聚类 | ADAPT it! 中用于 campaign attribution |
| Inter-Clustering | 跨域聚类 | ADAPT it! 中用于 group attribution |

## 2. CTI 与威胁情报

| 英文 | 建议译法 | 备注 |
|---|---|---|
| threat intelligence | 威胁情报 |  |
| cyber threat intelligence | 网络威胁情报 | CTI |
| CTI report | 网络威胁情报报告 | 可简称威胁报告 |
| threat report | 威胁报告 |  |
| incident report | 事件报告 |  |
| threat analysis report | 威胁分析报告 |  |
| security text | 安全文本 | TechniqueRAG 泛称输入文本 |
| observable | 可观测对象 | 如 IP、域名、文件哈希 |
| IOC | 失陷指标 | Indicator of Compromise |
| indicator of compromise | 失陷指标 | IOC |
| high-level IoC | 高层失陷指标 | TTP、行为模式、modus operandi 等抽象指标 |
| low-level IoC | 低层失陷指标 | hash、IP、域名、文件路径、注册表键等具体指标 |
| ransom note | 赎金信 | 勒索软件特定 IoC |
| leak site | 泄露站点 | 勒索组织用于公开施压或泄露数据的网站 |
| communication channel | 通信渠道 | 勒索软件谈判或联系攻击者的渠道 |
| pattern-based feature | 模式特征 | ADAPT it! 中从 strings 提取 IP、URL、key、hash、路径等 |
| infrastructure feature | 基础设施特征 | ADAPT it! 中 BGP、ASN、国家、证书等 |
| C2 | 命令与控制 | Command and Control |
| C&C | 命令与控制 | 同 C2 |
| TLP | 交通灯协议 | Traffic Light Protocol，情报共享分级 |
| contextualization | 上下文化 / 情境化 | LOCALINTEL/CyLens 语境 |
| organizational threat intelligence | 组织级威胁情报 | 结合组织本地上下文的 CTI |
| global threat repository | 全局威胁知识库 | 公开 CTI 源，如 CVE/NVD/CWE |
| local knowledge database | 本地知识库 | 组织内部私有知识库 |
| local organizational knowledge | 组织本地知识 | 资产、配置、维护计划、可信 CTI 等 |
| generic threat intelligence | 通用威胁情报 | 未结合组织环境的公开 CTI |
| contextualized CTI | 上下文化 CTI / 组织语境化 CTI | LOCALINTEL 输出 |
| contextualized completion | 上下文化生成结果 | LocalIntel 中的 C |
| zero-day trigger | 零日触发报告 | LocalIntel 输入 |
| correlation | 关联分析 | CTI 生命周期任务 |
| prioritization | 优先级排序 | CTI/SOC 任务 |
| remediation | 修复 / 缓解措施 |  |
| CVE | 通用漏洞披露 | Common Vulnerabilities and Exposures |
| CWE | 通用弱点枚举 | Common Weakness Enumeration |
| CVSS | 通用漏洞评分系统 | Common Vulnerability Scoring System |
| root cause mapping | 根因映射 | CTIBench 中 CVE -> CWE 任务 |
| vulnerability severity prediction | 漏洞严重性预测 | CTIBench 中 CVE -> CVSS vector 任务 |
| threat hunting | 威胁狩猎 |  |
| incident investigation | 安全事件调查 |  |
| incident response | 安全事件响应 |  |
| SOC | 安全运营中心 | Security Operations Center |

## 3. ATT&CK、TTP 与攻击链

| 英文 | 建议译法 | 备注 |
|---|---|---|
| MITRE ATT&CK | MITRE ATT&CK | 不翻译 |
| ATT&CK matrix | ATT&CK 矩阵 |  |
| tactics, techniques, and procedures | 战术、技术与过程 | TTPs |
| TTPs | 战术、技术与过程 | 保留缩写 |
| tactic | 战术 | ATT&CK 中表示攻击目的/阶段 |
| technique | 技术 | ATT&CK 语境 |
| sub-technique | 子技术 | ATT&CK 细粒度技术 |
| procedure | 过程 / 操作过程 | ATT&CK procedure example |
| procedure example | 过程示例 | MITRE ATT&CK 示例语境 |
| technique annotation | 技术标注 | TechniqueRAG 核心任务 |
| adversarial technique annotation | 对抗技术标注 / ATT&CK 技术标注 | TechniqueRAG 语境 |
| attack technique extraction | 攻击技术抽取 | CTIBench 中 CTI-ATE 任务 |
| technique ID | 技术编号 | 如 T1059.001 |
| text-technique pair | 文本-技术标注对 | TechniqueRAG 检索语料单元 |
| technique template | 技术模板 | AttacKG 中某个 ATT&CK 技术的典型行为结构 |
| technique knowledge graph | 技术知识图谱 | AttacKG 核心概念 |
| TTP extraction | TTP 抽取 | 从 CTI 报告识别 ATT&CK TTP |
| threat action | 威胁动作 / 攻击行为句 | Multi-Step LLM Pipeline 语境 |
| atomic threat action | 原子威胁动作 | 一条动作尽量对应一个 ATT&CK technique |
| actionable threat intelligence | 可行动威胁情报 | 可直接用于检测、狩猎或响应 |
| finished cyber threat report | 完整网络威胁报告 | TTPXHunter 语境 |
| minority class | 少数类 | 低频 TTP 类别 |
| contextual data augmentation | 上下文数据增强 | TTPXHunter 中用于缓解少数类 |
| IOC replacement | IOC 替换 | 将具体可观测对象替换为泛化占位符 |
| relevant sentence filtering | 相关句过滤 | 从完整报告中过滤 TTP 相关句 |
| report-level aggregation | 报告级聚合 | 句子 TTP 预测聚合为报告 TTP set |
| attack chain | 攻击链 |  |
| kill chain | 杀伤链 | Lockheed Martin Kill Chain |
| attack stage | 攻击阶段 | 可与 tactic 对应，但不完全等同 |
| attack step | 攻击步骤 |  |
| attack intent | 攻击意图 | 后续需定义标签体系 |
| intent recognition | 意图识别 |  |
| intent inference | 意图推断 |  |
| multi-label prediction | 多标签预测 | TechniqueRAG Expert 数据语境 |
| under-prediction | 漏标 / 欠预测 | 多标签场景下常见 |
| annotation inconsistency | 标注不一致 | TechniqueRAG 错误分析 |

## 4. 图结构、攻击行为与溯源

| 英文 | 建议译法 | 备注 |
|---|---|---|
| graph | 图 | 节点和边构成 |
| node | 节点 |  |
| edge | 边 |  |
| entity | 实体 | CTI 或系统图中均常见 |
| relation | 关系 |  |
| heterogeneous attributed graph | 异构属性图 | APT-MMF 语境；包含多类型节点、边和节点属性 |
| metapath | 元路径 | 异构图中按节点/边类型定义的路径模式 |
| report node | 报告节点 | APT-MMF 中表示 CTI report 的中心节点 |
| attributeless report node | 无属性报告节点 | 报告节点本身无结构化属性，需要由 IOC 邻居补全 |
| IOC type-level attention | IOC 类型级注意力 | APT-MMF 中按 IOC 类型聚合邻居贡献 |
| metapath semantic-level attention | 元路径语义级注意力 | APT-MMF 中聚合不同 metapath 的贡献 |
| relation triple | 关系三元组 | subject-predicate-object；Open-CyKG / OIE 语境 |
| attack graph | 攻击图 / 攻击行为图 | CTI 或日志中的攻击实体与关系图 |
| attack behavior graph | 攻击行为图 | AttacKG / EXTRACTOR 语境 |
| provenance graph | 溯源图 | 节点表示系统实体，边表示系统事件/信息流 |
| provenance query graph | 溯源查询图 | EXTRACTOR/POIROT 语境 |
| query graph | 查询图 | 用于在大规模日志图中搜索攻击模式的小图 |
| dependency graph | 依赖图 | DEPCOMM / causality analysis 语境 |
| dependency explosion | 依赖爆炸 | 因果分析导致图规模膨胀 |
| causality analysis | 因果分析 | 系统审计日志到依赖图 |
| graph alignment | 图对齐 | AttacKG 用于匹配攻击图和技术模板 |
| graph matching | 图匹配 |  |
| graph summarization | 图摘要 | DEPCOMM 语境 |
| graph reduction | 图约简 | 将大规模日志图压缩为调查相关子图 |
| community discovery | 社区发现 | HERCULE/DEPCOMM 语境 |
| process-centric community | 进程中心社区 | DEPCOMM 语境 |
| community compression | 社区压缩 | DEPCOMM 中压缩社区内部重复节点和边 |
| intimate processes | 紧密进程组 | DEPCOMM 中共同完成系统活动的一组进程 |
| InfoPath | 信息路径 | DEPCOMM 中表示社区输入到输出的信息流路径 |
| POI event | 关注事件 / 兴趣点事件 | Point-Of-Interest event，因果分析起点 |
| process lineage tree | 进程谱系树 | 表示进程父子关系 |
| whole-system provenance | 全系统溯源 | Kairos 语境，跨进程、文件、socket 和主机 |
| process | 进程 | provenance graph 节点类型 |
| file | 文件 | provenance graph 节点类型 |
| socket | 套接字 | provenance graph 节点类型 |
| system audit log | 系统审计日志 |  |
| audit log | 审计日志 |  |
| information flow | 信息流 | provenance graph 边方向语义 |
| attack summary graph | 攻击摘要图 | Kairos 输出的可调查攻击子图 |
| attack story reconstruction | 攻击故事重建 | HERCULE 语境 |
| attack reconstruction | 攻击重建 | Kairos/PIDS 评价维度 |
| productive sentence | 有效攻击行为句 | EXTRACTOR 中表示可观测攻击行为的句子 |
| non-productive sentence | 非攻击行为句 | 背景、描述、广告等句子 |
| semantic role labeling | 语义角色标注 | 用于识别谁对谁做了什么 |
| Open Information Extraction | 开放信息抽取 | OIE；不预设固定关系 schema |
| OIE | 开放信息抽取 | Open Information Extraction |
| named entity recognition | 命名实体识别 | NER |
| NER | 命名实体识别 | Named Entity Recognition |
| ellipsis subject resolution | 省略主语消解 | 补全 CTI 连续动作中省略的攻击主体 |
| pronoun resolution | 代词消解 | 将 it/itself 等代词映射回真实实体 |

## 5. Provenance-based Detection 与图学习

| 英文 | 建议译法 | 备注 |
|---|---|---|
| provenance-based intrusion detection system | 基于溯源的入侵检测系统 | PIDS |
| PIDS | 基于溯源的入侵检测系统 | Provenance-based Intrusion Detection System |
| anomaly detection | 异常检测 |  |
| attack agnosticity | 攻击无关性 | 不依赖已知攻击签名 |
| timeliness | 实时性 / 及时性 | Kairos 评价维度 |
| scope | 覆盖范围 | Kairos 评价维度 |
| reconstruction error | 重构误差 | Kairos 中用于衡量系统事件边异常程度 |
| suspicious node | 可疑节点 | 同时考虑 anomalousness 和 rareness |
| anomalousness | 异常性 | Kairos 语境 |
| rareness | 稀有性 | Kairos 语境 |
| time window | 时间窗口 |  |
| time window queue | 时间窗口队列 | Kairos 中串联 low-and-slow APT 异常活动 |
| low-and-slow attack | 低频慢速攻击 | APT 常见特征 |
| temporal graph neural network | 时间图神经网络 | TGN |
| TGN | 时间图神经网络 | Temporal Graph Network |
| GraphSAGE | GraphSAGE | 图神经网络模型名，不翻译 |
| graph embedding | 图嵌入 | PROGRAPHER 语境 |
| whole graph embedding | 整图嵌入 | PROGRAPHER 中的 snapshot-level representation |
| snapshot | 快照 / 图快照 | PROGRAPHER 中从长 provenance graph 切出的时间片段 |
| snapshot builder | 快照构建器 | PROGRAPHER 核心模块 |
| Rooted Subgraph | 根子图 | PROGRAPHER 中的局部图模式 |
| RSG | 根子图 | Rooted Subgraph 缩写 |
| key indicator | 关键指示物 / 关键指标 | PROGRAPHER 中从异常 snapshot 映射出的可疑证据 |
| indicator generation | 指示物生成 | 把异常 snapshot 落回 suspicious RSG/node |
| forgetting rate | 遗忘率 | 控制 snapshot 滑动删除比例 |
| transductive learning | 传导式学习 | 测试依赖训练阶段见过的结构或词表 |
| inductive learning | 归纳式学习 | 可泛化到训练阶段未见节点或结构 |
| node-level detection | 节点级检测 | THREATRACE 语境 |
| node-level tracing | 节点级追踪 | THREATRACE 中定位异常实体及邻域 |
| anomalous node detection | 异常节点检测 | THREATRACE 核心任务 |
| active node | 活跃节点 | 当前用于训练或检测的节点 |
| related node | 相关节点 | 在 K-hop 内可到达 active node 的节点 |
| dominant label | 显式标签 / 主标签 | THREATRACE 中对应 node type |
| hidden label | 隐式标签 | 同一 node type 下的具体功能角色 |
| multi-model framework | 多模型框架 | THREATRACE 中多个 GraphSAGE 子模型 |
| edge-level anomaly | 边级异常 | Kairos 语境 |
| graph-level detection | 图级检测 | UNICORN/PROGRAPHER 对比 |
| graph sketching | 图草图 | UNICORN 语境 |
| graph histogram | 图直方图 | UNICORN 中统计 provenance 子结构 |
| HistoSketch | HistoSketch | UNICORN 使用的相似性保持流式直方图草图 |
| Weisfeiler-Lehman subtree graph kernel | Weisfeiler-Lehman 子树图核 | WL subtree graph kernel |
| evolutionary model | 演化式模型 | UNICORN 中建模系统 metastates |
| metastate | 元状态 / 运行阶段状态 | UNICORN 中表示系统 boot、初始化、服务等状态 |
| model poisoning | 模型污染 | 在线更新模型被攻击者逐步带偏 |
| closed-world assumption | 封闭世界假设 | 未覆盖的正常行为可能被异常检测器误判 |
| concept drift | 概念漂移 | 正常行为分布变化导致误报 |
| false positive | 误报 | FP |
| false negative | 漏报 | FN |

## 6. RAG、知识图谱与检索

| 英文 | 建议译法 | 备注 |
|---|---|---|
| retrieval-augmented generation | 检索增强生成 | RAG |
| RAG | 检索增强生成 | 保留缩写 |
| retriever | 检索器 |  |
| re-ranker | 重排序器 | TechniqueRAG 中用 LLM 重排候选 |
| generator | 生成器 | TechniqueRAG 输出 technique IDs |
| retrieval corpus | 检索语料库 |  |
| candidate extraction | 候选抽取 |  |
| Technique Candidate Generator | 技术候选生成器 | 基于 ATT&CK procedure embedding 召回候选 technique |
| Validator | 验证器 | 对候选技术、意图或归因证据进行排序和过滤 |
| retrieved exemplar | 检索样例 | 用作 few-shot context |
| few-shot learning | 小样本学习 |  |
| zero-shot learning | 零样本学习 |  |
| instruction-tuned LLM | 指令微调大模型 |  |
| fine-tuning | 微调 |  |
| hard negative mining | 难负例挖掘 | 检索模型训练常用 |
| dense retrieval | 稠密检索 | 向量检索 |
| sparse retrieval | 稀疏检索 | 如 BM25 |
| BM25 | BM25 | 检索算法名 |
| vector RAG | 向量 RAG |  |
| GraphRAG | 图 RAG | 不强行翻译 |
| agentic retrieval | 智能体式检索 | Beyond RAG 语境 |
| hybrid retrieval | 混合检索 |  |
| vanilla RAG | 普通 RAG / 基础 RAG | 原始 query embedding 后直接检索 |
| closed-book | 闭卷 | 不使用外部检索，仅依赖参数知识 |
| domain-specific retrieval | 领域定制检索 | CTIConnect 语境 |
| Extract-then-Retrieve | 先抽取后检索 | EtR |
| Decompose-then-Retrieve | 先分解后检索 | DtR |
| CSKG-Guided RAG | 网络安全知识图谱引导 RAG | CTIConnect 多文档综合策略 |
| cross-source semantic gap | 跨源语义鸿沟 | 异构 CTI 源之间术语/抽象层差异 |
| knowledge graph | 知识图谱 | KG |
| KG | 知识图谱 | Knowledge Graph |
| cyber threat intelligence knowledge graph | 网络威胁情报知识图谱 | CTI KG |
| canonicalization | 归一化 / 标准化 | CTI KG 中常指实体、关系或别名合并 |
| entity canonicalization | 实体归一化 | 合并同一 actor/tool/malware 的不同表述 |
| knowledge graph fusion | 知识图谱融合 | 合并重复、等价或互补的图谱事实 |
| Neo4j | Neo4j | 图数据库名，不翻译 |
| heterogeneous knowledge source | 异构知识源 | CTIConnect 语境 |
| heterogeneous CTI | 异构网络威胁情报 |  |
| Entity Linking | 实体链接 | structured -> structured |
| Entity Attribution | 实体归因 | unstructured -> structured |
| Multi-Document Synthesis | 多文档综合 | unstructured -> unstructured |
| Threat Actor Profiling | 威胁行为体画像 | TAP |
| Malware Lineage Analysis | 恶意软件谱系分析 | MLA |
| Campaign Storyline Construction | 攻击活动故事线构建 | CSC |
| evidence utilization | 证据利用 | 检索到证据后是否能正确推理 |

## 7. LLM、Agent 与安全调查

| 英文 | 建议译法 | 备注 |
|---|---|---|
| large language model | 大语言模型 | LLM |
| LLM | 大语言模型 | 保留缩写 |
| LLM agent | 大模型智能体 |  |
| agent | 智能体 |  |
| security event | 安全事件 | SEvenLLM 核心对象 |
| multi-agent system | 多智能体系统 |  |
| agentic AI | 智能体式 AI |  |
| autonomous agent | 自主智能体 |  |
| planner agent | 规划智能体 |  |
| retriever agent | 检索智能体 |  |
| verifier agent | 验证智能体 |  |
| report writer agent | 报告生成智能体 |  |
| investigation graph | 调查图 | ExCyTIn-Bench 语境 |
| security question | 安全调查问题 | benchmark 中的问答任务 |
| multi-hop reasoning | 多跳推理 |  |
| evidence-backed narrative | 证据支撑叙事 | Cognitive SOC 语境 |
| playbook | 剧本 / 处置剧本 | 安全运营语境 |
| security operations | 安全运营 |  |
| security automation | 安全自动化 |  |
| benchmark | 基准测试 |  |
| instruction corpus | 指令语料 |  |
| Select-Instruct | 选择式指令生成 | SEvenLLM 中先选任务再生成指令数据 |
| task pool | 任务池 |  |
| understanding task | 理解任务 | 信息抽取、关系抽取等 |
| generation task | 生成任务 | 摘要、风险评估、响应建议等 |
| multitask instruction tuning | 多任务指令微调 |  |
| semantic similarity score | 语义相似度分数 | 生成式任务评价 |
| CTI-MCQ | CTI 多项选择题 | Cyber Threat Intelligence Multiple Choice Questions |
| CTI-RCM | CTI 根因映射 | Cyber Threat Intelligence Root Cause Mapping |
| CTI-VSP | CTI 漏洞严重性预测 | Cyber Threat Intelligence Vulnerability Severity Prediction |
| CTI-ATE | CTI 攻击技术抽取 | Cyber Threat Intelligence Attack Technique Extraction |
| CTI-TAA | CTI 威胁行为体归因 | Cyber Threat Intelligence Threat Actor Attribution |
| task taxonomy | 任务分类体系 | benchmark 设计语境 |
| multiple-choice question | 多项选择题 | MCQ |
| MCQ | 多项选择题 |  |
| evaluation harness | 评测框架 | CTIConnect 语境 |

## 8. 可信、可解释与不确定性

| 英文 | 建议译法 | 备注 |
|---|---|---|
| hallucination | 幻觉 | LLM 语境 |
| hallucination mitigation | 幻觉缓解 |  |
| evidence grounding | 证据 grounding / 证据锚定 | 可译为“证据支撑”但 grounding 更具体 |
| evidence chain | 证据链 |  |
| evidence sufficiency | 证据充分性 |  |
| evidence citation | 证据引用 |  |
| explainability | 可解释性 |  |
| interpretability | 可解释性 / 可理解性 | 视上下文 |
| uncertainty | 不确定性 |  |
| uncertainty estimation | 不确定性估计 |  |
| confidence | 置信度 |  |
| confidence calibration | 置信度校准 |  |
| overconfidence | 过度自信 | LLM/归因语境 |
| underconfidence | 信心不足 / 低置信正确 | 模型对正确答案置信度过低 |
| calibration | 校准 / 置信度校准 | 置信度是否反映真实正确概率 |
| consistency | 一致性 | LLM 多次输出稳定性 |
| consistency quantification | 一致性量化 | 重复调用稳定性评估 |
| unreliability | 不可靠性 | LLM-CTI 语境 |
| refusal | 拒答 | 证据不足时拒绝下结论 |
| safe abstention | 安全拒答 | 证据不足时明确说明不能回答 |
| correct refusal | 正确拒答 | 不可回答问题上的理想行为 |
| unanswerable handling | 不可回答处理 |  |
| opinion pool | 意见池 | 可信归因融合方法 |
| probability mass function | 概率质量函数 | PMF |
| PMF | 概率质量函数 |  |
| linear opinion pool | 线性意见池 |  |
| logarithmic opinion pool | 对数意见池 |  |
| attributor | 归因器 / 归因模块 | Opinion Pools 论文核心接口 |
| Pairing Aggregator | 成对聚合器 | 先成对对数意见池，再线性意见池 |
| monolithic attribution | 单体式归因 | 与模块化归因相对 |
| false flag | 假旗 / 误导性证据 | 威胁归因语境下可保留英文 |
| Brier score | Brier 分数 | 置信度校准指标 |
| expected calibration error | 期望校准误差 | ECE |
| ECE | 期望校准误差 | Expected Calibration Error |
| human-in-the-loop | 人在回路 |  |
| failure mode | 失败模式 |  |
| structural hallucination | 结构性幻觉 | 图 schema 不完整或图查询结果不足时产生的伪支撑 |
| spurious correlation | 虚假相关 | LLM-assisted CTI 风险 |
| conflicting evidence | 冲突证据 |  |
| temporal validity | 时间有效性 | CTI 时效性语境 |
| abductive reasoning | 溯因推理 | 威胁归因中从不完整证据推断最佳解释 |
| alias graph | 别名图 | CTIBench 中用于 actor 名称归一和评价 |
| related actor | 关联行为体 | CTIBench 中归因结果可标为 related |
| real-size report | 真实长度报告 | 区别于短句/段落评测 |
| prompt overfitting | prompt 过拟合 | few-shot 示例不能泛化到新报告 |
| world closing | 封闭世界约束 | 限定模型可选实体范围 |

## 9. 实验与评价指标

| 英文 | 建议译法 | 备注 |
|---|---|---|
| baseline | 基线方法 |  |
| ablation study | 消融实验 |  |
| case study | 案例研究 |  |
| hit@k | Hit@k | top-k 候选中是否包含正确答案 |
| precision | 精确率 |  |
| recall | 召回率 |  |
| F1-score | F1 分数 |  |
| accuracy | 准确率 |  |
| top-k accuracy | Top-k 准确率 |  |
| macro-F1 | 宏平均 F1 |  |
| micro-F1 | 微平均 F1 |  |
| technique-level evaluation | 技术级评价 |  |
| sub-technique-level evaluation | 子技术级评价 |  |
| evidence precision | 证据精确率 | 可自定义指标 |
| evidence recall | 证据召回率 | 可自定义指标 |
| attack step coverage | 攻击步骤覆盖率 | 可用于攻击链/摘要图评价 |
| graph match score | 图匹配分数 | 可用于 CTI 图和日志图对齐 |
| human evaluation | 人工评价 |  |
| annotation guideline | 标注指南 | 后续自建数据集需要 |
| information extraction | 信息抽取 | CTI 报告 -> 实体 |
| information generation | 信息生成 | APT 名称/描述 -> APT 画像 |

## 10. 暂不推荐的译法

| 原词 | 不推荐译法 | 推荐处理 |
|---|---|---|
| attribution | 属性 | 归因 |
| campaign | 战役 | 攻击活动 |
| tactic | 策略 | ATT&CK 语境译为战术 |
| technique | 技巧 | ATT&CK 语境译为技术 |
| procedure | 程序 | ATT&CK 语境译为过程 / 操作过程 |
| provenance graph | 来源图 | 溯源图 |
| hallucination | 错觉 | 幻觉 |
| agent | 代理 | 智能体 |
| evidence availability profile | 证据可用性画像 | Project05 新切口；描述当前案件可用/缺失的证据类型、粒度和可靠性 |
| evidence sufficiency scoring | 证据充分性评分 | 判断证据足以支持 technique / intent / campaign / actor 哪一层结论 |
| adaptive attribution granularity | 自适应归因粒度 | 证据不足时从 actor 降级到 campaign、intent 或 technique |
| refusal / abstention | 拒答 / 暂缓归因 | 证据不足、冲突或候选 actor 难区分时不强行输出 actor |
| over-attribution rate | 过度归因率 | 在证据不足时仍输出高置信 actor 的比例 |
| evidence path-enhanced reasoning | 证据路径增强推理 | TAA-EPLMR 语境；全文待获取，暂按高风险相关术语记录 |
| agentic attribution | 智能体式归因 | AURA 语境；多 agent 协作完成查询改写、检索、归因和解释 |
| justification synthesis | 解释合成 | AURA 语境；生成自然语言 attribution justification |
