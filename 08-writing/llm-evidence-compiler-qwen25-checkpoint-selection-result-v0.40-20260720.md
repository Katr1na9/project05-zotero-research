# Project05 Qwen2.5 checkpoint 选择结果 v0.40

日期：2026-07-20

## 1. 结论

冻结的 training-validation checkpoint 选择已完整通过。epoch 1、2、3 各评价 300 条，共 900 条；每个 checkpoint 的 16 条确定性重复面板均逐条 raw-output SHA-256 一致。按预注册的来源族等权 support-decision macro-F1 及冻结 tie-breakers，唯一选择结果为：

- epoch：2；
- optimizer step：150；
- adapter SHA-256：`D29F2BE6DF4310B22535FE8FB0D59BEDB23BF7CDCC431D3BBDD6882F4FA3DF11`；
- 服务器引用：`server-output/primary-adamw-detached-v0.37/checkpoint-epoch-002/adapter`；
- checkpoint/adapter 仍仅保留在服务器，未下载、未合并、未上传 Hub。

该结果只是在 training-validation 上选择后续配对评测所用的 adapter，不是 test 结果，也不证明微调优于 General Qwen。

## 2. 冻结指标

| checkpoint | family-macro support-decision F1 | canonical JSON exact | normalized-edge exact | pointer exact | assistant-token NLL | schema valid |
|---|---:|---:|---:|---:|---:|---:|
| epoch 1 | 0.339478 | 0.496667 | 0.500000 | 0.963333 | 0.003777 | 0.973333 |
| **epoch 2** | **0.470216** | 0.453333 | 0.453333 | 0.463333 | **0.001624** | 0.463333 |
| epoch 3 | 0.436981 | 0.393333 | 0.396667 | 0.400000 | 0.001711 | 0.403333 |

epoch 2 在主指标上严格高于 epoch 3 和 epoch 1，因此无需启用 tie-breaker 才得到选择结论。

## 3. 必须保留的负面诊断

三个 checkpoint 在 Loghub 与 Zeek 两个来源族上的 `supported` 类 F1 均为 0。它们没有在该验证集上产生被 scorer 接受的 supported 决策：

- epoch 1：主要统一输出 `unsupported_by_bound_pointer`，Zeek 另有 8 条 invalid；
- epoch 2：Loghub 为 64 条 unsupported + 86 条 invalid，Zeek 为 75 条 unsupported + 75 条 invalid；
- epoch 3：Loghub 为 68 条 unsupported + 82 条 invalid，Zeek 为 53 条 unsupported + 97 条 invalid。

因此，epoch 2 是“冻结规则下相对最优的 checkpoint”，不是“已证明有效的证据编译器”。类别塌缩必须进入后续结果解释；禁止只报告 macro-F1 而省略 supported-class F1=0。General vs selected QLoRA 配对评测必须允许得出 adapter 无增益或有害的负结果，并按预注册路径降级 adapter。

## 4. 完整性与资源 Gate

- audit SHA-256：`2E0EFF92CFF06D70317C87E63922881C082338CB9C4141BB761255B9BE0CB1EC`；
- metrics：900 行，SHA-256 `E2EE503E6AE0D543446215C0547FE1D5E388220A3107DDEECB19EFB62E4FBB20`；
- progress：91 行，SHA-256 `73E76F2867D1EC19F95B47A0509007ECBEDEAC68D6185E1B1A15CB82B40958A9`；
- raw generation：900 行，仅服务器保留，未下载；
- 三个 16 条重复面板：全部一致；
- wall time：9638.02 秒；
- peak allocated：6,955,277,312 bytes；
- cache normalization 前 free：109,182,976 bytes；
- cache normalization 后 free：18,658,492,416 bytes，超过 1 GiB Gate；
- 项目资源：30,837,780,096 bytes，低于 34,000,000,000 bytes Gate；
- failure audit：不存在；
- 完成后训练/选择进程已退出，固定 GPU 回到 18 MiB 使用、0% utilization。

## 5. 边界与下一步

本阶段未访问 train、development/test、C07–C12 或 M3，未执行 General vs Adapted，未修改 Paper A，也未授权正向论文主张。

用户已明确要求 checkpoint 选择结束后不中断进度。下一阶段将：

1. 以 epoch 2 adapter 作为唯一 Adapted 条件；
2. 冻结 General（adapter off）与 Adapted（同一底座、adapter on）的同输入、同 prompt、同 tokenizer、同量化、同 greedy 解码配对合同；
3. 先实现模型无关验证、哈希链与失败 Gate；
4. 再按新 authority 执行配对评测；
5. 若 Adapted 未达到预注册增益或出现更严重 supported-class collapse，则降级 adapter，不得事后换 checkpoint 或改指标。
