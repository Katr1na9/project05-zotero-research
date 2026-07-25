# LLM Evidence-safe Semantic Editor v0.8：L2 metadata-only 容量与 test-family 调研 v0.1

**日期**：2026-07-22

**权威基线**：feat/llm-editor-v0.8 @ 266313f

**状态**：capacity_audited_gate_failed
**机器审计**：

- llm-editor-v0.8-l2-capacity-audit-metadata-only-v0.1-20260722.json
- llm-editor-v0.8-l2-test-family-candidates-metadata-only-v0.1-20260722.json

## 1. 裁断

本轮完成了两项授权工作：

1. 用已提交审计、source manifest、Git tree 和归档目录元数据盘点现有来源的 lineage、sample-kind 与 modality 容量；
2. 从官方来源元数据中筛选独立 test-family 候选。

结果不是 L2 通过：

- train 虽有 4 个候选 family，但 BETH 在文件级只有 1 个单主机 artifact；Atomic、CAM-LDS、SOCBED 的目录或运行数仍只是 lineage 候选，独立性未核；
- development 虽有 2 个候选 family，但 Loghub Linux 只有 1 个 archive member；Zeek 的测试目录不能自动当作独立 provenance 事件；
- 历史 1,500 pairs 只能作为旧合同 proxy，不能继承为 v0.8 样本；
- pointer_absent、pointer_ambiguous、authority_injection、conflict_group 和 duplicate_retention 的可达量仍未知；
- SI-LLM-005 未关闭，observed、derived、reported、hypothesized、unknown 五类 trusted modality 均不能计数；
- SI-LLM-007 未关闭，polarity supervision 继续固定为 0；
- 新找到的 test family 只是 metadata candidate，尚未逐族批准、物化或冻结。

因此，train、development、test 三个配额均为 false，baseline 与微调继续禁止。

## 2. 审计方法

统计单位遵循 L2 合同：

| 单位 | 本轮如何处理 |
|---|---|
| corpus family | 只按独立数据集/采集工程计数 |
| lineage | 文件、目录、运行号或日期只能作为候选 grouping key |
| row / packet / prompt view | 不计独立重复 |

本轮只读取：

- 已提交 JSON/CSV 审计中的计数、revision、license 和 hash；
- Git tree 的 path、blob SHA 和 size；
- ZIP central directory 的 member name、size、CRC；
- TAR header 的 member name 和 size；
- 官方数据集页面/API 的来源身份、许可、版本、文件名、大小与 checksum。

没有读取：

- 日志、CTI 或 CSV record 内容；
- archive member 内容；
- 历史 pair payload；
- private gold；
- model generation。

## 3. 当前来源容量

| Family | 候选 split | metadata 可见结构 | lineage 裁断 | v0.8 sample-kind / modality |
|---|---|---|---|---|
| Atomic Red Team | train | 356 manifest entries；341 technique directories | technique 是剧本分类，不是独立执行；未核 | 仅有旧合同 150/150 proxy；trusted modality 未核 |
| CAM-LDS filtered | train | 17,242 archive members；4,744 steps members；883 step directories | step 可作 grouping 候选，但共享 sequence/host/time 未核 | 仅有旧合同 150/150 proxy；trusted modality 未核 |
| SOCBED Winlogbeat | train | 40 Winlogbeat files；4 host/config directories；10 run suffixes | 同一 suffix 的 4 文件最多算 1 run；独立性未核 | 仅有旧合同 150/150 proxy；trusted modality 未核 |
| BETH process events | train | 1 file；1 host；历史 409,931 rows | 文件级只有 1 lineage；明确不满足每族 ≥4 | 仅有旧合同 150/150 proxy；trusted modality 未核 |
| Loghub Linux | development | 1 archive member：Linux.log | 文件级只有 1 lineage；明确不满足每族 ≥4 | 仅有旧合同 75/75 proxy；trusted modality 未核 |
| Zeek non-PCAP tests | development | 1,119 manifest entries；915 可唯一回指路径；620 parent directories | 软件测试目录不是独立采集事件；未核 | 仅有旧合同 75/75 proxy；trusted modality 未核 |
| Splunk manifests | inactive | 仅 2 条历史 exclusion-passed records | 不计任何 active family quota | 无历史 pair；不计数 |

