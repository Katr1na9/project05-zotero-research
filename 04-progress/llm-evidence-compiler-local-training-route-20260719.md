# LLM evidence compiler：本地训练路线恢复记录

日期：2026-07-19
状态：`local_smoke_authorized_server_route_abandoned`

## 决策

用户已明确废止 RTX 4090 服务器训练提案，恢复本地 RTX 2080 Ti 路线。
自该决策起，不再授权连接服务器、安装服务器环境、下载服务器模型权重或执行
服务器训练。此前服务器尝试因磁盘空间不足在环境安装阶段失败；未下载 Qwen
权重、未执行模型训练，也不构成实验结果。

服务器路线的历史合同与审计链只作过程记录，不删除、不改写，也不再作为当前
执行权威。服务器上由本次尝试创建的隔离目录不在本决策中远程清理，以避免将
“废止路线”擅自扩大为删除操作。

## 当前本地执行边界

- 硬件：NVIDIA GeForce RTX 2080 Ti，11 GB，compute capability 7.5。
- 运行根目录：仓库内 Git-ignored `.local-qwen25-smoke/`。
- 模型：`Qwen/Qwen2.5-7B-Instruct`，固定 revision
  `a09a35458c702b33eeacc393d103063234e8bc28`。
- 方法：4-bit NF4、double quantization、FP16、LoRA r=16/alpha=32。
- smoke：20 条均衡样本、16 个 microbatches、1 个 optimizer step。
- 显存硬停：peak reserved VRAM 不超过 10.5 GiB。
- 输出：只允许 adapter；禁止 merged model、Hub upload 和原始生成文本入库。

## 授权范围

当前授权只覆盖本地隔离环境、固定权重下载与哈希验证、单步 smoke、adapter
保存/重载和一次 8-token training-validation generation。正式多轮训练、正式
推理、C07-C12、M3 接线、Paper A 修改与论文正向结论仍未授权。

## 下一硬停

本地 smoke 完成后必须提交运行环境、loss、trainable ratio、峰值显存、adapter
文件和边界审计。只有 smoke 通过并经结果复核，才能另行打开正式训练 Gate。
