# Project05 实验案例清单 v0.1

日期：2026-07-08  
状态：Stage 5 / Experiment Design - Phase 0  
对应实验方案：[experiment-plan-v0.1-20260707.md](experiment-plan-v0.1-20260707.md)

## 1. 目的

本清单用于把 Project05 的实验对象从“想法”落成可构造的数据单元。每个实验案例不是一篇论文或一个数据集，而是：

```text
一个攻击案例 / campaign scenario / attack trace
  + 一组 CTI 侧行为主张
  + 一组本地可观测证据
  + 一个完整证据版本
  + 多个遮蔽后的不完整证据版本
  + 可执行的取证动作集合
```

第一版 MVP 的目标不是覆盖所有 APT 归因场景，而是验证：

1. evidence state 是否能判断当前可支撑归因粒度；
2. acquisition action 是否能恢复被遮蔽证据；
3. Project05 planner 是否比 random / fixed-order / coverage-greedy 更低成本达到目标粒度。

## 2. 入选标准

### 2.1 必须满足

- 有公开或可构造的攻击行为链；
- 能映射至少 3 个 ATT&CK technique 或关键行为节点；
- 能构造本地证据集合，例如 provenance/log/network/IOC/sample/infrastructure；
- 能人为遮蔽证据并通过动作恢复；
- 有可定义的目标粒度，至少到 `G1 technique`、`G2 tactic/intent` 或 `G3 campaign`。

### 2.2 MVP 优先

- 本地证据结构清楚，最好来自 DARPA TC / OpTC / investigation graph；
- CTI 侧行为描述可从公开报告、ATT&CK procedure、POIROT/MEGR-APT query graph 或手工结构化描述得到；
- 不强依赖 named actor ground truth；
- 动作能直接映射到恢复被遮蔽的证据集合。

### 2.3 暂不作为 MVP 主案例

- 只有 CTI/IOC，没有本地 provenance/log 证据；
- 只有 actor 标签分类，没有攻击链证据；
- 需要在线访问商业情报源或不可公开数据；
- 只能验证 LLM 归因准确率，无法验证主动取证规划。

## 3. 推荐 MVP 案例池

| Case ID | 优先级 | 来源 | 场景定位 | 可用证据 | 目标粒度 | MVP 用法 |
|---|---:|---|---|---|---|---|
| C01 | P0 | DARPA TC / THEIA 类 Linux trace | 主机侧多阶段入侵 | provenance/log、process、file、network、IOC | G1-G3 | 第一版主案例，用于验证 stage mask 和 provenance action |
| C02 | P0 | DARPA TC / CADETS 类 FreeBSD trace | 系统审计日志中的攻击链 | provenance/log、process、file、network | G1-G3 | 第二个主案例，用于验证跨平台泛化 |
| C03 | P0 | DARPA TC / TRACE 类 Windows trace | Windows 主机攻击行为 | process、registry、file、network、command line | G1-G3 | 第三个主案例，用于验证 registry / Windows-specific evidence |
| C04 | P1 | OpTC enterprise telemetry | 企业级红队/攻击 trace | EDR/logon/process/network/DNS | G1-G3 | 扩展案例，用于验证更接近企业环境的日志 |
| C05 | P1 | POIROT / MEGR-APT query graph 示例 | CTI query graph 与 provenance graph 对齐 | CTI query graph、matched subgraph、unmatched nodes | G1-G3 | 用作 alignment-state 输入示例 |
| C06 | P1 | ExCyTIn-Bench 风格 investigation graph | 交互式安全调查图 | investigation graph、SQL/log evidence | G1-G3 | 用作 action-space / query-cost 扩展 |
| C07 | P2 | TAA-EPLMR APT32/OceanLotus case | IOC/CTI-KG 归因解释 | IOC、CTI-KG evidence paths、actor label | G3-G5 | 只做 CTI-KG baseline 和红线参照，不做主 MVP |
| C08 | P2 | APT-ATT / AADM 类 CTI 样本 | 闭集 CTI actor classification | CTI text、actor label | G5 only | 只做 closed-set actor baseline，不做主动取证主实验 |

