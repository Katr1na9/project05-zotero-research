# Research Progress

## 2026-07-09：M2 负结果后的 M3 方法研究

- 定位 C06 的核心失败：20 个 stage/discriminative 挑战条件均缺 `N01_initial_access`，Oracle 全部首选 `AA-001`，M2 却因 stage 粗粒度相同和手写 gain 偏置而全部首选 `AA-002`。
- 新增 2026 年高风险近邻 WinRegRL：其已覆盖 Windows forensic MDP、39 个 atomic actions、专家 transition、value iteration、有限 Q-learning 及 POMDP 扩展；Project05 不得再宽泛主张“MDP/RL 主动取证”。
- 主线收束为 GCEU-Net：预测 `action × current evidence-gap graph` 对每个关键 CTI 节点的解决概率，以及归因粒度迁移概率。
- 决定先做 M3a action-gap compatibility baseline，再做可校准 small model；独立 case 足够后才引入 GNN 和 depth-2 planning。
- LLM 保持受控角色：证据语义编译、动作到候选缺口节点映射、结果解释；不直接预测效用或自由归因。
- 完整设计见 `04-progress/m3-gap-conditioned-evidence-utility-research-20260709.md`。

## 2026-07-09：M2 动态边际效用规划器与 C06 留出验证

- M2 只使用公开动作元数据、当前覆盖缺口、动作签名、剩余预算和执行后的恢复数量反馈；信息边界测试禁止读取隐藏证据和真实可恢复集合。
- 冻结公式后，从 CADETS `official-2` 提取 2018-04-12 攻击窗口：7,828,382 条源事件中保留 318,821 条，坏行 0，引用节点解析 29,620/29,620。
- C06 编译得到 10/10 个真实 motif，覆盖 Nginx 入口、载荷通信与执行、Drakon/XIM、Micro/test C2 和内部扫描。
- 585 次留出运行全部保留；full-evidence 可达 G3，越过支持上限 0 次，负 Oracle regret 0 次。
- 总体成功率：M2 `0.5111`，M1 `0.5111`，coverage greedy `0.7111`，Oracle `1.0000`。
- 排除 18 个初始已达 G3 的条件后，27 个挑战条件中 M2/M1 均成功 `5/27`，coverage greedy `14/27`，Oracle `27/27`。
- 当前结论是负结果：动态反馈确实改变了部分首动作，但没有提升目标达成率。下一方法增量应转向“动作对具体缺失节点/证据需求的条件收益估计”，而不是继续调整固定权重。
- C06 仅是同数据集家族内部留出，不能宣称跨数据集泛化。

## 2026-07-09：DARPA TC E3 真实数据接入 Phase 0

- 已精读 47 页 E3 ground-truth report，并结合 operational event log 确认 topic 切换边界。
- R01 锁定为 FiveDirections 2018-04-11 Firefox/Drakon 完整链，对应 `ta1-fivedirections-e3-official-2.json.tar.gz`。
- R02 锁定为 CADETS 2018-04-06 Nginx/Drakon 失败链，对应崩溃前的 `ta1-cadets-e3-official.json.tar.gz`。
- 已记录官方 Google Drive ID、文档 SHA-256、本地/UTC 时间窗、自然不完整性与可支持粒度上限。
- 新增 manifest 验证器与 4 项真实数据清单测试；完整测试总数增至 18。
- 大型原始归档尚未下载，`raw/` 与 `extracted/` 已加入 Git 忽略规则。
- C 盘剩余约 842.85 GB，容量不是阻塞；官方 Google Drive 大文件连接被远端重置。
- 已审计 MAGIC 的 CADETS 预处理包：缺少原始 UUID/时间/边回指，不作为主数据。
- 已采用 ADAPT E3 commit `8fa6b58` 构建辅助候选索引，FiveDirections `9/9`、CADETS `11/11` ground-truth process UUID 全部命中。
- ADAPT 索引缺少时间戳和原始边，仅用于未来官方 CDM 回查，不用于直接生成最终 evidence claim。
- 已锁定 PIDSMaker E3 紧凑 PostgreSQL 转储：CADETS 约 1.4 GB、FiveDirections 约 3.2 GB，并登记官方文件 ID 与源码 commit `3260273`。
- 新增断点续传下载器；Google Drive 下载仍需只读 OAuth 或浏览器登录。令牌只从环境变量读取，不落盘。
- 后续抽取同时保留宽上下文窗和窄攻击标签窗，防止标签信息进入证据规划器。
- DARPA E3 官方原始归档已到位并完成 R01/R02 宽窗抽取，不再以 PIDSMaker dump 获取作为阻塞项。
- R01 扫描 256,634,196 条 Event，抽取 3,617,566 条，解析 278,976/278,983 个引用节点；R02 扫描 12,915,596 条，抽取 258,074 条，解析 16,646/16,646 个引用节点。
- R01 命中 `firefox.exe` 与 3 个基础设施 IP，但 provider CDM 中没有 `www.cnpc.com.cn`；R02 的 6 个预设 observable 全部命中。
- 新增流式 CDM 时间窗抽取器和紧凑可复现摘要，大型事件/节点/SQLite 产物继续排除在 Git 外。
- 已将 R01/R02 编译为 C04/C05 真实行为基元案例，每例 8 条 claim，全部具有真实 Event UUID 回指。
- 新增 `support_ceiling`：C04 full-evidence 到 G3，C05 full-evidence 正确停在 G2；1,080 次运行中没有 ceiling violation 或负 Oracle regret。
- 首轮真实实验中 CMI proxy 暂时优于完整 M1：总体成功率/成本为 `1.0000/1.5333`，M1 为 `0.9889/2.0112`。
- M1 在 C04 `random/60%/seed37` 失败，根因是静态 expected-effect 评分没有充分处理 action 的实际零恢复与动态重叠；该结果作为待改进问题保留，不在同一开发案例上事后调权。

## 2026-07-09：规划器信息泄漏修正、Oracle/CMI proxy 与 M1 消融

- 发现并修正普通规划器读取真实 `hidden_ids` 的 Oracle 信息泄漏；旧 675-run 快照退役。
- 新增 `oracle_optimal`，穷举预算内动作组合，给出达到目标粒度的最低成本路径。
- 新增 `cmi_proxy`；由于当前案例缺少多候选假设和动作结果分布，明确不宣称真实 CMI。
- 新增五个 M1 消融：移除 granularity、uncertainty、risk、coverage 或 cost。
- 严格版本包含 3 个独立案例、1620 个重复运行；所有非 `full_evidence` 结果相对 Oracle 的 cost regret 均非负。
- `project05_m1` success rate 为 0.9333，平均达标成本为 3.5714；`oracle_optimal` 为 2.3778，`coverage_greedy` 为 4.3077。
- `m1_no_uncertainty` 与 `m1_no_risk` 未改变结果，暴露当前动作元数据区分度不足；这是下一轮状态/动作建模需要解决的问题。

