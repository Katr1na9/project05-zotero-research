# C07-C11 双人盲标首轮结果 v0.1

日期：2026-07-13

状态：A/B 首轮 114/114 条可比；等待第三人裁决与粒度独立性确认

依据：`agreement_results.json`、`calibration_results.json`、`annotation_intake_manifest.json`

## 1. 导入与完整性

| 任务 | A 已审 | B 已审 | 双人可比 | A/B 分歧 |
|---|---:|---:|---:|---:|
| Claim 支持度与来源指针 | 27/27 | 27/27 | 27 | 7 |
| 公开动作意图 | 27/27 | 27/27 | 27 | 25 |
| 可支撑调查粒度 | 60/60 | 60/60 | 60 | 0 |
| 合计 | 114/114 | 114/114 | 114 | 32 |

六个源文件均已记录 SHA-256，未被覆盖。导入时共执行 12 项机械规范化：1 行未加引号的 Claim 备注逗号、4 个 `2_directl` 标签拼写、7 行 Intent 备注逗号或漏分隔符。所有修复均保留原值、新值和理由；规范化后 blind ID、候选节点和标签域全部通过冻结 packet 校验。

## 2. 首轮一致性

### 2.1 Claim 支持度

- 原始一致率：0.7407（20/27）
- Quadratic-weighted Cohen's kappa：-0.1455
- `U_unassessable` 比例：0
- 来源指针原始一致率：1.0000

Claim κ 未达到预注册的 0.70 门槛。两人标签都高度集中于 `1_partial`，边际分布失衡使 κ 与原始一致率方向不同；这不是把负 κ 简化解释为“低于随机”即可结束，但依然明确表示当前 codebook 没有获得可接受的跨标注者可靠性。来源指针 27/27 均被两人标为 `yes`，因此原始一致率为 1，但没有 `no` 或 `unassessable` 变异，不能证明标注者能识别错误指针。

### 2.2 公开动作意图

- Exact match：0.0741（2/27）
- Mean Jaccard：0.3673
- Micro precision：0.7407
- Micro recall：0.3636
- Micro F1：0.4878

Mean Jaccard 和 micro F1 均低于预注册的 0.70/0.80 门槛。25/27 条分歧说明“宽意图应选择一个直接节点还是一组可能节点”在当前 codebook 中没有被两名标注者一致理解。该结果直接否定“当前 intended 编译已经获得人工可复现性”的强主张。

### 2.3 可支撑粒度

程序计算得到原始一致率、within-one-level 和 quadratic-weighted kappa 均为 1.0000。但 A/B 两个粒度源文件的 SHA-256 完全相同，且所有自由文本也逐字节一致。在确认两份文件确由两名标注者独立完成之前，该结果只能记为来源异常，不能作为独立双盲一致性证据写入论文。

## 3. 裁决与校准状态

第三人盲裁决包已生成，共 32 项：7 个 Claim、25 个 Intent、0 个粒度项。裁决包不包含 A/B 标签、管理员 key、recoverable claims 或规划结果。当前 `calibration_results.json` 正确保持：

```text
status = awaiting_adjudication
calibrated_human_items = 0
```

因此尚不能报告 final-human 与 compiled intended/G0-G3 代理之间的校准指标，也不能判断粒度代理是否通过 `kappa >= 0.70` 且 over-granularity rate 不高于 0.10 的门槛。

## 4. 当前科学结论

1. “两名标注者已经提交全部题目”成立；“人工效度 Gate 已关闭”不成立。
2. Claim 与 Intent 首轮可靠性均未过预注册门槛，必须如实报告并修订 codebook，不能用裁决后的单一答案掩盖首轮分歧。
3. 第三人裁决可产生最终标签用于代理校准，但不会把 A/B κ 改写成通过。
4. 粒度任务需先确认独立完成来源；无法确认时必须由 B 或新的标注者重新独立填写。
5. C12 尚未加入本轮人工标注，actor/campaign 正确性仍没有人工终点。

## 5. 下一步

1. 将 `c07_c11_v0.2_adjudication_v0.1.zip` 交给第三名标注者，回收 7+25 行结果。
2. 确认粒度文件为何完全相同；不能确认独立性时重做该任务。
3. 合并裁决结果并运行 `analyze_annotation_calibration.py`。
4. 基于分歧模式建立 codebook round 2，新增“单节点直接目标”和“宽意图候选集合”的判定例。
5. 论文只写首轮负结果和待裁决状态，不宣称 claims、intended 或 G0-G3 已获人工验证。
