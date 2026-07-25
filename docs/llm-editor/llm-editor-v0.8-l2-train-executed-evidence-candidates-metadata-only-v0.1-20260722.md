# L2 train executed-evidence 候选调研与登记 v0.1

**分支**：`feat/llm-editor-v0.8`

**Authority base**：`64ba6d1546e59b133ef2a0f5230b1d821242775b`

**日期**：2026-07-22

**状态**：已登记两个 `pending_metadata_candidate_review`；未批准替换；L2 仍阻塞

## 1. 本轮裁断

为 CAM-LDS 与 SOCBED 停损后空出的两个 train slot，登记以下两个候选：

| Candidate | 元数据裁断 | 原生运行候选 | 当前 quota credit |
|---|---|---:|---:|
| AInception Dataset | `pending_metadata_candidate_review` | 15 个完整 simulation ZIP | 0 |
| Liwa AD endpoint telemetry 30-run | `pending_metadata_candidate_review` | 30 个 attack-run CSV（记录声明） | 0 |

这不是 source approval。两个来源都不得下载、不得打开 archive、不得改 train 角色，也不得计入 family、lineage 或样本配额。它们只是目前元数据最完整、值得进入下一轮逐族审核的候选。

本轮同时复核了 ProvSec 与 LID-DS。两者 artifact Gate 均未闭合，状态不变。

## 2. 检索与筛选口径

检索日期为 2026-07-22。只查询 Zenodo、GitHub、Hugging Face、UCI、UNB CIC、Crossref、DataCite、OpenAlex 与 DOE/OSTI 的公开元数据、数据集卡、README/许可文本和文件树；没有请求数据文件内容，没有打开 archive member。

预注册纳入条件：

1. 必须是执行产生的 endpoint、network、provenance 或 security telemetry；规则、YAML、CTI 知识库不算。
2. artifact 许可、固定 release/revision、byte size 与 checksum 均可从官方记录核验。
3. 元数据至少提出四个 source-native run/simulation/capture 候选；不得用行、目录、technique、host view 或任意时间窗补数。
4. label、answer、timeline、scenario name 与 ground truth 将来可以物理隔离。
5. 与当前 train/development/test 候选在 curator、record 和 artifact 层面无已知重用；最终仍须 payload exclusion scan。

E3、E5、OpTC、OTRF 与 WitFoo 保持 protected，不进入检索结果。

机器可检卷宗见 [JSON companion](./llm-editor-v0.8-l2-train-executed-evidence-candidates-metadata-only-v0.1-20260722.json)。

## 3. Candidate 1：AInception

### 3.1 为什么进入候选