## 2026-07-09：多案例实验矩阵跑通

- 模拟器已从 C01 单案例扩展为 C01-C03 批量运行。
- 新增 C02 FreeBSD audit/provenance 和 C03 Windows 多源主机证据 toy case。
- mask 设计扩展为 3 种缺失机制 × 3 档强度 × 5 个随机种子。
- 新增 `unittest` 回归测试，覆盖实验矩阵、mask intensity、案例发现、重复 case ID、引用完整性和独立样本统计。
- 当时的完整矩阵包含 3 个独立案例和 675 个重复运行。
- 当时 `project05_m1` 总体 success rate 为 1.0，平均达标成本为 2.5926；该结果后续确认受隐藏证据信息泄漏影响，已退役。
- 结论边界：仍是手工 toy case，只能说明工程闭环和实验协议可执行；下一步需要增加 oracle/CMI baseline、消融实验和更多真实 attack trace。

## 2026-07-08：C01 小样例与最小模拟器跑通

- 新增 `09-experiments/examples/C01/`，包含 `case_config.json`、`evidence_claims.json`、`acquisition_actions.json`。
- 新增 `09-experiments/scripts/run_mvp.py`，实现 evidence ablation、action recovery、state update、granularity judgment 和 5 个 planner：`random`、`fixed_order`、`coverage_greedy`、`project05_m1`、`full_evidence`。
- 已生成 `09-experiments/results/c01_mvp_results.csv`、`c01_mvp_summary.json`、`c01_mvp_traces.json`。
- 当前 C01 toy result：`project05_m1` success_rate 1.0，mean_cost_to_target 3.0；`coverage_greedy` 为 3.4，`fixed_order` 为 6.2667，`random` success_rate 为 0.4。
- 结论：最小闭环已经跑通，但还只是 toy simulator；不能作为论文结论。下一步应构造 C02/C03，并加入更多 mask 强度与统计汇总。

## 2026-07-08：实验案例清单与三个数据 schema 完成

- 新增 `08-writing/experiment-case-inventory-v0.1-20260708.md`，将 MVP 案例池收束为 C01 Linux provenance、C02 FreeBSD provenance、C03 Windows provenance 三个主案例，并保留 OpTC、POIROT/MEGR-APT、ExCyTIn、TAA-EPLMR、APT-ATT 作为扩展或 baseline 案例。
- 新增 `09-experiments/README.md` 和 `09-experiments/data_schema/`。
- 已建立三个 JSON Schema：`evidence_claim.schema.json`、`alignment_state.schema.json`、`acquisition_action.schema.json`。
- schema 已通过 PowerShell `ConvertFrom-Json` 解析校验。
- G5 当前状态：Phase 0/1 草案完成；下一步是构造 C01-C03 的小样例数据，并实现 evidence ablation + action recovery 模拟器。

## 2026-07-08：TAA-EPLMR 新主线复核完成

- 已按当前主线复核 `02-literature-notes/2025-Xiao-TAA-EPLMR.md`，确认它已覆盖 `CTI-KG evidence path retrieval + pruning/aggregation + LLM evidence-aware CoT + actor attribution explanation + confidence score`。
- 结论：旧的“证据路径增强 LLM APT 归因解释 / 置信度输出 / incomplete-noisy IOC 鲁棒归因”路线已被 TAA-EPLMR 强覆盖，不能再作为 Project05 主创新。
- 同时确认其没有覆盖 evidence sufficiency gate、归因粒度门控、拒答/降级、open-set unknown、主动取证动作价值估计、成本约束规划、对齐-补证-再对齐闭环，也不处理 CTI 与本地 provenance/log 证据的对齐状态。
- 对 Project05 的影响：TAA-EPLMR 应作为 `TAA-EPLMR-like CTI-KG evidence path + LLM actor attribution` 强 baseline / 红线参照；Project05 的实验必须比较“是否正确停止/降级/补证”，而不是只在删除 IOC 后继续做闭集 actor 分类。
- 当前剩余补洞：中文专利侧证据采集/取证规划检索、APTChaser/GAPT 正文获取或待办追踪。

## 2026-07-07：APT-ATT 正文获取并升级精读

- 用户找到 `1-s2.0-S1389128625004785-main(科研通-ablesci.com) (1).pdf`，确认对应 APT-ATT：`APT-ATT: An efficient APT attribution model based on heterogeneous threat intelligence representation and CTGAN`，DOI `10.1016/j.comnet.2025.111511`。
- 已将 `02-literature-notes/2025-Cai-APT-ATT-High-Risk-Related.md` 从高风险占位升级为正文精读。
- 结论：APT-ATT 覆盖 heterogeneous CTI representation + CTGAN minority-class augmentation + stacking ensemble APT organization classification；Project05 不能写异构 CTI 表示、CTGAN 数据增强或闭集 actor classifier 作为核心创新。
- 同时确认其不覆盖 evidence sufficiency、confidence calibration、missing evidence、refusal / abstention、attribution granularity gate 或 active evidence acquisition planning；因此不推翻当前“对齐感知证据状态建模 + 主动取证规划”主线。

## 2026-07-07：缺口精读笔记补齐

- 新增 6 篇精读笔记：`2019-Milajerdi-POIROT.md`、`2021-Wei-DeepHunter.md`、`2024-Aly-MEGR-APT.md`、`2025-NOCTA-Non-Greedy-Objective-Cost-Tradeoff-Acquisition.md`、`2025-ExCyTIn-Bench-Cyber-Threat-Investigation.md`、`2026-Adaptive-Malware-Detection-Sequential-Feature-Selection-DDQN.md`。
- 升级 2 篇原摘要级占位为全文精读：`2025-Li-CLIProv.md`、`2025-Qiu-APT-CGLP.md`。
- 结论进一步固定：POIROT -> DeepHunter -> MEGR-APT -> CLIProv -> APT-CGLP 已经覆盖 CTI/provenance/log 对齐、图匹配、语义检索、graph-language pre-training 和 LLM 合成 CTI；Project05 不再把 alignment 本身作为主创新。
- 实验理论与 baseline 侧补强：NOCTA 支撑非贪心 cost-aware acquisition，ExCyTIn-Bench 支撑 graph-grounded 调查评测，D3QN 恶意软件工作可作为安全侧顺序特征获取 baseline。
- 仍需保留的全文待办：APTChaser、GAPT；CLIProv/APT-CGLP/APT-ATT 已从待补全文中移除，TAA-EPLMR 已于 2026-07-08 完成新主线复核。

## 2026-07-07：实验方案 v0.1 完成

- 新增 `08-writing/experiment-plan-v0.1-20260707.md`。
- 实验路线确定为 evidence ablation：从完整攻击案例构造 CTI 行为图和本地证据图，遮蔽部分证据，再让不同取证策略逐步恢复证据并比较成本与归因粒度收益。
- 明确了 v0.1 的核心模块：证据状态表示、归因粒度规则、取证动作空间、动作价值函数、baseline、LLM 受控参与方式和评价指标。
- G5 当前状态：Phase 0/1 草案完成，案例清单与 schema 已于 2026-07-08 建立。
- 下一步：构造 C01-C03 的小样例数据，并实现 evidence ablation + action recovery 模拟器。

