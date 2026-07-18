# Zotero 文献库中证据语义层 LLM 来源统计 v0.1

日期：2026-07-18  
状态：`library_snapshot_audited / model-origin statistics ready for review`  
统计对象：Zotero 合集“攻击溯源与意图感知”（collection key `G5WLQGGJ`）  
数据访问：只读打开 `C:/Users/35393/Zotero/zotero.sqlite`，未修改 Zotero

## 1. 结论先行

不是所有论文都直接调用 GPT、Claude 这类闭源付费 API；但在本合集已核实的证据语义层主方法中，**所有论文的主路径至少依赖一个商业公司发布的模型或服务**。

这里必须把“商用模型”拆成两类：

1. **闭源商业 API**：GPT、Claude、Gemini、Qwen-Plus/QwQ-Plus 等，无法下载完整权重，通常按调用计费；
2. **商业公司开放权重**：Meta Llama、Alibaba Qwen、Mistral/Ministral、DeepSeek、Kimi 等，可以本地部署或再训练，但发布方仍是商业公司，而且“开放权重”不自动等于 OSI 意义的开源软件。

按 14 篇模型与使用方式均已从全文或精读笔记核实的核心论文统计：

| 主路径模型来源 | 论文数 | 比例 |
|---|---:|---:|
| 仅闭源商业 API | 4 | 28.6% |
| 仅商业公司开放权重 | 7 | 50.0% |
| 闭源 API + 商业开放权重混用 | 3 | 21.4% |
| 仅非营利/社区开放底座 | 0 | 0.0% |

换一种交叉口径：

- 7/14（50.0%）在正式推理主路径直接使用闭源商业 API；
- 10/14（71.4%）在正式主路径使用至少一种商业公司开放权重；
- 14/14（100%）至少使用一种商业机构来源的模型；
- 0/14 使用 AI2 OLMo 一类“非营利研究机构发布的开放底座”作为正式主模型。

因此，学界的真实做法不是“大家都用闭源商用模型”，而是：**大部分论文仍围绕商业机构的大模型生态展开，其中一半可完全用开放权重完成主推理，另一半直接或混合依赖闭源 API。**

## 2. 统计口径

### 2.1 文献漏斗

- Zotero 合集共有 109 条顶层记录，包含重复版本、专利、综述、benchmark 和非 LLM 方法；
- 题名/摘要关键词筛选、题名规范化和人工补充后，形成 46 条 LLM 相关工作候选；
- 其中 14 篇是模型身份、访问方式与适配方法均可核实的“核心证据语义层”方法；
- 另有 5 篇是已核实的相邻方法，包括通用网络安全指令模型或事件响应/规划系统；
- 7 篇只有题名/摘要或全文未固定实际 checkpoint，单列为 unresolved，不进入百分比分母；
- 综述、benchmark、可靠性测评、通用 agent safety、专利和重复记录不进入方法论文分母。

核心纳入标准是：LLM 直接读取 CTI、日志、provenance、PCAP、IOC/证据路径或调查上下文，并承担至少一种语义转换、对齐、结构化、图构建、检索验证或调查判断任务。

### 2.2 为什么不按 Zotero 条目数直接算

ExCyTIn-Bench、Kairos、THREATRACE 等在合集中存在重复题录。若按条目数计数，会把同一篇论文重复计权。本文按规范化题名/DOI 对论文去重，并且不把综述中列出的模型当成该综述自己的方法模型。

### 2.3 “微调”的定义

只有作者实际更新 LLM 权重才记为微调或继续训练。以下情形不计为微调：

- system prompt、CoT、few-shot、self-reflection；
- RAG、GraphRAG、向量检索；
- 多智能体角色编排；
- 给冻结 LLM 增加规则验证器；
- 只训练 BERT、图编码器、异常检测器或下游分类器，而 LLM 本身保持冻结。

## 3. 核心 14 篇逐篇结果

