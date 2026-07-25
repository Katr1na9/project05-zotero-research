# AInception metadata candidate review v0.1

**Branch / authority base**：`feat/llm-editor-v0.8` @ `0f53540c1969e68c39988291c6f8cc3f93d02e9d`

**日期**：2026-07-22

**评审模式**：single-family、metadata-only、train candidate

## 1. 裁断

`ainception_zenodo_2025` 的裁断为：

> **approve_as_metadata_candidate**

这表示官方 metadata 已足以固定一个值得进入下一道有界审计的候选身份。它**不表示**批准下载、打开 payload、采用为 train source、改变 family role、计入 family/lineage/sample 配额、运行 baseline、微调或通过 L2 Gate。

当前状态冻结为：

```text
approved_metadata_candidate_pending_bounded_acquisition_authorization
```

## 2. 官方 metadata 复核

2026-07-22 对 Zenodo 与 DataCite 官方接口的交叉核验结果如下：

| 字段 | 复核值 |
|---|---|
| Zenodo record | `17659656`，revision `4` |
| DOI | `10.5281/zenodo.17659656` |
| Concept DOI | `10.5281/zenodo.17659655` |
| DataCite state | `findable` |
| Published | `2025-11-26` |
| Creator | `The AInception Consortium` |
| Resource / access | `dataset` / `open` |
| License | `CC-BY-4.0` |
| Files | 15 个 simulation ZIP + 1 个 PDF |
| Total bytes | `133570505552`，约 `124.39 GiB` |

Zenodo 与 DataCite 对标题、年份和许可一致。Zenodo 对 15 个 ZIP 分别公开了文件名、byte size 与 MD5。本轮没有请求任何文件下载 URL，没有读取 ZIP member、PDF、README、日志、private gold 或模型输出。

## 3. 为什么 metadata candidate 可以通过

官方记录明确声明：

- 该 release 包含 15 个 complete simulations；
- 每个 simulation/variant 对应一个独立 ZIP 文件；
- 数据形态包含 Windows Event Logs、Sysmon、Linux audit、application logs、Suricata/NetFlow 以及 cyber-physical logs；
- 同一记录也明确列出了 timelines、labels、ATT&CK mappings、IOC/STIX 与多种 graph artifact。

前两点说明它至少有资格进入“逐 ZIP manifest/lineage audit”；后两点同时说明未来必须执行严格物理隔离，不能把数据集自带答案或 storyline 当作监督捷径。

本轮对来源质量作双轴判断：

| 轴 | 结论 |
|---|---|
| 来源类型 | 官方 descriptive dataset release，近似 Level VI |
| metadata identity fitness | **A**：DOI、revision、license、size、checksum 均闭合 |
| scientific train fitness | **C / 未闭合**：独立 lineage、pointer 与样本容量均未知 |
| peer review | 未从本轮官方 metadata 建立 |
| COI | 数据生产方自述，存在中等 intellectual/institutional self-description 风险 |
| predatory journal | 不适用；这是 Zenodo dataset record，不是期刊文章 |

因此通过的是“metadata 身份”，不是“科学 train 资格”。

## 4. Lineage 风险

15 个 ZIP 只对应三个共享 storyline。多个 `SL300_variant_*` 与 `SL700_variant_*` 很可能共享基础设施、脚本、攻击链或生成模板。冻结规则为：

> 一个精确选定的 simulation ZIP 最多贡献一个 lineage candidate；ZIP 内的 host、day、event、window、label、graph 或派生 view 不得增加 lineage 数。

当前：

| 项 | 状态 |
|---|---|
| metadata lineage candidates | 15 |
| verified independent lineages | 未知 |
| 每 family 最低要求 | 4 |
| lineage quota demonstrated | **false** |

即使四个 ZIP 文件不同，也必须进一步证明不是重复或共享模板产生的伪重复。

## 5. 容量约束

全量约 `124.39 GiB`，本轮明确禁止把 candidate approval 理解成全量下载授权。

按 size 排序的四个最小 ZIP 合计也有 `10683608849` bytes，约 `9.95 GiB`。这一数字只是未来有界 acquisition 的容量下界，**不是**推荐 subset：单纯选最小文件会集中到相同 storyline，可能加剧 nuisance correlation。

下一次若获授权，必须先冻结：

- 精确 ZIP keys；
- 每个 ZIP 的 byte size 与 MD5；
- 总下载上限；
- 选择理由，且不得只按大小选择；
- 一个 ZIP 最多一个 lineage candidate。

## 6. 强制排除合同

以下材料不得进入 model view、prompt、normalization supervision、training target、pointer hint、validator 或 admission：

- AttackMate timelines；
- labelled/annotated malicious-vs-benign subsets；
- ATT&CK mappings；
- IOC 与 STIX objects/infrastructure graph；
- alert graph、knowledge graph、attack-defence graph；
- storyline、scenario、variant 名作为标签或 path hint；
- README/PDF narrative；
- PCAP，直至另有 parser 与 pointer contract。

model-visible family/lineage ID 必须 opaque。文件名、路径和 storyline 不能替代 observation 或成为 target label。

## 7. 下一道审计必须做什么

即使本轮通过，仍须另开授权，且至少包含：

1. 冻结精确的 ZIP 子集、大小、MD5 和容量上限；
2. 下载后先校验 MD5，再读取授权范围内的 archive manifest；
3. 逐 member 检查 nested notice，并先物理隔离 labels、timelines、mappings、graphs、narrative、IOC/STIX 与 PCAP；
4. 验证至少四个 ZIP 是不同执行，而非共享模板或重复 variant；
5. 证明 admitted raw record 能生成稳定、可恢复的 source pointer；
6. 对 E3、E5、OpTC、OTRF、WitFoo 执行 exact/预注册 near-duplicate exclusion；
7. 输出 family × lineage × modality × sample-kind capacity，但不得自动授予配额。

若不足四个独立 lineage，候选不得进入 train；若只剩 graph、label、timeline 或 alert summary 可用，则降为 engineering-only；pointer 或 nested notice 范围不清则 quarantine。

## 8. Gate 状态

| Gate / 权限 | 状态 |
|---|---|
| metadata identity | **passed** |
| metadata candidate | **approved** |
| train source | **not approved** |
| bounded download | **not authorized** |
| manifest / lineage audit | **not authorized** |
| verified lineages | unknown |
| family / lineage / sample quota | 0 / 0 / 0 |
| baseline / fine-tuning | false / false |
| Kernel / Gamma / M3* | untouched |
| L2 Gate | **false** |
| Git push | **false** |

下一动作必须另行授权“有界子集下载 + manifest/lineage audit”。

## 9. 官方来源

- [Zenodo record 17659656](https://zenodo.org/records/17659656)
- [Zenodo metadata API](https://zenodo.org/api/records/17659656)
- [DataCite DOI record](https://api.datacite.org/dois/10.5281/zenodo.17659656)

机器可检裁断见 `llm-editor-v0.8-l2-ainception-metadata-candidate-review-v0.1-20260722.json`。
