# A Multi-Source Feature Fusion-Based Knowledge Graph Construction from Cyber Threat Intelligence to Facilitate APT Attribution in IDS

## 基本信息

- 作者：To Thi My Au, Khanh-Khoa Ngo, Van-Hau Pham, Phan The Duy
- 年份：2025
- 类型：conference paper / IEEE 线索
- 本地 PDF：`../07-zotero-exports/pdfs_20260706_deep/Au_2025_Multi_Source_Feature_Fusion_HKG_APT_Attribution_IDS.pdf`
- 本地抽取文本：`../07-zotero-exports/pdf_text_20260706_deep/Au_2025_Multi_Source_Feature_Fusion_HKG_APT_Attribution_IDS.txt`
- 当前状态：全文已获取并精读。

## 它在研究什么

该文提出一种从 Cyber Threat Intelligence 构建 heterogeneous knowledge graph 的 APT attribution 方法，目标是把 IDS 的低层告警与高层 APT 行为特征关联起来，从而辅助识别攻击背后的 threat actor。

核心问题是：

```text
OSCTI reports 非结构化、异构、体量大
  -> 难以自动组织为可用于归因的知识表示
  -> 构建 HKG 并学习 report node 表示
  -> 对 APT group 进行归因分类
```

## 方法框架

该文方法可以概括为：

```text
APT reports + MITRE ATT&CK + CVE + AvClass2 + VirusTotal
  -> 提取 report / IOC / tactic / technique / malware / vulnerability / domain / IP / URL 等节点
  -> 构建 STIX 风格 HKG
  -> 为节点生成三类特征
       attribute features
       textual features
       graph structural features
  -> multi-level attention
       IOC type-level attention
       neighbor node-level attention
       metapath-level attention
  -> report embedding
  -> APT group classification
```

### 1. 多源 CTI 与 HKG

数据来源包括：

- APTNotes；
- Trellix、Kaspersky 等厂商报告；
- MITRE ATT&CK；
- CVE；
- AvClass2；
- VirusTotal。

HKG 的实体包括至少 11 类 STIX/IOC 类型：

- tactics；
- techniques；
- malware；
- vulnerabilities；
- domains；
- file names；
- IPs；
- URLs；
- file paths；
- registries；
- emails。

关系包括 Include、Resolve、Association、Homology 等。

### 2. 多模态节点特征

论文明确融合三类特征：

1. attribute features  
   对 IP、ATT&CK ID、CVE ID 等 identifier-like attributes 进行结构编码；对非 identifier 类属性做 ordinal encoding；最终形成 64 维属性特征。

2. textual features  
   使用 BERT 对 technique description、domain name 等文本属性编码，取最后隐藏层均值并通过全连接层得到 64 维文本特征。

3. graph structural features  
   使用 node2vec 将 HKG 转为同构图后学习结构嵌入，得到 128 维图结构特征。

三类特征拼接得到节点综合表示。

### 3. 多层注意力

该文提出 three-level attention：

- IOC type-level attention；
- neighbor node-level attention；
- metapath-level attention。

metapath 覆盖 report-file-report、report-malware-report、report-domain-report、report-IP-malware-report、report-IP-domain-IP-report 等路径，用于学习不同语义层面的 report 关联。

## 数据与实验

论文构建了一个 HKG dataset：

- 9,740 nodes；
- 15,099 relationships；
- 25 APT groups；
- report nodes 按 6:2:2 划分 train / test / validation。

研究问题包括：

- 不同 metapath set 对归因性能的影响；
- attribute / textual / graph structural features 的贡献；
- IOC type-level、neighbor node-level、metapath-level attention 的贡献；
- 节点规模增长时的计算开销；
- 与其他 GNN 方法的性能比较。

## 关键结果

### Metapath 消融

完整 MPL1+MPL2+MPL3+MPL4 时：

- Micro-F1：0.7568；
- Macro-F1：0.6721。

### 多层注意力消融

完整 ITL + NNL + ML 时：

- Micro-F1：0.7568；
- Macro-F1：0.6721。

### 与 GNN baseline 比较

| Method | Micro-F1 | Macro-F1 |
|---|---:|---:|
| HAN | 0.5882 | 0.3565 |
| RGCN DBLP | 0.6471 | 0.5071 |
| GAT | 0.6667 | 0.5944 |
| GCN | 0.5071 | 0.4583 |
| Ours | 0.7568 | 0.6721 |

## 作者承认的限制与未来工作

论文未来工作包括：

1. 与更多可用 APT attribution 方法进行统计比较；
2. 集成 LLM 进一步提升 CTI report 语义理解；
3. 发展 Agentic AI 系统，自动化实时多源 CTI 数据处理流程，包括数据收集、增强、实体抽取和清洗；
4. 结合 RAG 与 LLM 改进 IOC detection 并持续更新 threat knowledge base；
5. 用 LLM 增强 attribution decision explainability；
6. 提升系统对 noisy data 的韧性；
7. 改善 human-system interaction；
8. 解决依赖输入报告质量、数据集多样性不足等问题。

## 对 Project05 的撞题影响

这是红色风险项。

它直接覆盖：

- multi-source CTI；
- heterogeneous knowledge graph construction；
- multi-modal feature fusion；
- attribute + BERT text + node2vec graph structure；
- multi-level attention；
- metapath-based report representation；
- APT group attribution；
- IDS 场景中的 APT attribution 支撑。

因此 Project05 不能写：

- 多源特征融合知识图谱用于 APT 归因；
- CTI HKG 构建并提升 APT attribution；
- BERT + node2vec + attribute feature fusion；
- metapath attention APT report embedding；
- 用 HKG 支撑 IDS 中的 APT attribution。

这篇进一步坐实 `collision-matrix-final-20260706.md` 的判断：`多源证据融合 / KG / GNN / HKG / metapath / feature fusion` 都不应作为 Project05 的核心。

## Project05 可避让空间

这篇仍没有覆盖 Project05 当前窄题的关键控制层：

1. 没有判断当前证据是否足以支持 actor-level attribution；
2. 没有归因粒度门控；
3. 没有证据不足时的 refusal / abstention 输出机制；
4. 没有 unknown actor / open-set 输出；
5. 没有 false flag / mimicry 风险触发的降级归因；
6. 没有缺失证据清单生成；
7. LLM 只出现在 future work，不是当前方法。

因此 Project05 应当把这类 HKG attribution model 视为上游候选归因系统，把它的输出作为输入：

```text
HKG / GNN / multi-source attribution model
  -> candidate actor + evidence/path/feature support
  -> Project05 evidence sufficiency profile
  -> attribution granularity gate
  -> actor / campaign / technique / unknown / refusal
  -> LLM controlled explanation
```

## 对专利 v0.2 的影响

专利 v0.2 中应避免把“多源 CTI 特征融合”写入独立权利要求的核心必要步骤。更稳妥的表述是：

> 获取由既有安全分析系统、归因模型、证据融合模型或人工分析过程产生的候选归因结果及其证据账本。

这样可以把该文方法作为输入来源之一，而不是 Project05 试图重新保护它。

## 风险等级

红色。

原因：该文全文直接覆盖了 Project05 原始宽题中的 `multi-source feature fusion + knowledge graph + APT attribution`，并且给出了完整模型、数据集和实验结果。