| 论文 | LLM 从哪里来 | 使用方式 | 是否更新 LLM 权重 |
|---|---|---|---|
| APT-CGLP | Meta Llama-3-8B 开放权重 | 本地 ICL，生成 Graph2CTI 数据并做 CTI 去噪 | 否 |
| AURA | OpenAI GPT-4o/mini、Anthropic Claude 3.5 | API + RAG + 多智能体归因 | 否 |
| CyberSleuth | GPT-4o/o3/GPT-5 + DeepSeek-R1/Kimi-K2/Llama-4 | OpenAI/Together.ai API，工具智能体分析 PCAP | 否 |
| CyLens | Meta Llama-3.2-1B、3.1-8B、3.3-70B | CTI curriculum continued training + instruction tuning | **是** |
| LLM-Assisted Proactive TI | GPT-4o | API + 实时 RAG | 否 |
| LOCALINTEL | GPT-3.5/GPT-4o + Llama/Mistral/Qwen 等 | API 与 Hugging Face 权重并列比较，global-local RAG | 否 |
| MM-AttacKG | Qwen-VL-72B、Qwen2.5-VL-32B/7B | 多阶段 prompting，图像增强攻击图 | 否 |
| Multi-Step LLM TTP Pipeline | ChatGPT-4o + OpenAI embedding | extractor + retrieval + validator | 否 |
| Policy-Guided Threat Hunting | ChatGPT 公共 API，未固定 checkpoint | CrewAI/Splunk triage | 否 |
| SEvenLLM | Llama-2-7B/13B、Qwen1.5-7B/14B | 多任务 instruction tuning | **是** |
| SherAgent | DeepSeek-V3.1 | 生产 SOC 中的查询—过滤—回溯 agent | 否 |
| SHIELD | Qwen2.5-32B | 本地 8-bit，provenance 图摘要/解释 | 否 |
| TAA-EPLMR | Qwen3-Plus/QwQ-Plus + DeepSeek-V3/R1 | 托管模型做 evidence-path RAG + CoT 归因 | 否 |
| TECHNIQUERAG | DeepSeek-V3 + Ministral-8B-Instruct | 冻结 reranker + LoRA generator | **仅 generator LoRA** |

完整字段、Zotero key 和本地证据位置见 [paper-model-evidence.csv](paper-model-evidence.csv)。

## 4. 大家到底有没有微调

### 4.1 核心方法

| LLM 适配方式 | 论文数 | 比例 |
|---|---:|---:|
| 真正更新 LLM 权重 | 3 | 21.4% |
| 仅 prompting / ICL / RAG / agent / verifier | 11 | 78.6% |

真正微调的三篇是：

- **CyLens**：在 Llama 1B/8B/70B 上做 CTI curriculum continued training 和 instruction tuning；
- **SEvenLLM**：在 Llama-2 和 Qwen1.5 上做多任务 instruction tuning；
- **TECHNIQUERAG**：冻结 DeepSeek-V3 reranker，仅对 Ministral-8B generator 做 LoRA。

其余论文即使把模型称为“核心推理模块”，大多数也只是提示工程、RAG、工具调用或多智能体编排，并没有训练新的安全 LLM。

### 4.2 加入相邻的 5 篇已核实工作

若把 CyberPal.AI、IRCopilot、AutoBnB-RAG、SOCpilot 和《Integrating LLMs into Security Incident Response》也纳入，已核实集合变为 19 篇：

| 指标 | 论文数 | 比例 |
|---|---:|---:|
| 仅闭源商业 API | 7 | 36.8% |
| 仅商业公司开放权重 | 8 | 42.1% |
| 混合两者 | 4 | 21.1% |
| 直接使用闭源 API（仅闭源 + 混合） | 11 | 57.9% |
| 使用商业公司开放权重（仅开放 + 混合） | 12 | 63.2% |
| 真正微调 LLM | 4 | 21.1% |
| 仅非营利/社区开放底座 | 0 | 0.0% |

新增的微调论文只有 CyberPal.AI：它对 Llama-3、Mistral-7B 和 Phi-3 做指令微调。

## 5. 模型依赖还有一层容易被忽略

“最终模型是开放权重”不等于训练链与商业模型无关。

核心 14 篇中，至少 3 篇用 LLM 合成正式训练数据：

- APT-CGLP：本地 Llama-3-8B 生成 provenance graph–CTI 配对；
- SEvenLLM：GPT-4 生成候选任务和指令数据，专家再修正；
- CyLens：GPT-4o、GPT-o1、Gemini-Pro、Pixtral-Large、DeepSeek-R1、Llama-3.1-405B 等组成多模型生成/修订池。

其中 SEvenLLM 和 CyLens 的训练数据链明确包含闭源商业模型。CyberPal.AI 虽未用闭源 GPT 作为默认 teacher，但使用商业公司开放权重 Mixtral 生成/扩增指令。

这意味着论文中常见三种商业依赖位置：

1. **正式推理依赖**：研究系统运行时调用 GPT/Claude/Gemini；
2. **训练数据依赖**：最终部署开放模型，但 instruction/CTI 数据由 GPT 等生成；
3. **评测依赖**：主模型开放，但用闭源模型作 judge、纠错或诊断。

只看最终 checkpoint 会漏掉后两种依赖。

## 6. 对 Project05 选型的直接含义

### 6.1 采用非营利开放模型不是学界硬性要求