### 3.1 伪重复风险

- BETH 的 409,931 rows 仍然来自一个单主机文件，不能把 row 数当 lineage 数。
- SOCBED 的 40 个 Winlogbeat 文件由 10 个 run suffix × 4 个 host/config 组成；同一 suffix 的四份文件应优先视为一个 run cluster。
- CAM-LDS 的 step directory 可能嵌套在同一 sequence、主机状态和时间窗下；883 不是已验证独立样本量。
- Zeek 的大量 baseline 文件来自软件测试体系，重复 blob 和共享 fixture 很常见。
- Atomic 的 technique/YAML 数量测量的是程序库覆盖，不是安全事件复现次数。

experimental-design 的 replication 原则直接影响了本裁断：技术重复只能提高一个 lineage 内的覆盖，不能增加独立重复。

## 4. Sample-kind 与 modality 结论

历史 data-gate 只能证明旧合同下存在：

- train：600 supported + 600 unsupported；
- development：150 supported + 150 unsupported。

这些计数不能自动映射到 v0.8：

| v0.8 项 | 当前状态 |
|---|---|
| candidate_supported / candidate_unsupported | historical_proxy_only_not_inheritable |
| pointer_absent / pointer_ambiguous | unknown |
| authority_injection | unknown |
| conflict_group / duplicate_retention | unknown |
| candidate-q | blocked by SI-LLM-002 |
| polarity supervision | blocked by SI-LLM-007 |
| formal temporal normalization | contract/gold missing |

历史 modality_audit 的 1,500/1,500 也不能继承，因为旧 transport modality 不等于 v0.8 trusted modality。SI-LLM-005 未关闭前，五类 trusted modality 的容量全部保持 null。

## 5. 独立 test-family 候选

### 5.1 Metadata candidate A：CMU CERT Insider Threat Test Dataset

官方来源：

