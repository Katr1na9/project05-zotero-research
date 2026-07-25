# REPROD dots.zip Acquisition Failure Audit v0.1

**终态：`terminal_failure_no_automatic_retry`**

唯一一次获批 acquisition 已失败并硬停。冻结的 launcher PID `17952` 与 curl PID `28492` 均已退出；没有自动重试、续传或换源。

## 结果

| 项 | 结果 |
|---|---|
| Attempt | 1 / 1 |
| Target | `reprod_dots_derived_provenance_archive` |
| Archive key | `dots.zip` |
| Expected bytes | 10,928,971,753 |
| Actual bytes | 3,964,978,900 |
| Completion | 36.280% |
| Missing bytes | 6,963,992,853 |
| curl exit | 18 |
| Exact-size Gate | **fail** |
| MD5 Gate | 未运行 |
| Verified | false |
| Automatic retry | false |
| Resume | false |
| Source substitution | false |

脱敏 stderr 结论：

```text
curl exit 18: end of response with 6963992853 bytes missing
```

由于 exact-size Gate 先失败，合同禁止计算或声称 MD5 通过。现有部分对象不是 verified archive，不得打开、列举、解析、复用或在当前 authority 下续传。

## Containment

- 两个冻结进程均不再运行；
- 没有发起第二次网络请求；
- 没有自动 retry 或 resume；
- 没有请求 PML 或 `summary.csv`；
- 没有换源；
- 没有打开、list 或 extract 部分对象；
- 没有读取 central directory、member 或 ordinary DOT content；
- 没有启动 reader freeze、nested-notice、manifest 或 lineage audit。

## Authority posture

当前 authority 已终止：

- 不重试、不续传、不换源；
- 不打开或复用部分对象；
- 不下载 PML 或 `summary.csv`；
- 不冻结 reader，不起 central-directory/nested-notice audit；
- 不写 effective catalog；
- 不改 family role 或 quota；
- 不计 family、lineage 或 sample credit；
- 不生成训练样本；
- 不跑 baseline 或微调；
- 不碰 Kernel、Γ 或 M3*；
- 不标 L2 通过；
- 不 git push。

任何后续网络动作都需要新的明确授权；本失败工件本身不提供 retry 或 resume authority。
