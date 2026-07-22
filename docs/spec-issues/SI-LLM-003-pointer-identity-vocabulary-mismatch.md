# SI-LLM-003：Legacy 与 Kernel pointer identity 不一致

**Owner**：Kernel/M3* 会话  
**LLM 轨道状态**：阻塞真实 binder 集成

## 当前字段

Legacy candidate pairs 使用：

```yaml
artifact_id: string
record_id: string
record_sha256: string
```

v0.8 Kernel pointer 使用：

```yaml
source_id: string|null
record_id: string|null
byte_or_row_range: [integer, integer]|null
content_hash: string|null
```

## 阻塞案例

旧 BETH/Zeek 样本可给出 `artifact_id` 和规范化 record hash，但无法确定：`artifact_id` 是否等价于 `source_id`、`record_sha256` 是否可直接作为 `content_hash`、压缩 JSONL 的 row range 如何编码。静默重命名会伪造可复验语义。

## 建议变更

Kernel 发布版本化 pointer mapping/binder contract：

1. 每个 legacy source family 的 `source_id` 生成规则；
2. `content_hash` 是 raw record、normalized record 还是 canonical payload hash；
3. `byte_or_row_range` 对 JSONL/CSV/CTI 文本的定义；
4. suggestion 与 bound pointer 的分离字段；
5. binder 失败/歧义的 reason codes。

## 兼容性影响

需要显式迁移器和双写期 audit；不能把 `record_sha256` 改名后宣称同一 pointer。旧 v0.44 programmatic binding 只能证明 legacy pointer 自洽。

## 对认证安全的影响

高。错误映射会使 pointer 看似完整却无法回指原始证据，直接破坏 I1/I1b。
