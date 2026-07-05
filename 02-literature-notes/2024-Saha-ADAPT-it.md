# ADAPT it! Automating APT Campaign and Group Attribution by Leveraging and Linking Heterogeneous Files

## 1. 基本信息

- 英文题名：ADAPT it! Automating APT Campaign and Group Attribution by Leveraging and Linking Heterogeneous Files
- 中文译名：ADAPT it!：利用并关联异构文件自动化 APT 活动与组织归因
- 作者：Aakanksha Saha; Jorge Blasco; Lorenzo Cavallaro; Martina Lindorfer
- 年份：2024
- Venue：RAID 2024
- DOI / URL：10.1145/3678890.3678909；https://github.com/SecPriv/adapt
- Zotero key：S9NRGWLV
- 阅读日期：2026-07-05
- 阅读优先级：重点读
- 所属主题：APT Campaign Attribution / APT Group Attribution / Malware Samples / Heterogeneous Files / Clustering

## 2. 一句话总结

ADAPT 将 APT 归因拆成两层无监督聚类：先用文件类型相关特征和通用静态特征做 Intra-Clustering，识别 campaign-level clusters；再用跨文件类型的 pattern 和 infrastructure linking features 做 Inter-Clustering，把不同 campaign 的样本关联到同一 threat group。

## 3. 研究问题

- 论文要解决什么问题？
  - APT group 会长期执行多个 campaign，且 campaign 会跨平台、跨文件类型演化。
  - 安全厂商对 actor/campaign 的命名不统一，导致情报碎片化、关联延迟和误归因。
  - 现有 malware clustering 多关注 malware family/variant，APT attribution 研究又多局限 Windows executables，缺少同时覆盖 documents、executables、campaign 和 group 的方法。
- 为什么重要？
  - Project05 的归因不能只停在 report-level actor classification，还要考虑真实样本、campaign granularity 和跨 campaign linking。
  - ADAPT 提供了一个从 forensic artifact 出发的归因基线，与 APT-MMF 的 CTI report/IOC graph 路线互补。
- 和 CTI、ATT&CK、provenance、LLM/RAG 的关系是什么？
  - 它不做 CTI 文本理解或 LLM 推理。
  - 它使用恶意样本本身的静态特征、capability、string、pattern、infrastructure。
  - 它可为 CTI 报告生成、RAG evidence retrieval、Opinion Pools 或 LLM attribution explanation 提供样本侧证据。

## 4. 核心贡献

1. 数据贡献：构建 6,134 个异构 APT samples 的 group-labeled dataset，覆盖 92 个 APT groups、17 年跨度、多文件类型。
2. Campaign 数据贡献：构建 reference campaign-labeled dataset，包含 230 samples、22 campaigns、17 groups。
3. 方法贡献：提出两层聚类框架，分别处理 APT campaign attribution 和 APT group attribution。
4. 特征贡献：为 executables/documents 提取 file-specific features，并用 capabilities、strings、pattern、infrastructure 等 linking features 连接异构样本。
5. 开放贡献：公开 source code、features 和 labeled dataset。

## 5. 方法框架

### 输入

- APT malware samples；
- executables：PE、ELF、MachO；
- documents：Word、Excel、PowerPoint、RTF、PDF、HWP、ZIP 等；
- VirusTotal reports；
- AlienVault OTX pulses；
- Unit42、Mandiant threat reports；
- MITRE Campaigns / Groups 信息。

### 输出

- campaign-level clusters；
- group-level clusters；
- 对 unlabeled samples 的潜在 group attribution；
- cluster 支撑特征，如 shared linker、capabilities、file paths、URLs、certificate issuers、Bitcoin patterns。

### 两层流程

```text
APT malware samples
  -> file type identification
  -> feature extraction
      -> specific features: executable/document features
      -> generic features: capabilities + strings
      -> linking features: patterns + infrastructure
  -> feature transformation
  -> autoencoder latent representation
  -> agglomerative hierarchical clustering

Intra-Clustering:
  executable/document samples + specific/generic features
  -> campaign-level clusters

Inter-Clustering:
  all file types + linking features
  -> group-level clusters
```