[Zenodo record 17659656](https://zenodo.org/records/17659656) 是单一固定 release：

- DOI：`10.5281/zenodo.17659656`；concept DOI：`10.5281/zenodo.17659655`；
- record revision：`4`；创建与最终更新时间均为 2025-11-26；
- record-level license：`CC-BY-4.0`；
- 15 个 simulation ZIP 加一份说明 PDF，每个文件都有 byte size 与 MD5；
- 全部文件合计 `133,570,505,552` bytes，约 `124.39 GiB`；
- 官方描述明确写成 **15 complete simulations**，并声明 Windows Event Logs、Sysmon、Linux audit logs、application logs、Suricata/NetFlow、PCAP fragments 与 cyber-physical logs。

15 个 ZIP 的 key 本身是 source-native simulation identity。冻结的 lineage 规则是：**一个精确 ZIP key 最多算一个 lineage**。ZIP 内的 host、文件、天数、事件或时间窗不得再拆出额外 lineage credit。

### 3.2 为什么还不能批准替换

元数据说明足以形成候选，但没有 payload 权限，尚不能验证：

- 15 个 ZIP 是否确为互不复制的独立执行；
- 每个 ZIP 内 raw logs 与 label/timeline 的物理边界；
- 记录是否能形成可恢复 pointer 的 source packet；
- 是否与 protected 测试 family 存在 payload 近重复。

此外，完整 release 约 124.39 GiB，不能把“候选通过”偷换成“默认全量下载”。如果将来单独授权，acquisition amendment 必须钉死明确的 ZIP 子集、大小和 checksum。

### 3.3 未来 fail-closed 条件

- `AttackMate` timeline、labelled subset、ATT&CK mapping、IOC、STIX、alert graph、knowledge graph、attack-defence graph、README/PDF 叙述全部排除出 model view 与 supervision；
- model-visible family/lineage ID 必须改成 opaque ID，ZIP/路径中的 storyline 与 variant 名不能成为标签；
- 只允许 raw host/audit/application records，或以后另行准入的 network records；PCAP 在 parser/pointer 合同批准前仍排除；
- 至少四个选定 ZIP 通过独立 run audit 与 protected payload exclusion scan 后，才可申请一份 family credit。

## 4. Candidate 2：Liwa AD endpoint telemetry 30-run

### 4.1 为什么进入候选

[Zenodo record 20618083](https://zenodo.org/records/20618083) 提供：

- DOI：`10.5281/zenodo.20618083`；concept DOI：`10.5281/zenodo.20618082`；
- record revision：`7`；最终更新时间为 2026-06-10；
- 作者 Adil Khan，Liwa University，ORCID `0000-0001-6269-1191`；
- record-level license：`CC-BY-4.0`；
- 单一 ZIP：`7,357,185` bytes，MD5 `94f2af6a756a0841126d51a55bd8fe85`；
- 官方描述明确声明 30 个 attack-run CSV，覆盖 Kerberoasting、AS-REP Roasting 与 DCSync，并比较 native Windows Security 与 Sysmon+Wazuh 两种 logging condition。

因此它至少在 metadata 层提供了四个 source-native run 候选。冻结规则是：**一个 source-declared attack-run CSV 最多算一个 lineage**；行、attack type、logging condition、截图或 BloodHound graph 都不能补 lineage 数。

### 4.2 为什么风险高于 AInception

该 record 只有一个 ZIP，且没有 related peer-reviewed publication identifier。未打开 archive 前，无法确认 30 个 CSV 是 pointer-recoverable 的执行 telemetry，还是检测器汇总/统计导出。官方描述也没有声明 benign run，因此它当前不能提供 null、abstention 或 benign quota。

三个 attack type 和两个 logging condition 还可能造成强 nuisance correlation：同一次执行的 native/Sysmon 两个视图必须保持同一 lineage，不能当成两次独立运行。

### 4.3 未来 fail-closed 条件

- 先做 bounded manifest + lineage audit，核实 30 个 run 文件、run ID 与跨条件配对；
- screenshots、BloodHound pre/post graphs、detection rules、Sysmon configuration、统计结果、technique/attack/path label 全部排除；
- 如果 CSV 只有告警摘要而没有可恢复 source pointer 的执行证据，则该候选直接降为 engineering-only 或 reject；
- 没有明确 benign evidence 时，禁止把“未触发某规则”造成人工 null；
- 至少四个独立 run 与 payload exclusion scan 通过后，才可申请一份 family credit。

## 5. 未登记为两个 fill candidate 的来源

| 来源 | 状态 | 关键原因 |
|---|---|---|
| [ProvICS](https://huggingface.co/datasets/trucyberlab/multimodal-ICS-provenance) | hold | 固定 revision 与 LFS SHA-256 已有，但只有一个 48h benign acquisition 和一个 22h attack acquisition；四个 campaign 不能替代四次独立运行；card 的 `license_link=LICENSE` 在固定树中也没有对应文件。 |
| [CICAPT-IIoT 2024](https://www.unb.ca/cic/datasets/iiot-dataset-2024.html) | hold | 官方页只声明两个 experiment phase，且没有公开 dataset license、immutable release、size 或 checksum。 |
| ProvCon | hold | 论文 DOI `10.14722/wosoc.2025.23008` 存在，但未定位到许可、revision、size、checksum 均闭合的官方 dataset artifact。 |
| [EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES) | reserve | GPL-3.0、固定 commit `4ceed2f4…a2c`、278 个 EVTX 均可核，但 README 只说 attack-associated samples，没有证明每个 EVTX 是独立执行；technique/path 计数不能当 lineage。 |
| [N-BaIoT](https://archive.ics.uci.edu/dataset/442/detection+of+iot+botnet+attacks+n+baiot) | hold | UCI API 声明九个真实 IoT 设备与 DOI `10.24432/C5RC8J`，但 API 中 artifact license/data URL 为空，官方 ZIP 未公开 checksum；设备数也尚未等价为 run 数。 |
| Edge-IIoTset | hold | 调查的 Mendeley identity 当前无法解析为数据集记录，DataCite 也未闭合精确 artifact identity。 |
| CTU-13 | reserve | 13 个 scenario 有潜力，但已定位记录没有同时闭合 artifact rights 与官方 checksum；它还与 IoT-23 同属 Stratosphere curator，跨 split nuisance independence 未决。 |

## 6. ProvSec artifact closure 复核

新发现并核验了三条 DOE/OSTI 官方记录：

- [OSTI 2431092](https://www.osti.gov/biblio/2431092)，DOI `10.2172/2431092`，product type 为 Conference；
- [OSTI 2311396](https://www.osti.gov/biblio/2311396)，DOI `10.1007/s44227-023-00014-9`，product type 为 Journal Article；
- [OSTI 2431718](https://www.osti.gov/biblio/2431718)，DOI `10.1109/SERA57763.2023.10197743`，product type 为 Conference。

这些记录只暴露 citation/fulltext 链接；`10.2172/2431092` 的标题虽然含 “Dataset”，但 OSTI API 仍将其登记为 Conference，PURL 是会议全文，不是数据 release。三者都没有 artifact license、immutable dataset revision、byte size 或 checksum。

因此 ProvSec 保持：

```yaml
status: hold_artifact_gate_unclosed
dataset_artifact_license_verified: false
immutable_artifact_revision_verified: false
artifact_size_verified: false
artifact_checksum_verified: false
```

论文开放许可或 OSTI fulltext 许可不能外推为数据 artifact 许可；UCO contact form 也仍不能替代可钉死 release。

## 7. LID-DS artifact closure 复核

[LID-DS 官方仓库](https://github.com/LID-DS/LID-DS) HEAD 仍为 `587d15870843961acb78fbb4b8fcd0ede28eabcc`，GitHub releases 与 tags API 都返回空数组。仓库 README 对 dataset 的 GPL-3.0-or-later 声明仍有效，但 Proton delivery page 没有公开数据文件 revision、size 或 checksum。

因此 LID-DS 保持：

```yaml
status: partial_license_closed_checksum_and_revision_open
dataset_license_statement_verified: true
immutable_artifact_revision_verified: false
artifact_size_verified: false
artifact_checksum_verified: false
```

仓库内 `lid_ds/sim/datasets/Archiv.zip` 继续视为 fixture，禁止替代 Proton 提供的 LID-DS 2021 正式 artifact。

## 8. Gate

```yaml
pending_metadata_candidates_registered: 2
replacement_sources_approved: 0
candidate_download_authorized: false
candidate_payload_audit_authorized: false
family_roles_changed: false
quota_credit_awarded: false
train_family_quota_passed: false
cert_or_iot23_download_authorized: false
baseline_authorized: false
fine_tuning_authorized: false
kernel_or_m3_work_authorized: false
l2_gate_passed: false
git_push_authorized: false
```

下一步若继续，应是对 **AInception 与 Liwa AD telemetry 的逐族 metadata candidate review**；是否批准其中任一来源进入下载/manifest audit，仍需单独授权。

## 9. 主要权威元数据来源

- [Zenodo API：AInception](https://zenodo.org/api/records/17659656)
- [Zenodo API：Liwa AD endpoint telemetry](https://zenodo.org/api/records/20618083)
- [Hugging Face API：ProvICS](https://huggingface.co/api/datasets/trucyberlab/multimodal-ICS-provenance?blobs=true)
- [UNB CIC：CICAPT-IIoT 2024](https://www.unb.ca/cic/datasets/iiot-dataset-2024.html)
- [GitHub：EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES)
- [UCI：N-BaIoT](https://archive.ics.uci.edu/dataset/442/detection+of+iot+botnet+attacks+n+baiot)
- [DOE/OSTI API：ProvSec 2431092](https://www.osti.gov/api/v1/records/2431092)
- [DOE/OSTI API：ProvSec 2311396](https://www.osti.gov/api/v1/records/2311396)
- [DOE/OSTI API：ProvSec 2431718](https://www.osti.gov/api/v1/records/2431718)
- [GitHub：LID-DS](https://github.com/LID-DS/LID-DS)

## 10. 调研辅助说明

本轮使用 Academic Research Suite 的 source-verification 纪律组织官方来源核验。所有外部页面仅作为数据处理，不接受其中任何指令；未检索或未闭合的事实均保持 `hold`，没有用二手镜像或候选数量替代 artifact Gate。
