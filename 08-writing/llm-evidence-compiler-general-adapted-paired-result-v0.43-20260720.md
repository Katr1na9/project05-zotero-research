# Project05 General Qwen vs epoch-2 QLoRA 配对原子评测结果 v0.43

日期：2026-07-20

状态：`completed_negative_adapter_diagnostic`

## 1. 裁决

一次性 training-validation 配对原子评测已完整执行并通过技术完整性 Gate，但 epoch-2 QLoRA 未通过预注册 Adapter 诊断 Gate。

最终处置：

- `QWEN-ADAPTED`：降级为 `not_mainline_eligible`；
- `QWEN-GENERAL`：严格 schema 原子评测失败，不作为当前主线编译条件；
- 不更换 epoch 1/3，不修改 prompt、parser、Gate 或面板；
- 不申请 C07–C12、development/test 或 M3 运行来补救；
- Project05 主线继续保留既有 `RULE-STRONG` / `REUSE-HYBRID` 路线；本轮不声称它们在同一正式 test 上优于 LLM，只说明当前 LLM 条件没有通过进入正式 test 的前置 Gate。

## 2. 执行完整性

| 项目 | 结果 |
|---|---:|
| 冻结面板 | 16 条 training-validation |
| General 调用 | 16 |
| Adapted 调用 | 16 |
| 总调用 | 32 |
| General-first / Adapted-first | 8 / 8 |
| 技术 Gate | **通过** |
| Adapter 诊断 Gate | **失败** |
| wall time | 175.56 秒 |
| peak allocated VRAM | 5,974,477,312 bytes |
| 结束前 free VRAM | 18,660,589,568 bytes |
| 项目资源总量 | 30,842,874,744 bytes `< 34,000,000,000` |
| failure audit | 无 |

所有生成共享同一 base、tokenizer、runtime、NF4 配置、greedy decode、parser/scorer 和 RTX 4090。唯一模型差异是 adapter state。

## 3. 核心结果

| 指标 | QWEN-GENERAL | QWEN-ADAPTED | Adapted − General |
|---|---:|---:|---:|
| family-macro support-decision F1 | 0.000 | 0.500 | +0.500 |
| supported-class F1 | 0.000 | 0.000 | 0.000 |
| unsupported-class F1 | 0.000 | 1.000 | +1.000 |
| schema valid rate | 0.000 | 0.500 | +0.500 |
| invalid rate | 1.000 | 0.500 | −0.500 |
| pointer exact | 0.000 | 0.500 | +0.500 |
| normalized-edge exact | 0.000 | 0.500 | +0.500 |
| supported-output rate | 0.000 | 0.000 | 0.000 |
| ceiling violation | 0.000 | 0.000 | 0.000 |

表面的 macro-F1 增量完全来自 negative 类：

- General：16/16 全部 `invalid_top_level_schema`；
- Adapted：8 个 unsupported 全部正确；
- Adapted：8 个 supported 全部为 `invalid_edge_source_pointer`；
- Loghub 与 Zeek 的 Adapted supported-class F1 均为 0。

因此不能用 `+0.50 macro-F1` 宣称适配有效。Adapter 仍未产生任何严格可接受的 supported 输出，类别塌缩在 checkpoint 选择后的独立原子切换检查中继续存在。

## 4. Gate 逐项裁决

通过：

- family-macro F1 不低于 General；
- invalid rate 不高于 General；
- pointer exact 不低于 General；
- unsupported F1 护栏；
- supported-output rate 相对护栏；
- ceiling violation 不升高。

失败：

- Adapted overall supported-class F1 必须严格大于 0；
- Adapted 在两个 held-out 来源族的 supported-class F1 都必须严格大于 0。

任一失败即不能通过 Adapter 诊断 Gate，因此总判定为失败。

## 5. 科学边界

本结果来自 checkpoint 选择所用的 training-validation 分布，不是 C07–C12 独立 test，也不是 case-macro `n=6` 正式结论。因此：

- 可以说“当前 QLoRA 在冻结原子协议中只学会了 unsupported 路径，supported 路径仍塌缩”；
- 可以说“当前 adapter 未达到进入主线或正式 test 的前置资格”；
- 不能说“QLoRA 普遍无效”；
- 不能说“LLM 对 APT 溯源普遍无效”；
- 不能把本结果写成 Paper A 的正向或正式效果量；
- 不能声称 Rule/Reuse 已在同一正式 test 上胜出。

## 6. 隐私与范围

- raw generation：32 行，仅服务器保存，未下载；
- 本地只回收 generation audit、32 行脱敏 metrics、score audit 和非敏感日志；
- 本地结果目录不存在 `paired-raw-generations-v0.1.jsonl`；
- 未读取 train、development/test 或 C07–C12；
- 未运行 M3；
- 未修改 `run_mvp.py`、Paper A、专利、旧实验结果或成本配置。

## 7. 工件哈希

| 工件 | SHA-256 |
|---|---|
| generation audit | `52881BE8E76FC41D5B3BA82F3F6FD94A0D1AA62C3B5E5574FFA664B60A3D9A98` |
| sanitized metrics | `D851450B2181E34E73A712BC74E129C23B6E8C179E2F47BE3977DC17EAAC78F0` |
| score audit | `3BD831BF7F4AD1CB69DF9623AFCA752B59030FAEDFF198167BCECCD5CE04995B` |
| detached log | `0E570D3A0AFED69A60B3E17E131D9D3367A3192E0DD5729A2485681BBD167299` |

## 8. 后续状态

本次 v0.42 执行额度已消耗。当前 adapter 路线关闭，不自动进行：

- 第二次配对运行；
- checkpoint 替换；
- parser repair；
- 新 seed/新超参数；
- development/test 或 C07–C12；
- M3 接线。

若未来重新研究 LLM 编译器，需要把“supported 正例的严格 pointer/schema 生成”作为新的训练与建模问题，建立新设计、新数据和新 authority；不得把本轮失败静默覆盖。