## 2026-07-06：US12530469 权利要求原文补读剔除

- 根据用户决策，US12530469 的“权利要求原文补读”从当前 workflow 中剔除，不再作为 G2/G4 阻塞项。
- US12530469 仍保留为摘要级专利红线材料，用于约束 Project05 不写成泛化的“LLM 告警调查 + 置信不足追加上下文 + 循环收敛”。
- 当前剩余补洞改为：中文专利侧证据采集/取证规划检索、APTChaser/GAPT 正文获取；APT-ATT 已于 2026-07-07 获取并精读，TAA-EPLMR 已于 2026-07-08 完成新主线复核。
- 下一步优先级不变：起草 `08-writing/experiment-plan-v0.1-20260706.md`。

## 2026-07-06：Stage 1 RQ 固化完成

- 新增 `03-ideas/topic-rq-brief-v2.1-g1-final-20260706.md`，作为当前主线的 G1 通过版研究问题卡。
- 将 Project05 当前研究对象明确为：对齐之后的证据状态建模与取证动作规划，而不是新的对齐算法、actor 分类器或 LLM 归因框架。
- 明确了 3 个可检验假设：对齐感知状态优于普通证据计数、主动取证优于随机/固定顺序补证、LLM 受控参与优于 LLM 直接归因。
- G1 判定：通过，但带两个条件进入下一阶段：继续补剩余深扫材料，并起草 experiment-plan-v0.1 验证数据与 baseline 可执行。US12530469 权利要求原文补读已剔除；CLIProv/APT-CGLP 已于 2026-07-07 升级为全文精读，TAA-EPLMR 已于 2026-07-08 完成新主线复核。

## 2026-07-06：全项目重扫并同步新主线索引

- 完成全项目增量重扫，确认当前新增量已经改变 Project05 主线：从“归因粒度门控 / 拒答解释 / 缺失证据 list”转向“对齐感知证据状态建模 + 面向归因粒度提升的主动取证规划”。
- 新增总报告：`04-progress/project-rescan-increment-20260706.md`。
- 已同步修正索引：`README.md`、`00-dashboard/research-dashboard.md`、`02-literature-notes/README.md`。
- 当前 RQ v2 见：`03-ideas/topic-rq-brief-v2-20260706.md`，G1 基本通过。
- 当前核心红线：不能把 CTI-local evidence alignment 本身作为主创新；CLIProv、APT-CGLP、POIROT/DeepHunter/MEGR-APT/ActMiner/ProHunter 等已经覆盖大量对齐/狩猎链路。
- 当前理论基座：Active Feature Acquisition / POMDP。Project05 的新贡献应落在“部分观测证据状态 + 取证动作价值估计 + 成本约束规划 + STOP/粒度门控”上。
- 下一步：补剩余高风险全文，并推进 `08-writing/experiment-plan-v0.1-20260707.md` 后续案例清单与 schema；US12530469 权利要求原文补读已剔除，TAA-EPLMR 已于 2026-07-08 完成新主线复核。

## 2026-07-06：新主线拍板"A 主 + B 辅"，首轮深扫立即修正 A 的定位

- 用户确认新主线：A（CTI-本地证据跨源对齐与语义提升）为论文主线 + B（证据价值建模与主动取证规划）为第二贡献。
- 随即执行 Stage 2 首轮深扫（英文论文侧），**发现红色警报**：威胁狩猎图匹配谱系 POIROT(2019)→DeepHunter(2021)→MEGR-APT(2024)→ActMiner(2025)→CLIProv(2025-07)→APT-CGLP(2025-11) 已完整覆盖"CTI 图↔溯源图对齐/匹配"机制，其中 CLIProv 还覆盖"日志→TTP 语义提升+攻击场景生成"。
- 主线修正（v2）：对齐模块降级为复用上游（POIROT/MEGR-APT/CLIProv 式匹配器作基座与 baseline），主创新上移为**"对齐感知证据状态建模 + 面向归因粒度提升的主动取证规划"闭环**——狩猎线的终点（匹配结果）是 Project05 的起点（证据状态）。
- 关键区分：整条狩猎谱系无一做"对齐之后"的归因粒度评估、对齐缺口的证据学解释、取证规划与迭代闭环。
- 2026-07-06 用户补充决定：**暂不引入 Project03/CENI 平台联动**，Project05 独立推进，实验立足公开数据集（DARPA TC/OpTC + 公开 CTI 报告的 evidence ablation 构造）。
- 新增文件：`04-progress/deep-collision-scan-alignment-20260706.md`、`02-literature-notes/2025-Li-CLIProv.md`、`02-literature-notes/2025-Qiu-APT-CGLP.md`、`07-zotero-exports/zotero-import-candidates-20260706-alignment.ris`。
- 剩余深扫待办：中文专利侧、ActMiner/ProvG-Searcher/ProHunter 细查、"证据采集调度"学术侧二轮换词检索。US12530469 权利要求全文补读已从当前 workflow 剔除，TAA-EPLMR 已于 2026-07-08 完成新主线复核。

## 2026-07-06：深扫第二轮——US12530469 定性 + 找到 B 模块理论基座 AFA

- 用户决定 Project05 与 Project03 解耦独立推进后，继续完成深扫第二轮。
- US12530469（Varonis，2026-01-20 授权）完成摘要+说明书概要级风险精读：任务边界是**告警真/假阳性判定**（剧本生成+风险分收敛循环），与归因粒度判定可区分；但"置信不足→拉数据→循环"的朴素写法被其覆盖，B 模块写法应限定在"归因粒度层级的证据价值估计 + 对齐缺口驱动的取证动作规划"。权利要求原文补读已从当前 workflow 剔除。新增笔记 `02-literature-notes/2026-Varonis-US12530469-LLM-Alert-Investigation.md`。
- **关键进展**：换词检索命中 ML 领域成熟研究线 Active Feature Acquisition（AFA，arXiv:2502.11067 综述，POMDP 统一形式化）。安全侧仅有"RL 顺序特征选择做恶意软件分类"（DQFSA、Dueling DDQN）的扁平特征先例；"AFA 形式化 + 对齐状态证据 + 归因粒度分层目标 + 异构取证动作"空档确认未被占据。B 模块从"控制层"升级为有理论根基的 POMDP 实例化问题。
- RIS 补充 4 条（AFA 综述、NOCTA、US12530469、DDQN 恶意软件）。
- 下一步：AFA 综述全文精读（A 级、可直接获取）→ RQ brief v2 起草。

## 2026-07-06：AFA 综述全文精读完成 + RQ brief v2 起草，G1 基本通过

