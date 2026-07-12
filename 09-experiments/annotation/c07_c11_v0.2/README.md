# C07-C11 双人盲标包 v0.2

状态：`awaiting_annotations`。本目录没有任何人工标签。

## 包内容

- `public/`：27 个 claim、27 个公开动作意图、60 个粒度状态。
- `annotator_A/`、`annotator_B/`：首轮独立空白 CSV。
- `adjudicator/`：一致性计算后只填写分歧行；首轮不得提供给 A/B 作为讨论媒介。
- `packet_manifest.json`：随机种子、计数、公开文件和来源 case 文件 SHA-256。
- `agreement_results.json`：当前为 `awaiting_annotations`。
- `calibration_results.json`：当前为 `awaiting_annotations`。
- `admin/admin_key.json`：本地管理员隔离映射，受 `.gitignore` 保护，不提供给标注者。

完整 codebook：[人工标注协议 v0.2](../../../08-writing/human-annotation-evaluation-protocol-v0.2-20260712.md)。

## 当前启动条件

- 公开意图任务：可开始。
- 粒度任务：可开始。
- Claim 任务：暂不完整启动。C11 的 8 条记录可本地回查，但 C07-C10 的 19 条精确原始记录尚未恢复；详见[来源访问台账](../../../08-writing/human-annotation-source-access-ledger-v0.1-20260712.md)。

项目 notes 不是独立来源证据。不得要求标注者仅凭 notes 把 C07-C10 claims 标为 direct/partial/unsupported。

## 执行顺序

1. 管理员分别复制 `public/` 与对应的 `annotator_A/` 或 `annotator_B/` 给两名标注者；不要提供 admin、对方目录、结果文件和论文案例结论。
2. 每完成一行，将 `reviewed` 填为 `yes`。Intent 节点集合允许为空，多节点用 `|` 分隔。
3. 两人全部完成后，先运行一致性分析，不读取管理员 key。
4. 只把分歧 item 交给第三名裁决者，在 `adjudicator/` 中填写对应行。
5. 裁决完成后，由管理员运行 calibration；程序只输出聚合指标。

```powershell
python 09-experiments/scripts/analyze_annotation_agreement.py 09-experiments/annotation/c07_c11_v0.2
python 09-experiments/scripts/analyze_annotation_calibration.py 09-experiments/annotation/c07_c11_v0.2
```

严禁使用代码标签、LLM 标签或管理员映射代替任一人工标注者。
