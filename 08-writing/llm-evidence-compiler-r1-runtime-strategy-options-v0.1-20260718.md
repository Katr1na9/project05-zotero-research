# Project05 LLM 编译层 R1 Runtime 路线裁决 v0.1

日期：2026-07-18  
状态：`superseded_no_qwen_execution_authority`  
取代文件：`llm-evidence-compiler-open-base-finetuning-amendment-v0.1-20260718.md`  
说明：用户于 2026-07-18 明确否决 Qwen。本文件仅保留为 CTINexus R0 后的历史选型记录，任何 Qwen 下载、环境安装、训练与推理建议均不得执行。  
上游结论：CTINexus 最小 import 通过，完整 Windows runtime 被依赖闭包阻塞  
非目标：立即下载模型、安装完整依赖、运行 CTI、C07–C12 或接入 M3

## 1. 裁决问题

Project05 需要的是：

```text
散乱日志 / CTI / provenance
→ LLM 语义编译
→ 可回指、可拒绝、controller_eligible=false 的图 sidecar
→ 后续适配冻结 M3 controller
```

CTINexus 已完成“LLM 从 CTI 抽取并对齐知识图”的主要前作，因此 Project05 不应声称首创 CTI→KG。Project05 的方法空间是：把该类组件包装成具有逐边来源指针、信息上限、越界拒绝和控制器隔离的编译层。

## 2. 三条可选路线

### R1-A：完整复现上游 CTINexus

在 WSL2/Linux 或独立容器安装上游完整依赖，使用本地 Ollama/Qwen 与本地 embedding。

优点：

- 可形成最忠实的已知工作复用基线；
- 能直接报告 CTINexus-compatible pipeline 的可运行性。

缺点：

- 新增 WSL/容器、CUDA、Ollama、LiteLLM 和 UI/科学栈；
- 与当前 Windows 2080 Ti 环境的部署差异较大；
- 工期和磁盘显著增加。

定位：可选 baseline，不应成为主方法的唯一依赖。

### R1-B：在 Windows 强行固定 CTINexus 完整依赖

为 LiteLLM 等依赖寻找旧版 wheel 或自定义兼容锁。

优点：保留 Windows 原生运行。

缺点：

- 偏离 CTINexus 当前无上限依赖声明；
- 很容易把依赖兼容问题误写成方法工作；
- 结果对特定包版本敏感，复现性较差。

定位：不推荐。

### R1-C：Project05 轻量本地编译器（推荐）

使用一个冻结的本地 Qwen2.5-7B-Instruct 4-bit 与小型本地 embedding，直接产生已经冻结的 CTINexus-compatible triplet bundle，再统一经过 Project05 adapter：

```text
Qwen compiler output
→ triplet schema
→ pointer resolution
→ same-record support
→ actor/campaign/attribution reject
→ target-graph sidecar
```

优点：

- 与主论文“语义建图层 → 调查控制层”结构直接对齐；
- 不需要 Gradio、完整 CTINexus app 或付费 API；
- 11 GB 显存下 7B 4-bit 具备现实可行性；
- 可以把 CTINexus 作为前作/接口基线，而不是把主方法绑死在第三方 UI 框架。

限制：

- 不得称为“运行了 CTINexus”；准确说法是“CTINexus-compatible clean-room compiler profile”；
- 模型、量化、embedding、prompt、解码和输入长度都必须另行冻结；
- unit smoke 通过前不得运行 CISA validation。

## 3. 推荐产品矩阵

| 层 | 推荐实现 | 论文角色 |
|---|---|---|
| 日志确定性规范化 | 既有 frozen adapters / Rule-Strong | 强基线与安全路径 |
| CTI 语义编译 | R1-C 本地 Qwen compiler | 主线前端方法组件 |
| 兼容接口 | CTINexus-compatible triplet schema | 与已知工作连接，不声称首创 |
| 来源与越界控制 | Project05 source-span / admission Gate | 主要系统贡献 |
| 调查控制 | 冻结后的 M3 | 是否可溯源、取证顺序、STOP |
| 上游 CTINexus runtime | R1-A，若资源允许 | 可选复用 baseline |

## 4. R1-C 的最小下一授权

下一轮仍建议只做配置设计和本机资源探测，不立刻下载权重：

1. 核对 GPU、CUDA、Ollama/Transformers 可用性；
2. 冻结 Qwen2.5-7B-Instruct 4-bit 的准确仓库、revision、许可和磁盘预算；
3. 冻结本地 embedding 候选及许可；
4. 冻结 CTID 1 文档的 unit prompt、最大 token、解码和失败条件；
5. 出 `R1-C model/runtime catalog` 供用户审阅。

该授权不包含权重下载、环境安装、正式推理、CISA validation、C07–C12 或 M3 接线。
