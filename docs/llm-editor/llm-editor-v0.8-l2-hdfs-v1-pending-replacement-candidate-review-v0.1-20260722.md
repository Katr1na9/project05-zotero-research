# HDFS-v1 pending replacement candidate review v0.1

**Branch / authority base**: `feat/llm-editor-v0.8` @ `3f5ed665d20dc7051a0aa23d6d57f0592edcd39a`

**Date**: 2026-07-22

**Review mode**: single-family, metadata-only

**Target replacement**: `logpai_loghub_linux`

## 1. 裁断

`loghub_hdfs_v1` 的裁断为：

> **approve_as_metadata_candidate**

这只表示官方 metadata 足以固定候选身份。它仍处于 `pending_replacement_candidate_review`，**不表示**批准替换、下载、payload 访问、family role 变更、L2 配额计数、baseline、微调或 L2 Gate 通过。

## 2. Metadata 复核

2026-07-22 对官方 Zenodo 与 GitHub API 的只读复核结果如下：

| 字段 | 复核值 |
|---|---|
| Zenodo record | `8196385` |
| DOI | `10.5281/zenodo.8196385` |
| Concept DOI | `10.5281/zenodo.1144100` |
| Published | `2023-07-31` |
| Record creator | `Curated by LOGPAI` |
| License | `CC-BY-4.0`（Zenodo release record） |
| Artifact | `HDFS_v1.zip` |
| Size | `186645559` bytes |
| MD5 | `76a24b4d9a6164d543fb275f89773260` |
| Repository | `logpai/loghub` |
| Pinned commit | `dd61d0952749ee7963bde24220d1be5ede023033` |
| GitHub repository SPDX field | `NOASSERTION` |

许可判断以 Zenodo release record 对候选 artifact 的 `CC-BY-4.0` 声明为依据；GitHub API 的仓库级字段没有给出 SPDX 断言，因此不能拿 GitHub 字段替代 artifact release 的许可证据。

本轮没有下载 `HDFS_v1.zip`，没有打开归档成员，也没有读取日志、label、private gold 或模型输出。

## 3. 与 Loghub Linux 的 curator / record 重叠

HDFS-v1 与现有 `logpai_loghub_linux`：

- 由同一个 `Curated by LOGPAI` 记录发布；
- 位于同一个 Zenodo record `8196385`；
- 分别是不同 artifact：`HDFS_v1.zip` 与 `Linux.tar.gz`；
- `Linux.tar.gz` 的 record metadata 为 232039 bytes、MD5 `6d1802d7778126f21c001c6aa7b6b106`。

因此二者“文件不同”，但 metadata **不能证明独立 curation 或独立科学 collection**。若 HDFS-v1 未来替换 Loghub Linux，可以继续评审；但不能把二者同时当成两个独立 LogPAI family 来增加 family 数或 lineage 配额。

## 4. Block ID 能否作为 lineage

公开 metadata 将 HDFS-v1 描述为一个 203-node HDFS benchmark collection，跨度约 38.7 小时、包含约 11,175,629 行，并按 HDFS block ID 组织 trace。

本轮对 block ID 的冻结解释是：

| 用途 | 允许？ |
|---|---|
| 可见实体或 cluster key | 是，未来另获 payload 权限后仍须遵守标签隔离 |
| causal trace / grouping candidate | 是 |
| 独立 run / replicate | **否，尚未验证** |
| 计入 independent-lineage quota | **否** |

block trace 数量不能被当成独立实验数量。所有 trace 仍可能来自同一 benchmark collection；直接用 block 数扩大科学重复会构成 pseudoreplication。任何 lineage 计数均需另行授权的 bounded audit。

## 5. Label 排除合同

以下信息不得进入 model view、prompt、normalization supervision、训练 target、pointer hint 或 path hint：

- normal / abnormal label；
- anomaly label file；
- label-derived filename 或路径；
- handcrafted anomaly rule 的结果；
- train/test split label；
- 异常比例或类别比例提示。

如果以后另获 payload 权限，必须先将 label artifact 物理隔离。block ID 只能作为可见实体或 grouping key。任何把 label 用作 private scorer gold 的方案都需要新的显式授权，并且 gold 永远不得回流模型、validator 或 admission path。

## 6. Hadoop 明确不构成第二独立族

同一 Zenodo record 中的 `Hadoop.zip` metadata 为 3,416,419 bytes、MD5 `34e28a9943704fd54933e2b455829fcc`。本轮仅记录这一 sibling-artifact 元数据以执行排除边界：

- `approved=false`；
- `approved_as_second_independent_family=false`；
- `counts_toward_l2_quota=false`；
- `role_changed=false`。

Hadoop 没有被批准，也没有被当作第二独立 family。

## 7. Gate 状态

| Gate / 权限 | 状态 |
|---|---|
| HDFS-v1 metadata identity | **passed** |
| metadata candidate | **approved** |
| replacement | **not approved** |
| family role change | **false** |
| download / payload access | **false / false** |
| lineage quota demonstrated | **false** |
| counts toward L2 quota | **false** |
| Hadoop second family | **false** |
| baseline / fine-tuning | **false / false** |
| Kernel / Gamma / M3* | **untouched** |
| L2 Gate | **false** |

下一动作仍需单独授权。当前不会对 CAM-LDS / SOCBED 做 lineage audit，不处理 ProvSec / LID-DS artifact gate，不下载 CERT / IoT-23，也不启动模型工作。

## 8. 官方元数据来源

- [Zenodo record 8196385](https://doi.org/10.5281/zenodo.8196385)
- [Zenodo record API](https://zenodo.org/api/records/8196385)
- [LogPAI Loghub repository](https://github.com/logpai/loghub)
- [Pinned Loghub commit](https://github.com/logpai/loghub/commit/dd61d0952749ee7963bde24220d1be5ede023033)

机器可检版本见 `llm-editor-v0.8-l2-hdfs-v1-pending-replacement-candidate-review-v0.1-20260722.json`。
