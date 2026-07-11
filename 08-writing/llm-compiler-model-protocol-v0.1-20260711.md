# Project05 可选 LLM 语义编译支线协议 v0.1

日期：2026-07-11  
状态：支线暂停；不属于主学习模型，尚未运行模型实验

## 1. 当前事实

当前 C01-C09 主实验没有使用任何 LLM：

- 没有模型 checkpoint；
- 没有模型 API；
- 没有 LLM 生成的 evidence claim、动作或归因结果；
- M1、M2、M3a 都是确定性算法；
- 现有 evidence claims、CTI 节点、motif 和动作由规则编译与人工复核得到。

因此，“当前使用的 LLM 模型”严格答案是：**没有**。在完成下面的独立实验前，不应把 LLM 写成已经验证的贡献。

## 2. 支线候选模型

### 通用 LLM 对照

`Qwen/Qwen1.5-7B-Chat`，4-bit 推理。

选择理由：

- 已进入 Project05 精读文献，而不是临时追逐新模型。
- SEvenLLM 以 Qwen1.5 为底座，论文报告 Qwen 系领域模型整体表现较好。
- LocalIntel 对多种本地开源模型的比较中，Qwen1.5-7B-Chat 的综合结果最好。
- 官方 Qwen1.5 提供开源模型和量化版本，适合可复现实验。
- 当前设备为 RTX 2080 Ti 11 GB；7B 模型 FP16 约 13.7 GB，不能稳妥装入，但 4-bit 权重约 3.4 GB，留有 KV cache 和结构化生成空间。

### CTI 领域 LLM 对照

`Multilingual-Multimodal-NLP/SEVENLLM-Qwen1.5-7B`，4-bit 量化推理。

该 checkpoint 由 SEvenLLM 官方项目链接的 Hugging Face collection 发布，可检验 CTI 领域指令微调是否优于同底座通用模型。其模型卡内容为空、原始权重标记为 F32、使用量很低，因此不能直接视为可靠赢家，必须记录量化来源、revision 和文件哈希，并与基础 Qwen 配对验证。

### 非 LLM 基线

- 当前规则编译器。
- 人工 gold evidence claims，只作为性能上界，不作为自动方法。

暂不使用 Qwen3-Plus：TAA-EPLMR 使用它，但它是服务型模型，不适合作为本地、可复现、硬件可控的首个实验版本。暂不使用 LLMAPT 中的 MalwareGPT/ThreatLlama：精读显示其训练与开源细节不足。

## 3. LLM 的唯一职责

LLM 只做离线语义编译：

```text
CTI 段落 / provenance motif 摘要 / 日志片段 / IOC 上下文
    -> 符合 evidence_claim.schema.json 的候选 claim
    -> schema 校验、来源指针校验、去重与拒收
    -> 进入确定性 evidence state
    -> M2 进行粒度判断、采集排序与停止
```

LLM 不直接输出 actor，不计算 Oracle，不选择最终采集动作，也不覆盖 M2 的停止规则。这样可以把模型理解能力与规划能力分别评估。

本支线不替代 Project05 的主模型路线。主模型依次为 Logistic Regression baseline、XGBoost action-value predictor 和条件具备后的 DQN/Dueling DQN 序贯策略。

## 4. 数据切分

- 提示与校验规则开发：C04-C06。
- 冻结测试：C07-C09。
- 输入单位必须保留 `source_id`、原始文本范围或事件/motif 指针。
- gold 输出由现有人工复核 claims 转换，并再次抽查，不允许直接把模型输出回写成 gold。
- 第一批 pilot 已生成 14 条真实代表事件样本，其中 10 条为原子事件主样本，4 条为上下文依赖对照；`model_input` 与 `gold_claim` 物理分栏，模型不得读取后者。

## 5. 第一阶段指标

- JSON/schema 合规率。
- claim existence precision、recall、F1。
- `source_type`、`event_time`、`entities`、`attack_stage` 等字段准确率。
- source pointer exact match / overlap。
- unsupported claim rate，即没有输入来源支撑的 claim 比例。
- 五次重复推理的一致性。
- 每条输入延迟、峰值显存和输出 token 数。

## 6. 第二阶段端到端指标

将三种 evidence claims 分别送入冻结的 M2：

1. 人工 gold claims；
2. 规则编译 claims；
3. Qwen1.5 / SEvenLLM 编译 claims。

比较目标成功率、支持粒度一致率、ceiling violation、采集动作 top-1 一致率和相对 gold 的预算 regret。只有当 LLM 编译能提升规则基线，或以可接受误差显著降低人工编译工作量时，才能说 LLM 在 Project05 中有实际效用。

## 7. 判定规则

- 若 LLM 只生成更流畅文本，但 schema、来源指针或端到端 M2 结果没有改善，则判定 LLM 无实质贡献，从论文标题和主贡献中移除。
- 若领域模型只改善抽取 F1，却增加 unsupported claim 或 ceiling violation，则不得宣称安全性提升。
- 若 Qwen1.5 与 SEvenLLM 持平，保留更易复现的 Qwen1.5。
- 若两者均弱于规则编译器，则保留 LLM 为失败对照或后续工作，不进入专利独立权利要求。

## 8. 复现记录要求

- 完整 Hugging Face model id 与 revision。
- 权重文件 SHA-256。
- 量化方法、bits、计算 dtype。
- `transformers`、`torch`、量化后端版本。
- prompt 版本、JSON schema 版本、temperature、seed、max tokens。
- 每次输出原文、校验错误和拒收原因。

## 9. 参考入口

- SEvenLLM 论文与项目：<https://arxiv.org/abs/2405.03446>；<https://github.com/CSJianYang/SEevenLLM>
- SEvenLLM 官方模型集合：<https://huggingface.co/collections/Multilingual-Multimodal-NLP/sevenllm>
- Qwen1.5 官方说明：<https://qwenlm.github.io/blog/qwen1.5/>
