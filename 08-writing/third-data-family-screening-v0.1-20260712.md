# 第三数据家族筛选记录 v0.1

日期：2026-07-12
状态：来源核验完成；选择 OTRF APT29 Day 1 进入 C11 内部冻结接入

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: plan
- Origin Date: 2026-07-12
- Verification Status: SOURCE-VERIFIED / EVENT-UNINSPECTED
- Version Label: third_family_screen_v0.1

## 1. 筛选目标

当前四个参数锁定真实案例来自两个主要数据家族：DARPA TC E5 与 DARPA OpTC。新增数据必须满足至少一个条件：

1. 引入第三种来源和遥测封装；或
2. 引入新的独立 engagement；并且
3. 优先支持同一 CTI 节点的多 claim corroboration。

重复 mask、intensity 或 seed 不计为新攻击案例。新来源也不能被用来修改 M2、M3a、XGBoost、AFA 或 Depth-2 的冻结参数。

## 2. 来源核验

- DARPA TC E5 官方仓库说明 E5 包含 CADETS、ClearScope、FiveDirections、THEIA、TRACE 等 performer，并明确数据由研究原型生成、可能不完整：[DARPA TC E5 release](https://github.com/darpa-i2o/Transparent-Computing/tree/244ae2401032ce92ac3b72f49b8039cae67d60d6)。
- PIDSMaker 当前数据表给出的预处理规模为：CADETS_E5 276 GB、FIVEDIRECTIONS_E5 280 GB、TRACE_E5 710 GB；这些来源仍属于 DARPA TC 家族：[PIDSMaker README](https://github.com/ubc-provenance/PIDSMaker/blob/32602734bc9f896be5fc0f03f0a185c967cd6624/README.md)。
- OTRF Security-Datasets 在固定提交中提供 APT29 Day 1 复合场景、主机日志、PCAP、Zeek 日志和 ATT&CK emulation plan：[APT29 dataset](https://github.com/OTRF/Security-Datasets/tree/d9d40ef123d2c87d5d3df28c96bcab4f0faccc87/datasets/compound/apt29)。仓库许可证为 [MIT](https://github.com/OTRF/Security-Datasets/blob/d9d40ef123d2c87d5d3df28c96bcab4f0faccc87/LICENSE)。
- GitHub contents API 在固定提交返回：主机 ZIP 13,944,973 bytes、combined Zeek log 1,243,861 bytes、SCRANTON PCAP ZIP 46,631,415 bytes、NASHUA PCAP ZIP 6,955,498 bytes。APT29 README 中的 `367M` 是数据集说明值，不作为压缩包精确字节数。

## 3. 候选矩阵

| 候选 | 独立性 | 多 claim 潜力 | 获取代价 | ground truth | 主要限制 | 决策 |
|---|---|---|---:|---|---|---|
| OTRF APT29 Day 1 | 第三来源；Windows Event/Zeek/PCAP，不同于 CDM/PGDMP/eCAR | 高：Sysmon、Security、PowerShell、WMI、Zeek 可跨通道组合 | 低，首轮约 15 MB；PCAP 可后补 | ATT&CK 仿真计划，步骤 1.A-10.B | 是 threat-actor emulation，不是真实 APT 现场；仓库主数据最后更新较早 | **选择** |
| DARPA E5 CADETS | 新 performer，但仍属 DARPA TC E5 | 中高：FreeBSD provenance | 高，PIDSMaker 标称 276 GB | TA5.1 E5 报告 | 不构成第三数据家族；下载和扫描成本大 | 后备 |
| DARPA E5 FiveDirections | 新 performer，但仍属 DARPA TC E5 | 中：Windows provenance | 高，标称 280 GB | TA5.1 E5 报告 | 与 C07/C08 同 engagement；体量大 | 后备 |
| DARPA E5 TRACE | 新 performer，但仍属 DARPA TC E5 | 中高：Linux provenance | 极高，标称 710 GB | TA5.1 E5 报告 | 体量与工程风险最高 | 暂缓 |

## 4. 选择结论

选择 **OTRF APT29 Day 1** 作为 `R08 -> C11` 候选，原因是：

1. 它能真实改变数据封装和采集通道，而不是只增加同一语料的另一个日期；
2. 在事件读取前即可从 emulation plan 锁定步骤、主机和期望证据家族；
3. 文件体量允许先冻结规则、再完整校验，不需要从数百 GB 数据中事后挑选“好看窗口”；
4. 它直接暴露当前真实案例“每节点单 claim”的结构短板。

本轮协议、内部冻结记录和结果在同一 Git 提交中首次公开，因此这里的“冻结”描述研究流程，不等同于第三方平台可验证的 preregistration。

## 5. 不能据此声称的内容

- 不能把 APT29 仿真标签当成未知样本上的 actor attribution accuracy。
- 不能把 C11 写成自然发生的真实 APT 入侵。
- 不能因为含有 APT29 标签，就把论文主线改回 actor classifier。
- 不能用 C11 结果调 M2/M3a/XGBoost 后再把 C11称为 holdout。
- 若关键节点不能恢复两个独立通道的 claim，必须报告多 claim Gate 失败或降低 support ceiling，不能换步骤补齐。

## 6. 获取后结构核验补记

固定来源下载后，主机 JSONL 与 Zeek 日志均完整可解析，但时间范围不重叠：主机为 2020-05-02，Zeek 为 2020-04-30。因此两者不能被写成同一次执行的事件级交叉佐证。C11 继续保留为第三数据家族候选，但多 claim 主路径改用内部冻结协议已允许的同包异 provider 组合（Sysmon、Security、PowerShell、WMI）；该处理不修改关键节点、AND 语义或通过门槛。