- AFA 综述（arXiv:2502.11067 v2）已全文精读（arXiv HTML 版），新增 `02-literature-notes/2025-Aronsson-AFA-Survey.md`：含 POMDP 形式化、短视/非短视谱系、四类方法分类、九条开放方向到 Project05 的逐条映射、"为什么不是直接套 AFA"的四点差异、可复用清单（baseline/方法候选/评测协议）。
- 新增 `03-ideas/topic-rq-brief-v2-20260706.md`：主 RQ + 4 个子 RQ + 输入/输出/场景/指标 + 撞题快查表 + G1 自检。
- **G1 判定：基本通过**，带两项黄色条件：(1) evidence ablation 数据构造方案待实验设计阶段细化；(2) 剩余深扫（中文专利等）仍需补。US12530469 权利要求原文补读已从当前 workflow 剔除，TAA-EPLMR 已于 2026-07-08 完成新主线复核。
- 复利日志新增"AFA 理论基座"条目。
- 下一步候选：(a) 完成剩余深扫过 G2；(b) 起草 experiment-plan-v0.1（含小规模可行性验证设计）。

## 2026-07-06：用户判定"归因控制层"方向偏弱，触发 G3 回退，启动主线转向

- 用户明确判断："归因可判定性评估 + 归因粒度门控 + 拒答解释 + 缺失证据生成"组合偏弱，本质是给别人的归因系统加保护层，不足以支撑硕士论文 + 专利主创新。
- 按 workflow v2 的 G3 回退规则，Project05 从 Stage 6/7 回退到 Stage 1（RQ Scoping）。
- 新增 `04-progress/mainline-pivot-candidates-20260706.md`：分析 4 个候选强主线，推荐"A：CTI 侧攻击图与本地流量/溯源证据的可验证对齐与语义提升"为论文主线，"B：证据价值建模与主动取证规划"为第二贡献模块。
- 本轮初步联网核查新增高风险专利：US12530469（LLM 多阶段告警调查，置信不足触发追加数据请求循环），直接压缩候选 B 的朴素专利写法；当前仅保留摘要级红线，不再补权利要求全文。
- 交互式调查 agent 方向（ExCyTIn-Bench、CyberSleuth、AutoBnB-RAG 等）确认拥挤，排除。
- 原充分性画像/粒度门控/拒答积累降级为候选主线的组成模块与评价维度，不作废。
- 待用户确认主线选择后，针对选定主线执行正式 Stage 2 深扫。

## 2026-07-06：缺全文项转待办并推进专利 v0.2

- 新增 `04-progress/fulltext-todo-20260706.md`：将 APT-ATT、APTChaser、GAPT、A Multi-Source Feature Fusion-Based Knowledge Graph for APT Attribution 四篇设为“全文待补，不阻塞主线”。
- 新增 `04-progress/collision-matrix-final-20260706.md`：合并主矩阵和补充矩阵，确定最终红线与白区。
- 新增 `08-writing/patent-claims-draft-v0.2-20260706.md`：将 v0.1 的“多源证据融合 + LLM 归因”重写为“归因粒度门控 + 可拒答解释”。
- 当前判断：可以继续推进实验设计 v0.1，但 v0.2 仍需标记为 incomplete draft，等待四篇全文和发明人确认。

## 2026-07-06：Multi-Source Feature Fusion HKG 全文已获取

- 新增 `02-literature-notes/2025-Au-Multi-Source-Feature-Fusion-HKG-APT-Attribution-IDS.md`。
- 本地 PDF 已归档到 `07-zotero-exports/pdfs_20260706_deep/Au_2025_Multi_Source_Feature_Fusion_HKG_APT_Attribution_IDS.pdf`。
- 已抽取全文到 `07-zotero-exports/pdf_text_20260706_deep/Au_2025_Multi_Source_Feature_Fusion_HKG_APT_Attribution_IDS.txt`。
- 结论：该文是红色风险项，直接覆盖 multi-source CTI + HKG + attribute/BERT/node2vec feature fusion + multi-level attention + APT group attribution。
- 待补全文清单中该项已从“待补”转为“已获取并确认红线”。

## 2026-07-06：形成当前结论简报

- 新增 `04-progress/project05-current-conclusion-brief-20260706.md`。
- 用于对外讨论当前调研范围、已完成工作、主线方向、拟定技术路线、预期效果和当前疑虑。

## 2026-07-06：APTChaser / GAPT / MLDSJ 补查与撞题修正

- 新增 `02-literature-notes/2025-Zhang-APTChaser-Attack-Technique-Modeling.md`：确认 APTChaser 已覆盖 `LLM + attack technique schema/profile + APT attribution`，禁止 Project05 把“LLM 细化 TTP 后归因”作为主创新。
- 重写 `02-literature-notes/2024-Chen-GAPT-Temporal-Relation-Embeddings.md`：当前只作为二级引用风险项保留，未找到可独立验证 DOI/全文，不能当作已精读文献。
- 新增 `02-literature-notes/2026-Duan-MLDSJ-Multi-Level-Feature-Joint-Attribution.md`：MLDSJ 直接覆盖 `多层 CTI 特征 + Dempster-Shafer 证据融合 + APT group attribution`，是 Project05 原始宽题的红色风险项。
- 新增 `04-progress/collision-matrix-supplement-20260706.md` 和 `04-progress/workflow-status-supplement-20260706.md`。
- 新增 `07-zotero-exports/zotero-import-candidates-20260706-supplement.ris`，包含 APTChaser、MLDSJ 和 `A Multi-Source Feature Fusion-Based Knowledge Graph for APT Attribution` 三条补充导入记录。
- 当前判断：2026 上半年并非空白；证据融合、KG 归因、LLM 技术建模方向都在推进。Project05 必须继续收窄为“归因粒度门控 / 可拒答解释 / 缺失证据清单”。

## 2026-07-06：APT-ATT 暂未获取情况下继续推进专利主线

- 新增 `04-progress/apt-att-unavailable-risk-note-20260706.md`：明确 APT-ATT 正文未获取是风险保留项，不作为当前主线阻塞项。
- 新增 `04-progress/final-topic-boundary-20260706.md`：将 Project05 推荐方向收束为“证据不完整场景下的 APT 归因可判定性评估、分层降级、拒答控制与 LLM 受控解释”。
- 新增 `08-writing/patent-claims-draft-v0.1-20260706.md`：形成专利权利要求草案 v0.1，核心模块包括证据可用性画像、证据区分度/充分性/冲突评分、归因粒度门控、开放集判断、LLM 受控解释和缺失证据采集建议。
- 当前判断：不再把“多源证据融合 + LLM 辅助归因解释”作为宽泛创新点，而是把“证据不足时系统是否允许输出 actor-level 归因”作为核心技术问题。

## 2026-07-06：二次深度撞题扫描完成

