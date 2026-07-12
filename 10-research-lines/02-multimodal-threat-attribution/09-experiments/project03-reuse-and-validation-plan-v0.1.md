# Project03 Reuse and Validation Plan v0.1

日期：2026-07-12  
状态：数据可行性预审；不是实验预注册，G5 前不启动模型实验。

## 1. 最小数据单元

独立样本单位暂定为一次有唯一 `run_id` 的 attack replay，而不是单个 packet、单个 hop 或数据库中的一条 threat 记录。

每个 run 至少保存：

```text
run_id
source_pcap_id + sha256
attack_family / behavior label source
controller_config + live_table_snapshot
intended_modality
capture[host1, s1_ingress, s1_egress, s3]
observed_wire_modality_per_hop + detector + evidence
packet_count / byte_count / duration / directionality
threat_id / stage_candidates / intent_candidates
timestamp / software commit / environment
```

## 2. 模态字段必须拆分

| 字段 | 含义 | 允许来源 |
|---|---|---|
| `configured_modality` | controller/交换机运行态 | live table snapshot 优先，state file 只作声明 |
| `intended_modality` | 数据生成或实验设计期望 | manifest；文件名前缀仅作兼容输入 |
| `observed_wire_modality` | 抓包字节支持的真实封装 | parser + EtherType/layer evidence |
| `resolved_modality` | 综合后的候选结论 | 推断模块，必须给 evidence/confidence |
| `modality_conflict` | 三类声明是否矛盾 | 明确规则或模型输出 |

禁止继续把 filename-first 结果写入 `True_Modal` 并当作 ground truth。

## 3. 配对与对照设计

1. 选择同一组 source PCAP/attack behavior，分别通过五种模式重放。
2. 保持攻击标签、包序、时间缩放、发送端和目标端尽量一致。
3. 每种模式至少重复多个 run，避免把一次链路故障当成模态属性。
4. 设置故意错配条件：配置与文件名不一致、运行态漂移、某 hop capture 缺失、封装剥离或错误解析。
5. SCION 在获得真实数据面封装前只进入 `intended-only` 组，不进入五模态 wire-level 性能平均。

## 4. 首轮不训练模型也能完成的验证

- 建立五模态 parser/unit tests；
- 生成 configured/intended/observed 一致性矩阵；
- 统计各 hop packet survival、封装变化和解析失败率；
- 用规则 baseline 定位第一个不一致 hop；
- 检查现有 stage/intent 在仅改变 modality label 时是否发生不合理变化；
- 量化 modality keyword 对 CAPEC 排序的实际贡献。

## 5. 候选指标

| 任务 | 指标 |
|---|---|
| 模态观测 | macro-F1、per-modality recall、unknown/abstain rate |
| 错配检测 | AUROC/AUPRC、conflict-type macro-F1 |
| 追溯定位 | first-error-hop accuracy、path edit distance、evidence coverage |
| 阶段/意图候选 | Recall@k、MRR、nDCG；有可靠标签时再用 accuracy/F1 |
| 可信度 | ECE、Brier、NLL、risk-coverage、selective accuracy |
| 鲁棒性 | missing-hop curve、label/wire conflict curve、leave-one-modality-out |

## 6. 泄漏与伪增益审计

- 文件名前缀不能进入行为/意图预测特征；
- `True_Attack`、`Predicted_Class` 和 CSV technique 不能同时作为输入与评价真值；
- 同源 PCAP 的五种重放必须按 source group 切分，不能跨 train/test；
- controller mode 不能替代 wire observation 真值；
- 重复字段和同一事件的格式转换不算独立模态；
- 先报告每个模态实际提供的新增信息，再报告融合增益。

## 7. 近期只做的资产恢复

1. 找回 120 条批次对应的 PCAP、CSV、bridge state 和远端运行代码版本。
2. 对五种模态各选 1-2 个样本制作 evidence bundle。
3. 为每个 bundle 生成 manifest 和 SHA-256，不提交原始大文件。
4. 核验 SCION 样本能否获得真实封装；不能则保留明确缺失状态。
5. 完成撞题检索后，再决定是否扩充数据或设计模型。

