# Endpoint/Provenance Independent-Run Search v0.4

**状态：`complete_one_reviewable_direction_found_fourth_slot_vacant`**

本轮严格串行、metadata-only。目标是为现有 REPROD 与 PANDAcap 之后寻找第 3、第 4 个方向；未为凑数降低 frozen Gate。

结论：

- 第 3 个方向：`logchunks_travis_ci_build_log_captures_2020`
- 裁断上限：`approve_for_separate_metadata_candidate_review_not_source_role`
- 第 4 个方向：**未找到，slot 保持 vacant**
- 新增 family / lineage / sample / quota credit：`0 / 0 / 0 / 0`
- Source role、train admission、catalog、L2：全部 false

## 1. 新方向：LogChunks

| 字段 | Metadata 结论 |
|---|---|
| Title | LogChunks: A Data Set for Build Log Analysis |
| Zenodo | `3632351`, revision 3 |
| DOI / concept DOI | `10.5281/zenodo.3632351` / `10.5281/zenodo.3632350` |
| Version | `1.0.0` |
| License | CC-BY-4.0 |
| Artifact | `LogChunks.zip` |
| Bytes | `24,108,826` |
| MD5 | `aafa45079bdae44e340f4474ca5c4340` |
| Curator capture statement | 797 Travis CI logs |
| Repositories / languages | 80 / 29 |
| Metadata-review direction | **approved** |
| Source role | false |
| Lineage credit | 0 |

Zenodo curator 直接声明收集了 797 个 Travis CI logs，而不是根据 ZIP member 数、目录数或表格行数反推。因此它满足“存在至少四个 source-native capture candidates”的 metadata 搜索门槛。

它仍不是已验证 lineage。后续逐族 review 必须证明：

1. 一个 log capture 是否对应一个唯一 Travis job/build ID；
2. build matrix 中多个 job 是否只是同一 build 的多视图；
3. retry、rerun、duplicate 与 truncated log 如何分组；
4. 是否存在稳定、可复核的 source-native pointer；
5. 手工 failure chunk、keyword 与 category 能否物理隔离；
6. nested notice、secret/privacy、protected overlap 是否闭合；
7. CI execution provenance 对 Candidate Claim IR 的科学贡献是否足够，而不是仅增加普通日志数量。

Crossref 验证了关联论文：

`LogChunks`, DOI `10.1145/3379597.3387485`, MSR 2020。

## 2. 第 4 个方向为何保持空缺

| 候选 | 当前处置 | 关键缺口 |
|---|---|---|
| CIBench / TravisTorrent extension | hold | Record 未声明 source-native build/job 数量或不可变 build-ID mapping |
| Java OSS Travis-CI Build Failure Dataset | hold | Zenodo license 缺失；upload 明示缺少 build-to-job association |
| Mining Branching LSCs | hold | Metadata 定义“一 trace = 一 execution”，但未声明至少 4 条 traces |
| Wf4Ever PROV corpus | hold | 说明 traces 来自 workflow runs，但未声明 run 数或稳定 run key |
| MALREC direction | reject | 未找到对应的不可变 execution-dataset record |

### CIBench

Zenodo record `4682056`, revision 3：

- License：CC-BY-4.0
- `data_set.tar.gz`：888,949,218 bytes，MD5 `432f53674235892d5e6fea83a47d45aa`
- `raw_logs.tar.gz`：38,286,433,036 bytes，MD5 `5338a3a569031f44877779cab45c5f16`

它说明自己扩展 TravisTorrent，但没有在 registry metadata 中声明 source-native execution 数量或 build-ID grouping。GitHub Search 命中的第三方仓库虽声称 519,373 builds，不属于 curator evidence，未采用。

### Java OSS Travis-CI logs

Zenodo record `1745638`, revision 9 明确：

- 一个日志对象对应一个 Travis job；
- commit 带 Travis build ID；
- 一个 build 可有多个 jobs；
- upload **缺少 build 与 job log 的关联数据**。

此外 record license 为 null。不能以日志文件数代替缺失的 mapping，也不能越过 rights Gate。

### Mining Branching LSCs

Zenodo record `581658`, revision 7 定义每个 XES trace 为一次 application execution（launch 到 termination），但只声明“两组 traces”，没有声明至少四条 traces。读取 XES 或 `index.html` 来取得数量超出本轮 metadata-only 授权，因此保持 hold。

### Wf4Ever PROV

Zenodo record `11607`, revision 12 说明 provenance traces 来自 Taverna/Wings workflow runs，但没有声明至少四次 executions 或稳定 run identifier。ZIP 内容没有被打开或计数。

## 3. Source verification

用于正面裁断：

- Zenodo Records API：record identity、revision、license、bytes、MD5、curator description；
- Crossref Works API：论文 DOI、作者、venue、年份；
- GitHub Search API：repository metadata，且排除非 curator 的数量声明。

未用于任何结论：

- Semantic Scholar：HTTP 429，未重试；
- OpenAlex：DOI 查询返回空对象；
- 论文全文、仓库文件、archive、member：均未读取。

## 4. Step A 自检

| 检查 | 结果 |
|---|---|
| 命中硬排除路径 | false |
| 触碰下载进程/cache/archive/ZIP/launcher | false |
| 安装或执行 reader | false |
| 输出仅在 `docs/llm-editor/` | true |
| Commit / push | false / false |

Step A 自检通过，可串行进入 Step B。