- 新增 `04-progress/deep-collision-scan-20260706.md`。
- 新增高风险材料包括：`CN121887534A`、`CN118802369A`、`TRAIL`、`APT-scope`、`APT-ATT`、`APTChaser`、`Construction of Cyber-attack Attribution Framework Based on LLM`、`Correlation Analysis of APT Attack Organizations Based on Knowledge Graphs` 等。
- 更新判断：Project05 不能再以 IOC/KG/HIN/流量/TTP/LLM 框架归因为核心；可保留空间进一步收缩为“归因粒度门控、可拒答解释、缺失证据生成和证据充分性画像”。
- 继续深扫后新增并精读/风险精读：`CN116467438A`、`CN117560223B`、`CN117786088B`、`CN119766567B`、`HG-CTA`、`AARGS`、`GAPT`、`BAN`。
- `08-writing/patent-claims-draft-v0.1-20260706.md` 已标记为偏宽草案，后续 v0.2 必须围绕“归因粒度门控”重写。

## 2026-07-06：基于新安装 research skills 重塑 workflow

- 新增 `01-sop/project05-skill-driven-workflow-v2.md`。
- 新增 `04-progress/workflow-status-20260706.md`。
- workflow 采用 `nature-literature-pipeline` 的检索/评分/归档思想、`nature-reader` 的全文精读约束、`nature-paper-to-patent` 的 source grounding 和 stage gate、`academic-research-suite` 的 research-to-paper pipeline、`experiment-agent` 的实验设计/验证 gate、`scientific-critical-thinking` 的红线审查框架。
- 当前正式定位：Project05 位于 Stage 6 功能级撞题矩阵，尚未通过 Stage 7 专利尽调 gate，不应继续扩写专利说明书。

## 2026-07-05：2026 H1 撞题补读已纳入

- 已完成 7 篇 2026 H1 关键文献的下载/抽取/精读登记：TTPrint、CTI-Thinker、OpenSec、Minerva、High-Precision APT Malware Attribution、Synthetic APTs、ARCANE。
- CTI-Thinker 本地下载为 Springer HTML 页面，未获得可抽取 PDF；已按网页全文/元数据纳入。
- 关键判断：`LLM + KG/GraphRAG + CTI attack reasoning`、`evidence-grounded TTP extraction`、`可验证 CTI LLM`、`abstention/OOS attribution` 在 2026 年上半年都有推进。
- Project05 的题目不能停留在泛化的 “多源证据融合 + LLM 辅助 APT 归因解释”；更稳的方向是 `证据不完整 + 开放集/未知 actor + 证据充分性评分 + 分层降级 + 拒答/暂缓归因 + 证据解释`。

## 总体里程碑

| 阶段 | 目标 | 状态 | 产物 |
|---|---|---|---|
| M1 | 建立科研工作区和 Zotero 流程 | 进行中 | project05-zotero |
| M2 | 完成 10 篇核心文献精读 | 进行中 | 精读笔记 |
| M3 | 形成 3 个候选选题 | 延后 | 所有文献读完后由用户手动决策 |
| M4 | 选定 1 个主选题 | 未开始 | 选题论证 |
| M5 | 完成最小实验设计 | 未开始 | 实验方案 |
| M6 | 开题报告初稿 | 未开始 | 开题文档 |

## 当前待办

- [x] 将 `A survey of cyber threat attribution` 写成精读笔记。
- [x] 将 `AttacKG` 写成精读笔记。
- [x] 将 `EXTRACTOR` 写成精读笔记。
- [x] 将 `Kairos` 写成精读笔记。
- [x] 将 `TechniqueRAG` 写成精读笔记。
- [x] 将 `DEPCOMM` 写成精读笔记。
- [x] 将 `CTIBench` 写成精读笔记。
- [x] 将 `Large Language Models are Unreliable for CTI` 写成精读笔记。
- [x] 将 `TTPXHunter` 写成精读笔记。
- [x] 将 `SEvenLLM` 写成精读笔记。
- [x] 将 `CTIConnect` 写成精读笔记。
- [x] 将 `LOCALINTEL` 写成精读笔记。
- [x] 将 `Beyond RAG for CTI` 写成精读笔记。
- [x] 将 `A Modular Approach to Automatic Cyber Threat Attribution using Opinion Pools` 写成精读笔记。
- [x] 将 `High Stakes, Low Certainty` 写成精读笔记。
- [x] 将 `Multi-Step LLM Pipeline for Enhancing TTP Extraction in CTI` 写成精读笔记。
- [x] 将 `Open-CyKG` 写成精读笔记。
- [x] 将 `UNICORN` 写成精读笔记。
- [x] 将 `THREATRACE` 写成精读笔记。
- [x] 将 `PROGRAPHER` 写成精读笔记。
- [x] 将 `APT-MMF` 写成精读笔记。
- [x] 将 `ADAPT it!` 写成精读笔记。
- [x] 整理威胁归因术语表 v0.1。
- [ ] 延后：所有核心/扩展文献读完后，再由用户手动决定是否比较 3 个候选选题。
- [ ] 对候选 idea 做 2024-2026 最新工作新颖性检查。

## 阅读记录

### 2026-06-30

- 已阅览并沉淀：`A survey of cyber threat attribution`
- 已阅览并沉淀：`AttacKG`
- 初步判断：
  - 综述提供威胁归因的层级地图和研究动机。
  - AttacKG 提供 CTI 报告结构化、ATT&CK 技术识别和知识图谱构建的方法抓手。
  - 当前值得推进的路线是：CTI 文本 -> 攻击图/TTP -> ATT&CK KG/RAG -> 攻击意图识别 -> 证据增强候选归因。

### 2026-07-01

- 已沉淀：`EXTRACTOR: Extracting Attack Behavior from Threat Reports`
- 已沉淀：`KAIROS: Practical Intrusion Detection and Investigation using Whole-system Provenance`
- 核心收获：
  - EXTRACTOR 关注 CTI 报告到 provenance graph 的转换，是 AttacKG 的重要前置基础。
  - 它的输出不是 ATT&CK technique，而是可被 threat hunting 系统使用的 query graph。
  - CTI 文本结构化的关键难点包括长句、领域术语、省略主语、代词指代、实体归一、关系抽取和非攻击行为过滤。
  - KAIROS 关注真实审计日志到 whole-system provenance graph 的构建与异常检测，并把异常边压缩为 compact attack summary graph。
  - KAIROS 的价值不仅是检测，更是把百万级日志边压缩成可调查、可解释的攻击摘要图。
- 对选题的影响：
  - 当前选题路线应明确区分“文本攻击行为图”和“系统审计 provenance graph”。
  - 后续不宜只做 CTI 文本侧 TTP 抽取，应考虑“CTI 文本攻击图 + 日志侧 provenance evidence”的双源证据融合。
  - KAIROS 自身不做 ATT&CK 标注、攻击意图识别或组织归因，这正好留下了向上层语义推理扩展的空间。

## 下一步阅读

### 2026-07-04

