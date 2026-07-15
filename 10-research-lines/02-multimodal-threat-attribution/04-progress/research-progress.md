# P05-L2 Research Progress

## 2026-07-12：工作区初始化

- 按 Project05 多研究线 SOP 创建独立 `00-09` 工作区。
- ARS 路由确定为 `deep-research / socratic`，当前停在 Stage 0 Inbox。
- 已记录原始多模态 idea、初始风险、共享资产边界和第一轮 RQ 问题。
- 尚未检索、形成 RQ、选择模态、指定模型、创建数据集或启动实验。
- 下一步：用户完成 Socratic 第一轮，随后生成 RQ Summary；用户确认后才进入正式 FINER/G1。

## 2026-07-12：Project03 五模态交接

- 将本线模态范围从泛化文本/图像/日志候选，收敛到 `IPv4 / IPv6 / MPLS / GeoNetworking / SCION` 五种网络协议/转发模式。
- 审计 Project03 的需求、理论边界、逐模态验收、开发/踩坑日志及核心 stage/intent 代码。
- 确认 Project03 的现有输出属于 observed-stage、chain candidate 与 intent candidate，不是完整行为因果重建或真实心理意图。
- 发现关键研究缺口：configured、intended 与 observed wire modality 被压缩为单字段；SCION 当前尤其存在 label/wire 不一致。
- 发现 intent 检索中的 modality 主要只是关键词，尚未证明对候选判断提供独立信息。
- 建立交接审计、五个候选 idea 和数据复用验证计划；I1/I3 优先进入截至 2026-07-12 的撞题检索。
- 尚未恢复 120 条批次原始 PCAP/CSV，也未冻结 RQ、方法或论文题目。

## 2026-07-12：候选 idea 初步撞题检索

- 核验 path verification、proof-of-transit、P4/INT、protocol-agnostic IDS、attack-stage uncertainty、network security provenance 和 forensic coverage 近邻。
- I1 宽版本被 EPIC、ID-INT、P4Prime、SecTracer、RFC 9315 与 proof-of-transit 专利覆盖。
- I2 被 protocol-agnostic IDS 与 2025 网络流量多模态融合工作显著压缩，只能作为鲁棒性/数据问题。
- I3 被 2025 EDL/XAPT 与 2026 StageFinder 直接覆盖，只能作为下游校准评价。
- 暂存 W1：协议 transformation 对攻击行为 evidence supportability 的影响；状态 `amber`。
- 已建立 P0-P2 阅读队列；下一步先读 P0 五篇，不生成论文题目。

## 2026-07-13：按用户贡献边界重置主线

- 用户明确：Project03 中可推广的是 PCAP/上游检测结果到 ThreatObservation、图谱查询匹配、溯源定位和意图候选；CENI controller/网元部署是工程妥协。
- 代码复核确认：显式 `threat_observation` 只覆盖 benign/unknown 分支，恶意样本使用 `threat + attack_stage`；当前没有统一的证据锚定 observation schema。
- 本地 CENI 图谱实际为 130 个 CAPEC attack pattern 和 24 条 `CanPrecede` 关系，未携带 technique/tactic；不能把它表述为完整 ATT&CK 多模态图谱。
- 将 IPv4/IPv6/MPLS/Geo/SCION 从“天然五模态”降为环境/协议条件；候选证据视图改为 packet、header/session、flow、上游模型输出和图谱证据。
- 建立截至 2026-07-13 的 PCAP + LLM + KG + trace/intent 检索协议。
- 初步发现 CyberSleuth、From Anomaly to Attack Path、Holmes、KLAGE、mmTraffic 和 Security Logs to ATT&CK Insights 等强撞题工作；宽泛的“PCAP + LLM + 图谱”不再具备新颖性。
- 下一步：冻结纳入集，逐篇获取全文并完成精读，再构建功能级撞题矩阵；在此之前不提交最终 idea。

## 2026-07-13：纳入图谱构建与流量/日志双线

- 用户确认新论文可纳入图谱构建，以及日志侧与流量侧的双侧贡献。
- 复核 HFish 路线：已定义数据库表、标准事件 schema、行为图节点/边和阶段/战术候选；但当前仓库不存在 `hfish_log_bridge.py`，属于可继承设计而非完成代码。
- 区分三类图：既有静态 CAPEC/ATT&CK/CTI 背景图、Project03 导出的任务子图、待新建的双源事件/证据图。新论文只可对第三类及其跨图对齐主张原创贡献。
- 检索范围扩展为 paired PCAP + log、multi-source security telemetry、dual-source event graph、LLM investigation 和 evidence grounding。

## 2026-07-13 至 2026-07-15：完成首轮语料与功能矩阵

- 将 C01-C41/F01-F05 按输入、图类型、LLM 角色、输出、raw anchor 和 cross-source edge 映射到功能矩阵。
- 精读 direct PCAP、traffic+log、provenance、trust/calibration 和 agent-last 文献；MuSAR 另审计官方代码/预处理数据。
- 宽泛 `traffic + logs -> graph -> LLM chain` 被直接文献覆盖，不再保留为创新主张。
- 将剩余问题收紧为 R1-R5：source-preserving dual graph、calibrated relation、conflict/missing propagation、chain-grounded goal intent 和 evidence replay。

## 2026-07-14 至 2026-07-15：二次撞题检索与新增精读

- 以 R1-R5 精确措辞执行二次检索、历史 prior-art 检索和 MuSAR/Traffic2Chain 引文 sweep。
- 新增 C42-C61/F06；完成 SAURONEYES、APTGuard、BotFence、APMP、ProHunter、SherAgent、ProvAgent 等全文精读。
- T-Trace、M-IDAS、Citar、ANTEATER 因访问/撤回状态降级为边界笔记，未冒充全文精读。
- BotFence 与 He et al. 2016 证明 broad network/packet+host/log graph 已存在；APMP/MPCA 证明 relation completion/confidence 宽词已存在。
- 二次检索后 R2 “campaign-disjoint calibrated multi-candidate packet-log relation”成为最强残余。

## 2026-07-15：数据、专利与候选题收敛

- 数据集排序：ProvICS > AIT v2 > CICAPT-IIoT > ProvCon；OpTC 只作 flow/log 辅助。
- 记录 CN121356897B、CN121940189A、CN113783896B、CN116112211A/B 等专利红线，禁止“首次多源图/首次攻击链/首次意图”表述。
- 形成 A/B/C 三个候选题、加权可行性矩阵、方法/实验框架和 kill criteria。
- 推荐“A 叙事 + B 必做核心 + C 可选扩展”；Devil's Advocate Checkpoint 2 允许提交用户选择，但禁止提前实现。
- Zotero 同步已核验：20 条新记录均进入目标集合，12 条附带可直接打开的存储 PDF，8 条为 metadata-only；未制造标题重复。
- SherAgent 已在全局文库存在且带 PDF，为避免重复未重新导入；它仍需用户在 Zotero 中手动拖入目标集合。
- 当前下一步：推送 GitHub 后，由用户人工选择方向。
