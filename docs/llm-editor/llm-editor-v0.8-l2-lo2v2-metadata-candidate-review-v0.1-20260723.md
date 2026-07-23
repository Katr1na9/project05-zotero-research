# LO2v2 逐族 metadata candidate review v0.1

日期：2026-07-23  
Authority base：`a950c4708351dba91489b9142cc3053231178ccf`

## 裁断

候选：

`lo2v2_microservice_observability_runs_2026`

裁断：

**`approve_as_metadata_candidate_not_source_role`**

LO2v2 通过了 metadata identity、artifact identity、record-scope license 和 curator-declared run-count Gate；它没有通过 lineage independence、label isolation、v1/v2 overlap、pointer、nested notice、privacy、safe evidence surface 或 scientific source-role Gate。

本轮不下载、不写 effective catalog、不授 source role，不产生 family/lineage/sample/quota credit，也不改变 L2 Gate。

## 已闭合的 metadata 事实

| 项目 | 结论 |
|---|---|
| Record | Zenodo revision 4，DOI `10.5281/zenodo.18937117` |
| 权利 | Dataset `CC-BY-4.0`；code `Apache-2.0` |
| Artifact identity | 6 个对象全部有 exact bytes + MD5 |
| 总大小 | `69,963,617,238` bytes |
| Curator run 定义 | 一次完整执行全部 54 tests |
| Declared runs | 115 |
| 每 run 构成 | 1 个 correct test + 53 个 error tests |
| 最窄未来审计面 | `LO2v2_index.json` |
| Index identity | `31,028,530` bytes；MD5 `2efcff67820ba1df40fae362919271eb` |

`Run` 是 curator 定义的完整执行边界。`LO2_run_UNIX` 中的时间戳是 run 的 source-native 标识，不是本轮分析者切出的日期窗口。115 不是文件、目录、行、host、sensor、configuration、class、attack 或 verdict 数量。

## 为什么仍不能给 lineage credit

115 次 run 都在同一合成 OAuth2 微服务系统上执行同一套 54-test battery。公开 metadata 尚未证明：

- 每个声明 run 都唯一、完整且没有 aborted/partial/retry/duplicate；
- 每次 run 前系统、container、cache 和 background state 是否复位；
- image、source revision、seed、host 与采集环境是否恒定；
- 连续采集是否造成 temporal autocorrelation；
- random test order、test duration 与 pause 是否足以形成统计独立性。

因此 115 只能算 metadata-level grouping candidates，verified independent lineage 仍为 `null`，credit 为 `0`。若未来获准切分，最小单位也必须是 whole run，不能把 54 个 tests 分散到 train/dev/test。

## 关键问题：correctness 泄漏

LO2v2 的 run 边界不依赖标签，因为每个 run 都包含完整的一套 correct/error tests；但 run 内部的 test/task identity 明确编码：

- `correct`；
- 具体 error-triggering task；
- 预期的 error response。

而 `LO2v2_index.json` 被 curator 描述为包含 test 顺序、开始、结束、时长，以及 log/trace/metric 数量和大小。test 名称、路径和派生统计都可能泄漏监督。

更重要的是，前序 LO2 官方记录明确警告：文件开头的 initialization rows 会泄漏 correctness，并把 `reduce_logs.py` 称为公平分析的重要步骤。当前公开 metadata 没有证明该风险在 LO2v2 已消失，所以必须 fail closed，不能事后假设“v2 已修复”。

以下字段或内容在后续任何 model-visible 路径中默认禁止：

- correct/error label；
- test/task 名称；
- specific error target 与 expected response；
- label-bearing directory/path；
- analysis outputs；
- initialization leakage proxy；
- 未经验证的 log/trace/metric counts 或 sizes。

## `LO2v2_index.json` 的准确定位

该对象只可作为未来 bounded manifest audit 的候选面，用于核验：

