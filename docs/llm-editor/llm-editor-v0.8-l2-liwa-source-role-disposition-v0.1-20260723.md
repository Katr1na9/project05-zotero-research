# Liwa Source-role Disposition v0.1

**裁断**：`downgrade_and_replace`

Liwa 从 `train_candidate` 降为 `inactive_engineering_only`，不再占用训练 family slot。family、lineage、sample quota 全部保持 0；替代 slot 重新标记为 vacant。

## 为什么不是继续 hold

字段隔离和 exclusion 的程序执行是成功的，但它通过的方式是将 1,109 条记录中的 1,047 条 quarantine。剩余 62 条只覆盖 3 个稳定 source-native run group，低于冻结的最少 4 组。

这不是一个继续补 metadata 就能闭合的问题：冻结 artifact 已经完成全量隔离与 exclusion。若要让 Liwa 重新满足门槛，只能依赖以下被禁止的操作：

- 调整 exclusion threshold、normalization 或 n-gram；
- 删除命中片段后放行记录；
- 把 paired logging views、文件、attack type 或时间窗口拆成假 lineage；
- 从标签缺失或 alert 缺失制造 null/unsupported。

因此让 Liwa 继续以 active train candidate 占位，会把一个已知无法获得 quota 的来源伪装成待闭合候选。科学上应直接停损。

## 降级后的允许范围

Liwa 只能在另行授权下作为 hash-only 的字段隔离/exclusion 回归 fixture；原 payload 不得进入 model view、train 或 development，也不能生成任何 target、null、benign、unsupported、abstention、temporal、candidate-q 或 polarity supervision。

不计划第二次 exclusion，也不允许修改 frozen exclusion 参数。

## 空出的替代 slot

新 slot：`train_executed_evidence_liwa_replacement_01`

候选必须同时满足：

1. 可验证的 artifact license、immutable revision、size 与 checksum；
2. payload 前至少 4 个 source-native run/capture group；
3. label、answer、scenario、detector output、文件名与路径监督可物理隔离；
4. protected exclusion 后仍至少保留 4 个稳定组；
5. 与 train/development/test 在 curator、artifact 和 nuisance 上独立；
6. 完成独立 bounded manifest、lineage、field-isolation、exclusion 与 capacity audit 前 quota=0。

## Metadata-only 优先队列

| 优先级 | 候选 | 当前姿态 | 主要阻塞 |
|---:|---|---|---|
| 1 | EVTX-ATTACK-SAMPLES | reserve | 278 个文件不能视为 278 次执行；须先证明至少 4 个 source-native execution group |
| 2 | N-BaIoT | hold | artifact license/checksum/data URL 未闭合；device count 不能代替 run；还需检查与 IoT-23 的跨 split 相关性 |
| 3 | 新 endpoint/provenance family | 未登记 | 须从 source identity、license、revision、checksum 和 lineage metadata 开始 |

以上均未获 replacement 批准，也未授权下载或 payload audit。AInception、ProVICs 和 CICAPT-IIoT 维持既有 fail/hold，不可用于填这个 slot。

ProvSec/LID-DS 已按现有 portfolio 约束优先服务 BETH/Atomic replacement，不能静默重复分配给该 slot。

## 终态

- Liwa role：`inactive_engineering_only`
- Liwa quota：0
- replacement slot：vacant
- training sample construction：false
- exclusion rerun/adjustment：false
- baseline/fine-tuning：false
- L2 Gate：false

本 disposition 只使用已提交的脱敏结果，没有重新读取 payload。
