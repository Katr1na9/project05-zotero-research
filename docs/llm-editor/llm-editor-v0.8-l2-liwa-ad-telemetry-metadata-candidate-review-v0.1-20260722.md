# Liwa AD endpoint telemetry metadata candidate review v0.1

**Branch / authority base**：`feat/llm-editor-v0.8` @ `0f53540c1969e68c39988291c6f8cc3f93d02e9d`

**日期**：2026-07-22

**评审模式**：single-family、metadata-only、train candidate

## 1. 裁断

`liwa_ad_endpoint_telemetry_30run_2026` 的裁断为：

> **approve_as_metadata_candidate — high-risk**

通过理由只是：官方 metadata 已把候选身份、许可、revision、archive size 和 checksum 固定到足以申请一次很小的 manifest-first audit。它**不表示**其 CSV 已被认定为原始执行证据，也不表示批准下载、采用为 train、改变 role、计入配额、运行模型或通过 L2 Gate。

当前状态冻结为：

```text
approved_metadata_candidate_pending_bounded_acquisition_authorization
```

## 2. 官方 metadata 复核

2026-07-22 对 Zenodo 与 DataCite 官方接口的交叉核验结果如下：

| 字段 | 复核值 |
|---|---|
| Zenodo record | `20618083`，revision `7` |
| DOI | `10.5281/zenodo.20618083` |
| Concept DOI | `10.5281/zenodo.20618082` |
| DataCite state | `findable` |
| Published | `2026-06-10` |
| Creator | `Khan, Adil`，Liwa University |
| ORCID | `0000-0001-6269-1191` |
| Resource / access | `dataset` / `open` |
| License | `CC-BY-4.0` |
| Artifact | 单一 ZIP，`7357185` bytes，约 `7.02 MiB` |
| MD5 | `94f2af6a756a0841126d51a55bd8fe85` |

Zenodo 与 DataCite 对标题、年份和许可一致。本轮没有请求 ZIP、没有读取 archive member name/content、CSV、screenshots、graphs、private gold 或模型输出。

## 3. 为什么只作 high-risk metadata approval

官方描述声明：

- 30 个 attack-run CSV；
- 三类 Active Directory 攻击；
- native Windows Security 与 Sysmon + Wazuh 两种 logging condition；
- 同一 archive 还包含 Wazuh screenshots、BloodHound graphs、custom rules、Sysmon configuration 和 statistical analysis。

这足以说明“存在一个可复验的小型候选 artifact”，但不能证明：

- CSV 是 raw Windows/Sysmon event，而不是 Wazuh alert 或统计汇总；
- 30 个 CSV 对应 30 次独立执行，而不是同一执行的成对视图或模板化重复；
- CSV 内存在稳定、可恢复、与 raw record 对应的 pointer；
- 数据能产生 Candidate Claim IR 样本。

因此本轮来源质量判断为：

| 轴 | 结论 |
|---|---|
| 来源类型 | 官方 descriptive dataset release，近似 Level VI |
| metadata identity fitness | **A**：DOI、revision、license、size、checksum 均闭合 |
| scientific train fitness | **D / 未闭合**：raw-vs-summary 与独立 lineage 都未知 |
| peer review | 未从本轮官方 metadata 建立 |
| COI | 单一生产方自行发布 dataset 与 study description，风险 moderate-high |
| predatory journal | 不适用；这是 Zenodo dataset record，不是期刊文章 |

`approve_as_metadata_candidate` 不能覆盖 scientific train fitness 的 D 级风险。

## 4. Lineage 冻结规则

官方 metadata 声明 30 个 attack-run CSV，但外部 metadata 没有公开 archive-member manifest。本轮不能核验这 30 个文件是否存在、如何命名、是否成对或是否复制。

冻结规则为：

> 一个 source-declared attack-run CSV 最多贡献一个 lineage candidate；同一次执行的 native/enhanced logging view 必须保持为一个 lineage。row、attack type、logging condition、screenshot、graph、filename 和任意 window 都不能增加 lineage 数。

当前：

| 项 | 状态 |
|---|---|
| metadata-declared run candidates | 30 |
| verified independent lineages | 未知 |
| 每 family 最低要求 | 4 |
| lineage quota demonstrated | **false** |

## 5. 强制排除合同

以下材料不得进入 model view、prompt、normalization supervision、training target、pointer hint、validator 或 admission：

- Wazuh alert screenshots；
- BloodHound pre/post graphs；
- custom detection rules；
- Sysmon configuration；
- statistical analysis；
- attack/technique 名和 ATT&CK ID 作为 target 或 path hint；
- filename、directory name、condition label 和 run label 作为监督。

model-visible family/lineage ID 必须 opaque。没有 alarm 或规则未触发，不能被转换成 null/benign。官方 metadata 未声明 benign run，所以该候选当前对 null、abstention、benign quota 的贡献为 0。

## 6. 下一道审计必须做什么

即使本轮通过，仍须另开授权。因为官方 release 只有一个约 7.02 MiB 的 ZIP，未来“有界下载”只能是精确固定这一个 archive，而不能泛化成对 record 或其他 revision 的授权。审计至少应：

1. 冻结 archive key、`7357185` bytes 与 MD5；
2. 下载后先校验 MD5，再只读取 archive manifest；
3. 复核 30 个 CSV 的存在性、size、schema 和稳定 run ID；
4. 判断 CSV 是 raw event telemetry 还是 detector/statistical summary；
5. 将同一次执行的 native/enhanced view 绑定为同一 lineage，并排除模板化复制；
6. 在看 candidate row 前物理隔离 screenshots、graphs、rules、configuration、statistics、attack labels 与 path labels；
7. 证明 admitted row 有稳定 source pointer，且 pointer 不依赖隐藏 label；
8. 对 E3、E5、OpTC、OTRF、WitFoo 执行 exact/预注册 near-duplicate exclusion；
9. 输出 family × lineage × modality × sample-kind capacity，但不得自动授予配额。

若 CSV 只是 detector/statistical summary、无法建立至少四个独立 execution lineage，或不能恢复 raw-record pointer，则直接拒绝 train 资格；不能通过放宽 parser 或按 row/window 补数。

## 7. Gate 状态

| Gate / 权限 | 状态 |
|---|---|
| metadata identity | **passed** |
| metadata candidate | **approved — high-risk** |
| train source | **not approved** |
| bounded download | **not authorized** |
| manifest / lineage audit | **not authorized** |
| verified lineages | unknown |
| family / lineage / sample quota | 0 / 0 / 0 |
| null / benign quota | 0 |
| baseline / fine-tuning | false / false |
| Kernel / Gamma / M3* | untouched |
| L2 Gate | **false** |
| Git push | **false** |

下一动作必须另行授权“精确单 archive 下载 + manifest/lineage audit”。

## 8. 官方来源

- [Zenodo record 20618083](https://zenodo.org/records/20618083)
- [Zenodo metadata API](https://zenodo.org/api/records/20618083)
- [DataCite DOI record](https://api.datacite.org/dois/10.5281/zenodo.20618083)

机器可检裁断见 `llm-editor-v0.8-l2-liwa-ad-telemetry-metadata-candidate-review-v0.1-20260722.json`。
