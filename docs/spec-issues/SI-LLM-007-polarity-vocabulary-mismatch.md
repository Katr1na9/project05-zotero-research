# SI-LLM-007：本地 boolean polarity 与 Kernel enum 不一致

**Owner**：Kernel/M3* 会话
**LLM 轨道状态**：不推翻 L1 本地护栏；阻塞 L2 polarity 样本与 Kernel 兼容声明

## 当前字段

L1 本地 provisional projection 和 fixture 使用：

```yaml
claim:
  polarity: boolean  # optional
```

v0.8 Kernel Claim IR 规格使用：

```yaml
polarity: positive|negative|unknown
```

两者在类型、词表和 unknown 表达上都不一致。当前 `compatibility_status=pending_kernel_schema` 只说明本地合同尚未对接，不能消除语义差异。

## 阻塞案例

1. 本地 `true` 是否严格等于 Kernel `positive` 尚未由共享 contract 确认；
2. 本地 `false` 可能被解释为 negative，也可能被误解为“字段不成立”；
3. 本地缺失 `polarity` 不能安全等价于 Kernel `unknown`；
4. 冲突标记器比较两个 boolean 时，无法表示 positive vs unknown 或 negative vs unknown；
5. 若转换器用 Python truthiness，字符串 `"unknown"` 可能被错误转成 `true`。

因此，当前 polarity 冲突只能视为 L1 本地 fixture 行为，不能声称已与 Kernel 语义一致。

## 建议变更

由 Kernel 会话和 LLM 轨道共同冻结显式 adapter contract：

```yaml
adapter_id: polarity-local-bool-to-kernel-enum-v1
mapping:
  true: positive
  false: negative
unknown_policy: explicit_enum_only
missing_policy: preserve_missing_or_reject
reverse_mapping:
  positive: true
  negative: false
  unknown: no_boolean_representation
```

必须明确：

1. `unknown` 不得映射为 `false`；
2. 字段缺失不得静默映射为 `unknown`；
3. adapter 必须记录版本/hash 和转换方向；
4. lossless round trip 仅适用于 positive/negative 子集；
5. 含 unknown 的样本必须保留 enum sidecar，或在本地 boolean schema 下 abstain/quarantine；
6. polarity-based conflict 只有在双方均为显式 positive/negative 且 adapter 通过时才可机械判定。

更干净的长期方案是本地 projection 直接采用 Kernel enum，但这属于共享接口迁移，不能在 L1 冻结后无 amendment 改写。

## 兼容性影响

在该 issue 关闭前：

- L2 不得物化 polarity-supervised train/development/test 样本；
- `polarity` 不计入正式 conflict coverage；
- 本地 bool fixture 继续只用于 L1 regression；
- 任何导出必须保持 `pending_kernel_schema`；
- baseline/微调不得把 boolean polarity 增益写成 Kernel-compatible 结果。

issue 关闭后需要：

1. 新的本地合同版本；
2. 双向 adapter 单元测试；
3. positive/negative/unknown/缺失四类边界 fixture；
4. 旧 L1 fixture 的迁移或版本化保留；
5. 对 conflict scorer 和历史输出的兼容性审计。

## 对认证安全的影响

高。将 unknown 或缺失错误地变成 negative，会伪造反证；将 negative 错误地变成 positive，会制造虚假支持。两种错误都会改变冲突图和后续调查优先级，因此 polarity 不能由 LLM、Python truthiness 或未版本化的字段重命名决定，更不能直接影响认证、Promote 或 STOP。