- 已沉淀：`TECHNIQUERAG: Retrieval Augmented Generation for Adversarial Technique Annotation in Cyber Threat Intelligence Text`
- 核心收获：
  - TechniqueRAG 已经较系统地覆盖“CTI 文本 -> ATT&CK technique/sub-technique 标注”任务。
  - 它使用 retriever、LLM re-ranker、fine-tuned generator 三段式框架，在少量标注样例下提升 technique annotation。
  - 它留下的缺口主要不是“再做一个 RAG 标注器”，而是 technique 之后的 intent layer、证据充分性、不确定性和日志侧 evidence 对齐。
- 对选题的影响：
  - 不能把“RAG 做 ATT&CK 标注”作为独立创新点。
  - 候选选题应向 evidence-grounded intent recognition、CTI-log provenance alignment 或 uncertainty-aware attribution 收窄。

### 2026-07-04：DEPCOMM

- 已沉淀：`DEPCOMM: Graph Summarization on System Audit Logs for Attack Investigation`
- 核心收获：
  - DEPCOMM 关注系统审计日志因果分析生成的 dependency graph 过大、难以人工调查的问题。
  - 它通过 process-centric communities、community compression 和 InfoPaths 生成攻击调查摘要。
  - 它和 Kairos 互补：Kairos 更偏异常检测后生成 attack summary graph；DEPCOMM 更偏从 POI 出发压缩 dependency graph。
- 对选题的影响：
  - 日志侧证据可以不直接输入 LLM，而是先压缩为 InfoPaths / attack summary graph。
  - 后续可考虑把 InfoPaths 映射到 ATT&CK technique、tactic 或 attack intent。

### 2026-07-04：CTIBench

- 已沉淀：`CTIBench: A Benchmark for Evaluating LLMs in Cyber Threat Intelligence`
- 核心收获：
  - CTIBench 将 LLM-CTI 能力拆成 CTI-MCQ、CTI-RCM、CTI-VSP、CTI-ATE、CTI-TAA 五类任务。
  - CTI-ATE 对应 ATT&CK technique extraction，可与 AttacKG、TechniqueRAG、TTPXHunter 对齐。
  - CTI-TAA 对应 threat actor attribution，是当前最贴近威胁归因主线的 benchmark 子任务。
  - 显式 reasoning prompt 并不能稳定提升 CTI-MCQ 准确率，说明“让模型解释一下”不是可靠 CTI 的充分方案。
- 对选题的影响：
  - CTIBench 可作为实验设计和 baseline 参考，但不能直接作为论文创新点。
  - 后续更有价值的扩展是 evidence-grounded attribution、uncertainty-aware CTI 和 CTI text + provenance evidence 融合评测。

### 2026-07-04：Large Language Models are Unreliable for CTI

- 已沉淀：`Large Language Models are Unreliable for Cyber Threat Intelligence`
- 核心收获：
  - 许多 LLM-CTI 工作在短句或短段落上评估，容易高估模型能力。
  - 该文用 350 篇真实长度 APT 威胁报告评估信息抽取和信息生成。
  - LLM 在真实报告上存在性能不足、重复调用不一致和置信度校准较差的问题。
  - few-shot 和 fine-tuning 不一定提升效果，有时会降低性能或校准。
- 对选题的影响：
  - 后续方法必须评价真实长度报告、consistency、ECE、Brier Score 和证据可靠性。
  - “可信威胁归因”可以落到可度量指标，而不是只写概念。

### 2026-07-04：TTPXHunter

- 已沉淀：`TTPXHunter: Actionable Threat Intelligence Extraction as TTPs from Finished Cyber Threat Reports`
- 核心收获：
  - TTPXHunter 使用 SecureBERT、上下文数据增强、IOC 替换和相关句过滤，从完整威胁报告中抽取 ATT&CK TTP。
  - 它扩展了 TTPHunter 只覆盖常见 50 个 TTP 的限制。
  - 论文报告在增强句子数据集上 F1 为 92.42%，在 149 篇真实报告数据集上 F1 为 97.09%。
- 对选题的影响：
  - TTP extraction 已经是比较成熟的中间层，后续不宜把“抽 TTP”作为最终创新。
  - 更值得推进的是：TTP -> intent、TTP + provenance evidence -> evidence chain、TTP + uncertainty -> trustworthy attribution。

### 2026-07-04：SEvenLLM

- 已沉淀：`SEvenLLM: Benchmarking, Eliciting, and Enhancing Abilities of Large Language Models in Cyber Threat Intelligence`
- 核心收获：
  - SEvenLLM 构建了双语 CTI 指令数据、领域微调模型和 SEvenLLM-Bench。
  - 它覆盖 28 类安全事件任务，包括理解任务和生成任务。
  - Select-Instruct 先选择任务再生成 instruction/answer/thought，比普通 self-instruct 更适合领域数据构造。
- 对选题的影响：
  - SEvenLLM 可作为领域模型和指令数据背景，不应成为当前主创新。
  - 它的 Attack Intent Analysis 任务提示了 intent 方向，但需要更严格的标签、证据和评价设计。

### 2026-07-04：CTIConnect

- 已沉淀：`CTIConnect: A Benchmark for Retrieval-Augmented LLMs over Heterogeneous Cyber Threat Intelligence`
- 核心收获：
  - CTIConnect 将 CVE、CWE、CAPEC、MITRE ATT&CK 和 35 个来源的威胁报告整合为 1,860 个专家验证 QA。
  - 任务分为 Entity Linking、Entity Attribution、Multi-Document Synthesis 三类。
  - 论文指出 CTI 中存在 cross-source semantic gap，通用 vanilla RAG 不足以解决。
  - Domain-specific retrieval 相比 vanilla RAG 在不同任务上最高提升 +35.2%、+16.0%、+11.3%。
- 对选题的影响：
  - 后续不能只说“大模型 + RAG”，必须说明异构源、任务路由、检索策略、证据利用和评价指标。
  - CTIConnect 没有纳入 provenance graph，留下 `CTI + 日志溯源证据融合` 的空间。

### 2026-07-04：LOCALINTEL

- 已沉淀：`LocalIntel: Generating Organizational Threat Intelligence from Global and Local Cyber Knowledge`
- 核心收获：
  - LocalIntel 将公开全局 CTI 与组织本地知识库结合，生成组织级威胁情报。
  - 它的本地知识包括资产配置、软件版本、维护计划、组织 wiki 和可信历史 CTI。
  - 论文证明同一个 CVE 的处置建议会因本地配置不同而改变。
- 对选题的影响：
  - “本地上下文”是从 CTI 走向可行动安全决策的关键。
  - 后续可把 LocalIntel 的 local knowledge database 扩展为 provenance graph / InfoPath / attack summary graph。

### 2026-07-04：Beyond RAG for CTI

