# LLM Editor v0.8：Portfolio A replace 候选调研 v0.1

**日期**：2026-07-22

**状态**：`metadata_research_complete_no_replacement_approved`

## 1. 裁断

CERT 与 IoT-23 已在新 catalog 中升级为 `approved_test_candidate`，但只是候选身份与 metadata 条件获批：下载、payload、normalization、private gold、baseline、微调和 L2 仍全部关闭。

Portfolio A 替代来源调研得到的结论是：

- **BETH**：ProvSec 科学形态最好，LID-DS 2021 次之；两者都缺数据 artifact 自身的可核许可/不可变 checksum，不能批准替换。
- **Loghub Linux**：HDFS-v1 的 DOI、CC BY 4.0、归档大小和 MD5 最完整，可以进入下一次候选评审；但与 Loghub Linux 同属 LogPAI 聚合体系，且 block ID 尚不能直接当独立 run。
- **Atomic**：确实需要实际执行日志替代才能支撑科学 lineage；候选仍是 ProvSec/LID-DS，不能与 BETH 同时复用同一 family。
- **Zeek**：如果只作 parser fixture 可保留工程用途；若要作科学 development，LANL Comprehensive 或 Unified 更合适，但公开页面没有逐文件 checksum，暂时只能 reserve。

因此，本轮 **批准替换数为 0，角色变更数为 0，Portfolio A Gate 与 L2 Gate 均为 false**。

机器可检详情见 `llm-editor-v0.8-l2-portfolio-a-replacement-candidates-metadata-only-v0.1-20260722.json`。

## 2. 调研方法与边界

本轮只读取了：

- 已提交的 source inventory、论文摘录和公开检索证据；
- Zenodo 记录级/文件级元数据；
- GitHub repository、commit、license 与 tree path 元数据；
- UCO Cyber 与 LANL 官方说明页。

没有下载数据集，没有读取 archive member、日志、CSV、private gold 或模型输出。Exa 与 parallel-cli 在当前环境没有 API key/CLI，因此没有安装或调用；调研使用已有证据与官方只读元数据端点完成。

实验设计技能影响了本轮裁断：日志行、文件、block ID、目录和天数都只能先算 cluster 候选，不能自动当独立重复。

## 3. BETH / Atomic 替代候选

### 3.1 ProvSec 2023——科学首选，metadata Gate 未过

