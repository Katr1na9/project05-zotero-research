# LLM 证据编译层主线融合 M2 数据与规则基线审阅包

日期：2026-07-17  
状态：`ready_for_user_m2_review`  
范围：WP2  
下一授权：无；M2 审阅通过前不进入 WP3，不安装模型或下载权重

## 1. 本轮交付结论

WP2 已完成“真实数据能否进入语义编译接口”和“最强确定性规则基线能否在不看答案的情况下运行”两项前置验证：

1. C04–C12 共 9 个案例、58 条冻结作者参考 claim 的 source pointer 全部解析到本地原始或有界工件；
2. 生成 58 个公开 artifact、37 个公开 target node、28 条公开 target edge 和 405 个公开可见性场景；
3. 生成 private scorer reference 与 private action→artifact revelation manifest，物理隔离于 public 输入；
4. public 文件中 canonical `Cxx-EC-xxx` 碰撞为 0；
5. target-node 资格词表由固定 observable operation 与公开 stage 语义生成，不从 private `required_claim_ids` 或作者参考 predicate 反推；
6. `RULE-STRONG` 仅在 C04–C06 development 上冻结，26 个公开记录生成 26 个候选，26 个全部通过同一机械 admission，形成 15 条保守 target link；
7. C07–C12 未运行 Rule，private reference 未被 Rule 或 admission 读取；
8. 未安装模型环境、未下载权重、未训练、未正式推理，也未启动双人审计。

机器可读工件：

- `09-experiments/llm_evidence_compiler_mainline/generated/wp2/data-readiness.json`
- `09-experiments/llm_evidence_compiler_mainline/generated/wp2/rule-strong-development/rule-strong-development-snapshot.json`

## 2. 数据就绪结果

| 项目 | 结果 |
|---|---:|
| 案例 | 9（development 3，test 6） |
| 冻结作者参考 claims | 58（development 26，test 32） |
| 已解析 pointer | 58/58 |
| public artifacts | 58 |
| public target nodes / edges | 37 / 28 |
| private acquisition actions | 50 |
| public visibility scenarios | 405 |
| public/private canonical-ID collision | 0 |
| 模型/训练/人工审计 | 均未使用 |

58 条不是把原有测试 gold 扩写了：其中 C07–C12 仍是此前冻结的 32 条 test reference，新增计数来自 C04–C06 的 26 条 development reference。所有 reference 仅在 private scorer 侧保存。

来源覆盖 E3、E5、OpTC eCAR、OTRF Windows 事件和 WitFoo 多通道事件。构建器没有用手写摘要替代缺失 pointer；本轮没有 pointer 缺失案例，因此无需降级案例。

## 3. public/private 边界

### 3.1 public 可见

- request-scoped artifact / record / node / scenario IDs；
- 原始或有界 source payload、record hash、source type、可用 scope/time；
- 固定 public stage target contract；
- 当前可见 artifact IDs。

### 3.2 private 保留

- canonical case/claim/node/action IDs；
- frozen author reference claims 和 reference links；
- mask strategy、intensity、seed 与 hidden claim IDs；
- action 成功时真实解锁的 artifact IDs；
- 原始 source pointer 与 reference-surface 诊断。

编译器和 admission 不读取 private 根目录。public scenario 不含 mask strategy、mask intensity、seed、hidden claims 或未来 action outcome。

### 3.3 本轮修正的答案泄漏风险

最初构建器曾试图按每个节点的 `required_claim_ids` 推导 allowed claim types/predicates；空 reference 节点因此触发构建失败。该做法也会把答案侧语义间接带入 admission。最终实现已删除这一路径，改为：

```text
observable operation vocabulary + public node stage/behavior
→ fixed public eligibility contract
```

因此空 reference 节点不再靠 gold 补合同，test reference predicate 也不进入 public allowlist。actor/campaign attribution 仅保留不可由 local observation 满足的 sentinel predicate，防止局部日志机械越级支撑高层归因。

## 4. RULE-STRONG 冻结状态

规则基线包含：

- E3/E5 provenance event 与 resolved node adapter；
- eCAR object/action、Windows EventID 和可观察字段 adapter；
- 固定 operation→predicate→claim type 映射；
- NFKC/case-insensitive surface admission；
- host/process/time scope 约束；
- 依据公开 target description 的 conservative unique-max linking；并列或无唯一证据时保留 unlinked observation，不强连边。

冻结结果：

