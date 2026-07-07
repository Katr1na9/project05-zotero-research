# Project05 当前调研结论与主线方向简报

日期：2026-07-06

## 1. 当前研究背景

Project05 当前关注方向是：

> 大语言模型辅助的 APT 攻击归因、威胁溯源、证据解释与可信安全分析。

最初设想偏向：

> 多源安全证据融合 + 大语言模型辅助 APT 归因解释。

经过多轮文献精读、2026 年上半年补查、专利红线分析和撞题扫描后，目前判断该宽题已经风险很高，需要收缩。

## 2. 已调研内容

### 2.1 CTI 文本结构化与 ATT&CK/TTP 抽取

已阅读和整理的方向包括：

- CTI 报告实体/关系抽取；
- ATT&CK technique 标注；
- TTP 抽取；
- CTI 文本到攻击行为图；
- LLM/RAG 辅助 TTP extraction。

代表工作包括：

- AttacKG；
- AttacKG+；
- MM-AttacKG；
- EXTRACTOR；
- TTPXHunter；
- TechniqueRAG；
- Multi-Step LLM Pipeline for Enhancing TTP Extraction；
- CTIBench；
- SEvenLLM。

结论：

> CTI -> TTP / ATT&CK technique 这条线已经比较成熟，不适合作为 Project05 的主创新。

### 2.2 知识图谱、RAG、GraphRAG 与 LLM-CTI

已调研内容包括：

- CTI knowledge graph；
- GraphRAG / HybridRAG；
- heterogeneous CTI retrieval；
- LLM-based CTI reasoning；
- agentic CTI workflow。

代表工作包括：

- Open-CyKG；
- CTIConnect；
- Beyond RAG for Cyber Threat Intelligence；
- CTI-Thinker；
- LocalIntel；
- AURA；
- LLMAPT；
- TAA-EPLMR；
- Construction of Cyber-attack Attribution Framework Based on LLM。

结论：

> “KG/RAG/GraphRAG + LLM 做 APT 归因或安全问答”已经有大量推进，不能再作为宽泛创新点。

### 2.3 APT 归因与多源/多模态特征融合

已重点调研：

- CTI-based APT attribution；
- report-IOC heterogeneous graph attribution；
- multimodal/multilevel feature fusion；
- Dempster-Shafer / Bayesian / weighted evidence fusion；
- malware/sample/infrastructure/TTP-based attribution；
- campaign/group attribution。

代表工作包括：

- APT-MMF；
- MLDSJ；
- A Multi-Source Feature Fusion-Based Knowledge Graph Construction from Cyber Threat Intelligence to Facilitate APT Attribution in IDS；
- APT-scope；
- TRAIL；
- HG-CTA；
- GAPT；
- ADAPT it!；
- Opinion Pools；
- BAN；
- ARCANE；
- High-Precision APT Malware Attribution。

结论：

> “多源/多模态证据融合后输出 APT actor”这条路线已经非常拥挤。继续做一个新的融合模型、知识图谱归因模型或 GNN attribution model，新颖性风险很高。

### 2.4 日志溯源、provenance graph 与攻击调查

已阅读：

- whole-system provenance graph；
- attack summary graph；
- node-level anomaly tracing；
- graph summarization；
- provenance-based APT detection；
- LLM 对 provenance attack graph 的解释。

代表工作包括：

- KAIROS；
- DEPCOMM；
- THREATRACE；
- PROGRAPHER；
- UNICORN；
- SHIELD。

结论：

> 日志/provenance graph 检测、压缩、攻击摘要和 LLM 解释也已有系统工作。Project05 不宜转成单纯日志图检测或日志图解释。

### 2.5 专利与红线分析

已纳入分析的专利方向包括：

- multiple evidence threat actor attribution；
- confidence-level cyber campaign attribution；
- APT KG + LLM 协同增强；
- GAT threat intelligence attribution；
- IP / threat intelligence knowledge graph attribution prediction；
- TTP 描述相似度匹配归因；
- threat intelligence language-model analysis。

结论：

> 中国和美国专利中已经存在多源证据、KG、置信度、TTP 匹配、LLM 安全分析等相关保护范围。专利题名不能再写得过宽。

## 3. 已完成的 Project05 工作

