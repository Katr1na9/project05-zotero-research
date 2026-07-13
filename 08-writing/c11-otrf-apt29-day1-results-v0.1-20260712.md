# C11 OTRF APT29 Day 1 结果简报 v0.1

日期：2026-07-12
状态：D1-D5 完成；结果冻结；2026-07-13 完成独立复核与表述收紧
主协议：`c11-otrf-apt29-day1-intake-protocol-v0.1-20260712.md`

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run + validate
- Origin Date: 2026-07-12
- Verification Status: VERIFIED
- Version Label: c11_result_v0.1

## 1. 一句话结论

OTRF APT29 Day 1 成功提供了第三种数据封装和真实可识别的多 claim 结构，但也暴露出三个必须保留的边界：Host/Zeek 不同窗、预锁定 N01 无事件支持、冻结 M2 在该案例上并非最低成本；AND 相对 OR 显著提高了取证成本，说明证据组合语义会实质改变内部结论。

## 2. Gate 结果

| Gate | 结果 | 证据 |
|---|---|---|
| D1 来源完整性 | PASS | 固定提交、字节数、Git blob hash、SHA-256 全部匹配 |
| D2 封装可解析 | PASS | ZIP CRC/路径安全通过；196,081 host rows 与 2,140 Zeek rows，0 malformed |
| D3 多 claim 可识别 | PASS | 5 个预锁定关键节点中 4 个各有至少 2 个 Windows provider family；门槛为 3 个，但不是独立传感器 Gate |
| D4 信息边界 | PASS | 5 个动作均 `intended != OR(recoverable)`；planner view 不含恢复集合 |
| D5 冻结评估 | PASS | `run_mvp.py` 的内置策略/消融未调参；AND 主分析和单字段 OR 敏感性均完成。XGBoost、AFA-VOI 与 Depth-2 未在 C11 上运行 |

## 3. 数据与编译事实

- Host ZIP：13,944,973 bytes；解压后 385,334,029 bytes；SHA-256 `98A07314...D0FDBE5`。
- Host：SCRANTON 131,119 rows；NASHUA 29,056 rows；另含 NEWYORK 与 UTICA 背景/其他场景记录。
- Host 时间：`2020-05-02T02:55:26Z-03:28:20Z`。
- Zeek 时间：`2020-04-30T00:06:38Z-00:45:00Z`；与 Host 无重叠，不进入事件级 claim。
- 预锁定 `3aka3.doc` 锚点命中 0 条，N01 不替换。
- N02-N05 共选择 8 条 event-backed claims，分别由 PowerShell+Sysmon 或 PowerShell+Security 组成；它们是同一主机归档内的多 provider 证据，不是 Host+Network 独立传感器证据。
- N02 与 N05 的 claim 对只支持压缩/归档文件创建，不单独证明节点名称中的网络外传成分。
- AND 下全证据仍缺 N01，因此编译目标与 ceiling 从 G3 降为 `G2_tactic_intent`。

## 4. AND 主结果

每个 planner 为 45 个重复条件，不是 45 个独立攻击。

| Planner | Success | Mean cost | Regret vs Oracle | Premature STOP | Ceiling violation |
|---|---:|---:|---:|---:|---:|
| Oracle | 1.0000 | 3.0000 | 0.0000 | 0.0000 | 0.0000 |
| Coverage greedy | 1.0000 | 3.2444 | 0.2444 | 0.0000 | 0.0000 |
| M1 | 1.0000 | 3.2444 | 0.2444 | 0.0000 | 0.0000 |
| M3a | 1.0000 | 3.5556 | 0.5556 | 0.0000 | 0.0000 |
| M2 | 1.0000 | 3.6667 | 0.6667 | 0.0000 | 0.0000 |
| Random | 0.6000 | 3.4444（仅成功） | 0.6889 | 0.4000 | 0.0000 |

C11 不支持“冻结 M2 跨所有家族仍是最低成本方法”。它支持的是：同一公开接口可以在第三数据封装与 AND 多 claim 条件下执行，且不会越 ceiling。

## 5. OR 敏感性

唯一改动为 `node_coverage_semantics: AND -> OR`。

| Planner | AND cost | OR cost | OR - AND |
|---|---:|---:|---:|
| Oracle | 3.0000 | 1.0222 | -1.9778 |
| M1 / coverage / CMI | 3.2444 | 1.0222 | -2.2222 |
| M3a | 3.5556 | 1.0222 | -2.5334 |
| M2 | 3.6667 | 1.0222 | -2.6445 |

两种语义下 M2 success 都是 1.0000，但 OR 只需显著更少的采集成本。原因不是模型更好，而是 OR 把节点所需的两条独立 provider claim 降成“任一条即可”。因此 OR 是乐观敏感性，AND 才是 C11 主结果。

## 6. 对论文主张的影响

### 可加强

- 第三数据家族工程接入不再完全空白；C11 提供 Windows JSONL/多 provider 的独立封装。
- 真实案例中第一次可以识别 OR/AND 差异，补上 C07-C10 每节点单 claim 的不可识别性。
- 自然缺失导致 G3→G2 的过程可审计，适合支撑“结论粒度截断”。

### 仍不能声称

- 不能声称真实世界 actor attribution accuracy 提升。
- 不能称 C11 为自然发生的 APT 事件；它是 APT29 emulation。
- 不能把 45 条重复条件当成 45 个攻击。
- 不能把 C11 G2 成本与 C07-C10 G3 成本直接求总均值。
- 不能声称 M2、M3a 或复杂策略具有新 SOTA 性能。

## 7. 下一步

1. 当前最高优先级仍是两名独立标注者完成盲标；C11 不替代人工粒度效度。
2. 若面向更高 venue，再增加一个自然发生或更接近运营现场的独立 engagement，而不是继续增加仿真 replay。
3. 将 C11 作为论文 v0.5 的独立外部效度/语义敏感性小节，不与四个 G3 主案例混合汇总。

## 8. 冻结声明边界

事件读取前的协议、ground-truth slice 与 motif spec 均有内部时间戳和 SHA-256 记录，但这些记录与结果在同一 Git 提交中首次公开。它们证明当前文件自记录时间后的字节一致性，不能向外部读者独立证明事件读取与冻结的先后关系。论文据此使用“内部冻结记录”或“预先指定”，不使用未经限定的第三方 preregistration 表述。
