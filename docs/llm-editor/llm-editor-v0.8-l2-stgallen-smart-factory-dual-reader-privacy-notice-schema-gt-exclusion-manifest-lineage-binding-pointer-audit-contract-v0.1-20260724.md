# St.Gallen dual-reader bounded audit contract v0.1

日期：2026-07-24

Authority base：`c9ddf09`

状态：`frozen_contract_only_audit_execution_not_authorized`

## 裁断

已冻结双 surface 的 reader 与复合 audit 合同，但没有运行：

1. protected manifest：只允许在内存中生成 opaque process-instance digest 与时间区间；
2. sensor：只允许逐物理行 strict UTF-8 JSON 解析；
3. 两面只允许在内存中做区间 membership probe；
4. 输出只能包含 aggregate count、aggregate digest、boolean Gate 和脱敏 reason code；
5. 任一 raw GT、标识符、时间戳、记录、字段值、offset 或 pointer 均不得落盘。

当前没有 execution-authority JSON，`audit_execution_authorized=false`。

## 冻结身份

| 对象 | SHA-256 |
|---|---|
| Acquisition result JSON | `abc473ef9ce4c01bb21a9f78658c9e70bf58fddca84dfc3377b0408acfce8389` |
| Dual-reader amendment JSON | `2bf84eccec7526c1cf6f310cad0d83c2ca94e8d01e4ec893aec4ed9ec62ada97` |
| Dormant audit script | `0291dc15193a5f6fe6d4d06b64d066bc6b98ac3bc2f4ad95227beefe6881e382` |

Audit script：

`datasets/llm/audit_stgallen_smart_factory_dual_surface_v0_1.py`

本轮仅做 AST parse，未运行 plan/execute，未由该 parser stat/open/read 任一 surface。

## 执行 Gate

未来 authority 必须：

- 状态为 `authorized_once`；
- 按冻结顺序同时点名两个 target；
- 钉死 script 与 contract SHA；
- 精确匹配全部 caps；
- 明确授权 manifest/sensor 的相应 open/read/parse；
- 明确禁止 retry、resume、protected GT model visibility、raw persistence、role/catalog/credit 变更；
- 确认 result JSON/Markdown 尚不存在。

缺失或不匹配时必须在 surface access 前 fail closed。

## Caps

| 类别 | 上限 |
|---|---:|
| Wall time | 300 秒 |
| Manifest source bytes | 111,548 |
| Sensor source bytes | 59,901,231 |
| Total source bytes read | 153,579,990 |
| Manifest JSON depth / nodes / candidates | 32 / 200,000 / 64 |
| Sensor lines / line bytes | 2,000,000 / 1,048,576 |
| Sensor depth / nodes per record / total nodes | 16 / 4,096 / 10,000,000 |
| Pointer round-trip samples | 32 |
| 每份 result bytes | 262,144 |
| Execute count | 1 |

任何 cap 超限都写脱敏 terminal failure 后硬停，不自动重试。

## Protected manifest Gate

一个 process-instance candidate 必须同时具有：

- 唯一 identifier 类字段；
- 可严格解析的 start；
- 可严格解析的 end；
- process descriptor；
- completion state。

Bounded manifest probe 的硬条件：

- unique instance count=`10`；
- storage=`5`，production=`5`；
- completed=`10`；
- unknown/active/suspended/terminated/aborted/other=`0`；
- duplicate ID=`0`；
- 无零时长或逆序区间；
- 区间不重叠。

raw instance ID 只可在内存中转为 domain-separated SHA-256；raw ID、时间、process/state 值和 JSON pointer 均不得输出。

即使以上通过，也不能证明 duplicate/retry/partial/reset/repeated-system policy 或统计独立性，lineage credit 仍为 `0`。

## Sensor schema、privacy 与 GT exclusion

本 probe 要求每个物理非空行都是 strict UTF-8 top-level JSON object。blank、invalid JSON、non-object 均 fail closed。

Sensor 中以下任一命中均阻断：

- process/activity/stage/station/completion/label 等 GT token；
- 与 protected manifest raw instance ID 的 exact digest overlap；
- credential/secret/token 等敏感 key；
- host/user/IP/MAC/URL/email/network 等标识符 key 或 value pattern。

只允许输出分类命中次数，禁止输出命中的 key/value。不得事后删 token 或调阈值把结果刷绿。

Notice probe 不能闭合 rights Gate：record-scope CC-BY-4.0 不自动覆盖文件级、字段级或第三方权利。

## Binding Gate

绑定只允许在内存中进行：

- 字符串时间必须是带时区 ISO-8601；
- numeric 时间只有 key 明确声明 `ms/us/ns` 时才接受；
- 每条 sensor record 必须恰有一个可解析时间候选；
- 同一记录不得命中多个 manifest interval；
- 每个 manifest interval 至少有一条 bound sensor record；
- interval 外记录只能计数并排除，不能定义 lineage 或 sample。

不得持久化 per-record binding 或 per-instance record count。只可输出 aggregate bound/unbound/ambiguous counts 和 aggregate binding digest。

Probe 通过也不是 admitted binding，状态仍为 `provisional_probe_only_not_admitted`。

## Pointer Gate

Sensor pointer candidate 的内部形状：

```text
artifact_md5
+ record_ordinal
+ byte_offset
+ byte_length
+ record_sha256
```

最多选择 32 条确定性样本，按 offset/length 重读 exact bytes 并校验 SHA-256。Manifest pointer 只保留 JSON pointer digest 与 opaque instance digest。

raw ordinal、offset、length、record hash、JSON pointer、instance ID 和 per-record pointer 均不得输出。即使 sample round trip 通过，pointer 仍为 `unbound`；正式 binder output 需要新合同。

## 结果解释

本 probe 的最高可能状态仍是：

`bounded_probe_hold_notice_full_lineage_semantic_fit_and_source_role_unclosed`

也就是说，成功只能说明这一份 bounded audit 没触发相应失败条件。它不意味着：

- notice/privacy/full-lineage Gate 已通过；
- source role 已批准；
- pointer 已 bound；
- Rule/Reuse 之外的 LLM 增益已证明；
- 可以生成训练样本；
- L2 Gate 可以通过。

## 当前权限

| 项 | 状态 |
|---|---|
| Reader/parser/contract | 已冻结 |
| Plan/execute | 均未运行 |
| Surface stat/open/read/parse/join | 未授权 |
| Execution-authority JSON | 未创建 |
| Protected manifest model visibility | 禁止 |
| Catalog / role / credit | 未改变，credit 全为 `0` |
| Baseline / fine-tuning / Kernel / Γ / M3* | 未授权 |
| L2 Gate | `false` |
| Commit / push 本轮五份工件 | 未执行 |
