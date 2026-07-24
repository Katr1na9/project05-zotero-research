# L2 Direction 04 独立 metadata-only 搜索 v0.9

日期：2026-07-24
Authority base：`8af437b3dd3df8f6f0e3f5e692facf163694ce1d`

## 裁断

本轮找到一个新的高风险 review 方向：

`toyota_hsr_book_placement_execution_trials_2021`

最高裁断仅为：

`approve_for_separate_metadata_candidate_review_not_source_role`

它现在只能进入下一道逐族 metadata review。它不是 source role、不是 train/development 数据、未获得任何 credit，也未授权下载。

## 为什么达到搜索门槛

[Zenodo curator](https://zenodo.org/records/4578539) 明确把源生执行单位称为 `trial`，并声明：

- train：48 个 successful trials；
- validation：6 个 successful trials；
- test：60 个 anomalous trials 与 7 个 successful trials；
- 合计：121 个 placement trials。

这里通过门槛的是 `trial` 这个源生执行单位及其 curator 明示数量，不是三个 archive、三个 split、两类 outcome、图像帧、传感器视图或时间窗口的数量。

但稳定的 label-independent trial ID、完整执行边界、重复/重试/中断/reset 策略和统计独立性均未验证，因此 lineage、sample 和 quota credit 仍全部为 `0`。

## 身份与权利

| 项 | metadata 结论 |
|---|---|
| Zenodo record | `4578539`, revision 3 |
| Dataset DOI | `10.5281/zenodo.4578539` |
| Concept DOI | `10.5281/zenodo.4578538` |
| Version chain | 单一发布版本 |
| License | CC-BY-4.0 |
| DataCite state | findable |
| Curators | Santosh Thoduka、Juergen Gall、Paul G. Plöger |
| Platform | Toyota Human Support Robot |
| Task | 将书放到书架上 |

[DataCite](https://api.datacite.org/dois/10.5281/zenodo.4578539) 与 Zenodo 的 CC-BY-4.0、publisher 和 creator 身份一致。

Crossref 找到同作者的 2021 IROS 论文 [Using Visual Anomaly Detection for Task Execution Monitoring](https://doi.org/10.1109/IROS51168.2021.9636133)，但 Zenodo record 没有显式链接该论文。因此它只能作为可能的书目匹配，不能用于关闭数据集的任何 Gate。

## 三个官方 archive（本轮未下载）

| Key | Bytes | MD5 | 当前边界 |
|---|---:|---|---|
| `place_action_test.tar.gz` | 4,384,127,358 | `701e3b17a831eef66efae7ac1ddcd700` | 外部 test，含 successful/anomalous outcome，hold |
| `place_action_train.tar.gz` | 3,387,726,028 | `4f1083bf76a6b3a1c83a177833097105` | 外部 train，仅 successful，hold |
| `place_action_validation.tar.gz` | 365,983,836 | `76cb0cab741c3a55eaf662df979f4637` | 外部 validation，仅 successful，hold |

总计 8,137,837,222 bytes；三个对象都有 MD5。文件身份闭合不等于内容安全、trial manifest、source role 或下载许可。

## 主要阻塞

### 外部 split 与 outcome 不能继承

Curator 的 `train`、`validation`、`test` 不是 Project05 角色。`successful`、`failed`、`anomalous` 和帧级 anomaly annotation 不得：

- 进入模型输入、prompt 或 target；
- 定义 Project05 lineage 或 split；
- 被用来筛选一个“更干净”的 archive；
- 转成 abstention、negative 或其他监督样本。

下一道 review 必须证明 trial identity 在不知道 outcome 和 annotation 的情况下仍可恢复。

### 多模态 surface 风险很高

Curator 声明的数据包括 RGB、depth、机器人模型渲染图、force-torque、joint effort/velocity/position、相机标定与帧级异常标注。当前没有独立的顶层 manifest 或非视觉 telemetry 对象。

因此尚未关闭：

- camera scene privacy；
- annotation/outcome 物理隔离；
- archive 内 nested notice；
- third-party robot model / calibration 权利；
- trial 到 record 的 pointer round trip；
- 压缩 archive 内的 bounded reader 与 member cap。

### 科学适配仍未成立

这是 physical robot task-monitoring benchmark，不是 malware、APT、honeypot 或 host-forensics 数据。它能否成为第四个 executed-evidence family，取决于：

1. 是否存在可物理隔离的非视觉 telemetry；
2. 是否能产生不依赖 outcome 的 trial manifest；
3. 是否能保持 modality 与 pointer；
4. LLM 是否比 deterministic trial/sensor parser 提供可测的 evidence-safe semantic increment。

这些问题都不能由 121 这个数量自动回答。

## 本轮未晋级方向

| Candidate | 处置 | 理由 |
|---|---|---|
| Policy-compliance syscall traces | hold | 有 CC-BY-4.0、bytes 和 MD5，但 registry 没有 exact execution count 或 label-independent trace manifest |
| KIT OS-virtualization artifact | hold | 描述了成对 system-call-trace execution；没有 exact execution count，9 个 bug 是 outcome，不是 run |
| MCDS workflow traces | hold | 一个 immutable archive，但未声明 workflow-run count，execution traces 与 training data 也未隔离 |
| COSCO container traces | hold | 未声明 source-native run count；simulation、container、host、algorithm 或 row 数不能替代 run |

## Portfolio 状态

| 位置 | 状态 |
|---|---|
| 01 | `reprod_ransomware_execution_provenance_2023` |
| 02 | `pandacap_ssh_honeypot_full_system_traces_2020` |
| 03 | `logchunks_travis_ci_build_log_captures_2020` |
| 04 | `toyota_hsr_book_placement_execution_trials_2021` — pending separate metadata review only |

本轮未下载或打开 artifact，未写 effective catalog，未授 role/credit，未设计 St.Gallen v0.2，未生成训练样本，未跑 baseline/微调，L2 Gate 仍为 `false`。

## 下一道合规入口

若继续，须另行授权 Toyota HSR 逐族 metadata candidate review。该 review 必须优先裁断：

1. trial ID 是否真正独立于 successful/anomalous outcome；
2. 外部 train/validation/test 是否能完全拒绝继承；
3. 帧级 annotation 与视觉 surface 能否保持物理排除；
4. 是否存在可审查的非视觉 telemetry 与 protected manifest 方案；
5. privacy、nested notice、lineage、duplicate/retry/reset 与 pointer 风险；
6. robotics provenance 的科学适配和 LLM 相对 Rule/Reuse 的可测增量。

该搜索不授权 acquisition、archive 打开、payload audit、catalog write、source role 或 credit。

## Sources

### Academic / peer-reviewed metadata

- [Thoduka et al., 2021 — Using Visual Anomaly Detection for Task Execution Monitoring](https://doi.org/10.1109/IROS51168.2021.9636133) — 仅为未显式绑定的可能书目匹配

### Official registry metadata

- [Zenodo record 4578539 — robot placement executions](https://zenodo.org/records/4578539)
- [Zenodo Records API — record 4578539](https://zenodo.org/api/records/4578539)
- [Zenodo version chain — record 4578539](https://zenodo.org/api/records/4578539/versions)
- [DataCite DOI metadata — 10.5281/zenodo.4578539](https://api.datacite.org/dois/10.5281/zenodo.4578539)
- [Zenodo record 7094561 — policy-compliance syscall traces](https://zenodo.org/records/7094561)
- [Zenodo record 7240401 — KIT artifact](https://zenodo.org/records/7240401)
- [Zenodo record 5779005 — MCDS workflow traces](https://zenodo.org/records/5779005)
- [Zenodo record 4897944 — COSCO execution traces](https://zenodo.org/records/4897944)