## 4. MVP 最小组合

建议第一版先做 3 个主案例，每个案例生成若干遮蔽版本：

```text
C01 Linux provenance case
C02 FreeBSD provenance case
C03 Windows provenance case
```

每个主案例至少结构化：

- 8-15 个 `evidence_claim`；
- 4-8 个 CTI 行为节点；
- 8-12 个候选 acquisition actions；
- 3 种遮蔽策略：random / stage / discriminative；
- 1 个固定遮蔽强度：40%；
- 5 个随机种子。

第一版实验 run 数：

```text
3 cases * 3 mask strategies * 1 intensity * 5 seeds * methods
```

如果 methods 先取 `random / fixed-order / coverage-greedy / Project05-M1 / full-evidence`，则总 run 数为：

```text
3 * 3 * 1 * 5 * 5 = 225
```

这个规模足够做 MVP 表格，但不会把实现压垮。

## 5. 案例详情

### C01：Linux provenance 多阶段入侵案例

- 来源类型：DARPA TC / THEIA 类 Linux trace。
- 当前状态：候选主案例，需确认本地可用原始日志或公开转换数据。
- 场景描述：攻击者在 Linux 主机上触发初始执行，下载或释放 payload，建立外联，访问敏感文件或执行后续命令。
- CTI 侧结构：
  - process execution；
  - script / shell invocation；
  - file write / payload drop；
  - outbound network connection；
  - sensitive file access。
- 本地证据：
  - process provenance edges；
  - file read/write edges；
  - network socket/connect edges；
  - command line / process metadata。
- 可映射粒度：
  - G1：execution / command and scripting interpreter / file write / network connection；
  - G2：execution + C2 / collection intent；
  - G3：同一时间窗内形成连续 campaign-level trace。
- 推荐遮蔽：
  - stage mask：隐藏 network/C2 证据；
  - discriminative mask：隐藏 payload hash 或关键 file write；
  - random mask：隐藏 40% provenance edges。
- 推荐动作：
  - `extend_log_window`；
  - `query_host_subgraph`；
  - `recover_network_summary`；
  - `ttp_local_probe`。
- MVP 价值：最适合验证 evidence state 中的 `cti_node_coverage`、`stage_coverage` 和 `unmatched_cti_nodes`。
- 风险：如果原始 trace 过大，需要先手工抽取小型 attack summary graph。

### C02：FreeBSD provenance 攻击链案例

- 来源类型：DARPA TC / CADETS 类 FreeBSD trace。
- 当前状态：候选主案例，需确认可访问的审计记录或已有 query graph。
- 场景描述：攻击在 FreeBSD 环境中形成 process-file-network 的因果链，适合测试跨平台 provenance 表达。
- CTI 侧结构：
  - remote access / command execution；
  - suspicious process spawn；
  - file modification；
  - network communication。
- 本地证据：
  - process provenance；
  - file provenance；
  - socket provenance；
  - user/session metadata。
- 可映射粒度：
  - G1：execution、persistence 或 network behavior；
  - G2：tactic/intent，例如 execution + persistence；
  - G3：连续攻击链支撑 campaign-level trace。
- 推荐遮蔽：
  - type mask：隐藏 network evidence；
  - stage mask：隐藏 persistence 或 post-exploitation evidence；
  - conflict injection：加入共享工具或无关 network event。
- 推荐动作：
  - `query_host_subgraph`；
  - `extend_log_window`；
  - `recover_network_summary`；
  - `human_review`。
- MVP 价值：验证方法不是 Linux 特定，且能处理局部冲突或噪声。
- 风险：不同平台字段不统一，需要 evidence_claim schema 做字段规范化。

### C03：Windows 主机攻击行为案例

- 来源类型：DARPA TC / TRACE 类 Windows trace，或 OpTC Windows telemetry 子集。
- 当前状态：候选主案例，适合补充 registry、PowerShell、command line 等证据类型。
- 场景描述：攻击者通过脚本解释器或可疑进程执行，修改注册表/文件，产生网络连接或凭证相关活动。
- CTI 侧结构：
  - command execution；
  - registry modification；
  - file creation / modification；
  - network connection；
  - possible credential access。
