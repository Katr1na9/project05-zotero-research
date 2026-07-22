# SI-LLM-004：Candidate-only 输出中的 lifecycle_state 边界

**Owner**：Kernel/M3* 会话  
**LLM 轨道状态**：需要澄清；本轨道默认不让模型输出

## 当前字段

v0.8 将 `lifecycle_state` 定义为 `generated|bound|admitted|promoted|revoked|rejected|abstained`，并明确它是由 binding/admission/promotion 状态派生的只读字段。用户给出的 LLM 默认强制字段不包含 `lifecycle_state`。

## 阻塞案例

若模型输出 `lifecycle_state=admitted`，candidate-only guard 应拒绝；但若 exporter 完全省略该字段，共享 schema 可能要求必填。若 guard 程序写 `generated`，又需要确认这是允许的派生行为，而非 LLM 自报状态。

## 建议变更

共享 schema 明确二选一：

1. candidate producer 省略 `lifecycle_state`，Kernel 读取时派生；或
2. producer-side guard 可写只读派生值，candidate 为 `generated`，abstention 为 `abstained`。

无论采用哪种方式，模型原始输出中的 `lifecycle_state` 都必须被拒绝，不能静默覆盖。

## 兼容性影响

决定 Candidate Claim IR 的 required 字段与 serializer。建议允许旧 producer 缺失，由 canonical materializer 统一派生。

## 对认证安全的影响

中高。若调用方能自报 `admitted/promoted`，会绕过 firewall；必须保持只读和可审计派生。
