# Project05 论文引文审计 v0.1

日期：2026-07-11
Zotero collection：攻击溯源与意图感知
导出：`paper-main-references-v0.3.bib`，88 entries

## 1. 审计规则

1. 引文必须支撑邻近句子的具体工作范围，不能只因题名相关而引用。
2. 领域原始论文优先于综述；预印本明确保留其版本属性。
3. 未获得全文的 APTChaser 只用于“基于攻击技术建模进行归因”的高层描述，不用于方法细节或性能主张。
4. “现有工作尚未共同覆盖本文闭环”属于基于已精读文献的综合判断，不伪装成单篇文献的直接结论。
5. 本项目自身实验数字由仓库结果文件支撑，不用外部文献替代。

## 2. 主张-引文对应

| 正文主张 | Zotero key | 支撑等级 | 备注 |
|---|---|---|---|
| CTI 查询图与审计图对齐 | `milajerdi_poirot_2019` | direct | 全文精读；DOI 已补入导出快照 |
| 从报告抽取攻击行为 | `kiavash_satvat_extractor_2021` | direct | 全文与 DOI 可用 |
| technique knowledge graph 构建 | `zhenyuan_li_attackg_2022` | direct | 全文与 DOI 可用 |
| evidence-path LLM attribution | `xiao_taa-eplmr_2025` | direct | 已补入 Zotero；全文精读 |
| multi-agent knowledge-enhanced attribution | `rani_aura_2025` | direct | arXiv；全文精读 |
| heterogeneous CTI + CTGAN attribution | `cai_apt-att_2025` | direct | Computer Networks；全文精读 |
| attack-technique modeling attribution | `zhang_aptchaser_2025` | bounded | 摘要级，只作高层定位 |
| multimodal LLM attack-graph construction | `zhang_mm-attackg_2025` | direct | arXiv；全文精读 |
| multi-source LLM APT attribution framework | `alshamrani_llm-based_2026` | direct | MENACOMM；已获得正文 |
| LLM-agent threat investigation benchmark | `yiran_wu_excytin-bench_2025` | direct | arXiv/ICML 2026 版本信息提交前复核 |
| active feature acquisition formulation | `aronsson_survey_2025` | synthesis | 综述作为理论谱系入口 |
| non-greedy cost-tradeoff acquisition | `noauthor_nocta_2025` | direct | 本地 BibTeX 已补作者；Zotero 父记录仍需元数据清理 |
| RL-based registry investigation | `ghanem_leveraging_2026` | direct | Scientific Reports；已补入 Zotero |

## 3. 本轮 Zotero 修复

补入规范父级记录：TAA-EPLMR、AURA、APT-ATT、MM-AttacKG、LLMAPT 和 WinRegRL，共 6 条；Zotero 可导出记录由 82 增至 88。导入文件为 `07-zotero-exports/missing-project05-core-20260711.bib`。

## 4. 提交前仍需处理

- 用目标期刊 CSL 重新生成参考文献，不手工维护编号。
- 复核 ExCyTIn-Bench 的最终发表状态与卷页。
- 为 NOCTA 的 Zotero 父记录补作者，避免下一次完整导出覆盖本地修复。
- APTChaser 在取得全文前不得承担细粒度方法或实验主张。
