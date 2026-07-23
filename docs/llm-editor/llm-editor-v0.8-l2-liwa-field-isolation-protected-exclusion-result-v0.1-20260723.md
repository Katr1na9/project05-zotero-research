# Liwa 字段隔离与 protected-exclusion 执行结果 v0.1

**日期**：2026-07-23

**机器状态**：`passed_no_authority_transition`

**科学状态**：字段隔离与 exclusion 执行合格；排除后的 lineage/capacity 预失败，Liwa 不获得任何 quota。

## 执行边界

本次执行以本地提交 `05d7e07` 中冻结的合同为基础，并由独立 execution-authority 工件限定。执行器只读取冻结的 Liwa archive 与不含 raw private gold/test payload 的 protected signature lock；未读取 protected 原文，未提取 archive，未持久化 Liwa 字段值、member path、监督字段值或模型输出。

本次没有构造训练样本，没有运行 baseline、微调或 L2 Gate，也没有修改 Kernel、Γ 或 M3*。

## 字段隔离

| 项 | 结果 |
|---|---:|
| CSV members | 31 |
| records | 1,109 |
| unknown fields | 0 |
| forbidden-supervision 非空值 | 2,146 |
| detector-summary 非空值 | 18,312 |
| binder-only 非空值 | 4,436 |
| candidate raw-event 非空值 | 51,193 |
| ambiguous pointer candidates | 0 |
| bound case evidence | 0 |

字段 action map 在读取行值前编译；deny 优先，未知字段 fail closed。`source_rule_*`、MITRE 映射、score 与包装器/decoder 元数据未进入 model-view scanner；程序 pointer 只输出不可逆 hash，原始 member path 不可见。

结果只保存字段类别计数、字段身份 hash 数、header-shape hash、run-group hash 与 pointer candidate hash，不保存任何原始字段值。

## Protected exclusion

保护集合保持为 E3、E5、OpTC、OTRF 与 WitFoo，方法与合同一致：

- normalized exact：`NFKC+casefold+whitespace-collapse` + SHA-256；
- near duplicate：normalized character 5-gram Jaccard；
- 阈值：`>=0.85`；
- 命中单位：整条 record 及其所有派生 packet；
- 命中后不得调阈值、删词或缩小 quarantine 单元。

### 首遍

| 项 | 结果 |
|---|---:|
| archive exact match | 0 |
| member exact match | 0 |
| normalized-exact matched records | 1,047 |
| near-duplicate matched records | 0 |
| quarantined records | 1,047 |
| maximum Jaccard | 1.0 |

这不是 near-duplicate 阈值边缘效应。所有 quarantine 均由冻结 normalized-exact 检查触发。

### Post-quarantine 复扫

| 项 | 结果 |
|---|---:|
| rescanned records | 62 |
| remaining exact matches | 0 |
| remaining near matches | 0 |
| maximum Jaccard | 0.6764705882352942 |

复扫集合清洁，因此 exclusion 过程本身通过；`passed_no_authority_transition` 只表达这一点。

## 排除后的容量诊断

原 bounded audit 给出 30 个稳定 source-native run group。exclusion 后：

- 27 个稳定 run group 被完全 quarantine；
- 仅 3 个稳定 run group 保留至少一条 clean record；
- clean records 合计 62；
- 既有 future role review 最少 4 个稳定组的门槛已无法满足。

因此 Liwa 不能因为本次技术执行通过而获得 family、lineage 或 sample credit。它仍只是 effective catalog 中的 `train_candidate`，当前更准确的科学解释是：**隔离可实现，但 protected overlap 导致可用容量与 lineage 不足，等待独立 source-role disposition；不应进入样本物化。**

## Quota 与权限终态

| 项 | 终态 |
|---|---:|
| family credit | 0 |
| lineage credit | 0 |
| sample credit | 0 |
| sample materialization authorized | false |
| baseline authorized | false |
| fine-tuning authorized | false |
| L2 passed | false |

下一道门只能是独立的 quota-capacity、lineage 与 source-role disposition。根据本次结果，若保持冻结的最少 4 组要求，Liwa 当前不会通过该门；不能通过重切窗口、拆分 logging view 或改变 exclusion 参数补救。

机器可检结果见同名 JSON。