| 指标 | 数值 |
|---|---:|
| development cases / requests | 3 / 3 |
| artifacts / records | 26 / 26 |
| raw candidates | 26 |
| mechanically admitted claims | 26 |
| admitted links | 15 |
| unresolved/skipped records | 0 |
| candidate/link rejections | 0 / 0 |
| test cases processed | 0 |

这些数值只证明接口与规则覆盖已经达到可比较状态，不证明 26 条都与作者 reference 语义一致，也不证明规则优于 LLM。15 条 link 是保守基线：没有唯一公开语义匹配的 11 条 claim 被保留为 unlinked evidence，未为了提高 recall 强制连边。

Rule snapshot SHA-256：`26A4B2FACCAC3857687F75D4DF21A8E19821BECC984398D241529224AEE2B2D9`。

## 5. reference surface 诊断边界

58 条作者 reference 中：

- subject surface 可直接在解析 payload 中复现：43；
- object surface 可直接复现：28；
- subject 与 object 均直接复现：24。

这是诊断而非失败计数。既有作者 reference 包含聚合、规范化或跨字段描述，而当前 G0 admission 要求每个自动候选的 subject/object 都能在所指 record 中机械复现。因此 Rule 的 26 个 admitted claims 与作者 reference 不是同一套措辞，后续只能通过独立 E1 scorer 计算 frozen-reference agreement，不能把 surface diagnostic 当作 gold 命中率。

## 6. 验证终态

| 验证 | 结果 |
|---|---|
| Python 编译 | 5 个主线 compiler scripts 通过 |
| compiler 定向测试 | `35 passed`，另有 `131 subtests passed` |
| 新增 WP2 测试 | 10 项：pointer、hash、public/private、scenario、action map、Rule snapshot、development-only boundary |
| 排除并行 M3Star 测试文件后的仓库回归 | `440 passed, 6 skipped, 339 subtests passed` |
| 完整仓库回归 | `465 passed, 6 skipped, 339 subtests passed, 1 failed` |

完整回归的唯一失败为并行出现、未由本工作修改的：

`09-experiments/tests/test_run_m3star.py::M3StarExperimentRunnerTests::test_method_matrix_contains_dual_head_ablation_and_frozen_baselines`

该失败是 M3Star method matrix 期望四元组但当前加载结果表现为三元组/缺少 shield 字段的断言差异。本轮没有修改或删除任何 M3Star 文件，也没有用更改冻结数据的方式掩盖该失败。compiler 定向测试与排除该并行测试文件后的仓库回归均通过。

旧主线不变性：

| 文件 | SHA-256 | M1 对比 |
|---|---|---|
| `run_mvp.py` | `A7EBCF2739B7CD708011DB378D0F18AF3EB970C6236813BE7F8258D5394A952E` | 一致 |
| `evidence_claim.schema.json` | `5FCA1B77512C5C966860781214DCB83BEE76CFECA56B9E4AE3B91657D73CA63A` | 一致 |
| `alignment_state.schema.json` | `462C8E5F657A4467FC4B945FBAB60A2FF86D1D1470DBA8D5C3937F46E14EA61E` | 一致 |

## 7. 尚未完成、不得误写为结果

- 尚未实现或运行 `REUSE-HYBRID`；
- 尚未安装或运行任何 LLM；
- 尚未做 E1 frozen-reference claim/link F1；
- 尚未在 C07–C12 上运行任何自动编译条件；
- 尚未构造 Stage 2 临时 controller case view；
- 尚未证明编译层改善路径质量、STOP 或取证成本；
- 尚未证明“语义正确”“减少幻觉”或 human-validated grounding；
- 尚未触发 E2 双人最小语义审计；
- 尚未修改论文或专利结果段。

## 8. M2 审阅问题与下一 Gate

M2 只需判断：

1. 是否接受 58/58 pointer 与 public/private 数据包为 Stage 1 输入基础；
2. 是否接受 fixed public stage vocabulary 替代 reference-derived node allowlist；
3. 是否接受当前 `RULE-STRONG` 作为 development 冻结的确定性下限；
4. 是否接受 11 条无唯一 target 的 observation 保持 unlinked，而不是强制连边；
5. 是否批准进入 WP3：第三方组件 revision/license/运行可行性复核、adapter stub 与 development component Gate。

若 M2 批准，WP3 仍不自动授权安装模型、下载权重、训练或正式 LLM 推理。只有先判断可复用混合组件是否已足够，才进入独立的 WP4 模型授权 Gate。
