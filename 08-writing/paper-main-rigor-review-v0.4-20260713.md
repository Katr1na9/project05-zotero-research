# Project05 论文语义严谨性审计 v0.4

日期：2026-07-13

对象：`paper-main-draft-v0.6-c11-policy-transfer-20260713.md`、C07-C10 主结果、C11 OTRF AND/OR 与冻结策略迁移结果、信息边界回归测试及 C07-C11 标注包

## 总评

综合评分：**4.3/5，二线安全/系统或应用方法 venue 为 Borderline；Top 安全 venue 仍为 Weak Reject。**

C11 的主要价值是把同一调查控制接口迁移到第三种 Windows JSONL/多 provider 封装，并用固定锚点未命中形成可审计的 G3→G2 自然降级。新增冻结迁移补齐了 Logistic、XGBoost、AFA-VOI 和 Depth-2：学习器与一步 AFA 在 C11 降低 M2 成本，而 Depth-2 产生一次退化，进一步反证固定策略排序可跨场景保持。它仍未补足人工粒度效度、真实 actor/campaign 正确性或独立自然攻击样本，因此不能据此升级为跨域泛化或归因性能贡献。

本评分评价的是稿件内部的语义严谨性，不等同于 venue 接收概率。稿件对负结果和边界的处理已经成熟，但核心构念效度与外部任务终点仍决定投稿上限。

## 六维评分

| 维度 | 分数 | 判断 |
|---|---:|---|
| D1 Evidence relevance | 4 | 主要主张均由冻结结果、原始回指或回归测试支撑；内部 success 仍不能支撑真实归因能力 |
| D2 Falsifiability | 5 | RQ1-RQ4、策略升级门槛、C11 失败保留和 OR/AND 反事实均可证伪 |
| D3 Scope calibration | 5 | C11 被限定为单个 APT29 emulation、第三封装和 G2 压力，不并入 G3 聚合 |
| D4 Argument coherence | 4 | 问题、信息边界、策略比较、负结果和结论一致；人工效度尚未闭环 |
| D5 Exploration integrity | 5 | C07-C10 负结果、C11 学习器正向迁移、Depth-2 退化与 M2 非最低成本均原样保留 |
| D6 Methodological rigor | 3 | 265 项回归、固定源回指、哈希复现和多类基线较完整；仍缺双人标签、真实任务终点和官方 AFA 复现 |

## C11 新增的有效证据

1. **接口可迁移性**：同一 schema、规划接口和 STOP/粒度约束可接入 OTRF Windows JSONL，而不需要把隐藏恢复集合暴露给非 Oracle 策略。
2. **自然缺口保留**：固定 `3aka3.doc` 锚点未命中后没有替换任务节点，目标按冻结规则由 G3 降为 G2。
3. **语义敏感性**：在 claims、动作、mask、seed、目标和预算不变时，仅把 AND 改为 OR，M2 成本从 3.6667 降至 1.0222。
4. **策略外推反例**：Coverage/M1 在 C11 的平均成本 3.2444，低于 M2 的 3.6667，因而 M2 只能称 C07-C10 的透明部署锚点。
5. **来源可复核性**：固定 OTRF commit、ZIP 字节数和 SHA-256，8 条 claim 的行号、RecordNumber 与锚点测试通过；重跑摘要哈希与冻结结果一致。
6. **冻结策略排序反转**：XGBoost/Logistic 在 C11 的成本为 3.0667，AFA-VOI Myopic 为 3.5556，均低于 M2 的 3.6667；Depth-2 success 为 0.9778。三个 XGBoost 模型哈希与 C07-C10 主评估一致，C11 未进入训练。
7. **离线—序贯指标分离**：Logistic 的离线 AP 高于 XGBoost，但两者序贯成本相同，反证 action-level 分类指标可替代闭环策略效用。

## 仍然成立的 Major 风险

### Major 1：人工构念效度为空

C07-C11 盲标包已有 27 个 claim、27 个公开意图和 60 个粒度状态，共 114 个 item，但 A/B 与裁决模板均为空。没有 IAA、裁决与工程代理校准前，G0-G3 只能称结构代理，内部 success 不能改写为归因准确率。

### Major 2：外部效度增量有限

C11 增加的是一个 APT29 emulation 链和第三种遥测封装，不是自然发生的独立 APT engagement。45 个条件是同一案例内的 mask/intensity/seed 重复，不能作为 45 个独立攻击样本。

### Major 3：证据独立性与节点语义有限

多 claim 来自同一主机归档内不同 Windows provider family，不是独立传感器 corroboration；Host 与 Zeek 时间窗不重叠。N02/N05 只证明 collection/archiving，不能单独证明网络 exfiltration。

### Major 4：C11 排序反转仍是单案例证据

C11 已补齐冻结策略族，但只有一个 AND 多 Claim/G2 仿真链。XGBoost/Logistic 的成本优势不能据此写成稳定跨域改进；AFA-VOI 仍是同接口领域适配，不是 NOCTA 或 WinRegRL 官方实现。

### Major 5：真实任务终点缺失

稿件没有 actor/campaign ground-truth accuracy、分析师节省时间、建议采纳率或错误归因风险终点。标题已用 investigation control 限定任务，但该缺口仍限制重要性主张。

## 冻结写作红线

1. C11 只称“内部冻结”或“预先指定”，不称外部可验证 preregistration。
2. C07-C10 的 180 个条件与 C11 的 45 个条件分别报告，不计算五案例总成本均值。
3. M2 只称 C07-C10 的透明部署锚点，不称跨场景最佳、全局最优或 SOTA。
4. C11 只支持 G2 调查链、封装迁移和覆盖语义压力，不支持未知 actor 预测或 campaign 正确性。
5. LLM 未进入主实验，不能作为实验增益来源或标题核心模块。
6. C11 中 XGBoost/Logistic 的结果只称冻结迁移反例，不称跨域泛化或新主模型。

## 最终审稿姿态

- **可支持的稿型**：以信息边界、可审计调查控制、透明策略局部价值和完整负结果为核心的安全系统/应用方法论文。
- **不可支持的稿型**：新的 actor attribution SOTA、跨域最优规划器、真实多传感器融合或 LLM 增益论文。
- **下一项最高收益工作**：27/27 来源摘录已经恢复；现在直接完成双人盲标、IAA 与粒度校准，随后再增加自然 engagement 或分析师效用终点。
