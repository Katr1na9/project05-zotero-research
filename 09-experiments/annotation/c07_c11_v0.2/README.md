# C07-C11 双人盲标包 v0.2

状态：A/B 首轮 `complete`，114/114 条可比；当前为 `awaiting_adjudication`，并等待粒度文件独立性确认。

## 包内容

- `public/`：27 个 claim、27 个公开动作意图、60 个粒度状态。
- `annotator_A/`、`annotator_B/`：已导入并机械规范化的首轮 CSV；原始 SHA-256 和修复记录见 `annotation_intake_manifest.json`。
- `adjudicator/`：一致性计算后只填写分歧行；首轮不得提供给 A/B 作为讨论媒介。
- `packet_manifest.json`：随机种子、计数、公开文件和来源 case 文件 SHA-256。
- `agreement_results.json`：114/114 条首轮一致性结果。
- `calibration_results.json`：当前为 `awaiting_adjudication`，不得提前报告最终代理校准。
- `annotation_round_status.json`：当前 round 的结构化状态、阈值判定和来源异常。
- `admin/admin_key.json`：本地管理员隔离映射，受 `.gitignore` 保护，不提供给标注者。

完整 codebook：[人工标注协议 v0.2](../../../08-writing/human-annotation-evaluation-protocol-v0.2-20260712.md)。

## 当前结果

- Claim：raw agreement 0.7407，weighted kappa -0.1455，7 项待裁决。
- Intent：exact 0.0741，mean Jaccard 0.3673，micro F1 0.4878，25 项待裁决。
- Granularity：程序结果为 1.0000，但 A/B 源文件 SHA-256 完全相同；确认独立来源前不得作为双盲证据。
- 第三人包：`../distribution/c07_c11_v0.2_adjudication_v0.1/`，共 32 项，不含 A/B 答案和管理员映射。

项目 notes 不是独立来源证据。管理员已向首轮标注者提供本地 source excerpt；来源可访问不等于标签可靠性通过。

## 执行顺序

1. 将第三人裁决 ZIP 交给未查看 A/B 结果的裁决者。
2. 回收 7 个 Claim 与 25 个 Intent 结果，并合并到 `adjudicator/` 的对应行。
3. 单独确认两份粒度文件是否由两人独立完成；无法确认时重新独立标注。
4. 裁决和来源确认完成后，由管理员运行 calibration；程序只输出聚合指标。

```powershell
python 09-experiments/scripts/analyze_annotation_agreement.py 09-experiments/annotation/c07_c11_v0.2
python 09-experiments/scripts/analyze_annotation_calibration.py 09-experiments/annotation/c07_c11_v0.2
```

严禁使用代码标签、LLM 标签或管理员映射代替任一人工标注者。
