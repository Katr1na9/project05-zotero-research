# Project05 论文引文审计 v0.2

日期：2026-07-11

Zotero collection：攻击溯源与意图感知

当前导出快照：`paper-main-references-v0.3.bib`，88 entries

## 1. 本轮新增审计重点

Reviewer 要求引入外部 AFA 邻域，正文已加入 AFA survey、NOCTA 和 WinRegRL。文中必须区分“相关方法原论文”与“本项目同接口领域适配”：

| 正文用途 | Zotero key | 支撑边界 |
|---|---|---|
| AFA 的成本约束序贯采集谱系 | `aronsson_survey_2025` | 综述入口，不承担本项目性能结论 |
| 非贪心 objective-cost trade-off | `noauthor_nocta_2025` | 直接支撑方法定位；本项目未复现其官方模型/代码 |
| 专家 MDP + value iteration/RL 的注册表调查 | `ghanem_leveraging_2026` | 直接支撑近邻任务；本项目未复现其 MDP |

## 2. 核心引文边界

| 研究线 | 代表 key | 文中允许的描述 |
|---|---|---|
| CTI/攻击图抽取与对齐 | `milajerdi_poirot_2019`; `kiavash_satvat_extractor_2021`; `zhenyuan_li_attackg_2022` | 上游表示、图构建和对齐，不声称其不能进行归因 |
| LLM/evidence-path 归因 | `xiao_taa-eplmr_2025`; `rani_aura_2025`; `alshamrani_llm-based_2026` | 基于已有证据的推理/解释，不用作同动作空间基线 |
| 多源/多模态归因 | `cai_apt-att_2025`; `zhang_mm-attackg_2025` | 证据表示或归因推理近邻，不等同调查控制 |
| 主动采集 | 上述 AFA/NOCTA/WinRegRL | 承认宽泛问题已存在；本文只主张安全信息结构与接口增量 |

## 3. 禁止写法

1. 不写“现有工作都假设动作收益已知”；应写“部分实现或离线评价可能通过特征/动作定义隐含可恢复性”。
2. 不写“首次将 AFA/MDP 用于安全取证”；WinRegRL 等已经覆盖相关方向。
3. 不把本文 AFA-VOI 结果描述成 NOCTA/WinRegRL 失败。
4. 不因 APTChaser 只有摘要级材料而引用其细节或性能。
5. 不把内部实验数字交给外部引文支撑；所有数字回指仓库结果。

## 4. 提交前待办

- 用目标 venue CSL 重新导出参考文献，并复核 NOCTA 的作者字段、ExCyTIn-Bench 发表状态和所有 DOI/页码。
- 若加入官方 AFA 代码复现，新增独立协议、版本/commit、许可证和超参数记录。
- 引文审计不替代人工全文复核；任何新增强比较句必须先补直接证据。
