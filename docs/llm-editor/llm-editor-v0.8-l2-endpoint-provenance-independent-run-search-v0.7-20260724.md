# L2 vacant 04 独立 metadata-only 搜索 v0.7

日期：2026-07-24  
Authority base：`f9fb6f0a73707f5baab8076f25e348590871eaf7`

## 裁断

**vacant 04 继续空缺。**

本轮没有候选同时闭合：

1. curator 明示的至少 4 个 source-native、label-independent execution/run/session/capture groups；
2. 不可变 artifact 身份、license、bytes 与 checksum；
3. 与现有第 3 个 LogChunks CI/CD 方向的独立性。

最高潜力方向是 `gharuns_github_actions_workflow_execution_metadata_2026`，但裁断仅为：

`hold_explicit_curator_run_count_and_portfolio_distinctness_unclosed`

它没有进入 separate metadata candidate review，更没有 source role、train admission 或任何 credit。

## 搜索硬门槛

- 只接受 curator 或不可变官方记录明确声明的 source-native execution、workflow run、session、job、trial 或 capture。
- group identity 不得依赖 class、attack、technique、verdict、status 或 conclusion。
- 至少 4 个 group 必须由明确数字或明确下界证明。
- 禁止用 artifact bytes、file、directory、row、host、repository、sensor view、date window、configuration、class、attack、technique、status、conclusion 或 verdict 数量代替 run 数。
- 不重新晋级 REPROD、PANDAcap、LogChunks、StreamSpot、COW160x4、LO2v2 或任何既有 hold/reject/disposition。

## 最强候选：GHARuns

| 项 | metadata 结论 |
|---|---|
| 标题 | GHARuns: A Large Dataset of GitHub Actions Workflow Execution Metadata |
| Zenodo record | `20427454`, revision 3 |
| DOI | `10.5281/zenodo.20427454` |
| Concept DOI | `10.5281/zenodo.20427453` |
| 日期 / version | 2026-07-08 |
| Dataset license | CC-BY-4.0 |
| Curators | University of Mons |
| Collector | `sgl-umons/gharuns-collector` |
| Collector README pin | `ade9ce31dc27b154f3796586e14ed76ec6b9a8f1` |
| 官方对象 | 5 个，合计 24,359,573,224 bytes |
| MD5 | 5 个对象均有 |
| Source-native group | GitHub Actions workflow run ID |
| 明确 run 数 | **未给出** |
| Search disposition | **hold** |

### 为什么它像一个真实方向

Zenodo curator 明确说明：

- `runs.parquet` 每行对应一个 workflow run；
- `runs.jsonl.zst` 每个 JSON object 对应 processed run table 中的一个 workflow run ID；
- jobs 和 steps 是 workflow run 的下层对象。

因此它的候选 group 边界是 GitHub Actions 原生 workflow run，而不是人工切出的日期窗、目录、class 或 verdict。这个边界在语义上合格。

### 为什么仍不能晋级

公开 Zenodo record 与钉死的 curator README 都没有写出：

- exact workflow-run count；或
- “至少 4 个 workflow runs”这样的明确下界。

“large dataset”、五个大文件、“workflow runs”复数以及“一行一个 run”都不能替代明确计数；冻结合同也禁止从 Parquet 行数或文件体量反推。因此 `>=4` Gate 未通过。

### 即使将来补齐数量，仍有硬风险

`runs.parquet` 的 curator 字段表包括：

- `repository`、`path`、`name`、`event`；
- `run_attempt`、`head_sha`、`head_branch`；
- `status`、`conclusion`；
- `original_repo_name`。

raw JSONL 还声明包含 actor、triggering actor、commit、pull request、repository object、API URL，以及 job/step 的 name、status、conclusion。

后续若另获授权，至少要先解决：

1. status/conclusion 与 job/step outcome 的物理隔离；
2. actor、repository、branch、commit、PR 和 URL 的 privacy/nuisance 边界；
3. run attempt、rerun、cancelled、partial 与 duplicate policy；
4. whole-run split 与 immutable run manifest；
5. 可恢复但不泄漏 protected identifiers 的 pointer；
6. 与 LogChunks 的 curator、repository、execution 和 nuisance 独立性。

