# Project03 -> P05-L2 Handoff Audit

日期：2026-07-12

## 1. 交接目的

本文件把 Project03 已有的五模态网络实验、行为追溯和攻击意图候选能力转化为 P05-L2 的可审计研究起点。交接不等于继承其结论：Project03 是工程与实验资产来源，P05-L2 必须重新定义研究问题、标签、数据切分、baseline 和评价指标。

源目录：`D:/Software/Codex/Workplace/workspace/Project03-网络流量检测工具/`

## 2. 已核验的系统主链

```text
controller 设置路径/模态
-> sender.py 重放 PCAP
-> 网元3接收/回收
-> bridge_results_to_api.py 组合 PCAP 特征与 CSV 标签
-> /api/detect
-> threat
-> observed-stage approximation
-> chain candidate
-> local index / Neo4j / rule fallback
-> intent candidate
```

Project03 的准确能力边界是：

> 基于多模态流量观测的威胁语义解释、攻击链候选构造与攻击意图候选感知。

它尚不能证明完整攻击过程重建，也不能读取攻击者真实心理意图。

## 3. 五模态可信度矩阵

| 模态 | 控制面名称 | 当前识别依据 | 已有证据 | 当前可信度 | 研究使用边界 |
|---|---|---|---|---|---|
| IPv4 | `ipv4` | 文件名前缀或 IP 层嗅探 | 主链基线、threat/chain/intent 闭环 | 较高 | 可作为基线模态 |
| IPv6 | `ipv6` | 前缀、IPv6 layer、`0x86dd` | 2026-06-16 四点抓包与 intent 补查 | 较高但样本少 | 必须保留逐跳抓包和样本质量记录 |
| GeoNetworking | `geonet` | 前缀、外层 EtherType `0x8947` | 数据面外层已实测 | 较高 | 需要同时解析 Raw 内层 IP |
| MPLS | `mpls` | 前缀、EtherType `0x8847/0x8848` | 已有识别与验收流程 | 中等 | 尚缺本地完整验收证据包 |
| SCION | `scion_v2` | 当前主要依赖 `scion_*` 文件名前缀 | 样本 wire 表现为普通 IPv4/UDP | 低 | 只能称 intended modality；不得宣称 SCION 封装已验证 |

关键发现：Project03 当前把文件名前缀视为 authoritative modality。该设计保证演示链稳定，却混合了三类概念：

1. `configured_modality`：controller 希望采用的模式；
2. `intended_modality`：数据集/文件名声明的模式；
3. `observed_wire_modality`：抓包字节实际证明的封装。

这三者不能继续压缩成单一 `True_Modal`。

## 4. 可复用资产

| 资产 | 可复用内容 | P05-L2 需要补做 |
|---|---|---|
| 五模态 controller/sender/receiver 链 | 可控的异构协议路径与逐跳观测点 | 固化版本、导出配置和逐跳 capture manifest |
| `bridge_results_to_api.py` | PCAP 统计、模态识别入口、API schema | 拆分三种 modality 字段；保存判定依据与置信度 |
| `intent_resolution.py` | stage evidence、候选和 fallback 接口 | 由单值/启发式分数升级为可校准分布；验证模态是否真有独立信息 |
| `local_intent_store.py` | CAPEC/ATT&CK 候选检索与排序 | 当前模态只作为关键词，尚未形成模态条件化推断 |
| `local_intent_index.json` | 130 个 attack pattern 的本地语义底座 | 记录来源版本、许可证、覆盖率和候选标签质量 |
| `threat_context.py` | threat-chain-intent 上下文图接口 | 增加 Observation、Hop、Evidence、ModalityClaim 和冲突边 |
| 逐模态验收流程 | 五步闭环和逐跳定位方法 | 转为可复现实验协议，而非人工演示清单 |
| HFish 路线 | 独立行为观测源的最小图设计 | 只作为辅助证据支线，不能冒充五种网络模态之一 |

## 5. 不能直接复用的内容

- `attack_type -> stage` 的单值或手工加权结论；
- CSV 中已有 attack label 作为模型输入后再评价同一标签的结果；
- 文件名前缀推断出的 modality 作为数据面真值；
- `stage_confidence` 的启发式数值作为统计校准结果；
- 同一 PCAP 的改名、重封装或重复字段作为独立多模态证据；
- 120 条已提交记录作为现成 benchmark。当前仓库没有对应 PCAP/CSV、固定 split 和完整 provenance；
- SCION 已通过真实封装验证的主张；
- intent Top-1 等于真实攻击者意图的表述。

## 6. 当前数据与代码缺口

1. Project03 本地目录没有提交 PCAP/CSV 数据；120 条批次只见开发记录，不能从当前仓库复现。
2. `app.py` 引用的 `prediction_engine.py`、`config.py`、`graph_db.py`、`threat_chain.py` 等运行文件不在当前本地快照中。
3. 五种模态尚未形成同一攻击行为的严格配对样本；无法直接测跨模态不变性。
4. 当前 `Window_Summary` 对单样本固定写入 `multi_modal: false`；“多模态”更接近多种可切换协议，而非同一决策窗口的证据融合。
5. `LocalIntentStore` 把 modality 加入关键词，但 attack pattern 文本通常不含协议名，因此模态的独立贡献很可能接近零。
6. 小切片、背景流、控制边界和双向 PCAP 单端重放会污染 `packet_rate`、包数和方向语义。

## 7. 交接结论

Project03 最值得继承的不是现成分类结果，而是一个真实且可控的研究问题现场：

> 同一行为经过异构网络协议路径时，系统如何区分“配置/声明的模态”与“实际观测的模态”，并把逐跳一致性、缺失和冲突作为行为追溯及意图候选判断的证据？

该表述目前只作为候选问题母体。进入正式 RQ 前，仍需完成最新文献与专利撞题检索。

## 8. 快照完整性

本次审计基于 2026-07-12 本地快照。关键 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `理论边界说明.md` | `8B003C43615AEDAA0ACF1C2059F48DA5F4939194A8BB74EC18E9667D4B1285AB` |
| `逐模态标准验证流程.md` | `AF597ACE0504C4D1152366723EB2AC8B2069EBB6D6E466377335C2A0DF5D7F4C` |
| `bridge_results_to_api.py` | `286428D1528B57B2E5D456941130193CBA3ACA115F9EE55D8F0F5C7C59515AA7` |
| `intent_resolution.py` | `D9919F223864ADAA39E50B1C759049B54EF57BB9A9975E0E53AF36ACF979C99F` |
| `local_intent_store.py` | `58C5ABD7642B3CFF44122D42FBD716576BCB46929DEF8EF8C31F994F2D07004B` |
| `local_intent_index.json` | `E5292EFB86182039E16186090D1DB0C24789438379D96A507D81C2BBE37958F5` |

