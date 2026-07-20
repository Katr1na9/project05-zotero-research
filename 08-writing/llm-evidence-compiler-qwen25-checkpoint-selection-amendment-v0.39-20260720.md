# Project05 Qwen2.5 checkpoint 选择实施修订 v0.39

日期：2026-07-20

用户在 v0.38 正式训练完整通过并被明确告知下一步后要求“继续推进”。本修订仅授权 Task 5：使用冻结的 300 条 training-validation 对 epoch 1/2/3 三个 checkpoint 做确定性评价并选择唯一 adapter；不授权 General vs Adapted 配对比较、development/test、C07–C12 或 M3。

## 冻结协议

- 数据：`training-validation.jsonl.gz`，SHA-256 `7607F79387CD2139640B2DB323C45C87815D2E8780B84D979092432ADAFBF552`；
- 组成：Loghub Linux 150 + Zeek non-PCAP 150；每族 supported / unsupported-by-bound-pointer 各 75；
- checkpoint：epoch 1/2/3 全量评估，不得按 train loss 预删；
- 解码：greedy，`do_sample=false`，`max_new_tokens=256`，invalid/超长/无 EOS 均按错误，不修复、不重试；
- 主指标：两来源族等权的 support-decision macro-F1；
- tie-breakers：canonical JSON exact、normalized-edge exact、pointer exact、较低 assistant-token NLL、较早 epoch；其中 NLL 按该 checkpoint 全部 assistant target tokens 加权聚合，不按样本长度等权平均；
- 每个 checkpoint 额外对预冻结的 16 条平衡面板重复生成，raw output SHA-256 必须逐条一致；
- 原始 generation 仅留服务器，新提交只包含脱敏的哈希、逐样本机械指标和 aggregate audit。

模型、tokenizer、4-bit NF4、FP16 compute、prompt、schema、pointer、训练数据和 checkpoint 文件哈希均继承 v0.38，不得修改。评价在固定 RTX 4090 GPU 2 上以 detached worker 执行；任何 CUDA/OOM、非有限 NLL、哈希漂移、显存/容量失败均停止，不自动 retry 或换 checkpoint。

## 结果边界

checkpoint selection 只决定后续正式比较可使用哪个 adapter。training-validation 分数是模型选择数据上的诊断，不能写成论文 test 结果，也不能证明 adapter 优于 General。选择完成后硬停在 General vs Adapted paired evaluation 的单独授权点。