### Campaign Attribution Features

| 特征类别 | 对象 | 说明 |
|---|---|---|
| EXF | executables | exported functions、configuration version 等；用 LIEF 提取 |
| DCF | documents | macros、obfuscated strings、document author、application language、suspicious keywords；用 oletools 提取 |
| CAP | generic | Malcat Community YARA rules 检测 capabilities，如 injection、persistence、privilege escalation、packers |
| STR | generic | FLOSS 提取 ASCII/UTF/stack/decoded strings，CountVectorizer 1-3 grams，最多 10,000 features |

### Group Attribution Linking Features

| 特征类别 | 说明 |
|---|---|
| PAT | 从 strings 中抽取 IP、URL、auth keys、API keys、embedded hashes、Bitcoin addresses、emails、Unix/Windows file paths |
| INF | 对 URL/IP 查询 Censys，补充 BGP prefix、ASN、country code、certificate fingerprint、issuer organization |

- PAT 使用 24 个正则表达式；6,134 个样本中 4,506 个样本至少有一种 pattern。
- INF 对 2,345 个样本可用。
- 对 raw linking features 使用 sentence transformer embedding。
- 最佳组合为 `multi-qa-MiniLM-L6-cos-v1`，similarity threshold = 0.8。
- 去除出现在超过 75% 样本中的过常见特征。

### Clustering

- 使用 agglomerative hierarchical clustering。
- 用 autoencoder 压缩高维特征：
  - input layer；
  - hidden layers：32 和 16 units；
  - ReLU；
  - sigmoid output。
- 用 SSE 和 elbow method 选择 cluster 数。
- 也尝试过 HDBSCAN 和 K-means，结果相近。
- 对特征不足样本使用 analyst-defined threshold 排除，以减少 singleton clusters 或 misclustering。

## 6. 数据集与实验

### Group-labeled Dataset

- 初始来源：
  - AlienVault DirectConnect API 查询 APT-related pulses；
  - Unit42 和 Mandiant 2022-01 到 2023-03 报告。
- 初始数据：
  - 5,990 unique SHA256 hashes，至少 172 threat group tags；
  - 额外从 Unit42/Mandiant 获得 465 hashes；
  - 从 VirusTotal 下载 6,455 samples。
- 重标注：
  - 2,260 samples 有多个 APT names/aliases；
  - 239 samples 有 5 个或更多 group names；
  - 使用 Malpedia 和 MITRE 统一 label；
  - 对 Malpedia/MITRE 分歧样本由两名研究者查 Unit42/Mandiant 报告裁定；
  - 删除 321 NotAPT samples；
  - 保留 44 unlabeled samples。
- 最终规模：
  - 6,134 samples；
  - 92 APT groups；
  - median sample count per group = 24。

### File Type Distribution

- executables：3,603 samples，占 58.73%。
  - PE EXE：2,516；
  - PE DLL：1,019；
  - ELF：39；
  - MachO：29。
- documents：1,611 samples，占 26.26%。
  - OOXML/Word/RTF/Excel/ZIP/PDF/HWP/PowerPoint 等。
- 其他：
  - APK、LNK、scripts、text、HTML、Flash、RAR 等；
  - 152 unknown formats。

### Campaign-labeled Reference Dataset

- 基于 MITRE APT Campaign Framework 和 Mandiant 报告补充。
- 最终：
  - 230 samples；
  - 22 campaigns；
  - 17 groups；
  - 142 executable binaries；
  - 62 documents。

### 主要结果

| 任务 | 样本类型 | Clusters | Precision | Recall | F1 | SSE | SC |
|---|---|---:|---:|---:|---:|---:|---:|
| Campaign attribution | executables | 18 | 0.93 | 0.92 | 0.91 | 1.45 | 0.50 |
| Campaign attribution | documents | 9 | 0.95 | 0.94 | 0.92 | 0.72 | 0.36 |
| Group attribution | all/linking | 15 | 0.92 | 0.89 | 0.89 | 2.70 | 0.41 |