- 已沉淀：`Beyond RAG for Cyber Threat Intelligence: A Systematic Evaluation of Graph-Based and Agentic Retrieval`
- 核心收获：
  - 论文比较了 Semantic RAG、GraphRAG、Agentic GraphRAG 和 HybridRAG 四类 CTI 检索架构。
  - 图结构有助于 simple、single-hop、multi-hop CTI 问题，尤其适合 actor / malware / vulnerability / campaign 等关系推理。
  - 单纯 GraphRAG 不是可靠升级，会因为 text-to-Cypher 错误、schema gap 和空查询结果产生结构性幻觉。
  - HybridRAG 用图查询和文本检索互补，在 guided analyst-style questions 和拒答场景中更稳。
  - 可信 CTI/归因系统不能只看平均回答质量，还应评价拒答能力、延迟稳定性和灾难性失败模式。
- 对选题的影响：
  - 后续若做 LLM 增强威胁归因，不能只选 vector RAG 或 GraphRAG 单一路线。
  - 更稳的方向是 `CTI 文本证据 + ATT&CK/KG 图证据 + provenance/InfoPath 本地证据` 的混合检索与证据链生成。
  - 需要把 unanswerable / insufficient evidence 作为实验任务，要求模型在证据不足时拒绝归因并指出缺失证据。

### 2026-07-04：Opinion Pools

- 已沉淀：`A Modular Approach to Automatic Cyber Threat Attribution using Opinion Pools`
- 核心收获：
  - 论文把威胁归因从单体式黑盒分类改造成模块化架构。
  - 每个 attributor 基于一类证据输出候选 actor 的 PMF，再由 opinion pool 融合。
  - Pairing Aggregator 先对不同特征模块成对使用 logarithmic opinion pool，再用 linear opinion pool 得到最终 PMF。
  - 模拟实验显示模块化方法在 top-k accuracy 和 F-measure 上优于 Linear SVM / XGBoost 等 monolithic baselines，但该实验不能代表真实归因效果。
  - 中间 PMF 可以帮助分析师看到哪些证据支持哪些 actor，并发现可能的 false flag。
- 对选题的影响：
  - LLM 不应被设计成唯一归因裁判，而应作为 CTI/RAG attributor 或 evidence reasoning attributor。
  - 后续方向可采用 `CTI attributor + ATT&CK/KG attributor + provenance attributor + local context attributor -> weighted opinion pool -> actor PMF`。
  - 评价指标应包括 top-k accuracy、calibration、false-flag robustness 和解释性，而不只是 actor label accuracy。

### 2026-07-04：High Stakes, Low Certainty

- 已沉淀：`High Stakes, Low Certainty: Evaluating the Efficacy of High-Level Indicators of Compromise in Ransomware Attribution`
- 核心收获：
  - 论文用 20 位专家访谈和 27 份真实勒索软件事件报告检验高层 IoC/TTP 在勒索软件归因中的有效性。
  - 从业者实际更依赖 ransom note、communication channel、leak site、network IoC 等低层或勒索软件特定证据。
  - TTP 在同一 RTA 内部平均 overlap 只有 0.37，不同 RTA 聚合 TTP 平均 overlap 为 0.21，silhouette score 为负值，说明 TTP 很难形成清晰 actor cluster。
  - RaaS、rebranding、affiliate turnover 和 false flag 会削弱“actor 拥有稳定 TTP 签名”的假设。
- 对选题的影响：
  - TTP/ATT&CK 标注只能作为攻击行为语义层，不能直接当作高置信 actor attribution evidence。
  - Opinion Pools 中的 attributor 权重应考虑证据类型的区分度和可靠性，TTP attributor 不应默认高权重。
  - 后续方法应输出 evidence sufficiency、relative/absolute attribution 层级、actor PMF 和拒答，而不是单一 actor label。

### 2026-07-04：Multi-Step LLM Pipeline

- 已沉淀：`Multi-Step LLM Pipeline for Enhancing TTP Extraction in Cyber Threat Intelligence`
- 核心收获：
  - 论文将 TTP 抽取拆为 `Extractor -> Technique Candidate Generator -> Validator` 三阶段。
  - Extractor 将复杂 CTI 文本拆成 atomic threat actions；Candidate Generator 用 ATT&CK procedure embedding 召回 top-k technique；Validator 用 LLM 排序和过滤候选。
  - 作者框架报告 Precision 86.14、Recall 78.76、F1 82.28，优于 TTPXHunter、Finetuned-SecureBERT、AttacKG、LADDER 和单 ChatGPT-4o baseline。
  - Atomic reconstruction prompt 与候选约束对降低 LLM TTP 抽取幻觉有价值。
- 对选题的影响：
  - `CTI -> ATT&CK technique` 已经有成熟的多阶段 LLM + retrieval 方法，不能作为最终创新点。
  - 该 pipeline 可作为文本侧 TTP baseline 或前置模块，后续创新应放在 intent、evidence sufficiency、uncertainty-aware attribution 或 CTI-log alignment。
  - Validator 思想可上移为 technique validator、intent validator、evidence sufficiency validator 和 attribution confidence validator。

### 2026-07-04：Open-CyKG

- 已沉淀：`Open-CyKG: An Open Cyber Threat Intelligence Knowledge Graph`
- 核心收获：
  - Open-CyKG 提供了传统 CTI KG 构建路线：cybersecurity NER 识别实体，attention-based neural OIE 抽取关系三元组，再通过 canonicalization / fusion 构建知识图谱。
  - 它的开放仓库包含 OIE、NER、KG canonicalization notebook 和 Neo4j 可视化流程。
  - 它补齐的是 `CTI 文本 -> 实体/关系三元组 -> CTI KG` 底座，不直接解决 actor attribution、attack intent 或 evidence sufficiency。
- 对选题的影响：
  - CTI KG 可作为 GraphRAG / HybridRAG 的结构化证据源，但 KG 构建本身已经不是足够新的最终创新点。
  - 后续更有价值的是给 KG edge 加上 source sentence、confidence、temporal validity，并与 provenance graph / InfoPath 对齐。
  - Open-CyKG 可和 AttacKG、EXTRACTOR 一起构成 CTI text structuring 相关工作线。

### 2026-07-04：UNICORN

- 已沉淀：`UNICORN: Runtime Provenance-Based Detector for Advanced Persistent Threats`
- 核心收获：
  - UNICORN 将 whole-system provenance graph 流式转换为 graph histogram，再用 HistoSketch 生成固定长度 graph sketch，并用演化式聚类模型做 APT 异常检测。
  - 它针对 APT 的 low-and-slow、zero-day、长期潜伏和模型污染风险设计，不依赖预定义攻击签名。
  - 在 StreamSpot、DARPA TC 和自建 supply-chain APT 场景上表现较强，但输出主要是 graph-level alarm。
- 对选题的影响：
  - Provenance-based APT detection 已经有成熟经典基线，后续创新不宜只做“检测是否异常”。
  - 更稳的 Project05 方向是把异常检测信号转成可解释 evidence chain，再映射到 ATT&CK / intent / attribution confidence。
  - UNICORN 可作为 Kairos、DEPCOMM、THREATRACE、PROGRAPHER 之前的日志侧对比基线。

### 2026-07-05：THREATRACE

