# `intended_cti_node_ids` 标注规范 v0.1

日期：2026-07-10  
状态：生效；配套测试 `09-experiments/tests/test_intended_not_recoverable_or.py`  
相关：`contribution-boundary-and-results-brief-v0.1.md`、P0-#1 通道可靠性

## 1. 目的

公开字段 `intended_cti_node_ids` 表示取证**请求语义**希望解决的 CTI 缺口节点，必须能从自然语言请求 / CTI schema / 调查问题推导，**禁止**从隐藏的 `recoverable_claim_ids`（或其 OR 覆盖节点集）复制或反推。

否则 M3a 的 `intended ∩ unmatched` 在通道在线时等价于答案键。

## 2. 硬约束（CI 强制）

对每个非 STOP 动作，令：

```text
covered = OR-cover(cti_nodes, recoverable_claim_ids)
intended = set(intended_cti_node_ids)
```

则必须：

1. `intended ⊆` 该 case 的 `cti_nodes.node_id`；
2. **禁止** `intended == covered`，除非 `intended = covered = ∅`（噪声/良性审查、无 CTI 缺口意图）；
3. 不得根据 `recoverable_claim_ids` 自动生成 `intended`（编译器/脚本禁止该捷径）。

实现检查：`run_mvp.intended_equals_recoverable_or(config, action)` 必须为 false。

## 3. 允许的合法不对齐（推荐写法）

| 模式 | 含义 | 示例 |
|---|---|---|
| **过宽意图** | 请求问的是一段链，本动作只恢复其中一环 | 网络摘要请求“C2 与后续提权线索”，`intended={N01,N02}`，只恢复 `N01` |
| **过窄意图** | 请求只点名主目标，实现顺带覆盖邻接证据 | `intended={N01}`，recoverable 实际还能盖住另一节点（少用，需注释） |
| **空意图噪声** | 良性/对照审查，不宣称解决攻击链缺口 | `intended=[]` 且 `covered=∅` |

每条不对齐应在 `notes` 或 motif/编译报告中写一句**请求侧理由**（不是“为了过测试”）。

## 4. 标注流程（人工或离线 LLM）

```text
1. 写 natural_language_request / target（公开）
2. 从请求映射 intended_cti_node_ids（只看 CTI 图与请求）
3. 另据 trace 能力填写 recoverable_claim_ids（隐藏实现）
4. 跑 intended≠OR 检查；若相等 → 回到步骤 2 修正意图，禁止改 recoverable 去“凑不等”
5. 通道先验与可靠回退按 P0-#1 登记
```

LLM 若参与步骤 2：只输入请求文本 + CTI 节点列表；**不得**输入 `recoverable_claim_ids` 或 event UUID 恢复集合。

## 5. 遗留债务

**已清零（2026-07-10）**：C01–C06 已按过宽意图重标，CI 不再保留 allowlist。新案例与旧案例一律必须 `intended ≠ OR(recoverable)`（空意图且无覆盖的噪声动作除外）。

## 6. 与通道可靠性的关系

- 通道门控：运行时“声明 ≠ 实现”（离线零收益）。
- 本规范：编译时“意图 ≠ 可恢复 OR 覆盖”。
- 两者互补；只做通道门控不足以消除通道在线时的答案键。
