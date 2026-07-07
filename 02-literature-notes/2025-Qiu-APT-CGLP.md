# APT-CGLP: Advanced Persistent Threat Hunting via Contrastive Graph-Language Pre-Training

## 1. 基本信息

- 英文题名：APT-CGLP: Advanced Persistent Threat Hunting via Contrastive Graph-Language Pre-Training
- 中文译名：APT-CGLP：基于对比图-语言预训练的高级持续性威胁狩猎
- 作者：Xuebo Qiu, Mingqi Lv, Yimei Zhang, Tieming Chen, Tiantian Zhu, Qijie Song, Shouling Ji
- 年份：2025；2026 KDD accepted
- Venue：SIGKDD 2026 Research Track accepted；arXiv
- DOI / arXiv / URL：https://arxiv.org/abs/2511.20290
- Zotero key：待补
- 阅读日期：2026-07-07
- 阅读优先级：必读
- 所属主题：Graph-language pre-training / Provenance graph / CTI report / LLM synthetic data
- 阅读状态：全文精读；由原“摘要级红线占位”升级

## 2. 一句话总结

APT-CGLP 是 Project05 必须重点避开的最新红线：它直接做 provenance graph 与 CTI report 的端到端语义匹配，用 LLM 合成图-文本训练对并净化 CTI，再用对比学习和跨模态 masked modeling 学习粗细粒度攻击语义对齐。

## 3. 研究问题

- Provenance-based threat hunting 需要把 CTI 中攻击模式与系统 audit logs 派生的 provenance graphs 对应起来。
- 传统流程先从 CTI 抽 attack graph，再与 provenance graph 匹配，存在信息损失和人工标注成本。
- Provenance graph 是低层异构结构，CTI report 是高层自然语言叙事，两者存在结构和语义模态鸿沟。

## 4. 核心贡献

1. 提出 end-to-end graph-language pre-training，直接匹配 provenance graph 与 CTI report。
2. 用 LLM Graph2CTI 从 benign audit logs 采样子图并合成高保真 graph-CTI report 训练对。
3. 用 LLM CoT denoising 从 noisy web-sourced CTI 中抽取可操作攻击叙事。
4. 多目标训练：graph-text contrastive、graph-text matching、masked graph modeling、masked language modeling。
5. 两阶段威胁狩猎：粗粒度向量检索缩小候选，再细粒度 multimodal encoder 匹配。

## 5. 方法框架

### 输入

- Provenance graphs from audit logs。
- CTI reports，包括 DARPA 报告和 web-sourced vendor reports。
- LLM 生成的 synthetic graph-CTI pairs。

### 输出

- 与给定 provenance graph 最匹配的 CTI report。
- APT hunting / alert validation 结果。
- 匹配概率和候选排序。

### 关键模块

| 模块 | 作用 | 对 Project05 的意义 |
|---|---|---|
| Graph2CTI | LLM 将 provenance subgraph 转成 CTI-like report | LLM 合成安全情报训练数据已被覆盖 |
| CTI denoising | CoT 提取实体、交互、攻击叙事 | LLM 做 CTI 净化/结构化已被覆盖 |
| Graph encoder + text encoder | 分别编码 provenance graph 和 CTI report | 对齐基座 |
| Multimodal encoder | token-node cross-attention 学细粒度语义 | 跨模态对齐红线 |
| Two-stage retrieval | 先粗检索再精匹配 | 可作为上游 evidence alignment |

### 方法流程

```text
benign audit logs
  -> provenance graphs
  -> sampled activity subgraphs
  -> LLM Graph2CTI synthetic reports
provenance graphs + CTI reports
  -> graph/text encoders
  -> graph-language pre-training
  -> two-stage retrieval and matching
  -> APT hunting / alert validation
```

## 6. 数据集与实验

