# MOLE: Provenance Graph Generation Framework Based on LLM Prompting

## 1. 基本信息

- 系统名：MOLE
- 中文译名：MOLE：基于大模型提示的溯源图生成框架
- 作者：Yiming Ren; Haoqiang Wang; Yilong Chen; Zhou Zhou; Chengxiang Si; Qingyun Liu
- 年份：2025
- Venue：International Joint Conference on Neural Networks (IJCNN), pp. 1-8
- DOI：https://doi.org/10.1109/IJCNN64981.2025.11229381
- 阅读状态：`metadata-only`；出版社记录与摘要已核验，全文在本轮检索中不可获取
- 阅读日期：2026-07-13
- 阅读优先级：重点读（Auto-Prov 的同功能前序）
- 所属主题：LLM Prompting / Log Parsing / Provenance Graph Generation

## 2. 一句话总结

MOLE 用 LLM 根据少量日志生成 provenance graph 抽取模板，再在本地批量解析日志建图，目标是替代每种日志手写 regex；它直接占据“LLM 生成日志建图规则”，但公开摘要不足以核验节点/边正确性、跨源融合、下游攻击链或证据可审计性。

## 3. 研究问题

- 如何减少 audit-log-to-provenance-graph 中按日志类型手写规则的成本？
- 如何让 LLM 只生成模板而不是处理数千万条原始日志？

## 4. 核心贡献

1. 通过 LLM prompting 自动生成 provenance extraction template。
2. 将模板在本地应用于全量日志，避免逐条调用 LLM。
3. 论文摘要报告处理 5,000 万条日志只消耗约 20k tokens，并把数天人工编码缩短到数分钟。

## 5. 方法框架

- 可确认链路：少量日志样本 -> LLM instruction/template generation -> local parser -> provenance graph。
- 节点/边 schema、模板验证、失败回退和跨日志实体连接细节因全文不可得而待核验。

## 6. 数据集与实验

- 摘要只确认 5,000 万条日志与 20k token 规模声明。
- 数据集、日志类型、graph ground truth、edge precision/recall 与下游 detector 增益均待全文核验。

## 7. 关键知识点

- 把 LLM 用于“规则归纳”而非全量在线解析，是日志图构建的重要工程模式。
- token/速度不能替代 graph fidelity 与 evidence lineage 评价。

## 8. 优点

- 解决 LLM 逐条解析昂贵和输出不稳定的问题。
- 与 Auto-Prov 的 candidate extractor -> rule generator 思路形成直接前后对照。

## 9. 局限

- 当前只能确认摘要信息，不能判断真实跨源图构建能力。
- 未确认是否保留 raw log ID/hash、错误模板检测和版本演化。
- 未确认是否进行 chain/stage/intent 或 LLM 调查输出。

## 10. 对我选题的启发

- “LLM 自动生成构图模板”本身已不是空白。
- 我们若复用这一模式，贡献必须是双侧证据核验、跨源边不确定性和下游链/意图可审计增益。

## 11. 可转化的研究问题

1. 如何验证 LLM 生成的抽取模板不会系统性传播错误？
2. 模板版本漂移时，既有 evidence graph 如何保持可回放？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| Auto-Prov | 同功能更完整、更晚的系统，含流式日志类型发现、下游检测和解释评估 |
| UTLParser | 后者多依赖预定义 parser/POI；MOLE 用 LLM 生成模板 |

## 13. 论文写作可引用句式

- 已有方法将大模型用作日志到溯源图抽取模板的生成器，以避免逐条推理成本；因此，新的图构建工作必须进一步证明跨源证据关系的正确性和可审计性。

## 14. 我的批注与疑问

- 全文获取前不引用 20k token 以外的任何方法或性能细节。
- 该项保留为 metadata-only direct collision，不作为最终 novelty 证据的唯一来源。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：4/5
- 实验可复现性：1.5/5（全文未得）
- 作为硕士论文基础价值：4/5
- 是否进入核心文献：是（metadata-only；由 Auto-Prov 提供全文级对照）