GHARuns 与 LogChunks 的平台不同（GitHub Actions vs Travis CI），surface 也不同（structured execution metadata vs captured build/job logs），但两者都属于 CI/CD 执行证据。仅凭平台不同还不能证明这是科学上独立的第四族。

## 官方文件身份（未下载）

| Key | Bytes | MD5 | 当前边界 |
|---|---:|---|---|
| `runs.jsonl.zst` | 8,269,900,279 | `0671def6c5b21a8a507b52277deefc17` | raw API metadata，默认排除 |
| `runs.parquet` | 1,439,256,233 | `8d9a98d18c3764d1a57fd08c00c2baea` | 最窄潜在 review surface，未授权 |
| `details.jsonl.zst` | 7,307,152,330 | `03b0460925e6f9596f3dfa23d219f27d` | nested raw metadata，默认排除 |
| `jobs.parquet` | 1,610,006,548 | `181a17725d13bcc1aa250afd24127709` | 下层 job，不得当独立 run |
| `steps.parquet` | 5,733,257,834 | `3fadc711be0a315d3f7362dde420d42c` | 下层 step，不得当独立 run |

这些信息仅来自 Zenodo registry metadata。本轮未下载或打开任何对象。

## 其他新方向

| Candidate | 处置 | 理由 |
|---|---|---|
| GHALogs: Large-Scale Dataset of GitHub Actions Runs | hold | 论文 DOI `10.1109/MSR66628.2025.00104` 可核，但本轮未闭合 immutable artifact、artifact license、bytes、checksum、明确 run 数及相对 LogChunks 的独立性 |
| A dataset of GitHub Actions workflow histories | reject | 声明的单位是 workflow files / histories / configurations，不是 workflow executions |
| GADFPD | reject | failure-prediction outcome 表面带监督，未形成物理隔离的 label-independent execution family |
| MD2POS random-seed instances | reject | 400 个 scheduling problem instances 是配置/输入，不是 endpoint 或 provenance 执行证据 |

## Portfolio 状态

| 位置 | 状态 |
|---|---|
| 01 | `reprod_ransomware_execution_provenance_2023` |
| 02 | `pandacap_ssh_honeypot_full_system_traces_2020` |
| 03 | `logchunks_travis_ci_build_log_captures_2020` |
| 04 | **vacant** |

本轮：

- effective catalog 未写；
- role 未改；
- family / lineage / sample / quota credit 全为 `0`；
- L2 Gate 仍为 `false`；
- 未下载、未打开 payload 或 archive；
- 未跑 baseline、微调或生成训练样本；
- 未 commit、未 push。

## 后续仅有的合规入口

GHARuns 只有在 curator 或不可变官方记录发布明确 run 总数或至少 4 的明确下界后，才可另行申请逐族 metadata candidate review；该 review 仍须单独处理与 LogChunks 的 CI/CD portfolio distinctness。

GHALogs 若要继续，必须先另行闭合 immutable artifact、license、bytes、checksum、curator run count 与 distinctness，不能仅凭论文标题晋级。

## Sources

### Academic / peer-reviewed

- [Moriconi et al., 2025 — GHALogs: Large-Scale Dataset of GitHub Actions Runs](https://doi.org/10.1109/MSR66628.2025.00104)
- [Cardoen et al., 2024 — A dataset of GitHub Actions workflow histories](https://doi.org/10.1145/3643991.3644867)

### Official registry and curator metadata

- [Zenodo record 20427454 — GHARuns](https://zenodo.org/records/20427454)
- [GHARuns Collector — curator repository](https://github.com/sgl-umons/gharuns-collector)
- [Zenodo record 20340547 — GitHub Actions workflow histories artifact](https://zenodo.org/records/20340547)
- [Mendeley Data DOI 10.17632/mggwn7rj9f.1 — GADFPD](https://doi.org/10.17632/mggwn7rj9f.1)
- [Zenodo record 18931661 — MD2POS](https://zenodo.org/records/18931661)
