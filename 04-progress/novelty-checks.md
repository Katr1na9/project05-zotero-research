# Novelty Checks

## 2026-07-01：EXTRACTOR + AttacKG 统一中间表示是否已被做过？

### 初步结论

“把 CTI 文本攻击行为图与 ATT&CK 技术层统一起来”这个宽泛 idea 已经高度接近已有工作，尤其是：

- AttacKG+
- MM-AttacKG
- TechniqueRAG / H-TechniqueRAG
- ThreatPilot / IntelEX
- Text2TTP / NCE / LADDER
- UniTTP
- AttackSeqBench

因此，不能把“统一攻击行为中间表示”本身作为创新点。

### 关键撞车点

#### AttacKG+

AttacKG+ 已经提出用 LLM 构建 attack knowledge graph，并将一次 cyber attack 表示为 temporally unfolding event。其每个 temporal step 包含：

1. behavior graph；
2. MITRE TTP labels；
3. state summary。

这已经非常接近我们之前讨论的“系统行为层 -> ATT&CK 技术层 -> 摘要/解释层”的中间表示。

#### MM-AttacKG

MM-AttacKG 进一步把 threat images 等多模态信息纳入 attack graph construction。

#### TechniqueRAG / H-TechniqueRAG

TechniqueRAG 已经把 RAG 用于 CTI 文本中的 adversarial technique annotation。H-TechniqueRAG 进一步做层次化 RAG，提高效率和泛化能力。

#### ThreatPilot / IntelEX

ThreatPilot/IntelEX 属于 LLM-driven attack-level threat intelligence extraction，已覆盖 LLM + MITRE ATT&CK + attack-level extraction。

#### AttackSeqBench

AttackSeqBench 已经把问题推进到“LLM 是否理解 CTI 报告中的攻击行为序列”。

### 仍可能存在的缺口

初步看，可能还没有被完全做透的不是“统一表示”，而是以下更细的问题：

1. evidence-grounded intent recognition：从 behavior graph / TTP sequence 推断攻击意图，并给出证据片段。
2. uncertainty-aware attribution：在证据不足时输出低置信度或拒答，而不是硬归因。
3. CTI text graph 与 audit-log provenance graph 的可验证对齐：把报告侧攻击图与系统日志侧溯源图匹配起来。
4. conflict-aware CTI reasoning：多份 CTI 报告或 ATT&CK procedure examples 之间存在冲突时如何处理。
5. evaluation benchmark：针对 intent recognition / evidence chain / attribution confidence 的公开评测仍可能不足。

### 对当前 idea 的处理

- `Attack Behavior Intermediate Representation`：降级为背景概念，不作为创新点。
- `Technique Knowledge Graph + Intent Layer`：需要重新查重，重点看是否已有 intent/tactic-level reasoning 论文。
- `CTI 文本攻击图与日志溯源图的双视角证据融合`：暂时保留。Kairos 已读，说明日志侧 attack summary graph 可作为证据底座；仍需读完 DEPCOMM、AttacKG+ 后判断新颖性和实现难度。

### 下一步必须读

1. AttacKG+
2. TechniqueRAG
3. ThreatPilot / IntelEX
4. AttackSeqBench
5. DEPCOMM
6. Kairos 复盘：重点回看 attack summary graph 如何作为 ATT&CK/intent 的输入