- 本地证据：
  - process event；
  - command line；
  - registry event；
  - file event；
  - network / DNS event。
- 可映射粒度：
  - G1：PowerShell / registry / network technique；
  - G2：execution + persistence / credential access intent；
  - G3：多阶段 Windows attack trace。
- 推荐遮蔽：
  - type mask：隐藏 registry；
  - discriminative mask：隐藏 command line 或 payload filename；
  - stage mask：隐藏 credential access 相关证据。
- 推荐动作：
  - `ttp_local_probe`；
  - `query_host_subgraph`；
  - `recover_network_summary`；
  - `human_review`。
- MVP 价值：验证多证据类型 schema，尤其是 Windows-specific evidence。
- 风险：如果缺少稳定 CTI 对应描述，第一版可以只做到 G1-G2。

### C04：OpTC enterprise telemetry 案例

- 来源类型：OpTC enterprise telemetry。
- 当前状态：扩展案例，MVP 后再接入。
- 场景描述：企业环境中多主机、多用户、多进程日志形成攻击 trace。
- 本地证据：
  - process；
  - network；
  - DNS；
  - logon；
  - file。
- 可映射粒度：
  - G1-G3 为主；
  - 若能找到稳定 campaign 描述，可尝试 G4。
- 推荐动作：
  - `extend_log_window`；
  - `recover_network_summary`；
  - `query_host_subgraph`；
  - `infrastructure_history`。
- 价值：更接近真实企业日志，适合论文扩展实验。
- 风险：数据体量和清洗成本较高。

### C05：POIROT / MEGR-APT query graph 对齐案例

- 来源类型：论文/代码中的 query graph 与 matched suspicious subgraph。
- 当前状态：扩展案例，可用于构造简化 alignment state。
- 场景描述：已有 CTI query graph 与 provenance graph 的匹配输出。
- 可直接抽取：
  - matched nodes；
  - unmatched query nodes；
  - matched edges；
  - matching score；
  - suspicious subgraph。
- MVP 用法：
  - 不重做对齐算法；
  - 把匹配输出转成 `alignment_state`；
  - 测试 planner 是否能根据 unmatched nodes 选择取证动作。
- 风险：不同论文/代码输出格式不统一。

### C06：ExCyTIn-Bench 风格 investigation graph 案例

- 来源类型：investigation graph / SQL log environment。
- 当前状态：方法参考和扩展案例。
- 场景描述：安全调查问题对应图上证据链，agent 通过查询日志表获取证据。
- 可用作 Project05 的动作映射：
  - SQL 查询 = acquisition action；
  - 查询表成本 = action cost；
  - 返回行 = recovered evidence；
  - graph path completion = granularity gain。
- 价值：适合验证 active evidence acquisition，而不是验证 actor attribution。
- 风险：偏安全 QA，不是 APT attribution，需要改造 reward。

### C07：TAA-EPLMR APT32/OceanLotus CTI-KG 案例

- 来源类型：TAA-EPLMR case study。
- 当前状态：baseline / 红线案例。
- 可用证据：
  - malware hash；
  - domains；
  - IP；
  - CTI-KG evidence paths；
  - APT32/APT34 candidate evidence subgraphs。
- 用法：
  - 构造 TAA-EPLMR-like baseline；
  - 验证“证据路径增强 LLM actor output”已经存在；
  - 不能作为 Project05 主 MVP，因为缺少本地 provenance/log action。
- 可测试问题：
  - 如果隐藏 first-order domain/IP path，TAA-EPLMR 是否仍输出 actor？
  - Project05 是否会降级或要求补充 infrastructure / local observation？

### C08：APT-ATT / AADM 类闭集 CTI 分类案例

- 来源类型：APT-ATT 使用的 AADM / AADM+ 类 CTI 数据。
- 当前状态：闭集 actor classifier baseline，不进入主 MVP。
- 可用证据：
  - CTI 文本；
  - actor label；
  - 文本特征。
- 用法：
  - 验证 closed-set actor classifier 在证据缺失时可能过度归因；
  - 不适合验证 active evidence acquisition。
