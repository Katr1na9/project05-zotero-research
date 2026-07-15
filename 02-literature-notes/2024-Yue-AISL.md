# Detecting APT Attacks Using an Attack Intent-Driven and Sequence-Based Learning Approach

## 1. 基本信息

- 系统名：AISL
- 中文译名：使用攻击意图驱动与序列学习方法检测 APT 攻击
- 作者：Hao Yue; Tong Li; Di Wu; Runzi Zhang; Zhen Yang
- 年份：2024
- Venue：Computers & Security, 138, 103748
- DOI：https://doi.org/10.1016/j.cose.2024.103748
- 前身预印本：https://ssrn.com/abstract=4238362
- 阅读状态：`metadata-only / extended publisher HTML`；全文 PDF 在本轮检索中不可获取，以下结论不单独支撑 novelty 判断
- 阅读日期：2026-07-13
- 阅读优先级：必读（术语与功能碰撞）
- 所属主题：Heterogeneous Audit Data / Provenance Ontology / Intent-Guided Tagging / Sequence Learning

## 2. 一句话总结

AISL 用网络事件本体整合 system、DNS、browser/network 等异构审计数据，依据专家预先定义的敏感资产与攻击目标规则传播安全标签、扩充正样本，再以标签序列模型识别攻击并重构场景；这里的 intent 是先验输入和标注依据，不是模型从未知证据中推断出的攻击意图。

## 3. 研究问题

- 如何用统一 ontology 消除跨操作系统与多类审计数据的语义差异？
- 如何利用专家给定 attack intent 识别潜在攻击行为并缓解正样本稀缺？
- 如何从 provenance graph 构造攻击/非攻击序列并恢复关键攻击步骤？

## 4. 核心贡献

1. Host、Subject、Object、Event、Tag 为核心的 network event ontology。
2. 将多源审计数据转换为同构 provenance graph。
3. 根据敏感数据、关键服务、白名单等 intent knowledge 设计 tag initialization/propagation policy。
4. 从告警实体邻域生成标签事件序列并训练语义模型。

## 5. 方法框架

- 日志通过规则解析器映射为 provenance graph。
- 可信/未知、公开/私密等标签由白名单、敏感资产与专家规则初始化并沿边传播。
- 以攻击实体为起点提取可达领域子图，合并重复事件与语义等价实体，形成 attack sequence。
- 剩余图中随机选普通实体形成 non-attack sequence。
- 模型判定实体/事件是否攻击相关并据此恢复关键步骤。

## 6. 数据集与实验

- 论文报告在 10 个 realistic/public APT attacks 上评估。
- 平均 precision 93.05%、recall 98.12%、F1 95.36%。
- 结论部分报告 event detection F1 99.91%。
- 由于本轮未取得全文 PDF，具体场景、拆分、消融和标注分母不得仅依据本笔记引用。

## 7. 关键知识点

- `intent-driven` 不等于 `intent inference`：AISL 以攻击意图知识生成标签，输出仍是攻击检测/场景重构。
- ontology 可以统一多日志 schema，但跨源实体是否属于同一事件仍需独立匹配与证据验证。
- 专家标签传播能扩正样本，也可能把先验答案泄漏到检测标签。

## 8. 优点

- 明确处理异构审计源和语义同构化。
- 将 intent 作为可操作的敏感资产/服务先验，而不是模糊自然语言概念。
- 输出关键攻击步骤，不只是普通二分类。

## 9. 局限

- intent 是预设规则，不是开放世界目标、动机或 actor 意图推断。
- 图与标签依赖人工 ontology、白名单和工业专家知识，迁移成本高。
- 可能存在 intent/tag policy 到训练标签的泄漏。
- 未见原始 PCAP packet 锚点、跨源边校准、LLM 或拒答机制。
- 当前为扩展出版商 HTML 阅读状态，实验细节仍需全文复核。

## 10. 对我选题的启发

- 论文必须把 intent prior、latent behavioral intent 和 inferred attack objective 分开定义。
- AISL 可作为 ontology/tag-rule baseline；我们的目标应是证据驱动候选、显示先验影响并允许 unknown。
- 双源图中敏感资产信息可作为背景知识节点，但不能直接充当 ground truth。

## 11. 可转化的研究问题

1. 在不把 intent prior 泄漏为标签的条件下，如何评价目标候选推断？
2. traffic/log 双源证据能否区分相同 TTP 下的不同 attack objective？
3. 对敏感资产先验做遮蔽或扰动时，模型的意图结论是否保持校准？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| Sentient | AISL 使用显式 intent rules；Sentient 学习无语义 latent intent embedding |
| StageFinder | 输出阶段概率但无意图；可作为 stage-to-objective 上游 |
| Project03 | HFish/traffic 事件可映射 ontology，但需新增原始 evidence anchor 与边核验 |

## 13. 论文写作可引用句式

- 现有所谓“意图驱动”方法主要将专家定义的敏感资产与攻击目标作为标签生成先验，而不是从不完整、冲突的观测证据中推断并校准未知意图。

## 14. 我的批注与疑问

- 该文是防止我们误把“意图”写宽的关键红线文献。
- 正式引用方法细节前仍需取得 publisher PDF 或作者稿复核。
- 预印本题名 SLAII 与期刊题名 AISL 有变化，应以期刊 DOI 为准。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：4/5
- 实验可复现性：2.5/5（全文未得）
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是（明确标为 metadata-only，不独立支撑 novelty）
