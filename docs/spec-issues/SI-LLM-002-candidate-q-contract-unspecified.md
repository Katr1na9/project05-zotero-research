# SI-LLM-002：Candidate-q 的机器合同未定义

**Owner**：Kernel/M3* 会话
**LLM 轨道状态**：阻塞 candidate-q proposer 与两项 q 指标

## 当前字段

v0.8 描述候选 `q`、candidate coverage、双查询与 candidate-level / level-level certification，但没有给出 LLM candidate-q 的独立输出 schema、稳定 identity、允许引用字段或 scorer 输入。

## 阻塞案例

LLM 提议“initial foothold = credential abuse”时，不清楚它应表示为 Claim IR、有限域 hypothesis id、predicate bundle 还是只读 recommendation。若直接复用 Kernel `q`，LLM 可能越权写入 certified level、solver status 或依赖隐藏 ground truth 的 action。

## 建议变更

由 Kernel 会话定义只读 candidate-q schema，至少明确：

- q 的稳定 id 与目标层级引用；
- 只允许引用已存在 candidate claim ids；
- `candidate` 状态与 `certification_authority.allowed=false`；
- 禁止 solver result、certificate、STOP 和 action execution 字段；
- unsupported 的定义以及 Candidate-q Recall / Unsupported Rate 的 scorer 口径。

## 兼容性影响

未定义前，LLM 轨道只保留 `NotImplemented` shell，不产生 q 文件。未来 schema 应允许旧输出缺失 q，而不是把缺失解释为否定结论。

## 对认证安全的影响

高。若 proposer 输出与 Kernel q 混为一体，模型建议可能被误当成 SAT/UNSAT 或可认证结论。
