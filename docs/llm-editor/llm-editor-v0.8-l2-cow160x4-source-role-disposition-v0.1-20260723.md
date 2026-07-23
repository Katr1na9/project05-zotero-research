# COW160x4 source-role disposition v0.1

日期：2026-07-23
Authority base：`6708da1b85d54a6aa7072d52d11f324a6b381815`

## 裁断

**Reject replacement and downgrade.**

COW160x4 降为 `inactive_metadata_only_privacy_notice_failed`，只能保留为脱敏的
负 source-gate 证据。它不取得 source role，不进入 train/development，不占用
第四 replacement 方向，也不获得 family、lineage、sample 或 quota credit。

本 disposition 不写 effective catalog；如未来需要把 inactive 状态写入
catalog，必须另行授权。

## 决定性证据

| Gate | 结果 |
|---|---|
| Bounded lines | `4,096` |
| Decompressed bytes | `2,486,457` |
| Schema probe | PASS |
| Schema signatures | `1` |
| Sensitive-key records | `4,096 / 4,096` |
| Field isolation | **FAIL** |
| Full privacy Gate | **FAIL** |
| Nested notice Gate | **FAIL** |
| Unique session candidates in prefix | `4,096` |
| Duplicate candidates in prefix | `0` |
| Statistical independence | 未验证 |
| Pointer canonicalization | PASS |
| Pointer binding | `unbound` |

这是完整 bounded panel 上的 privacy 失败，不是少量脏行。精确敏感 key/value
按合同没有持久化；无需重新读取数据寻找事后例外。

Schema 通过、bounded prefix 中存在 4,096 个 unique session、pointer
canonicalization 通过，都不能覆盖 privacy/notice Gate，也不能证明全局
session 去重、reconnect/retry/campaign 处置、统计独立性或 source round trip。

## 明确拒绝的补救

- 不删除、缩窄或绕过敏感字段规则；
- 不把 unknown/event-type/command-like 字段重新标成可见字段；
- 不改 parser、caps、allowlist、notice/privacy Gate 后重跑；
- 不切换到 `data_all.zip`；
- 不下载或审计 transferred files/metadata、malformed 或其他更脏表面救场；
- 不把 160 hosts、4 configurations、国家、日期、文件、event type、attack 或
  verdict 当作执行 lineage；
- 不把 bounded 4,096 unique sessions 写成全局独立 lineage；
- 不把 canonical pointer 写成 bound pointer；
- 不为凑配额恢复 replacement 资格。

## 降级后的允许范围

允许保留已经提交的 acquisition identity 与脱敏负 audit result，用于科学报告
中的 source-gate 失败记录。若未来要作为 parser/fail-closed regression fixture，
也必须另行授权。

gzip 不得在本 disposition 下重新打开，JSONL 不得重读，不能生成训练样本、
abstention/null 样本、temporal/polarity supervision 或 pointer binding。

## Replacement slot

第四方向恢复为：

`vacant_cow160x4_rejected_privacy_notice_gate`

替代来源必须同时具备：

1. 至少四个 source-native、label-independent execution/session/run/capture；
2. 物理隔离且 privacy-safe 的 evidence surface；
3. immutable rights/notice、schema、field-isolation、lineage、pointer、
   protected-overlap 与 nuisance-independence Gate。

不能自动晋级下一个候选。新的 replacement 搜索或 catalog amendment 均需独立
授权。

## Scope confirmation

本 disposition 只读取已提交的脱敏结果与既有合同。没有重新打开 gzip、读取
JSONL、重跑 audit、修改敏感规则、下载其他 COW160x4 表面、生成训练样本、
运行 baseline/微调、修改 Kernel/Γ/M3*、写 catalog 或 push。