- 已沉淀：`THREATRACE: Detecting and Tracing Host-Based Threats in Node Level Through Provenance Graph Learning`
- 核心收获：
  - THREATRACE 将主机威胁检测形式化为 provenance graph 上的 anomalous node detection and tracing。
  - 它用 GraphSAGE 学习 benign node roles，把 node type 作为监督标签，并通过 multi-model framework 缓解节点类别不平衡和隐藏角色差异。
  - 相比 UNICORN 的 graph-level alarm，THREATRACE 能定位异常实体和 2-hop 局部上下文，更接近调查证据。
- 对选题的影响：
  - 日志侧证据粒度已经可到 node-level，Project05 后续创新不宜只做异常节点检测。
  - 更有价值的是把 anomalous nodes / local context 聚合成 attack story、InfoPath 或 attack summary graph，并映射到 ATT&CK / intent / evidence sufficiency。
  - THREATRACE 可作为 node-level provenance graph learning baseline。

### 2026-07-05：PROGRAPHER

- 已沉淀：`ProGraPher: An Anomaly Detection System based on Provenance Graph Embedding`
- 核心收获：
  - PROGRAPHER 将 streaming provenance graph 切成 temporal snapshots，用 graph2vec 学习 whole graph embedding，再用 TextRCNN 预测下一个 snapshot embedding。
  - 相比 UNICORN 的 graph-level alarm，PROGRAPHER 通过 Rooted Subgraph 排名把异常 snapshot 映射回 suspicious nodes，进一步降低分析师工作量。
  - 真实 Production EDR 数据上 PROGRAPHER AUC 0.943，显著高于 UNICORN 的 0.542。
- 对选题的影响：
  - PROGRAPHER 可作为 snapshot-level provenance graph embedding baseline。
  - 它证明日志侧 detector 可以输出 key indicators，但还不能自动生成 ATT&CK、intent 或 actor attribution explanation。

### 2026-07-05：APT-MMF

- 已沉淀：`APT-MMF: An advanced persistent threat actor attribution method based on multimodal and multilevel feature fusion`
- 核心收获：
  - APT-MMF 将 APT reports 与 IOC 信息建模为 heterogeneous attributed graph，融合 attribute type、BERT text、Node2vec topology 三类节点特征。
  - 它通过 IOC type-level、metapath-based neighbor node-level、metapath semantic-level 三层 attention 学习 report node 表示并进行 actor classification。
  - 数据集包含 1,300 reports、21 APT groups、24,694 nodes、40,335 relationships；最终 Micro-F1 0.8321、Macro-F1 0.7051。
- 对选题的影响：
  - APT-MMF 是 CTI/IOC graph-based actor attribution 强基线。
  - 它提供了 report-IOC-metapath 的证据组织方式，但仍缺少 unknown actor、false flag、证据不足拒答和日志侧 provenance evidence 对齐。

### 2026-07-05：ADAPT it!

- 已沉淀：`ADAPT it! Automating APT Campaign and Group Attribution by Leveraging and Linking Heterogeneous Files`
- 核心收获：
  - ADAPT 将 APT attribution 拆成 campaign-level Intra-Clustering 和 group-level Inter-Clustering。
  - 它覆盖 executables 与 documents，使用 file-specific、generic、pattern-based 和 infrastructure linking features。
  - 数据集包含 6,134 APT samples、92 groups；campaign reference dataset 包含 230 samples、22 campaigns、17 groups。
  - Reference dataset 上 campaign clustering 对 executables F1 0.91、documents F1 0.92，group attribution F1 0.89。
- 对选题的影响：
  - ADAPT 是样本侧 heterogeneous file-based campaign/group attribution 强基线。
  - 它与 APT-MMF 互补，可共同支撑“报告侧 + 样本侧 + 日志侧”的多源证据融合方向。

## 下一步任务

1. 主线阅读已完成一轮沉淀。
2. 下一步维护 `04-progress/mainline-synthesis-20260705.md`，整理主线收束图：日志侧 evidence、CTI/IOC graph attribution、样本侧 campaign/group attribution、LLM/RAG/KG、可信归因评估。
3. 在完成文献沉淀并初步凝练方向后，做截至 2026-07-04 的最新成果/撞题检索。

## 主线校准

- 当前主线：LLM 增强威胁溯源 / 攻击归因。
- 支撑模块：CTI 报告、ATT&CK/TTP、RAG/KG、provenance graph、可信评估。
- 阅读判断标准：每篇论文是否帮助 LLM 更好地理解溯源证据、重构攻击链、识别攻击意图、生成证据增强归因解释，或评估归因可信度。

## 延后事项

- `形成 3 个候选硕士论文题目，并用可行性矩阵比较`：推迟到所有核心/扩展文献读完后，由用户手动决定。
- `Agentic AI / 多智能体安全调查`：后置为 appendix 补充阅读，先完成 LLM 与现有溯源/归因/RAG/KG 主线。

## 周进展模板

### Week YYYY-WW

- 本周目标：
- 本周完成：
- 读完论文：
- 关键收获：
- 新增 idea：
- 遇到问题：
- 下周计划：
### 2026-07-05：撞题补读 AURA / Guru / AttacKG+ / MM-AttacKG / TAA-EPLMR

- 已沉淀：
  - `AURA: A Multi-Agent Intelligence Framework for Knowledge-Enhanced Cyber Threat Attribution`
  - `On Technique Identification and Threat-Actor Attribution using LLMs and Embedding Models`
  - `AttacKG+: Boosting Attack Knowledge Graph Construction with Large Language Models`
  - `MM-AttacKG: A Multimodal Approach to Attack Graph Construction with Large Language Models`
  - `TAA-EPLMR: Threat Actor Attribution via Evidence Path-Enhanced Large Language Model Reasoning`，当时全文待获取；2026-07-08 已完成新主线复核。
- 核心收获：
  - AURA 已经把 RAG、多智能体、LLM、APT attribution 和自然语言 justification 结合起来，且输入包括 TTP、IOC、malware、tools、timeline。
  - Guru et al. 已经做了 `CTI -> TTP -> actor ranking`，并证明 TTP-only attribution 噪声高、只能优于随机但不足以自动化高风险归因。
  - AttacKG+ 已经用 LLM 构建文本 attack knowledge graph；MM-AttacKG 进一步把 CTI 图像纳入多模态 attack graph construction。
  - TAA-EPLMR 题名高度接近 Project05 原始 idea；2026-07-08 已确认其覆盖 evidence path、confidence、reasoning chain、incomplete/noisy robustness，但不覆盖 refusal、granularity gate、active evidence acquisition。
- 对选题的影响：
  - 不能再把“多源证据融合 + LLM 辅助 APT 归因解释”作为宽题直接推进。
  - 更稳的切口是：面向证据不完整场景的证据充分性感知、置信度校准、分层降级归因与可拒答机制。
  - 方法设计应以 `能不能归因到 actor` 为核心，而不是只追求输出一个 actor label。
