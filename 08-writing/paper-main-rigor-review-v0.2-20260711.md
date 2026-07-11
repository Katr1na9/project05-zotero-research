# Project05 论文语义严谨性审计 v0.2

日期：2026-07-11

对象：`paper-main-draft-v0.4-major-revision-20260711.md`、三张主图、AFA/敏感性结果与 Reviewer 回复矩阵

## 总评

综合评分：**4.1/5，二线 venue Borderline / major revision；Top 安全 venue 仍为 Weak Reject。**

本轮真正改善的是主张—证据一致性：稿件已停止包装新归因器或新规划器，增加同接口 AFA 适配、M2/粒度敏感性、形式接口性质和唯一权威文档入口。没有改善的核心天花板仍是人工效度、独立案例数和真实归因终点，因此不因写作更完整而上调为顶会可接收。

## 六维评分

| 维度 | 分数 | 判断 |
|---|---:|---|
| D1 Evidence relevance | 4 | 主要经验主张均有冻结结果；AFA 与敏感性数字已进入回归测试 |
| D2 Falsifiability | 5 | RQ1-RQ4、升级门槛和复杂策略负结果均明确保留 |
| D3 Scope calibration | 5 | 四案例/两家族、内部代理、领域适配、LLM 未调用均清楚 |
| D4 Argument coherence | 4 | 标题、摘要、框架、实验和专利边界统一到调查控制 |
| D5 Exploration integrity | 5 | M3a、学习、AFA、Depth-2 和 Gate B 的负结果均未隐藏 |
| D6 Methodological rigor | 2 | 双人标注为空、无真实 attribution accuracy、外部 AFA 非官方复现 |

## 已关闭的 Reviewer 风险

1. **算法叙事错位**：M2 改为透明部署策略，M3a/学习/AFA/前瞻改为同接口策略族。
2. **辅稿漂移**：建立 `AUTHORITATIVE-DOCUMENTS-20260711.md`，旧 M3a/三案例文件标为历史。
3. **完全缺少 AFA 对照**：实现并预登记 Myopic/Rollout-H3 领域适配，且不冒充官方复现。
4. **M2 系数未经检查**：完成 16 个单权重 ±25% 扰动。
5. **覆盖语义未检查**：完成 OR/AND 压力，并识别真实四例的不可识别性。
6. **图表统计单位含混**：三张图均写出独立案例和重复条件边界。

## 仍然阻止强主张的问题

### Major 1：人工效度未交付

标注包存在但两名分析师标签为空。当前 G0-G3 只是内部代理；OR/AND 开发压力已经证明组合语义会显著改变 success。没有 IAA、校准和 adjudication 前，不能把 success 写成“归因能力”。

### Major 2：外部效度仍低

C07-C10 只有四个参数锁定案例，来自 DARPA TC E5 与 OpTC 两个主要家族。180 个 episode 是重复测量。现有结果适合证明实现与失败边界，不适合统计泛化。

### Major 3：AFA 基线只部分关闭

领域适配确保了同动作空间的公平比较，但不是 NOCTA/WinRegRL 官方实现。它足以避免“完全没有 AFA 对照”，不足以证明相对公开方法的 SOTA。

### Major 4：缺少真实任务终点

论文没有 actor/campaign ground-truth accuracy、分析师节省时间、调查建议采纳率或错误归因风险终点。题目已用 investigation control 限定，但重要性上限仍受此约束。

## 形式性质审计

- 性质 1 只证明节点级恢复映射泄漏，正文已明确不等于 claim 身份或完整 Oracle。
- 性质 2 只在图、语义、阈值和 `support_ceiling` 固定且 claims 单调增加时成立；正文未外推到人工判断。
- 性质 3 是 Bellman STOP 条件；正文正确指出一步 gain-cost 在互补/解锁存在时通常不是充分条件。

这些性质提高了接口清晰度，但不是新算法的性能定理。

## 最终审稿姿态

- 当前可以投稿：强调可审计框架、信息边界、透明部署锚点与完整负结果的安全系统/应用方法 venue。
- 当前不可投稿为：声称提高 APT actor attribution accuracy 或提出优于 AFA/学习方法的新 SOTA 规划器。
- 下一次最有价值的修订：双人盲标与人工粒度校准；其次才是第三数据家族和官方 AFA 映射。
