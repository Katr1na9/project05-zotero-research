# Project05 主线 Qwen2.5 QLoRA：Task 4 显存硬停记录

日期：2026-07-19

状态：`failed_primary_capacity_gate_no_checkpoint`

## 裁决

唯一获授权的本地 primary QLoRA 训练已启动，但在第 3 个 optimizer step 完成后的资源检查中超过预注册的 `10.5 GiB` peak reserved VRAM 上限。执行器按合同立即停止，没有自动重跑、没有改变序列长度、LoRA rank、batch、数据、随机种子或硬件。

这是一项容量 Gate 负结果。它不说明 Qwen 或 QLoRA 的任务质量，也不能用于判断 adapter 是否改善证据编译；因为训练没有完成，根本没有形成可进入选择或评估的 checkpoint。

## 已执行范围

| 项目 | 结果 |
|---|---:|
| 训练执行次数 | 1 |
| 已完成 microbatches | 48 / 3600 |
| 已完成 optimizer steps | 3 / 225 |
| 已完成 epoch | 0 / 3 |
| checkpoint | 0 |
| adapter | 未保存 |
| 训练墙钟 | 328.282 秒 |

逐步日志在越界前完成了前两个 step 的写入：

- step 1：loss mean `0.598694`，gradient norm `1.682900`，peak reserved `11,240,734,720` bytes；
- step 2：loss mean `0.669790`，gradient norm `1.884643`，peak reserved `11,249,123,328` bytes；
- 冻结上限：`11,274,289,152` bytes；
- step 3 在越界检查处停止。当前失败 manifest 没有记录该步的实际峰值，因此不得事后编造数值。

## 失败后的完整性

- 本地失败 manifest：841 bytes，SHA-256 `D18D4A58875C45602D2ADF767345D5234D9B5D8286D2881D5169F785B2222DEB`；
- 本地 progress JSONL：699 bytes，SHA-256 `A7CECF88D484B790AA533731B6E20DB899283DA95E28A5722A55A07A988465FF`；
- GPU 已释放至 0 MiB、0% utilization；
- 不存在 final training audit 或 checkpoint 目录；
- 未执行 generation、checkpoint selection、development/test、C07–C12、M3、服务器连接或 Paper A 修改。

## 当前硬停

原 v0.25 单次执行授权已经消费并以失败结束。禁止自动重跑或从头再训。后续若继续，必须先形成新的显存修订，明确是保持科学配置不变的 allocator/实现稳定化，还是书面修改 10.5 GiB 资源阈值；两种路线都需要新的预检和用户显式授权。

在新修订获批前，checkpoint selection、正式推理、C07–C12 与 M3 接线全部保持关闭。

## 验证

- Task 4 failure-result 专项测试：7/7 通过；
- primary / smoke / preflight / execution / failure 完整链：67/67 通过；
- 相邻 LLM compiler 回归：149 项中 145 passed、1 skipped、2 failures、1 error；
- 相邻非绿项仍是已有的 citation-report SHA、positive-remap 历史 records root 和 WP2 sidecar SHA 三项，与本次训练执行及失败结果无关。
