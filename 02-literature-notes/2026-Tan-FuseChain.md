# FuseChain: Runtime Evidence Reconstruction for Software Supply-Chain Attacks

## 1. 基本信息

- 中文译名：FuseChain：面向软件供应链攻击的运行时证据重构
- 作者：Zhuoran Tan; Yutian Tang; Jeremy Singer; Christos Anagnostopoulos; Ke Xiao
- 年份：2026
- Venue：arXiv preprint
- arXiv：https://arxiv.org/abs/2606.15811
- Zotero key：E88YJILE（PDF：82ZQHBSU）
- 阅读日期：2026-07-13
- 阅读优先级：必读
- 所属主题：Multisource Evidence Graph / TGN / Stage Reconstruction

## 2. 一句话总结

FuseChain 将网络流、DNS/HTTP/TLS 元数据、告警和主机/包/凭据/云日志统一为带来源指针的时间异构事件证据图，通过关系 TGN 排序异常并恢复可观测攻击阶段。它已经占据本课题的双源图谱与阶段重构前半段，但没有 LLM、主张级叙事验证、意图候选和行为体归因。

## 3. 研究问题

- 软件供应链攻击跨包、主机、服务和云边界时，如何在单源证据稀疏的情况下恢复运行时链？
- 如何不依赖 IOC/阶段标签训练异常模型，同时保留阶段解释能力？

## 4. 核心贡献

1. 多源事件六元组和带来源的时间异构事件图。
2. 自监督关系 TGN 进行时间链路预测和异常排序。
3. 异常检测骨干与冻结阶段解释器解耦。
4. PairDedupe、SourceQuota、GroupCap、Adaptive 等证据多样化策略。

## 5. 方法框架

- 事件：`e_i=(t_hat,u_i,r_i,v_i,a_i,sigma_i)`，包含统一时间、源/目标实体、关系、属性和遥测源。
- 图：`G(t_hat)=(V,E_o ∪ E_c)`；`E_o` 为观测边，`E_c` 为规则派生 CAUSE 边。
- 节点类型：PKG、PROC、CMD、FILE、NET、HOST、USER、CRED、ARTIFACT、ALERT、SYSCALL。
- 先异常排序，再按时间邻近、共享实体和 provenance 关系聚类，做 Top-K 阶段恢复。
- 无 LLM；解释器是轻量分类解码器。

## 6. 数据集与实验

- 使用 SynthChain 7 场景，处理约 330,013 事件；平均语义阶段 6.9、可观测阶段 5.1。
- 覆盖全部场景时 AUROC 0.638、AUPRC 0.198、P@500 0.215、StageRec@500 0.405，约 176 ms/1K 边。
- 默认 Top-500：P@500 0.191、IOC Recall 0.101、Stage Recall 0.524。
- PairDedupe/Adaptive 把 IOC 映射阶段召回提升到 0.643/0.655。
- 冻结阶段解码器 `PredStage@500` 从 0.369 升至 0.881；不能与 IOC 映射 Stage Recall 混为同一指标。

## 7. 关键知识点

- `source file id + original row index + IOC` 是可直接复用的原始证据谱系。
- 规则派生 CAUSE 边不是观测事实，必须标明证据等级。
- “可观测阶段召回”不能当作完整 Kill Chain 重构率。

## 8. 优点

- 真正多源、显式事件图和来源回指。
- 单源/多源及证据多样性实验较完整。
- 将检测与解释解耦，便于替换 LLM 推理层。

## 9. 局限

- 仅 7 个合成供应链场景；历史前缀可能含未标注攻击。
- 阶段解码器仍需标签，CAUSE 边依赖确定性规则。
- 主要是流/元数据，不是细粒度 PCAP payload。
- 无 LLM 证据忠实度、意图候选、行为体归因和自然语言主张验证。

## 10. 对我选题的启发

- 该文适合作为统一事件图、双源消融和阶段恢复的核心 baseline/数据基础。
- 本课题差异应落在 LLM 对显式证据子图的候选链/意图推理、支持/反证路径与校准拒答。
- Project03 PCAP 与 HFish 日志需保留 source record index，并区分 observation/derived/inferred。

## 11. 可转化的研究问题

1. LLM 能否在不改变 FuseChain 检测骨干的情况下提高链语义与意图可读性，同时保持证据忠实？
2. PCAP payload 细节对流元数据+日志阶段恢复有多少额外贡献？
3. 如何把阶段不确定性传播到多意图候选和拒答？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| SynthChain | FuseChain 的数据与可观测性基础 |
| StageFinder | 同为双源事件图阶段估计；FuseChain更强调证据排序与来源多样性 |
| HunterAgent | 后者用 LLM+验证器补缺失路径和反取证 |

## 13. 论文写作可引用句式

- 多源事件图的价值不仅在增加事件量，还在于补足缺失阶段并提供稳定跨源连接键。

## 14. 我的批注与疑问

- 需谨慎区分 `StageRec@K`、`PredStage@K` 和完整链指标。
- 表中 FuseGraph 应视为 FuseChain 命名笔误。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是