- [CMU Figshare record](https://api.figshare.com/v2/articles/12841247)
- [DOI 10.1184/R1/12841247.v1](https://doi.org/10.1184/R1/12841247.v1)

元数据：

- CC BY 4.0；
- Figshare article 12841247，version 1；
- 10 个 release archive，均有 file ID、size 和 MD5；
- 官方描述明确说明数据是合成 background + synthetic malicious actor 活动，且后续 release 通常是前序生成能力的 superset；
- answers.tar.bz2 是独立 answer key。

判定：metadata_candidate_not_approved。

必要条件：

1. 只选一个 release，禁止混合 superseding releases；
2. answers.tar.bz2 物理排除，除非未来另行批准 private-gold 用途；
3. lineage 必须按 scenario/user/time 构造，archive 和 row 数不算重复；
4. scenario、malicious-user 和答案字段不得进入模型输入或路径提示；
5. 论文必须标为 synthetic，不能外推真实企业；
6. nested notice、exclusion、duplicate 和 sample-kind 容量审计另行通过。

### 5.2 Metadata candidate B：IoT-23 v1.0.0

官方来源：

- [Zenodo record 4743746](https://zenodo.org/api/records/4743746)
- [Stratosphere IoT-23 page](https://www.stratosphereips.org/datasets-iot23)
- [DOI 10.5281/zenodo.4743746](https://doi.org/10.5281/zenodo.4743746)

元数据：

- CC BY 4.0；
- version 1.0.0；
- full archive 21,510,801,277 bytes，MD5 7132e603f9750b8580b6cebdbcd43e9c；
- 23 captures：20 malware、3 benign；
- 官方页面提供只含 labeled flows、不含 PCAP 的 lighter variant。

判定：metadata_candidate_not_approved。

必要条件：

1. 只使用 non-PCAP flow/log；
2. 若采用 lighter archive，获取后必须自己冻结 checksum；当前 Zenodo checksum 只覆盖 full archive；
3. 一次 capture 最多贡献一个 lineage group，flow 行不增加重复数；
4. malware、device、scenario 和 label 字段必须从 model view 和路径提示中剥离；
5. label spreadsheet 或 labeled suffix 不得作为模型输入；
6. 由于 development 使用 Zeek test logs，必须单独报告 Zeek-format correlation；格式相同不等于来源重叠；
7. nested notice、protected exclusion 和 near-duplicate scan 必须先通过。

### 5.3 条件储备：LANL Unified Host and Network Dataset

官方来源：

- [LANL dataset page](https://csr.lanl.gov/data/2017/)
- [dataset publication DOI](https://doi.org/10.1142/9781786345646_001)

优点：

- 官方页面明确作出最大程度的 copyright/related-rights waiver；
- 约 90 天企业 host + network events；
- 页面列出 90 个 WLS 日文件和 89 个 Netflow 日文件；
- publisher 与现有六族独立。

阻塞：

- 数据端点需要登记，HEAD 请求返回 HTTP 401；
- 当前无法取得每个日文件的不可变 checksum manifest；
- 90 天属于一个企业，不能写成 90 个独立企业；
- 因而只列为 conditional reserve，不计两个 metadata candidate。

## 6. 否决与暂缓

| Source | 裁断 | 主要理由 |
|---|---|---|
| EVTX-ATTACK-SAMPLES | hard reject | TTP/path 标签；部分文件明确由 Atomic Red Team 产生；与 train generation 重叠；13 tactic directories 不是 lineage |
| ADFA-LD/WD | reject | custom academic-only、commercial prohibited；无检查到的 immutable dataset checksum；模态过窄 |
| TON_IoT | hold | custom academic-use license；缺少统一 immutable revision/checksum；异构子集不能方便地算一个 family |
| HAI | reject | GitHub metadata 未声明 SPDX license |
| CISA Vulnrichment | reject for test | CVE enrichment 不是 case evidence；与既有 CISA KEV feasibility 有同 publisher/record-overlap 风险 |
| AIT AECID aggregate | reject | 与 CAM-LDS train 不独立；底层 terms 混合 |
| OpenStack Nova logs | reject | routine rows 多但缺乏可辩护 pointer/object relation；单 family 伪重复 |
| Omer EVTX fixture | reject | 单一 parser fixture，不能满足每族 ≥4 lineages |

## 7. Gate

| Gate | 结果 |
|---|---|
| metadata capacity audit | completed |
| ≥2 独立 test-family metadata candidates | completed：CERT + IoT-23 |
| test family 正式批准 | false |
| train lineage quota | false |
| development lineage quota | false |
| test lineage/row quota | false |
| sample-kind quota | false |
| trusted modality quota | false |
| L2 Gate | false |
| baseline authorized | false |
| fine-tuning authorized | false |

下一步必须另行授权和决策：是否把 CERT、IoT-23 中任一来源写入待审 source catalog。即使两者获批，仍需先解决 BETH/Loghub 的 lineage 缺口、SI-LLM-005 modality 计数和 v0.8 sample-kind 容量，不能直接进入 payload、baseline 或微调。

## 8. 调研限制

这是面向 source gate 的 targeted search，不是覆盖所有安全数据集的系统综述。公开页面可以确认身份、许可和版本，但不能证明：

- payload 内存在足够的 pointer-recoverable claim；
- labels 能完全从 model view 剥离；
- test 与模型预训练语料无污染；
- scenario/day/user 真正满足独立性；
- 五类 trusted modality 均能达到最低配额。

因此所有候选都保持 candidate 或 reserve，而不是 approved。
