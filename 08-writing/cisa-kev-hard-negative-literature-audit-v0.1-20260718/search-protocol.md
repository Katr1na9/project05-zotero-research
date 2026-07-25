# CISA KEV 作为 observation-compiler null/hard-negative 的快速证据审查协议

日期：2026-07-18  
审查类型：目标明确的 rapid evidence review（非效果量 meta-analysis）  
冻结时间：首次外部检索前

## 1. 研究问题

### RQ1：官方语义

CISA KEV 的条目和字段究竟声明什么？它们是否记录具体案件中观察到的主机、进程、文件、网络或 provenance 事件，还是记录漏洞类型及其“已在野利用”状态？

### RQ2：直接学术先例

是否有同行评审论文、权威预印本或官方技术报告，明确将 CISA KEV 条目用于以下任一任务：

1. 案件级安全事件/observation extraction 的 `null`；
2. 来源支撑/自然语言蕴含意义上的 `hard negative`；
3. 漏洞利用预测的 positive、negative 或 unlabeled 标签。

### RQ3：方法学有效性

若没有直接先例，PU learning、开放世界知识图谱、事件抽取/关系抽取中的负样本构造原则，是否允许把 KEV 条目解释为：

- “真实世界没有发生利用”的负样本；
- “该文本不蕴含一个具体案件事件”的 contract-negative；
- 仅用于小比例对比/挑战集的 lexically hard non-entailing example。

## 2. 预注册判定

| 证据情形 | 判定 |
|---|---|
| 有直接、可复现论文将 KEV 用于同一案件级 observation-null 任务，并报告防 shortcut/标签噪声措施 | 可有条件保留为 train-null 候选 |
| 只有漏洞利用预测论文把 KEV 当 positive 或把 non-KEV 当 negative/unlabeled | 不构成案件级 null 的直接背书 |
| 官方语义只支持“漏洞存在且有在野利用证据”，不支持“本案件没有事件” | 禁止称 benign/null ground truth |
| PU/open-world 文献表明未标注不等于负例 | 禁止用目录缺失或未提及推断未发生 |
| NLI/IE 文献支持同词汇但不蕴含目标关系的 hard negative，且 Project05 明确标签为 contract-negative | 最多允许小比例辅助挑战样本，不得承担正式 train-null 数量 Gate |
| 找不到直接背书且存在模态 shortcut 风险 | 从正式训练 null 来源中移除；可保留为独立诊断集 |

## 3. 数据库与检索式

检索日期：2026-07-18。检索范围以英文为主，不限起始年份，截至检索日。

### A. 官方规范

域：`cisa.gov`, `nist.gov`, `cve.org`, `github.com/cisagov`

- `CISA Known Exploited Vulnerabilities catalog criteria evidence active exploitation`
- `Binding Operational Directive 22-01 known exploited vulnerabilities definition`
- `CISA KEV JSON schema shortDescription knownRansomwareCampaignUse`

### B. KEV 的学术机器学习用法

库/域：Semantic Scholar、arXiv、ACM Digital Library、IEEE Xplore、USENIX、Springer、ScienceDirect

- `"CISA KEV" "negative samples"`
- `"Known Exploited Vulnerabilities" "hard negative"`
- `"CISA KEV" machine learning exploit prediction labels`
- `"Known Exploited Vulnerabilities catalog" non-KEV negative unlabeled label noise`
- `vulnerability exploitation prediction positive unlabeled KEV`

### C. 方法学原则

库/域：ACM、IEEE、ACL Anthology、arXiv、Springer、Semantic Scholar

- `positive unlabeled learning cybersecurity vulnerability exploit prediction`
- `open world knowledge graph negative sampling unobserved not false`
- `event extraction hard negative non-entailing lexically similar`
- `relation extraction negative sampling false negatives distant supervision`
- `intrusion detection unlabeled traffic is not benign negative label noise`

## 4. 纳入与排除

纳入：

- CISA/NIST/CVE 官方规范、数据字典、指令；
- 明确说明 KEV 标签角色的同行评审论文或可核验预印本；
- 与 PU/open-world/IE 负样本语义直接相关的基础或综述论文；
- 能核验标题、作者、年份、venue/DOI/URL 及相关段落。

排除：

- 只把 KEV 当新闻列表、未说明标签语义的博客；
- 没有全文/摘要证据支持所声称用法的二手转述；
- 将 CVE 漏洞级分类与主机事件级抽取混为一谈的材料；
- 仅讨论 LLM 输出格式、与负样本语义无关的论文。

## 5. 证据分级

| 等级 | 含义 |
|---|---|
| A | 官方规范或同任务、同行评审、方法细节完整的直接证据 |
| B | 相邻任务的高质量同行评审证据，可支持原则但不能直接外推 |
| C | 预印本、系统说明或间接方法证据 |
| D | 搜索摘要/二手材料，只用于定位，不用于最终裁决 |

## 6. 防止结论漂移

1. `KEV-listed` 不能被解释为“某个 Project05 案件发生了该事件”。
2. `not in KEV` 不能被解释为“没有在野利用”。
3. `shortDescription` 没写案件事件不能自动推出真实世界未发生事件。
4. 若最终允许使用，只能以任务合同定义的 `non-entailing contract-negative` 命名，不能写 benign、normal 或真实未发生。
5. 没有直接文献背书时，默认 fail-closed，不以单人意见补足外部效度。