[ProvSec 论文](https://doi.org/10.1007/s44227-023-00014-9)报告 11 个攻击案例，每个案例各有 benign 与 adversary 两个独立录制实例，并保留 system call、process、file 和 network 字段；这比单一 BETH 文件或 Atomic YAML 更贴近 evidence editor 的目标。[UCO Cyber 官方页面](https://uco-cyber.github.io/research/)只提供 Google Form 下载入口，没有公开不可变 artifact revision/checksum。

阻塞点：

- 论文是 CC BY 4.0，不等于 supplementary dataset 自动获得同一许可；
- 下载入口不是可钉死的 artifact；
- benign/adversary、case 名称和文件路径都是潜在标签，未来必须从 model view 物理剥离；
- recorder-side 补写字段必须标记为 derived，不能伪装成 raw observed。

建议：若后续取得 artifact license、revision、checksum，优先用于替换 BETH；若 BETH 已有其他替代，再考虑 Atomic。一个 ProvSec family 不能同时填两个 active family 配额。

### 3.2 LID-DS 2021——可行备选，artifact 身份未闭合

[LID-DS 2021 论文](https://doi.org/10.1007/978-3-031-35190-7_6)说明其面向 system-call HIDS 的场景录制；[官方仓库](https://github.com/LID-DS/LID-DS)已钉死到 commit `587d1587…eabcc`。GitHub API 对许可返回 `NOASSERTION`，仓库 LICENSE 文本为 GPL-3.0-or-later，但数据由独立 Proton 链接提供。

阻塞点：

- 不能把代码仓许可自动外推给单独托管的数据 artifact；
- Proton artifact 没有 metadata-visible 的 immutable checksum、byte size 和 release ID；
- scenario/attack 名称可能从目录路径泄漏监督。

建议：作为 ProvSec 的备选；只有 artifact 许可和 checksum 闭合后才值得申请 source candidate review。

## 4. Loghub Linux 替代候选

### 4.1 HDFS-v1——metadata 最完整，但不是无条件替换

[Loghub Zenodo 记录](https://doi.org/10.5281/zenodo.8196385)将 `HDFS_v1.zip` 固定为 186,645,559 bytes、MD5 `76a24b4d9a6164d543fb275f89773260`、CC BY 4.0；[Loghub 论文/仓库](https://github.com/logpai/loghub)说明它来自 203-node HDFS benchmark、跨度 38.7 小时，日志按 block ID 切成 trace。

优点：release、license、size 和 checksum 均可钉死，block/node/entity 字段适合 literal relation。

限制：

- 与 Loghub Linux 同属 LogPAI 聚合体系，只能说数据生成系统不同，不能说 curator 完全独立；
- block ID 是 causal cluster 候选，不等于独立 benchmark run；
- normal/abnormal label 与 label 文件必须完全排除；
- security evidence 相关性弱于 ProvSec/LANL。

裁断：可进入下一次逐族候选评审，但本轮不批准、不下载。

### 4.2 Hadoop MapReduce——同源 reserve

同一 [Zenodo 记录](https://doi.org/10.5281/zenodo.8196385)将 `Hadoop.zip` 固定为 3,416,419 bytes、MD5 `34e28a9943704fd54933e2b455829fcc`。application/job ID 可能形成 run cluster，但尚未核验，而且它与 HDFS-v1 同属一个 LogPAI-curated record，二者不能作为两个独立 replacement family。

## 5. Zeek / 跨角色 reserve

### 5.1 LANL Comprehensive Cyber Events 2015

[LANL 官方页面](https://csr.lanl.gov/data/cyber1/)给出 dataset DOI `10.17021/1179829`、CC0、58 天、五类数据源，以及 authentication、process、DNS、network flow 与独立 red-team event set。它比 Zeek software fixture 更适合科学 development，也可以作为 BETH/Loghub 的跨角色 reserve。

阻塞点：官方页未提供不可变逐文件 checksum；58 天仍来自同一企业；red-team event set 必须从 model view 与 supervision 分离。

### 5.2 LANL Unified Host and Network 2017

[LANL 官方页面](https://csr.lanl.gov/data/2017/)给出 CC0、公开发布号 `LA-UR-17-20763`、90 个 host 日文件和 89 个 network 日文件。host schema 有 process/parent-process，network schema有 source/destination/protocol/port/packet/byte 字段。

阻塞点：data-fence 登记、无公开逐文件 checksum、90 天不是 90 个独立企业。它与 LANL Comprehensive 不能未经审计就跨 split 同时启用。

## 6. 否决或暂缓

| 来源 | 裁断 | 理由 |
|---|---|---|
| AWSCTD | reject | [GitHub 仓库](https://github.com/DjPasco/AWSCTD)没有声明许可 |
| SAGA | hold | [论文](https://arxiv.org/abs/2411.13138)存在，但未定位到官方不可变 dataset artifact |
| 完整 BETH 多主机数据 | 非 replace | 可能修复 BETH lineage，但仍是同一个 BETH corpus family |
| OTRF/Mordor | blocked | 属于现有 protected/test exposure 集，不能进 train/development |

## 7. 推荐的 Portfolio A 排序

1. BETH：ProvSec → LID-DS；
2. Loghub Linux：HDFS-v1 → LANL Comprehensive；
3. Atomic：在 BETH 未占用的 ProvSec/LID-DS 中择一；
4. Zeek：LANL Comprehensive 或 Unified，且最多选择一个 LANL family/role；
5. 任何候选都不得跨 split 复用或同时替换两个 family。

当前唯一达到“可进入下一次 metadata 候选评审”的是 HDFS-v1；这不等于 source approval，也不授权下载。

## 8. Gate

```yaml
approved_test_candidates: 2
test_download_authorized: false
replacement_sources_approved: 0
roles_changed: false
portfolio_a_gate_passed: false
payload_access_authorized: false
l2_gate_passed: false
baseline_authorized: false
fine_tuning_authorized: false
```

## Sources

Academic / peer-reviewed:

- [Shrestha et al., 2023 — ProvSec](https://doi.org/10.1007/s44227-023-00014-9)
- [Grimmer et al., 2023 — LID-DS 2021](https://doi.org/10.1007/978-3-031-35190-7_6)
- [Huang et al., 2024 — SAGA](https://arxiv.org/abs/2411.13138)

Official dataset and repository metadata:

- [UCO Cyber research index](https://uco-cyber.github.io/research/)
- [LID-DS official repository](https://github.com/LID-DS/LID-DS)
- [Loghub Zenodo record 8196385](https://doi.org/10.5281/zenodo.8196385)
- [Loghub official repository](https://github.com/logpai/loghub)
- [LANL Comprehensive Cyber Events](https://csr.lanl.gov/data/cyber1/)
- [LANL Unified Host and Network Dataset](https://csr.lanl.gov/data/2017/)
- [AWSCTD repository](https://github.com/DjPasco/AWSCTD)
