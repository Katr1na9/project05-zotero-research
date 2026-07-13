# Project05 论文语义严谨性审计 v0.5

日期：2026-07-13

对象：`paper-main-draft-v0.7-c12-operational-stress-20260713.md`、C07-C10 主结果、C11 OTRF 结果、C12 WitFoo 两级 Gate 与冻结策略迁移、外部 AFA 源码审计、信息边界回归测试及 C07-C11 空标注包

## 总评

综合评分：**4.4/5，二线安全/系统或应用方法 venue 为 Borderline；Top 安全 venue 仍为 Weak Reject。**

C12 与外部源码审计提高了稿件的外部效度和比较诚实性：框架已经接入一个生产 SOC 衍生的 ASA/Windows AD 双流 incident，并能把厂商相关图限制为 context；AFABench、AACO 和 WinRegRL 的官方/作者代码也已固定到 commit 并完成任务端点审计。二者都没有改变论文的核心上限：C12 没有 actor/campaign 真值，只有一个 G1 incident；公开实现与本文任务不等价，尚无可称为官方同任务复现的数值；人工粒度效度仍为空。

本评分评价稿件内部的语义严谨性，不等同于 venue 接收概率。v0.7 已比 v0.6 更完整，但新增证据主要强化“可接入、会拒绝伪多源、会限制主张”，而不是形成新的算法优越性。

## 六维评分

| 维度 | 分数 | 判断 |
|---|---:|---|
| D1 Evidence relevance | 4 | 主要主张均有冻结结果、来源哈希或回归测试；内部 success 仍不能支撑真实归因能力 |
| D2 Falsifiability | 5 | RQ1-RQ5、来源 Gate、策略升级门槛和语义反事实均可证伪 |
| D3 Scope calibration | 5 | C11、C12 分别限定为单个 G2 仿真链与 G1 运营 incident，均不并入 G3 聚合 |
| D4 Argument coherence | 4 | 问题、信息边界、外部方法映射、分层结果与结论一致；人工终点仍未闭环 |
| D5 Exploration integrity | 5 | C12 剔除 3 个伪多源候选，并保留 AFA Myopic 变差、Depth-2 案例特定变好等双向结果 |
| D6 Methodological rigor | 4 | 两级来源 Gate、锁文件、源码 commit、跨实验模型哈希和回归较完整；仍缺双人标签、external endpoint 数值和真实任务终点 |

## v0.7 新增的有效证据

1. **运营数据可接入**：同一 schema 可从生产 SOC 衍生 embedded leads 编译 claims、动作、STOP 与 G1 上限。
2. **伪多源可拒绝**：13,119 条模板记录经元数据 Gate 得到 5 条，事件源 Gate 只保留 2 条；3 条因产品标签多源但原始 stream 单源被剔除。
3. **原始证据与投影分离**：选定 C12 的 49 条 GraphML 边全部为 `INCIDENT_LINK`；gold observations 来自 117 条 ASA 和 2 条 Windows AD leads。
4. **自然粒度上限**：`actors` 为空，actor/campaign 节点没有 required claims，target 与 ceiling 固定为 G1，45 个条件均无越界。
5. **第三次策略排序变化**：C12 中 Depth-2/Oracle 成本 0.8889，M2 为 1.4222，AFA Myopic 为 1.5111；该结果反证按方法族固定方向外推。
6. **外部方法来源闭环**：AFABench、WinRegRL、AACO 仓库 commit 与能力清单已冻结；C07-C12 实际动作类型 5/5 可映射到 WinRegRL 动作族。
7. **任务不等价被显式记录**：静态 feature reveal、完整训练实例或专家 MDP 均不等于隐藏恢复、通道执行和粒度终点，因此没有制造错误的官方同任务数值。

## 仍然成立的 Major 风险

### Major 1：人工构念效度仍为空

C07-C11 盲标包有 114 个 item，但 A/B 与裁决模板仍为空；C12 尚未加入独立人工标注。没有 IAA、裁决与代理校准前，G0-G3 只能称结构代理。

### Major 2：独立样本仍过少

C07-C10 只有四个 G3 案例，C11 与 C12 各只有一个案例。C12 的 45 个条件是同一 incident 内重复，不是 45 个自然攻击；单一公开数据集也不能代表多组织部署。

### Major 3：C12 不是独立攻击真值

incident、ATT&CK 映射、模板报告和 GraphML 均来自厂商自动相关。`Disrupted` 表示分析师确认并介入，但不提供 actor/campaign ground truth；清洗实体和时钟冲突还限制跨流因果重建。

### Major 4：正式外部数值基线仍未闭合

源码和任务映射已完成，但 direct same-task Gate 不通过。现有 AFA-VOI 仍是本文领域适配；正式 external endpoint adapter 需要另行冻结静态目标、训练可见性、STOP、成本和 feature-to-channel 转换。

### Major 5：策略排序反转仍是案例证据

C11 与 C12 都改变了 C07-C10 排序，但各自只有一个目标/动作结构。Depth-2 在 C11 退化、C12 匹配 Oracle，不能据此推出非短视规划的平均运营收益。

### Major 6：真实任务终点缺失

稿件没有 actor/campaign accuracy、分析师节省时间、建议采纳率或错误归因风险终点。标题已限定 investigation control，但该缺口仍限制重要性主张。

## 冻结写作红线

1. C07-C10、C11、C12 分层报告，不计算跨 G3/G2/G1 总成本均值。
2. C12 只称生产 SOC 衍生、分析师已处置的双流 incident，不称自然 APT actor benchmark。
3. GraphML 只称厂商相关投影 context，不称原始遥测图或独立因果链。
4. M2 只称 C07-C10 的透明部署锚点；Depth-2 在 C12 只称案例特定结果。
5. AFA-VOI 只称领域适配；AFABench、AACO、NOCTA、WinRegRL 不称官方同任务复现。
6. LLM 未进入主实验，不能作为实验增益来源或标题核心模块。
7. 45 个 C12 条件不得重计为 45 个真实攻击。

## 最终审稿姿态

- **可支持的稿型**：信息边界、可审计调查控制、分层来源 Gate、透明策略局部价值和跨场景负结果为核心的安全系统/应用方法论文。
- **不可支持的稿型**：新的 actor attribution SOTA、真实多传感器因果融合、官方 AFA 复现、跨域最优规划器或 LLM 增益论文。
- **下一项最高收益工作**：完成双人盲标和粒度校准；随后冻结 external endpoint adapter，或增加第二个独立运营 incident 与分析师效用终点。