### Feature Importance

Executables：

| Feature Category | # Features | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| EXF | 22,042 | 0.85 | 0.72 | 0.70 |
| EXF + CAP | 22,099 | 0.88 | 0.87 | 0.85 |
| EXF + STR | 77,697 | 0.91 | 0.90 | 0.89 |
| EXF + CAP + STR | 77,759 | 0.93 | 0.92 | 0.91 |

Documents：

| Feature Category | # Features | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| DCF | 85 | 0.88 | 0.84 | 0.79 |
| DCF + CAP | 142 | 0.93 | 0.93 | 0.92 |
| DCF + STR | 44,035 | 0.92 | 0.91 | 0.91 |
| DCF + CAP + STR | 44,097 | 0.95 | 0.94 | 0.92 |

### Case Studies

- Gamaredon 2017 / 2022 campaigns：
  - ADAPT Intra-Clustering 分别聚到 C1 和 C2；
  - 支撑特征包括 AdjustTokenPrivileges、MSVC linker、temporary file pattern、RIPEMD160、GetKeyState、batch script pattern、Russian language naming convention。
- APT29：
  - WellMess / WellMail 跨 ELF 和 PE 被 Inter-Clustering 聚到同一 group；
  - 支撑特征包括 Golang module file paths、mutex、curve25519 crypto library、MD5 patterns。
- Lazarus：
  - JMTTrade 和 CelasTradePro 被聚到同一 group；
  - 支撑特征包括 Bitcoin pattern、URLs、email addresses、certificate issuer organization。
- Unlabeled samples：
  - ADAPT 将 44 个 unlabeled samples 中 9 个关联到已知 APT groups；
  - 其中部分通过 VirusTotal community comments 或公开信息得到佐证。

## 7. 关键知识点

### 概念

- Threat campaign：由同一或多个 threat source 组织的一组协调攻击事件，通常按时间顺序展开，有特定目标、工具和方法。
- Threat group：组织并执行多个 campaigns 的 actor/entity。
- Intra-Clustering：在 executable 或 document 域内根据 campaign-level malicious characteristics 聚类。
- Inter-Clustering：跨文件类型使用 linking features 连接不同 campaigns 到同一 group。
- Linking features：能跨样本、跨 campaign、跨文件类型连接 actor 操作习惯或基础设施的特征。

### 和 APT-MMF 的差异

```text
APT-MMF:
  CTI reports + IOC graph
  -> supervised actor classification
  -> report-level / IOC-level evidence

ADAPT:
  malware samples + heterogeneous file features
  -> unsupervised campaign/group clustering
  -> sample-level / feature-level evidence
```

### 和 Project05 主线的关系

```text
日志侧 provenance evidence:
  THREATRACE / PROGRAPHER / Kairos / DEPCOMM

CTI 报告侧 graph attribution:
  APT-MMF

样本侧 campaign/group linking:
  ADAPT it!

可信融合:
  Opinion Pools + LLM/RAG explanation
```

## 8. 优点

- 明确区分 campaign attribution 和 group attribution，比单一 actor label 更符合真实 APT 分析流程。
- 覆盖 executables 和 documents，而不是只关注 Windows PE。
- 使用轻量静态特征，适合快速 triage 和 forensic prioritization。
- 提供公开 artifact，数据集和特征对后续研究很有价值。
- 对 false flag/code reuse、concept drift、dataset representativeness 有清醒讨论。

## 9. 局限

- 主要依赖静态特征，面对 packing、obfuscation、embedded content 时会受限。
- document pipeline 当前未充分利用视觉特征，例如 Operation Dream Job 中 Boeing image 这类线索。
- INF features 只覆盖 38.22% 样本，group attribution 在缺少 infrastructure evidence 时容易依赖常见路径并错聚类。
- 共享 offensive tools、共享基础设施和 Cobalt Strike 等会导致 unrelated groups 被聚到一起。
- 需要 analyst-defined threshold 排除特征不足样本，说明完全自动化仍有限。
- 对 adversarial manipulation / false flag 只做初步分析，系统鲁棒性仍是未来工作。
- 无监督聚类评价依赖 reference dataset，真实场景中的 ground truth 仍难获得。