- 是否确有 115 个唯一完整 runs；
- 是否每个 run 恰有 54 个 tests；
- 是否存在缺失、重复、retry 或 partial run；
- run identifier 能否形成稳定的 pointer candidate；
- v1/v2 run 是否 exact/near overlap。

它不是 Candidate Claim IR evidence，也不能替代 logs、metrics 或 traces。指向 index record 的 pointer 不能自动绑定到从未打开和验证的 runtime archive member。

## Candidate Claim IR 的潜在价值与科学边界

LO2v2 的潜在 evidence surface 是受控微服务运行中的：

- container/Locust logs；
- host 与 container metrics；
- distributed traces；
- source-native run provenance。

若未来有安全的 evidence surface，它可能支持 `component_reported_log_record`、`component_reported_metric_value`、trace span 关系或 runtime record 与 run 的候选关系。

这些关系目前都未实物核验。LLM 仍只能输出 candidate，不能把 reported/derived 提升为 observed，不能绑定 pointer，不能取得 certification 或 Promote 权。

此外，LO2v2 不是 APT、malware、host-forensics 或 security-incident telemetry。它最多是 synthetic microservice operational provenance。它是否足以占用 executed-evidence portfolio 的 source role，必须另作科学评审，不能由 115-run 数量代替。

## 版本与论文关系

当前 Crossref 可核论文：

- `10.1109/ieeedata.2026.3701668`
- *Descriptor: An Improved Microservice Dataset of Logs and Metrics (LO2v2)*
- IEEE Data Descriptions，2026

论文作者集合与 dataset creators 一致，但 Zenodo related-identifiers 没有直接绑定该 DOI；本轮只把它作为高置信 publication identity，不把它当作 artifact audit 证据。

LO2v2 还声明两个前序关系：

- dataset relation `10.5281/zenodo.14257989`，Zenodo API 解析到前序记录 `10.5281/zenodo.14938118`；
- software relation `10.5281/zenodo.14229369`，解析到 `10.5281/zenodo.14229370`，并绑定 GitHub commit `4f0c304942dba0797348c4b52119762cca8ebbcd`。

前序论文为 `10.1145/3727582.3728682`。v1/v2 的 run、sample、analysis derivative 是否重叠尚未核验；任何 future split 前都必须关闭该 Gate。

## 后续若另获授权

第一步只能为 `LO2v2_index.json` 冻结 exact bounded acquisition contract：

- exact bytes：`31,028,530`；
- exact MD5：`2efcff67820ba1df40fae362919271eb`；
- 其余五个 archive 全部排除。

执行前还必须钉死 JSON reader、版本、executable/package identity、SHA-256、invocation、parser、byte/object/depth/time caps、redaction 与 fail-closed 行为。

第一次 bounded execution 只能做 schema、notice、manifest、115-run、duplicate/retry、protected-label、v1/v2 overlap 和 pointer-candidate probe；不得持久化 raw run IDs、test/task names、paths、timestamps、service identifiers 或 ordinary values。

即使 index audit 通过，也只进入独立 source-role disposition，不自动下载 bulk runtime archive、不自动进 train、不自动授 quota。

## 权限与 Gate

| 项 | 状态 |
|---|---|
| Metadata candidate | 通过 |
| Source role | 未通过 |
| Download / audit | 未授权 |
| Effective catalog | 未写 |
| Family / lineage / sample / quota credit | 全部 `0` |
| L2 Gate | `false` |
| Baseline / fine-tuning | 未授权 |
| Commit / push | 未执行 |

## 自检

- 未触碰 `datasets/**`、`local_audit_cache`、archive 或 download launcher。
- 未下载或打开任何 artifact/payload。
- 未读 publication full text 或 repository source。
- 工件仅写入 `docs/llm-editor/`。
- 未写 catalog，未改 role/quota，未生成训练样本。
- 未运行 baseline、微调、Kernel、Γ 或 M3*。
- 未 commit，未 push。

