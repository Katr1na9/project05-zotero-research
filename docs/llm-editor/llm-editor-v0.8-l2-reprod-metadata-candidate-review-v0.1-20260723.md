# REPROD 逐族 Metadata Candidate Review v0.1

**裁断：`approve_as_metadata_candidate_not_source_role`。**

REPROD 可以保留为一个独立 executed-evidence metadata candidate：官方记录固定了版本、许可、15 个对象的 bytes+MD5，并明确声明 405 次 ransomware binary executions；PML 文件以 MalwareBazaar SHA-256 命名，因此候选 grouping key 不依赖 class path 或攻击标签。

这不是 source-role 批准。当前不写 effective catalog，不分配 family、lineage、sample 或 quota credit，不填补 Liwa replacement slot，也不通过 L2 Gate。本轮未下载、未打开任何 archive、未读取 `summary.csv`、payload、label/ground truth、论文全文、仓库代码或模型输出。

## 1. 逐族裁断

| 项 | REPROD 结论 |
|---|---|
| Metadata identity | pass |
| Record-scope license | pass；nested notice 未审 |
| Artifact identity | pass；15 个对象均有固定 bytes+MD5 |
| 官方声明的 execution groups | 405 |
| `>=4` source-native group 声明 | pass |
| 一 SHA 对应一次唯一 execution | 未核 |
| VM reset / snapshot restore | 未声明 |
| duplicate / repeat execution policy | 未声明 |
| PML ↔ DOT binding | 未核 |
| Pointer recoverability | 未核 |
| Protected exact/near exclusion | 未执行 |
| Benign/null capacity | 0 |
| Metadata candidate | **approved** |
| Train source role | **false** |
| Catalog write | **false** |
| Download / payload audit | **false / false** |
| Family / lineage / sample / quota credit | `0 / 0 / 0 / 0` |
| Replacement slot | vacant |
| L2 Gate | false |

因此，405 是“值得做下一道有界审计”的来源方声明，不是 405 个已批准 lineage。861 个 DOT 输出是 PML 执行的派生视图，也不能追加 lineage。

## 2. Evidence

### 2.1 身份、版本、许可