## 10. 对我选题的启发

- 可以直接借鉴：
  - campaign-level 与 group-level 分层归因；
  - linking features 作为跨证据源关联的核心；
  - artifact-level evidence 可与 report-level CTI evidence 互补。
- 可以改进：
  - 把 ADAPT 的 sample-level linking features 与 APT-MMF 的 report-IOC graph 对齐；
  - 用 LLM 将 cluster supporting features 解释为 campaign objective、ATT&CK tactic/technique 或 intent；
  - 为 cluster attribution 加 evidence sufficiency 和 false-flag risk scoring；
  - 将 provenance graph 中的文件/进程/网络证据接入 sample/IOC linking。
- 可以作为 baseline：
  - heterogeneous file-based APT campaign/group attribution baseline；
  - 和 APT-MMF 一起构成“CTI 报告侧 + 样本侧”的自动化归因对比。

## 11. 可转化的研究问题

1. 如何把 ADAPT 的 sample cluster evidence 与 APT-MMF 的 CTI report-IOC graph 融合为统一 attribution evidence graph？
2. 如何用 LLM 对 ADAPT cluster 的支撑特征生成可审计解释，而不是只输出 cluster id？
3. 如何判断 sample-level linking features 是强证据、弱证据，还是可能被 false flag 操纵？
4. 如何把日志侧 provenance evidence 连接到 sample-level campaign cluster 和 CTI report-level actor evidence？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| APT-MMF | APT-MMF 从 CTI 报告/IOC 图做 actor classification；ADAPT 从真实样本特征做 campaign/group clustering。 |
| Opinion Pools | ADAPT 可作为 sample/artifact attributor，与 CTI/IOC graph、LLM/RAG、provenance attributors 融合。 |
| High Stakes, Low Certainty | ADAPT 讨论 shared tools、code reuse、false flags，与证据可靠性问题高度一致。 |
| THREATRACE / PROGRAPHER / Kairos / DEPCOMM | 这些方法提供日志侧 evidence；ADAPT 提供样本侧 evidence。 |
| TTPXHunter / TechniqueRAG | 这些抽取 CTI 文本中的 TTP；ADAPT 直接从恶意样本静态特征聚类 campaign/group。 |
| APT attribution survey | ADAPT 是 automated APT attribution 中样本侧、多文件类型、双层归因的重要代表。 |

## 13. 论文写作可引用句式

- ADAPT demonstrates that APT attribution should distinguish campaign-level clustering from group-level attribution, since a single actor may operate multiple evolving campaigns.
- Heterogeneous file artifacts provide complementary evidence to CTI reports, especially when executable, document, infrastructure, and pattern-based features can be linked across campaigns.
- However, sample-level clustering remains vulnerable to obfuscation, shared tooling, false flags, and insufficient evidence, motivating uncertainty-aware fusion with report-level and provenance-level evidence.

## 14. 我的批注与疑问

- 这篇读完后，主线基本闭合：文本/报告、IOC 图、样本文件、日志 provenance、RAG/KG、可信评估都已经有代表文献。
- ADAPT 的最大价值是提醒我：actor attribution 之前还有 campaign attribution，不能把所有样本直接推到 actor 标签。
- 它和 APT-MMF 组合起来非常适合做硕士论文的相关工作对照：一个监督分类，一个无监督聚类；一个报告/IOC 图，一个样本/linking features。
- 对 Project05 来说，后续选题应优先考虑“多源证据融合 + 可审计解释 + 证据不足拒答”，而不是再做一个孤立分类器。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是，作为 heterogeneous file-based campaign/group attribution 核心基线进入主线。