当前集合没有显示“证据语义层必须使用闭源 API”或“必须使用商业公司开放权重”。更准确的事实是：前作普遍优先选择能力成熟、生态完善的模型；模型来源本身通常不是论文创新点。

因此，Project05 可以使用 AI2 OLMo 2 作为正式底座，理由是：

- 权重来源和本地运行链更易审计；
- 能明确区分于前作常见的 GPT/Llama/Qwen 路线；
- 适合把贡献写成“受约束证据编译接口 + 主线调查控制”，而不是借助某个闭源模型的不可复现实力。

但不能把“使用 OLMo”本身写成创新。创新仍须来自：来源指针、机械准入、跨源实体/节点绑定、语义上限，以及编译结果对 M3 成本约束调查控制的实质传导。

### 6.2 如果只要求“不调用闭源付费 API”

已有充分前例支持本地开放权重路线：APT-CGLP、SHIELD、SEvenLLM、CyLens、MM-AttacKG 和 TECHNIQUERAG 都证明了 Llama/Qwen/Mistral 类权重可以承担这一层任务。Project05 不需要为了“跟论文一样”而调用 GPT-4o。

### 6.3 如果要求“模型发布方也不能是商业公司”

那么 Llama、Qwen、Mistral、DeepSeek、Kimi 都不满足这一更严格口径；它们虽可开放权重部署，发布方仍是商业机构。此时 OLMo/AI2 一类非营利研究机构底座才符合要求，而这会使 Project05 在本 Zotero 样本中成为少见路线。

### 6.4 最稳妥的实验叙事

建议保持以下比较，不把模型品牌当贡献：

```text
Rule-Strong
  vs 非营利开放底座 General
  vs 同底座 task/schema-adapted adapter
  vs 可复用组件 Hybrid
  -> 统一 G0 机械准入
  -> EvidenceClaim / EntityBinding / ClaimNodeLink
  -> 冻结 M3 控制器
```

如果不调用闭源 API，论文应如实写“未与闭源前沿模型做同成本对比”，但这不妨碍验证 adapter 是否优于同底座 General、规则基线和复用组件。

## 7. 未进入百分比的 7 篇

以下记录因本地 Zotero 无全文、只有摘要，或论文没有固定实际 checkpoint，均未强行猜测：

- Cognitive SOC；
- iThelma；
- Construction of Cyber-Attack Attribution Framework Based on LLM；
- LLM-Based Advanced Persistent Threat Attribution（LLMAPT）；
- APT Attack Inference and Multidimensional Visual Representation；
- TIBlender；
- Multi-Agent Collaboration in Incident Response with Large Language Models。

LLMAPT 虽提到 TacticBERT、MalwareGPT、ThreatLlama，但没有把实际运行的底座、revision 和训练过程固定到可复核程度，因此不能把这些概念名当成已实现模型进行计数。

## 8. 与此前讨论的四篇前作对照（不进 Zotero 分母）

以下全文/笔记目前存在于项目目录，但不属于本次 Zotero 合集去重分母：

| 前作 | 实际 LLM 路线 |
|---|---|
| Llama-PcapLog | Llama-3-8B 4-bit LoRA；GPT-4o 扩增训练数据 |
| Auto-Prov | GPT-4o 做候选 provenance 抽取；Llama-3-70B 生成规则与解释；不微调 |
| AttacKG+ | GLM-4 等商业 API，多阶段 prompting；不微调 |
| CTINexus | GPT-3.5/GPT-4 与 Llama-3/Qwen2.5 对比，核心为 ICL；不微调 |

它们与 Zotero 核心统计结论一致：主流不是“人人自己从头训练一个非商业 LLM”，而是利用成熟底座，通过 prompting/RAG/agent 或小规模 adapter 完成任务；训练数据还经常由更强商业模型生成。

## 9. 限制

- 这是用户当前 Zotero 快照的库内统计，不是全领域系统综述；
- 7 篇模型身份未核实的候选已排除，避免用猜测改变比例；
- “商业公司开放权重”按发布机构和权重可得性分类，不代表各模型许可证完全相同；
- DeepSeek、Kimi、Llama 等在部分论文中通过托管 API 使用，因此“模型家族开放”与“该实验是否本地运行”是两个不同字段；
- 统计只回答模型从哪里来、怎样适配，不评价各论文结果是否可信或可复现。

## 10. 可复核工件

- [逐篇模型来源与证据表](paper-model-evidence.csv)
- Zotero 只读快照：`C:/Users/35393/Zotero/zotero.sqlite`
- 关键本地全文：`07-zotero-exports/pdf_text_20260704/`
- 精读笔记：`02-literature-notes/`