- 风险：容易把 Project05 拉回 actor accuracy，需严格作为对照。

## 6. 案例到 schema 的映射

每个案例最终应拆成三个核心对象。

### 6.1 evidence_claim

每条证据主张表示一个可被对齐和遮蔽的最小证据单元：

```text
claim_id
case_id
source_type
claim_type
subject / predicate / object
time_window
mapped_tactic / mapped_technique
evidence_strength
source_pointer
observable_status
```

示例：

```text
C01-EC-004:
  process powershell/bash executed encoded command
  mapped technique = T1059
  source_type = local_log
```

### 6.2 alignment_state

每个遮蔽版本和每一步取证后都生成一个状态：

```text
state_id
case_id
step_index
visible_claims
hidden_claims
matched_cti_nodes
unmatched_cti_nodes
conflicts
candidate_hypotheses
supportable_granularity
budget_used
remaining_actions
```

### 6.3 acquisition_action

每个动作必须能映射到可恢复证据，不能只是自然语言建议：

```text
action_id
case_id
action_type
target
cost
preconditions
recoverable_claim_ids
expected_granularity_gain
expected_uncertainty_reduction
```

## 7. 遮蔽设计

### 7.1 MVP 遮蔽矩阵

| 遮蔽策略 | 强度 | 用例 | 目标 |
---|---:|---|---|
| random | 40% | C01-C03 | 普通缺失 |
| stage | 40% | C01-C03 | 某攻击阶段不可观测 |
| discriminative | 40% | C01-C03 | 隐藏最能提升粒度的关键证据 |

### 7.2 暂缓遮蔽

| 遮蔽策略 | 暂缓原因 |
|---|---|
| type mask | 与 stage mask 部分重叠，第二轮加入 |
| conflict injection | 需要定义噪声/反证标签，MVP 后加入 |
| actor open-set mask | 需要稳定 actor label，当前不适合第一版 |

## 8. 取证动作初始成本表

| action_type | 成本 | 主要恢复证据 | 适用案例 |
|---|---:|---|---|
| `extend_log_window` | 2 | 时间窗口内日志/provenance 边 | C01-C04 |
| `query_host_subgraph` | 3 | 某主机/进程局部 provenance 子图 | C01-C05 |
| `recover_network_summary` | 2 | 网络连接、DNS、C2 摘要 | C01-C04 |
| `ioc_enrichment` | 1 | IP/domain/hash 富集 | C04, C07 |
| `malware_analysis` | 4 | 样本静态/动态行为 | C01, C07 |
| `infrastructure_history` | 3 | 基础设施复用关系 | C04, C07 |
| `ttp_local_probe` | 2 | 指定 technique 的局部证据 | C01-C04 |
| `human_review` | 5 | 冲突或低置信证据复核 | C02-C04 |

## 9. 第一轮需要人工确认的事项

| 编号 | 问题 | 默认处理 |
|---|---|---|
| Q1 | 本地是否已有 DARPA TC / OpTC 数据？ | 若没有，先用手工抽取 attack summary graph 做模拟 |
| Q2 | C01-C03 是否能稳定映射 ATT&CK technique？ | 先人工标注 8-15 条 evidence_claim |
| Q3 | 是否强行做 actor-level？ | 第一版不做，聚焦 G1-G3 |
| Q4 | 是否接入真实 LLM？ | 第一版离线生成 evidence_claim，不进在线 planner |
| Q5 | 是否需要复现 POIROT/MEGR-APT？ | 不复现，只用简化对齐器或人工 alignment state |

## 10. 当前选择

MVP 采用：

```text
C01 + C02 + C03
G1-G3
40% mask
random / stage / discriminative
random / fixed-order / coverage-greedy / Project05-M1 / full-evidence
```

暂不采用：

```text
named actor-level G5
online LLM planning
full POIROT/MEGR-APT reproduction
conflict injection
RL / MCTS / non-myopic POMDP
```

这个选择能先验证 Project05 的核心命题：在证据不完整时，显式 evidence state + cost-aware acquisition action 是否比简单补证策略更有效。
