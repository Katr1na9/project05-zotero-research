# CAM-LDS + SOCBED 有界 lineage-only audit 结果 v0.1

**Frozen contract commit**: `db10f11`

**Contract SHA-256**: `38FFD0F43B9589CCF831B0B00EFADE621271A0AE5F7DE5422E8138083C2F76CA`

**Audit date**: 2026-07-22

**Overall status**: `completed_no_authority_transition`

## 1. 裁断

两族的 lineage-only audit 都执行完毕，但都没有证明 statistically independent lineage：

| Family | 冻结规则下的结果 | 独立 lineage 配额 |
|---|---|---|
| CAM-LDS | `source_native_collection_grouping_supported_independence_unproven` | 不计入 |
| SOCBED | `source_native_run_grouping_not_fully_supported` | 不计入 |

本结果不改变 family role、train quota 或 L2 Gate，不授权 baseline 或微调。

## 2. CAM-LDS

### 2.1 有界读取

| 项目 | 结果 |
|---|---:|
| Archive SHA-256 | `BA824F500AF6D64925792D6A693E54AFB761D1CFB5FE515EFB2206035772BADE` |
| Archive bytes | 213,771,977 |
| Central-directory members | 42,596 |
| Central-directory uncompressed bytes | 4,442,710,861 |
| 合规 member | 1,484 |
| 按冻结首尾规则读取 member | 1,308 |
| 实际读取 bytes | 25,920,449 |
| 采样行 | 75,540 |
| 可解析 timestamp | 9,797 |

没有打开 `sequences`、`techniques`、`configs`、`attacker`、`facts.json` 或 `eve.json`，也没有保留 event message、命令、IP、label 或原始路径。

### 2.2 Grouping 结果

冻结规则以 `/steps/` 之前的 prefix 作为 `collection_anchor`，以 `/logs/` 之前的 prefix 作为 `step_anchor`。结果为：

- 1,061 个 step group；
- 但全部落入 **1 个 collection candidate**；
- 该 collection 中有 5 个 path-level host scope、13 个 payload-level host hash；
- timestamp 样本覆盖 15 个 UTC 日期；
- `independent_run_verified=false`。

因此不能把 1,061 个 step 当作 1,061 次独立运行。它们是同一个 source-native collection 下的 repeated views。CAM-LDS 在当前证据下无法满足每族至少四个独立 lineage 的要求。

## 3. SOCBED

### 3.1 有界读取

| 项目 | 结果 |
|---|---:|
| Archive SHA-256 | `7EDA65F08BBE6F274C1FEFF178AE132CFD0E8EDBDF0A10EF08321259B6FACC54` |
| Archive bytes | 77,984,817 |
| Central-directory members | 244 |
| Central-directory uncompressed bytes | 1,264,018,131 |
| 合规 `winlogbeat_<run>.jsonl` | 40 |
| 为内容哈希与有界前缀审计流式读取 bytes | 854,099,561 |
| 白名单字段采样行 | 20,480 |
| Parent views | 4 |
| Run suffix candidates | 10 |

文件的完整字节只用于 duplicate hash；语义字段只从每文件前 512 行中提取 timestamp/host 白名单。输出没有保存事件文本、原始文件名、hostname 或 label。

### 3.2 Grouping 结果

冻结规则把相同数字 suffix 的四个 parent view 合并为一个 run candidate：

- 10/10 suffix 均包含 4 个 distinct view；
- 10/10 通过结构 Gate；
- 没有发现跨 run 的相同 member hash 或相同 timestamp signature；
- 0/10 通过冻结的 sampled-day intersection Gate；
- 因而 `bounded_run_group_count=0`。

这不表示 10 个 suffix 一定是同一次运行，而是说明当前有界字段无法按预注册时间规则证明四个 view 属于同一 run。不能在看到失败后将四视图时间相交规则改成更宽的“日期范围大致重叠”。若上游另有 source-native experiment/run manifest，可以在新的、独立授权中作为外部 lineage 证据评审；本轮不能用事后规则补救。

## 4. 科学解释

### CAM-LDS

目录层面有大量 step，但 lineage 的正确统计单位不是 step。冻结算法揭示这些 step 共用一个 collection anchor，因此按 step 计数会产生严重 pseudoreplication。

### SOCBED

suffix 是有价值的 run proposal，但仅有文件命名还不足以证明多视图时间一致性和共享 testbed 状态下的独立性。它比 CAM-LDS 更接近可用 lineage，但在当前合同下仍不能取得配额信用。

## 5. Authority 与 Gate

| 项目 | 状态 |
|---|---|
| Label 用于判断/监督 | **否** |
| Raw event/semantic fields 持久化 | **否** |
| Normalization / training pair 生成 | **否** |
| Family role 变更 | **否** |
| Train lineage quota 通过 | **否** |
| Baseline / 微调 | **未运行** |
| HDFS 正式替换 | **暂缓，未推进** |
| CERT / IoT-23 下载 | **暂缓，未下载** |
| Kernel / Gamma / M3* | **未触碰** |
| L2 Gate | **false** |

## 6. 后续决策点

本审计只提供证据，不自动执行以下任何动作：

1. CAM-LDS：降为 inactive/engineering-only，或寻找独立运行来源替换；
2. SOCBED：评审上游、不可变的 experiment/run manifest，或降为 inactive/寻找替代；
3. 接受当前 train lineage quota 失败并保持 L2/baseline/微调关闭。

任何选择都需要新的显式授权，不能通过重分 step、任意时间切窗或放宽已冻结时间 Gate 来增加 lineage 数。

机器可检结果见 `llm-editor-v0.8-l2-cam-socbed-bounded-lineage-audit-result-v0.1-20260722.json`。
