# Project05 Research Dashboard

## 当前定位

Project05 当前主线已经从“证据不完整场景下的 APT 归因粒度门控 / 拒答解释”进一步收束为：

> 面向 APT 归因的对齐感知证据状态建模与主动取证规划。

更具体地说，项目不再把“CTI-日志 / CTI-provenance 对齐算法”本身作为主创新，因为这一块已经被 POIROT、DeepHunter、MEGR-APT、ActMiner、CLIProv、APT-CGLP、ProHunter 等工作覆盖。Project05 的更安全位置是把这些对齐结果作为“证据状态”，进一步判断当前证据能支撑的归因粒度，并规划下一步最值得获取的证据。

## 当前主 RQ

> 在证据不完整的 APT 归因场景中，如何以“CTI 侧攻击行为图与本地观测证据的对齐状态”为证据画像，估计各候选取证动作对归因粒度可提升性的期望增益，并在成本约束下规划取证动作序列，使系统通过“对齐-评估-补证-再对齐”闭环，以最小取证成本达到证据可支撑的最高归因粒度？

G1 通过版详见：[topic-rq-brief-v2.1-g1-final-20260706.md](../03-ideas/topic-rq-brief-v2.1-g1-final-20260706.md)

## 当前技术路线

```mermaid
flowchart LR
  A["公开 CTI 报告 / ATT&CK / 历史情报"] --> B["CTI 侧攻击行为图"]
  C["本地日志 / provenance / IOC / 样本 / 基础设施证据"] --> D["本地观测证据图"]
  B --> E["对齐与缺口建模"]
  D --> E
  E --> F["对齐感知证据状态"]
  F --> G["归因粒度可支撑性评估"]
  G --> H{"是否达到目标粒度或预算终止?"}
  H -- 是 --> I["粒度受控归因结论 + LLM 证据化解释"]
  H -- 否 --> J["候选取证动作价值估计"]
  J --> K["主动取证规划"]
  K --> C
```

## 创新点边界

保留空间：

- 对齐状态不是终点，而是主动取证规划的状态输入。
- 输出不是单一 actor label，而是“当前可支撑的最高归因粒度 + 下一步证据获取策略”。
- 方法目标不是让 LLM 直接归因，而是让 LLM 参与证据语义规范化、缺口解释、动作说明和最终可审计表达。
- AFA / POMDP 提供形式化基础：部分观测证据、取证动作、成本、停止动作、目标粒度收益。

红线：

- 不能把“多源证据融合 + LLM APT 归因解释”作为宽泛创新点。
- 不能把“CTI 图与 provenance/local evidence 对齐”作为单独主创新。
- 不能只产出“缺失证据 list”，否则贡献偏弱。
- 不能写成泛化的“置信度不足 -> 让 LLM 拉更多数据 -> 循环调查”，这会撞 US12530469 的大范围思路。

## 新增关键材料

| 类别 | 文件 | 作用 |
|---|---|---|
| 理论基座 | [2025-Aronsson-AFA-Survey.md](../02-literature-notes/2025-Aronsson-AFA-Survey.md) | Active Feature Acquisition / POMDP 形式化基础 |
| 撞题红线 | [2025-Li-CLIProv.md](../02-literature-notes/2025-Li-CLIProv.md) | 日志到情报语义对齐 / provenance 分析红线 |
| 撞题红线 | [2025-Qiu-APT-CGLP.md](../02-literature-notes/2025-Qiu-APT-CGLP.md) | provenance graph 与 CTI report 图语言预训练红线 |
| 专利红线 | [2026-Varonis-US12530469-LLM-Alert-Investigation.md](../02-literature-notes/2026-Varonis-US12530469-LLM-Alert-Investigation.md) | LLM 多阶段告警调查循环的专利风险 |
| 主线修正 | [deep-collision-scan-alignment-20260706.md](../04-progress/deep-collision-scan-alignment-20260706.md) | 说明为什么单独做对齐已经不安全 |
| RQ v2.1 | [topic-rq-brief-v2.1-g1-final-20260706.md](../03-ideas/topic-rq-brief-v2.1-g1-final-20260706.md) | G1 通过版研究问题定义 |

## 当前 Gate 状态

| Gate | 状态 | 说明 |
|---|---|---|
| G1 RQ 清晰性 | 基本通过 | RQ v2 已形成，主线更强 |
| G2 撞题扫描 | 进行中 | CLIProv/APT-CGLP/APT-ATT 已升级全文精读，TAA-EPLMR 已完成新主线复核；仍需补中文专利侧、APTChaser/GAPT 正文 |
| G3 创新强度 | 暂时好转 | 从“保护层/list 生成”转为“主动取证规划” |
| G4 专利权利要求 | 未通过 | v0.2 已是历史草稿，需等新主线后重写 v0.3 |
| G5 实验可执行性 | 草案完成 | `experiment-plan-v0.1-20260707.md` 已形成，下一步验证案例清单和数据 schema |

## 下一步

1. 根据 `08-writing/experiment-plan-v0.1-20260707.md` 建立案例清单和数据 schema。
2. 保留 APTChaser、GAPT 正文获取待办，并继续中文专利侧证据采集/取证规划检索；US12530469 仅作为摘要级专利红线保留。
3. 将 POIROT/DeepHunter/MEGR-APT/CLIProv/APT-CGLP 作为上游对齐谱系写入相关工作和 baseline 设计。
4. 在最小可行实验通过后判断是否可以启动新专利 v0.3。