- 数据：DARPA TC E3 的 Cadets、Trace、Theia；OpTC。
- OpTC 规模：超过 17B events，1000 Windows hosts。
- 训练：仅使用第一周 benign audit logs，Graph2CTI 生成 45,225 provenance graph-CTI report pairs，避免 attack data leakage。
- 测试：malicious/benign provenance graphs + 5,172 web-sourced CTI reports。
- 指标：threat hunting 准确性、效率、消融、alert validation gains。
- 结论：报告在多个真实 APT 数据集上优于 SOTA threat hunting baselines，并且 fine-grained alignment 比仅做 CLIP 式 global contrastive learning 更有效。

## 7. 关键知识点

### 概念

- Graph-language pre-training：把 provenance graph 与 CTI report 放入跨模态预训练框架。
- Graph2CTI：LLM 根据图三元组生成 CTI 报告。
- CTI denoising：LLM 用分步推理抽取实体、交互和时间有序攻击叙事。
- Fine-grained semantic alignment：不仅全局图文接近，还要 token-node 级别对齐。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| graph-language pre-training | 图-语言预训练 | APT-CGLP 核心 |
| provenance graph-CTI report pair | 溯源图-CTI 报告配对 | LLM 合成 |
| CTI denoising | CTI 去噪 / 净化 | LLM CoT 模块 |
| alert validation | 告警验证 | 不是归因粒度控制 |

## 8. 优点

- 直接绕过 query graph 抽取导致的信息损失。
- 把 LLM 用在数据合成和 CTI 净化，而不是简单问答。
- 实验设置较强，使用 DARPA E3 和 OpTC，并强调只用 benign logs 训练以防泄漏。
- 对“跨模态对齐”做了粗细粒度训练，比单纯 embedding 检索更强。

## 9. 局限

- 仍是 APT hunting / alert validation，不是 APT actor attribution。
- 数据评估依赖 paired audit data and attack reports，作者也承认可用 benchmark 范围有限。
- 没有证据不完整条件下的 attribution granularity gate。
- 没有主动取证规划：匹配失败或置信不足时，不输出下一步最优证据动作。
- LLM hallucination 仅作为风险讨论，未成为核心受控机制。

## 10. 对我选题的启发

- 极强红线：不能把“provenance graph 与 CTI report 的端到端跨模态语义对齐”作为主创新。
- 极强红线：不能把“LLM 生成/净化 CTI，辅助 graph-language matching”作为独立核心。
- 可复用：APT-CGLP 可以作为 Project05 的最强上游对齐器或 SOTA baseline。
- Project05 的空间必须在它之后：把 APT-CGLP 的匹配结果转成 evidence state，并在不完整证据下规划补证动作。

## 11. 可转化的研究问题

1. APT-CGLP 输出 top-k CTI report 和 matching probability 后，如何判断当前能支持 technique/campaign/actor 哪一层？
2. 当 top-k CTI 候选冲突时，应优先获取哪类证据来消歧？
3. Graph2CTI 合成数据能否用于 Project05 的 evidence ablation 实验生成？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| POIROT | APT-CGLP 明确批评 query graph 抽取的信息损失 |
| DeepHunter / MEGR-APT | 作为 graph learning-based matching baselines |
| CLIProv | 同属跨模态语义对齐；CLIProv 是 log-to-intelligence，APT-CGLP 是 graph-language |
| Project05 | 作为上游 SOTA，对齐算法本身让位于证据状态与主动取证 |

## 13. 论文写作可引用句式

- End-to-end graph-language pre-training has substantially advanced provenance-to-CTI matching for APT hunting; nevertheless, these systems still optimize matching and alert validation rather than attribution-granularity control under incomplete evidence.

## 14. 我的批注与疑问

- 这篇是“语义统一/跨模态对齐”最后的封门文献。Project05 再沿这个方向写会很危险。
- 但它也给了我们强理由：既然对齐越来越强，新的问题自然变成“对齐之后如何用，尤其在证据不完整时如何决定补证”。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是