当前已经完成：

1. 建立 Project05 Zotero 研究工作区。
2. 完成第一轮主线文献精读。
3. 完成 2026 年上半年补读和新颖性扫描。
4. 导入并整理 Zotero 条目。
5. 合并 Zotero collection 和重复条目。
6. 形成多份精读笔记和风险笔记。
7. 建立撞题矩阵：
   - `collision-matrix-20260705.md`
   - `collision-matrix-supplement-20260706.md`
   - `collision-matrix-final-20260706.md`
8. 形成待补全文清单：
   - `fulltext-todo-20260706.md`
9. 形成专利权利要求草案：
   - `patent-claims-draft-v0.1-20260706.md`
   - `patent-claims-draft-v0.2-20260706.md`
10. 将当前 Project05 工作同步到 GitHub 仓库：
    - `Katr1na9/project05-zotero-research`

## 4. 当前仍待补全文

目前剩余较难获取但仍需后续复核的高风险项：

1. **An efficient APT attribution model based on heterogeneous threat intelligence representation and CTGAN**
   - 简称：APT-ATT
   - 可能覆盖：异构威胁情报表示、CTGAN、APT attribution。

2. **APTChaser: Cyber Threat Attribution via Attack Technique Modeling**
   - 当前已有 Springer 元数据和摘要。
   - 可能覆盖：LLM 构建 attack technique schema/profile 并服务归因。

3. **GAPT: A Graph-based APT Attribution Framework Using Temporal Relation Embeddings**
   - 当前只在二级引用中看到。
   - 可能覆盖：temporal relation embedding + graph-based APT attribution。

这些不再阻塞主线推进，但正式定稿前需要复核。

## 5. 当前主线方向

经过收缩后，当前主线不再是：

> 多源证据融合与 LLM 辅助 APT 归因。

而是：

> 面向证据不完整、证据冲突、共享 TTP、攻击者模仿、伪旗和 unknown actor 场景，判断当前证据最多能支持哪一级 APT 归因结论，并在证据不足时拒绝或降级 actor-level 归因。

当前拟定题名之一：

> 一种面向多模态证据不完整场景的 APT 归因粒度判定与缺失证据需求生成方法。

但目前对该题名仍有疑虑：

> 如果最终只是输出“缺失 evidence list”，贡献可能偏弱，更像调查辅助层或风险控制层，而不是强方法。

因此当前更推荐把方向表述为：

> 基于证据语义编译与归因可判定性评估的 APT 归因粒度门控方法。

或者：

> 面向不完整多模态证据的 APT 归因可判定性评估与主动证据获取规划方法。

## 6. 拟定技术路线

当前技术路线可以概括为：

```text
多模态/异构安全输入
  -> LLM 证据语义编译
  -> 证据主张图
  -> 证据-结论蕴含推理
  -> 证据充分性与区分度评估
  -> 冲突/模仿/伪旗/未知行为体风险检测
  -> 归因粒度门控
  -> 缺失证据需求或主动证据获取规划
  -> LLM 受控解释
```

### 6.1 输入

输入可以包括：

- CTI 报告；
- IOC；
- ATT&CK/TTP；
- 恶意样本特征；
- 基础设施信息；
- 网络流量摘要；
- 系统日志或 provenance graph 摘要；
- 时间线信息；
- 人工分析记录。

### 6.2 LLM 证据语义编译

LLM 不直接输出 actor，而是把异构输入转换为统一的证据主张表示：

```json
{
  "evidence_id": "E12",
  "source_type": "CTI_report",
  "claim": "attacker used PowerShell to download payload",
  "mapped_technique": "T1059",
  "entities": ["PowerShell", "payload"],
  "supports_level": ["technique", "intent"],
  "not_enough_for": ["actor"],
  "source_ref": "report paragraph 8"
}
```

### 6.3 证据主张图

不是构建传统 APT attribution knowledge graph，而是构建 evidence claim graph：

```text
evidence claim
  -> supports technique / intent / campaign / actor
  -> contradicts another claim
  -> requires missing evidence
  -> insufficient_for actor-level attribution
```

图谱在这里的作用不是直接预测 actor，而是表示证据与结论之间的支撑、冲突、缺失和不可推出关系。