[Zenodo record 8123115](https://zenodo.org/records/8123115)、[Zenodo Records API](https://zenodo.org/api/records/8123115) 与 [DataCite DOI record](https://api.datacite.org/dois/10.5281/zenodo.8123115) 共同固定：

| 字段 | 核验值 |
|---|---|
| Title | `Ransomware Execution PROvenance Dataset (REPROD)` |
| Record revision | `2` |
| Version | `1.0` |
| DOI | `10.5281/zenodo.8123115` |
| Concept DOI | `10.5281/zenodo.7933806` |
| Access | open |
| License | CC-BY-4.0 |

Zenodo 与 DataCite 均将 resource type 写为 `ConferencePaper`，但记录实际提供了数据对象。这是 metadata-quality warning，不影响本轮对 DOI、revision、license、bytes 和 MD5 的钉死；它也不能替代 archive 内第三方 notice 审计。

### 2.2 Artifact identity

官方记录列出 15 个对象，总计 `144,708,035,023` bytes（约 134.77 GiB），每个对象都有 MD5：

| Artifact group | 对象数 | Bytes | 审查姿态 |
|---|---:|---:|---|
| `pmls_split.zip` + `.z01`–`.z12` | 13 | 133,778,960,405 | Raw ProcMon PML multipart；未下载、未打开 |
| `dots.zip` | 1 | 10,928,971,753 | SPADE 派生 DOT；未下载、未打开 |
| `summary.csv` | 1 | 102,865 | 未读取；保持 model/supervision/pointer view 排除 |

逐对象 bytes 与 MD5 已写入配套机器可检 JSON。本轮通过的是 immutable artifact identity，不是 archive content、nested notice 或 reader/tool Gate。

### 2.3 Execution 与 lineage 声明

Zenodo 官方描述给出：

1. 原始 PML 对应 405 次 ransomware binary executions；
2. PML 使用所执行样本的 MalwareBazaar SHA-256 命名；
3. 861 个 DOT 是从这些 PML 经 SPADE 处理和查询产生的 subgraphs。

这使 `SHA-256` 成为 label-independent candidate grouping key，并满足“来源方明确声明至少 4 个 execution groups”的 metadata 门槛。但是官方 metadata 没有给出：

- immutable 的“一 SHA ↔ 一 execution ↔ archive member”manifest；
- VM reset、snapshot restore 或 sandbox reinitialization 合同；
- duplicate 或 repeat execution 的处理规则；
- PML member 到各 DOT 输出的机器可核绑定；
- 可复现的 PML record pointer；
- 不同 execution 统计独立性的证明。

所以 `minimum_four_source_native_group_declaration_gate_passed=true`，但 execution manifest、statistical independence 和 lineage Gate 均为 false，lineage credit 仍为 0。

### 2.4 关联论文与工作流身份

Crossref 验证同一作者组的 ACM CSET 2023 论文：

> Gehani et al. “Towards Reproducible Ransomware Analysis.”  
> DOI: [10.1145/3607505.3607510](https://doi.org/10.1145/3607505.3607510)

Crossref reference metadata 引用了 REPROD concept DOI `10.5281/zenodo.7933806`。这加强了 artifact 与研究工作的来源关联，但论文身份和 DOI citation 不能代替 execution reset、去重、split grouping 或 pointer 审计。

[REPROD-prov/REPROD-workflow](https://github.com/REPROD-prov/REPROD-workflow) 的 repository metadata 固定到 HEAD `b53fc64a0f9675f21a24fc58d52f43d6fd776fdd`；未发现 release、tag 或声明的 repository license。本轮没有读仓库内容，也不批准使用代码。未来若审 PML 或复现 SPADE 转换，reader、parser 与 transformation 必须另行版本和 hash pin。

### 2.5 证据适配与隔离

REPROD 的两种 surface 与 Candidate-only Evidence-safe Semantic Editor 有较强任务相关性：

- Windows ProcMon PML：endpoint execution events；
- SPADE DOT：由同一执行派生的 provenance subgraphs。

但两者不是两个独立 family，也不是两个独立 lineage。所有同 SHA 的 PML、DOT 和任何 repeat view 必须在同一 lineage 和同一 split。

`summary.csv` 未经字段级审计不得进入：

- model input；
- target 或 supervision；
- prompt；
- pointer surface；
- split/grouping decision。

同样禁止把 malware family、detector/verdict、hidden answer/ground truth 或 SHA 本身作为攻击标签。SHA 只有在 future manifest audit 通过后，才可作为 opaque grouping key 候选。

REPROD 官方声明的执行全部为 ransomware，因此 metadata 阶段 benign/null capacity 为 0。它不能单独解决 train 的正负平衡问题。

## 3. Inference

1. REPROD 比依赖 class path 或文件计数猜 lineage 的候选更强：405 次执行和 SHA-256 命名语义由 curator 明确声明。
2. 这仍不足以授予 source role。文件名可能对应重复执行、重复成员或未复位环境，只有 manifest/lineage audit 能区分。
3. 861 个 DOT 是同批 PML 的派生视图；把它们计作额外 lineage 会造成伪重复。
4. Endpoint + provenance 形态有利于未来构造 candidate Claim IR 和 pointer suggestion，但二进制 PML reader、DOT record identity、时间字段及 PML↔DOT 绑定尚未核验。
5. CC-BY-4.0 关闭了 record-scope 权利身份，却没有关闭 ProcMon、MalwareBazaar、SPADE 或 archive 内 notice 的第三方范围。
6. 由于没有 benign/null execution，本 family 即使未来通过，也只是 executed-malicious evidence source，不是 train-null 修补源。

## 4. Recommendation

当前只登记独立 review 的结论，不写 catalog：

> `approved_metadata_candidate_pending_separate_bounded_acquisition_contract_and_manifest_lineage_audit`

若后续另行授权，顺序必须是：

1. 先选定 exact artifact surface 或明确有界 multipart subset，钉死 revision、object key、bytes、MD5、URL、总字节上限、resume 与 retry 规则；
2. 在执行前钉死 PML/DOT reader 的名称、版本、包或 executable identity、hash 与 invocation；
3. 先看 central directory 与 nested notices，再决定是否允许读取 member content；
4. 验证至少 4 个非空、唯一且无标签依赖的 execution members；
5. 检查 duplicate/repeat、reset/snapshot 和 PML↔DOT binding，所有派生视图保持同 lineage、同 split；
6. 冻结字段 allowlist，验证 record-level pointer 可恢复性；
7. 执行 protected exact/near exclusion；
8. 完成后仍进入独立 source-role review，不自动写 catalog、授配额或进 train。

任何一步无法在不读取 label/hidden ground truth 的条件下闭合，都应 fail closed。当前没有下载授权、没有 payload/manifest audit 授权、没有 source-role 或 catalog-write 授权，也没有 baseline、微调、Kernel/Γ/M3*、L2 Gate 或 git push 授权。

## 5. Primary-source verification matrix

| Source | 支持内容 | 结论 |
|---|---|---|
| [Zenodo record/API](https://zenodo.org/records/8123115) | identity、revision、license、15 个 bytes+MD5、405 executions、SHA filenames、PML→DOT 派生 | VERIFIED |
| [DataCite](https://api.datacite.org/dois/10.5281/zenodo.8123115) | DOI、concept DOI、title、creator、version、rights | VERIFIED |
| [Crossref](https://api.crossref.org/works/10.1145/3607505.3607510) | ACM 论文身份、作者组、dataset concept DOI citation | VERIFIED |
| [REPROD-prov workflow repository](https://github.com/REPROD-prov/REPROD-workflow) | workflow repository identity、HEAD；无 release/tag/license 声明 | METADATA VERIFIED / CONTENT NOT READ |

完整机器判定、逐对象 checksum、Gate 和 authority flags 见同名 JSON。
