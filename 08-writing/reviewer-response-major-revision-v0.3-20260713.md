# Reviewer Major Revision 回复与落实矩阵 v0.3

日期：2026-07-13

基准：用户提供的最新稿重审报告；修订稿 `paper-main-draft-v0.7-c12-operational-stress-20260713.md`

## 总体回应

我们接受 Reviewer 对稿件类型的核心判断：当前证据不支持“新规划器性能论文”或“新 actor attribution SOTA”。v0.7 继续把贡献限定为信息边界约束的调查控制框架，并把 M2 限定为 C07-C10 的透明部署锚点。新增 C12 关闭一个生产 SOC 双流数据接入缺口，外部源码审计关闭公开 AFA/取证规划代码是否遗漏的过程缺口；二者都不被包装成算法优越性、actor 真值或官方同任务复现。人工效度和真实任务终点仍明确保留为投稿门槛。

## Major concerns

| Reviewer concern | 处理状态 | 已完成修订 | 剩余风险 |
|---|---|---|---|
| M1 科学突破与工程协议混淆 | 已处理 | 标题、摘要、引言、贡献和结论均以框架/接口为中心 | 顶会重要性仍受独立样本与外部终点限制 |
| M2 没有胜过强锚点的新算法 | 已处理 | M2、学习、AFA、Depth-2 均作为可证伪策略；C11/C12 排序反转原样报告 | 不再主张算法 SOTA |
| M3 内部 success 与“归因”错位 | 部分处理 | 使用可支撑调查结论粒度；C12 actor 节点留空且上限 G1 | 双人盲标仍 `awaiting_annotations`，无 actor accuracy |
| M4 独立样本与外部效度 | 部分处理 | C11 增加仿真第三封装；C12 增加一个生产 SOC 双流 incident | C12 仍是单 incident，45 条件是重复测量 |
| M5 辅稿叙事漂移 | 已处理 | v0.7、作者记录、权威索引、严谨性审计同步升级 | 历史稿仅保留为过程档案 |
| M6 缺外部 AFA 基线 | 部分处理 | 完成 AFABench、WinRegRL、AACO 官方/作者仓库 commit 与任务映射审计 | direct same-task Gate 不通过，尚无冻结 endpoint adapter 数值 |

## A 级修订

1. **贡献锁定**：已完成。题目与主张均为调查控制；禁止“新归因器/规划器更优”暗示。
2. **人工标注**：未完成。C07-C11 模板、管理员映射和分析脚本已冻结；C12 尚未入包，不得用 LLM 或代码代填。
3. **AFA 基线**：领域适配已有数值；官方代码来源、commit、能力和任务差异审计已完成。下一 Gate 是冻结 external endpoint adapter，而非直接改名。
4. **辅稿统一**：v0.7 权威索引、作者记录和严谨性审计已同步；C11、C12 与 G3 主结果分层报告。
5. **专利法律门槛**：技术一致性已复核；中文补检、权属、公开日和代理师审查未完成。

## B/C 级修订

| 项目 | 状态 | 结果 |
|---|---|---|
| M2 权重敏感性 | 完成 | 16 个 OAT 变体均保持 success=1；13 个完全同序 |
| 粒度阈值敏感性 | 完成 | 三档阈值未改变 C07-C10，受关键节点条件主导 |
| OR vs AND | 完成 | C11 只改 AND→OR 即把 M2 成本从 3.6667 降至 1.0222 |
| 非短视边界 | 完成 | C11 Depth-2 退化、C12 匹配 Oracle；不启动 DQN，不外推平均收益 |
| 动作映射真实 SOC | 完成一层 | C07-C12 五种动作类型 5/5 映射 WinRegRL 家族；词汇映射不等于同任务 |
| Related Work 对照 | 完成 | 加入 AFABench、AACO、NOCTA、WinRegRL 的状态/端点边界 |
| C12 来源 Gate | 完成 | 13,119→5→2；剔除 3 条产品标签多源、实际 stream 单源候选 |
| C12 冻结策略迁移 | 完成 | Depth-2/Oracle 0.8889，M2 1.4222，AFA Myopic 1.5111；均零越界 |

## 新增证据的边界

- C12 只支持一个生产 SOC 衍生 incident 的来源回指、信息边界与 G1 截断，不支持自然 APT actor 归因。
- 119 条 leads 不是 119 个攻击；45 个 mask/intensity/seed 条件不是 45 个独立 incident。
- 49 条 GraphML 边均为厂商 `INCIDENT_LINK`，只作 context，不作原始遥测或因果真值。
- `Disrupted` 是分析师确认/介入筛选，不是独立 actor/campaign ground truth。
- Depth-2 在 C12 匹配 Oracle 只支持单案例结果；其在 C11 的退化禁止“非短视普遍更优”表述。
- AFABench、AACO、WinRegRL 的源码审计不等于官方同任务数值复现；现有 AFA-VOI 继续称领域适配。
- 人工标签仍为空；本文不得报告 kappa、人工准确率或分析师效用。

## 修订后推荐姿态

在双人标注、更多独立运营 incident、真实任务终点和 external endpoint adapter 尚未闭合前，v0.7 仍不应包装成 Top 安全会的成熟算法贡献。它已经成为一篇范围更诚实、来源更可复核、负结果更完整的调查控制框架稿；下一次质量跃迁应来自人工构念效度或独立运营终点，而不是增加模型名称。
