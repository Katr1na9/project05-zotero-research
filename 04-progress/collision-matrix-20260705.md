# Project05 撞题矩阵 - 2026-07-05

## 目的

本矩阵用于判断 Project05 的最终选题还能落在哪里。矩阵不是文献综述，而是“避坑地图”：哪些能力已经有人做，哪些能力还可能留下空间。

标记说明：

- `强`：该工作明确覆盖或核心贡献就是该方向。
- `中`：该工作部分涉及，但不是主贡献或机制不完整。
- `弱`：只在动机、讨论、案例或未来工作中出现。
- `无`：未见明显覆盖。
- `?`：全文或细节尚未拿到，需继续确认。

## 撞题矩阵

| 工作 | 多源证据 | KG/RAG | 证据路径 | LLM推理 | 解释 | 置信度 | 校准 | 不完整/噪声 | 拒答 | 开放集 | 假旗/模仿 | 分层降级 | 日志/溯源 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TAA-EPLMR | 中 | 强 | 强 | 强 | 强 | 强 | 无 | 强 | 无 | 弱 | 弱 | 无 | 无 |
| LLMAPT | 强 | 中 | 中 | 强 | 强 | 强 | 强 | 中 | 弱 | 弱 | 中 | 弱 | 中 |
| AURA | 强 | 强 | 中 | 强 | 强 | 弱 | 无 | 弱 | 无 | 无 | 无 | 无 | 无 |
| US12368730B2 | 强 | 中 | 中 | 无 | 中 | 强 | 弱 | 弱 | 无 | 无 | 弱 | 无 | 无 |
| US20210281585A1 | 中 | 无 | 弱 | 无 | 中 | 强 | 无 | 中 | 无 | 无 | 无 | 无 | 无 |
| CN120110776B | 强 | 强 | 中 | 中 | 中 | 无 | 无 | 弱 | 无 | 无 | 无 | 无 | 中 |
| CN118646607A | 中 | 强 | 弱 | 中 | 中 | 无 | 无 | 无 | 无 | 无 | 无 | 无 | 无 |
| APT-MMF | 强 | 强 | 中 | 无 | 弱 | 无 | 无 | 中 | 无 | 无 | 无 | 无 | 无 |
| APT-ATT | 强? | 中? | ? | 无? | ? | ? | ? | ? | ? | ? | ? | ? | 无? |
| High-Precision APT Malware Attribution | 弱 | 无 | 无 | 无 | 弱 | 中 | 无 | 中 | 强 | 强 | 无 | 无 | 无 |
| OpenSec | 中 | 无 | 无 | 强 | 中 | 中 | 强 | 强 | 强 | 无 | 中 | 无 | 无 |
| Kitten or Panda? | 中 | 中 | 无 | 无 | 无 | 无 | 无 | 强 | 无 | 无 | 中 | 无 | 无 |
| Synthetic APTs | 弱 | 无 | 无 | 中 | 弱 | 无 | 无 | 中 | 无 | 无 | 强 | 无 | 无 |
| ARCANE | 中 | 无 | 无 | 无 | 弱 | 强 | 中 | 中 | 中 | 弱 | 中 | 无 | 无 |
| Cascade Log Campaign Attribution | 弱 | 中 | 中 | 无 | 弱 | 无 | 无 | 中 | 无 | 无 | 无 | 中 | 强 |
| SAGA | 无 | 无 | 无 | 无 | 无 | 无 | 无 | 中 | 无 | 无 | 无 | 无 | 强 |
| Unveiling Cyber Threat Actors | 弱 | 无 | 无 | 无 | 弱 | 中 | 无 | 中 | 无 | 弱 | 中 | 无 | 无 |
| DRL APT Attribution | 弱 | 无 | 无 | 无 | 弱 | 中 | 无 | 中 | 无 | 无 | 无 | 无 | 无 |

## 已经不安全的题目空间

以下方向已经不适合作为 Project05 主创新：

1. 多源证据融合威胁行为体归因。
2. LLM-based APT attribution framework。
3. CTI-KG / GraphRAG / evidence path 增强的 LLM 归因。
4. APT KG + LLM 增强问答。
5. LLM/RAG/KG/TTP/attack tree 攻击组织归因。
6. 置信度评分 + information gap + hunting recommendation。
7. TTP / IOC graph / malware / command sequence 的单一归因模型。

## 仍可能保留的空隙

矩阵显示，真正还没有被强覆盖的组合是：

```text
证据可用性画像
  + 证据充分性/区分度/冲突/可模仿性评分
  + 归因粒度门控
  + open-set / unknown actor / false flag / mimicry 下拒答
  + 缺失证据解释与补充取证建议
  + CTI 与本地 provenance/log evidence 对齐
```

单独拆开看，这些点都有人提过一部分；但作为一个完整机制，目前还没有看到完全覆盖。

## Project05 应该怎么收窄

不建议题名：

> 一种基于多源证据融合与大语言模型的 APT 归因解释方法

也不建议题名：

> 一种基于证据路径增强大语言模型推理的威胁行为体归因方法

更安全的题名方向：

> 一种面向证据不完整与开放集场景的 APT 归因证据充分性门控与可拒答解释方法

或更专利化：

> 一种基于证据可用性画像和归因粒度门控的 APT 行为体可拒答归因解释方法

## 关键差异化模块

Project05 如果继续推进，应包含以下模块：

1. Evidence Availability Profiler  
   输出当前案件可用/缺失的证据类型、粒度、可靠性、时间有效性。

2. Evidence Distinctiveness Scorer  
   判断某证据是否为 actor-specific、是否被多个 actor 共享、是否可被模仿。

3. Conflict and Mimicry Detector  
   检测 TTP 重叠、共享基础设施、恶意软件复用、false flag 或 synthetic APT mimicry。

4. Attribution Granularity Gate  
   判断当前证据最多能支持哪一层结论：actor、campaign、intent、technique。

5. Refusal / Abstention Controller  
   在证据不足、open-set、候选 actor 不可区分、冲突明显时拒绝高置信 actor 归因。

6. Missing Evidence Explainer  
   输出缺失证据和补充取证建议。

## APT-ATT 的影响

APT-ATT 仍是未决项。它可能进一步压缩：

- heterogeneous threat intelligence representation；
- CTGAN 数据增强；
- APT attribution closed-set classification；
- 缺失/不平衡情报下的分类鲁棒性。

但即便 APT-ATT 很强，它大概率仍不会完全覆盖：

- 可拒答；
- open-set unknown actor；
- false flag / mimicry；
- 归因粒度门控；
- LLM 解释缺失证据。

因此，APT-ATT 需要继续找全文，但不应阻塞 Project05 向“证据充分性门控与可拒答解释”收窄。