### 6.4 归因可判定性评估

系统判断：

- 当前证据能否支持 technique-level？
- 能否支持 intent-level？
- 能否支持 campaign-level？
- 能否支持 actor-level？
- 是否应输出 unknown actor？
- 是否必须 refusal？

判断依据包括：

- 证据类型组合；
- 证据数量；
- 证据来源可靠性；
- 证据时间有效性；
- actor-specific 区分度；
- 候选 actor margin；
- 共享 TTP / 共享基础设施；
- false flag / mimicry 风险；
- 缺失关键证据类型。

### 6.5 归因粒度门控

门控模块输出：

```json
{
  "max_supported_granularity": "campaign",
  "forbidden_outputs": ["actor"],
  "decision": "downgrade",
  "reason_codes": [
    "low_actor_specificity",
    "shared_TTP",
    "missing_infrastructure_link"
  ]
}
```

也就是说，它回答的不是“最像哪个 actor”，而是：

> 当前证据最多允许输出什么粒度的归因结论？

### 6.6 缺失证据需求 / 主动证据获取规划

如果证据不足，系统不只是生成普通 list，而是尝试回答：

- 若要从 technique 升级到 campaign，需要补什么证据？
- 若要从 campaign 升级到 actor，需要补什么证据？
- 哪类证据最可能提升归因粒度？
- 哪类证据最能降低混淆风险？

示例：

```json
{
  "current_level": "technique",
  "target_level": "actor",
  "next_best_evidence": [
    {
      "evidence_type": "C2 infrastructure history",
      "expected_gain": "technique -> campaign",
      "reason": "当前 IOC 与多个 actor 共享，基础设施历史可减少候选重叠"
    },
    {
      "evidence_type": "malware sample similarity",
      "expected_gain": "campaign -> actor",
      "reason": "样本实现细节比通用 TTP 更具 actor-specific 区分度"
    }
  ]
}
```

### 6.7 LLM 受控解释

最后 LLM 只负责受控解释：

- 解释当前为什么不能输出 actor；
- 解释当前最高支持粒度；
- 解释缺失证据为什么重要；
- 不允许编造证据；
- 每条解释必须回指 evidence claim。

## 7. 期望达到的效果

目标不是单纯提高 actor accuracy，而是：

1. 降低证据不完整场景下的过度归因风险。
2. 让系统在证据不足时不强行输出 actor-level attribution。
3. 明确当前证据最多支持哪一级归因。
4. 让归因解释可回溯到证据主张。
5. 给出下一步调查所需的关键证据类型。
6. 在多模态证据缺失、不均衡或冲突时，指导分析师优先补充高价值证据。

可评价指标包括：

- over-attribution rate；
- correct abstention rate；
- granularity selection accuracy；
- open-set rejection rate；
- false-flag robustness；
- evidence grounding correctness；
- missing / next-best evidence usefulness；
- calibration：ECE、Brier score；
- selective accuracy / coverage。

## 8. 当前核心疑虑

目前最主要的问题是：

> 如果系统最终只是生成“缺失证据清单”，贡献会偏弱。

需要进一步讨论的问题包括：

1. 该方向是否足以支撑一篇专利和论文？
2. 是否应把“缺失证据清单”升级为“主动证据获取规划”？
3. 是否需要引入可学习的 next-best-evidence ranking model？
4. LLM 的核心贡献应聚焦在 evidence semantic compilation，还是 evidence-conclusion entailment？
5. 多模态是否作为主线，还是只作为证据不完整场景的限定？
6. 是否应该转向更强的技术主线，例如：
   - 多模态 CTI 证据语义编译；
   - 归因可判定性建模；
   - 交互式 APT 调查 agent；
   - 主动证据获取策略学习。

## 9. 当前建议

短期建议：

1. 先不要继续扩写完整专利说明书。
2. 用本简报和导师/同行讨论方向强度。
3. 若认可“归因可判定性 + 主动证据获取规划”，再写实验方案 v0.1。
4. 若认为该方向偏弱，则应尽快转向更实质的技术主线。

当前最稳但仍需确认的方向是：

> LLM-based evidence semantic compilation + attribution sufficiency assessment + granularity-gated attribution + next-best-evidence planning。

