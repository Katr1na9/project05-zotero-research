# Endpoint/provenance independent-run search v0.6

日期：2026-07-23  
Authority base：`a950c4708351dba91489b9142cc3053231178ccf`

## 裁断

在 COW160x4 因隐私与 notice Gate 失败并正式退出 replacement 后，第四个可单独逐族评审的方向为：

`lo2v2_microservice_observability_runs_2026`

本轮裁断严格停在：

**`approve_for_separate_metadata_candidate_review_not_source_role`**

本轮没有写 effective catalog，没有批准 source role、train admission 或下载，也没有授予 family、lineage、sample、quota credit；L2 Gate 仍未通过。

## 为什么它满足“至少 4 次 label-independent 执行声明”

Zenodo revision 4 的 curator 对 `Run` 给出了明确语义：

- 一个 `Run` 是全部已定义测试的一次完整执行；
- LO2v2 有 115 个 runs；
- 每个 run 固定包含全部 54 个 tests：1 个 `correct` test 和 53 个 `error` tests；
- 每个 run 内的 test 顺序随机打乱，test 时长和 test 间停顿也随机化；
- 每个 run 有 `run_log.log` 记录 test 顺序、开始与结束；
- run 目录名为 `LO2_run_UNIX`，其中时间戳是 curator 定义的完整执行标识，而不是本轮分析者切出的日期窗口。

因此，本轮 candidate group 是“一次完整的 curator-defined Run”，不是文件、目录、行、host、sensor view、日期窗、configuration、class、attack、technique 或 verdict 的计数。

每个 run 都执行同一套完整的 54-test battery，所以 run 边界本身不依赖 `correct/error` 标签。不过，这不等于统计独立性已经成立，也不等于 test 名称可进入模型视图。

## Metadata identity

| 项目 | 值 |
|---|---|
| Zenodo record | `https://zenodo.org/records/18937117` |
| DOI | `10.5281/zenodo.18937117` |
| Record revision | 4 |
| License | Dataset `CC-BY-4.0`; code `Apache-2.0` |
| Curators | University of Oulu / University of Helsinki |
| Declared runs | 115 |
| Tests per run | 54 |
| Preferred future review surface | `LO2v2_index.json` |
| Preferred surface bytes | `31,028,530` |
| Preferred surface MD5 | `2efcff67820ba1df40fae362919271eb` |
| All six objects total | `69,963,617,238` bytes |

六个官方对象均有 exact bytes 与 MD5。本轮未下载、未打开任何对象。

## 为什么只盯 `LO2v2_index.json`

这是唯一非 archive 且最窄的公开对象。Curator 声明它包含：

- 115 个 runs 的开始、结束与时长；
- 每个 run 内 test 的执行顺序、开始、结束与时长；
- log 与 trace 的行数和大小；
- metric 文件数量与总大小。

这使它可能成为后续 lineage/manifest 评审面，但也带来硬风险：test/task 名称会编码 `correct` 或具体 error 场景。后续若获授权，必须先冻结字段 allowlist、物理 protected exclusion 和整 run 切分规则；test 名称、task 名称、expected response、error target、分析结果不得进入模型视图。

## 科学价值与边界

LO2v2 提供同一合成 OAuth2 微服务系统在受控重复执行中的 container/Locust logs、Prometheus/cAdvisor/NodeExporter metrics 与 Jaeger traces。它与 ransomware、SSH honeypot、CI build logs 和 Cowrie aggregation 在 curator、系统、采集技术和运行模态上均不同。

但它不是 APT、malware 或 host-forensics ground-truth 数据。它能否作为“executed-evidence”组合中的独立 operational-provenance family，仍是后续逐族评审的科学 Gate，不能由本次 run-count 搜索替代。

## 仍未闭合

1. 115-run 声明尚未通过 immutable manifest 实物核验。
2. 115 次运行复用同一合成系统和同一 54-test battery，统计独立性与 repeated-system nuisance 未核。
3. `correct/error` 与具体错误任务会出现在 test/task 身份中，protected-label 隔离未核。
4. `LO2v2_index.json` 的字段 allowlist、nested notice、隐私/标识符边界和 pointer round trip 未核。
5. LO2v2 是早期 LO2 dataset/software 的新版本；跨版本 exact/near overlap 未核，禁止跨 split 静默复用。
6. 时间戳只能保留为 source-native run 标识的一部分，不能被重新解释为 lineage 或日期窗配额。
7. 与现有 train/dev/test 的 protected overlap、跨族 nuisance independence 和科学组合价值未核。
8. Crossref 可核到 2026 IEEE Data Descriptions 论文 `10.1109/ieeedata.2026.3701668`，但 Zenodo related-identifiers 没有直接绑定该论文 DOI。

## 本轮未晋级方向

| 候选 | 处置理由 |
|---|---|
| XRP Ledger consensus traces | Curator 说一 trace file 对应一 consensus round，但公开 metadata 未给 exact trace count 或无需开 archive 即可核的 manifest；不能用推测文件数凑 run |
| XRP Markov-chain trace partitions | 五个 dataset partitions 不是五次独立执行 |
| WinMET CAPE executions | 虽声明 31,844 次执行，但 raw trace 含进程、WinAPI/system call、参数、返回值与 OS resources，mapping 又带 supervision；本轮保持高风险 hold |
| DALiuGE workflow trials | 声明 trial executions，但未公开 exact run count 或 immutable run manifest |
| CPM RO-Crate | 七个 CreateActions 是一次 pipeline execution 内的步骤，不是七次独立 run |
| VLM robotic traces | annotated traces 带 ground-truth outcome，且视频面巨大；label 与 payload 边界不适合作为本轮第四方向 |

## 本轮权限状态

- Candidate：`lo2v2_microservice_observability_runs_2026`
- 最高裁断：`approve_for_separate_metadata_candidate_review_not_source_role`
- Effective catalog：未写
- Download / audit：未授权、未执行
- Source role / train admission：未批准
- Family / lineage / sample / quota credit：全部 `0`
- L2 Gate：`false`
- Commit / push：未执行

若要继续，下一步必须另行授权 LO2v2 的逐族 metadata candidate review；该评审应先处理 scientific fit、早期 LO2 版本重叠、repeated-system nuisance、test-label 隔离、index 精确边界与未来 bounded acquisition 可行性，而不是直接下载。

## 自检

- 启动 HEAD 已精确核对为 authority base。
- 未触碰 `datasets/**`、`local_audit_cache`、任何 archive 或 download launcher。
- 未下载或打开 payload/artifact。
- 未重新晋级 REPROD、PANDAcap、LogChunks、StreamSpot、COW160x4 或任何既有 hold/reject。
- 未把 file、directory、row、host、sensor view、date window、configuration、class、attack、technique 或 verdict 当作 run。
- 未降低 `>=4` source-native label-independent groups 门槛。
- 工件仅写入 `docs/llm-editor/`。
- 未写 catalog，未授 credit，未 commit，未 push。
