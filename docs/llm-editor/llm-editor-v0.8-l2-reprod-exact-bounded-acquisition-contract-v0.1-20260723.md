# REPROD Exact Bounded Acquisition Contract v0.1

**状态：`frozen_contract_only_download_not_authorized`。**

本合同只完成对象选择和 acquisition 边界冻结。首轮唯一选定对象是 `dots.zip`；不下载 PML multipart，不虚构 PML member-level 子集，也不读取 `summary.csv`。当前没有网络请求、下载、续传、archive 打开、central-directory、nested notice、role、catalog、quota 或 L2 授权。

Authority base：`315300e880d12eae5b9804eb103d19a0485db934`。

## 1. Surface 选择

裁断：

> `select_dots_zip_for_first_bounded_acquisition_defer_raw_pml`

| 路线 | 固定对象 | 总 bytes | 本轮决定 |
|---|---:|---:|---|
| Raw PML 完整 multipart | `pmls_split.zip` + `.z01`–`.z12`，共 13 个 | 133,778,960,405（约 124.59 GiB） | defer；不授权 |
| Raw PML 有界子集 | 官方未发布独立 subset object/checksum | 无法钉死 | 不可立约 |
| Derived DOT | `dots.zip`，单对象 | 10,928,971,753（约 10.18 GiB） | **首轮选定** |
| Summary | `summary.csv` | 102,865 | 排除 |

选择 DOT 的理由是：它是唯一能以一个 Zenodo immutable object、一个 MD5 和 10.18 GiB 硬上限先做低成本 lineage/rights 淘汰的 surface。PML 是 split ZIP；在当前官方 metadata 下，没有独立可下载、独立校验的 member subset。byte range、局部 slice 或根据文件名猜 subset 都不能形成可复现实验对象。

这项选择有明确科学限制：

- DOT 是 SPADE 从 PML 派生的 provenance subgraph；
- DOT 通过 audit 也不能批准 raw ProcMon PML evidence；
- 不能据此声称 405 个 raw executions 已验证；
- 不能声称 LLM 从 raw evidence 生成了这些 DOT；
- DOT 的 861 个输出不能当成 861 个 lineage。

因此，未来若 DOT 审计通过，只能进入“derived provenance-evidence surface”的独立 source-role review。若论文实验必须验证 raw evidence → candidate Claim IR，仍需另开完整 PML multipart 的容量与 acquisition 合同。

## 2. 唯一 frozen target

来源记录：

| 字段 | 值 |
|---|---|
| Zenodo record | [8123115](https://zenodo.org/records/8123115) |
| Revision | `2` |
| Updated | `2023-07-10T02:26:48.679692+00:00` |
| DOI | `10.5281/zenodo.8123115` |
| Version | `1.0` |
| Record-scope license | CC-BY-4.0 |

未来只有另行点名授权时，才可考虑以下 target：

| 字段 | 冻结值 |
|---|---|
| Target ID | `reprod_dots_derived_provenance_archive` |
| Source key | `dots.zip` |
| Exact bytes / write ceiling | `10,928,971,753` |
| MD5 | `d9e3f24ba36a9b9503a55eb1cf677345` |
| Frozen URL | `https://zenodo.org/api/records/8123115/files/dots.zip/content` |
| Future local root | `datasets/llm/local_audit_cache/reprod-bounded-v0.1/raw` |
| Future relative path | `dots.zip` |
| Download authorized now | **false** |

最大 archive 数为 1，最大 persisted payload 为 `10,928,971,753` bytes。未列出的 archive 数和 bytes 上限都是 0。禁止换 revision、concept record、mirror、cache、object 或 local path。

## 3. Future acquisition controls

本合同不执行 acquisition。若以后另行授权：

1. 授权必须点名 `reprod_dots_derived_provenance_archive`；
2. 最多一次 initial attempt；
3. terminal failure 后不得自动重试，partial file 不得自动 resume；
4. 只能从 frozen URL 发起，HTTP body 只能写入 frozen local path；
5. 即将超过单对象上限即 fail closed；
6. acquisition 阶段不得 list、open、extract 或读取 archive；
7. 完成后先验证 exact size，再计算 MD5；
8. size 与 MD5 均匹配才可记录 `verified`；
9. 失败只记录脱敏 target、bytes、exit status 和 stderr，然后停止；
10. 不得失败后自动切换到 PML、summary、mirror 或其他 revision。

`verified` 只表示本地对象与 Zenodo 发布的 `dots.zip` 身份一致。它不表示 rights、manifest、lineage、pointer、protected exclusion 或 source role 已通过。

## 4. Central-directory + nested notice 是下一道独立 Gate

即使未来完成 size+MD5，也必须硬停。随后才可另开 reader-pinned 的 bounded central-directory + nested-notice contract：

1. 打开前再次核验 exact size+MD5；
2. 先冻结 ZIP reader 的名称、版本、package/executable identity、hash、invocation 和 parser；
3. 先读取 central directory，检查 unsafe path、collision、member metadata 和 notice candidates；
4. 再按预先冻结的 member/byte caps 点名流式读取 notice；
5. notice 阶段禁止读取 ordinary DOT payload，也禁止 extract 到磁盘；
6. raw member paths、raw notice text 与 payload 不得提交；
7. central-directory/notice 通过后，也不得自动进入 manifest/lineage 或 source-role review。

本合同没有预先授权上述读取，也没有用观察后的 archive 结构来调整阈值。具体 notice token、member cap、per-member cap、total-byte cap 和允许持久化字段必须在打开 archive 前写入下一份合同。

## 5. Authority posture

| 动作 | 当前授权 |
|---|---|
| 保存本合同 | **是** |
| 下载 `dots.zip` | **否** |
| 下载 PML 任一 volume | **否** |
| 读取 `summary.csv` | **否** |
| HTTP request / resume | **否** |
| 打开 central directory/member | **否** |
| Nested notice / manifest / lineage audit | **否** |
| 安装或下载 reader | **否** |
| 写 effective catalog | **否** |
| Source role / family / lineage / sample / quota | **否 / 0** |
| 生成训练样本 | **否** |
| Baseline / 微调 | **否** |
| Kernel/Γ/M3* | **否** |
| L2 Gate | **false** |
| Git push | **否** |

下一步若获单独授权，只能对 frozen `dots.zip` 执行一次 acquisition，并在 exact-size + MD5 后停止。central-directory + nested notice 仍是之后的独立合同和独立执行授权。
