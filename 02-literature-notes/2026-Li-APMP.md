# APMP: APT Attack Detection in Few-Shot Scenarios Based on Entity Potential Relations

## 1. 基本信息

- 中文译名：APMP：基于实体潜在关系的少样本 APT 攻击检测
- 作者：Jiacheng Li; Tong Li; Runzi Zhang; Zilong Wan; Zhen Yang
- 年份：2026
- Venue：Cybersecurity, 9, Article 172
- DOI：https://doi.org/10.1186/s42400-026-00592-5
- 开放全文：https://link.springer.com/content/pdf/10.1186/s42400-026-00592-5.pdf
- 阅读日期：2026-07-14
- 阅读优先级：必读（图内关系补全直接红线）
- 所属主题：Provenance Graph / Relation Prediction / Few-shot APT Detection / BERT

## 2. 一句话总结

APMP 从审计 provenance graph 中抽取攻击序列，用 BERT 预测 14 类实体关系并把潜在边补回图中，再以抽象攻击模式训练序列检测器；它直接占据“学习潜在关系补全 provenance graph”的宽泛创新，但预测对象是同一审计图内的语义关系，既不是 traffic-log 跨源记录配对，也没有概率校准、来源冲突或原始证据回放。

## 3. 研究问题

- 在每个新 campaign 只有少数已知攻击实体时，如何扩大可用于检测的攻击上下文？
- 仅沿已有 provenance edge 扩展为何会漏掉攻击实体之间未显式记录的依赖？
- 能否从历史攻击序列学习实体关系类型，将潜在关系补入 provenance graph？
- 补边是否能提高少样本条件下的攻击实体检测率？

## 4. 核心贡献

1. 将少样本 APT 检测改写为已知攻击实体驱动的图扩展与攻击实体识别。
2. 将路径、URL、IP、进程和文件等实体分词，使用 BERT 的 MLM/NSP 学习攻击事件上下文。
3. 对实体对输出 14 类关系的 Softmax 分布，并用形态抽象后的已知攻击模式过滤候选。
4. 将保留的潜在关系写回 provenance graph，再用 Conv1D/LSTM/全连接网络判断候选序列的攻击相关性。
5. 在 ATLAS 提供的十个实验性 APT campaign 上报告关系预测与实体检测结果。

## 5. 方法框架

### 输入

- 由系统、Web 和 DNS 审计记录构成的已有 provenance graph。
- 每个调查的 1-8 个初始攻击实体；主实验使用 4 个。
- 历史 campaign 中的实体、关系和攻击实体标签。

### 输出

- 实体对的潜在关系类型及 Softmax 分数。
- 补充潜在边后的 provenance graph。
- 攻击实体集合及供案例展示的攻击序列。

### 关键模块

| 模块 | 作用 | 对本支线的边界意义 |
|---|---|---|
| Event tokenizer | 细分路径、URL、IP 和进程标识 | 可借鉴为日志侧语义编码，但不提供跨源真值 |
| BERT relation predictor | 对 14 类图内关系分类 | 是“学习补边”的直接 baseline |
| Pattern-based filter | 只保留符合抽象攻击模式的关系 | 属规则后验过滤，不等于确定性证据验证 |
| Sequence detector | 判断扩展序列是否攻击相关 | 终点是实体检测，不是链/意图正确性 |

### 方法流程

```text
审计 provenance graph + 初始恶意实体
  -> 攻击序列与实体对抽取
  -> BERT MLM/NSP + MLP 关系分类
  -> pattern filter -> 潜在边写回图
  -> 序列抽象 -> Conv1D/LSTM 检测
  -> 攻击实体扩展
```

## 6. 数据集与实验

- 数据来自 ATLAS 的十个基于真实 APT 报告复现的 campaign，而非十次自然发生的现场攻击；共约 197,500 个实体、2,849,638 个事件，绝大多数为 system log。
- 关系类别共 14 类，其中 `read` 占 61.26%，类别高度不平衡。
- 关系预测随机使用 80%/20% 攻击序列切分：BERT Precision/Recall/F1 为 95.29%/97.21%/96.24%；ALBERT 和 RoBERTa 明显更低。
- 四个初始恶意实体条件下，实体检测平均 Precision/Recall/F1 为 100%/93.18%/96.30%；无关系预测时为 98.75%/87.20%/91.88%。
- 留一 campaign 报告 Precision 97.9 +/- 2.1%、Recall 88.3 +/- 3.5%；一个 seed 时性能明显下降，方法依赖有效初始线索。
- 论文另抽查 100 个预测恶意节点：92 个被专家确认、5 个不确定、3 个明确误报，却将未确认的 8 个称作“8% false-positive rate”。这实际更接近预测集合内的未确认比例，既不是标准 FPR，也与主表 `FP=0` 的口径不一致。

## 7. 关键知识点

- “预测缺失关系并补全 provenance graph”截至 2026 年已有明确实现，不能单独作为创新。
- 其所谓 `potential relation` 是同一审计事件空间内的语义边，不是两个独立传感源之间的 observation identity/link。
- Softmax 分数只用于 argmax 与过滤；没有 Brier、ECE、reliability diagram 或独立 calibration set，不能称为校准概率。
- 预测边写回原图后没有 `observed/candidate/verified/rejected` 分层，模型假设容易被下游当作事实。
- 关系级 F1、实体级 F1 都不能证明攻击链顺序、因果关系、高层意图或原始记录忠实度。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| Potential relation | 潜在关系 | 模型推测的图内关系，不是观测证据 |
| Provenance graph completion | 溯源图补全 | 应与原始观测层分开存储 |
| Initial attack entity | 初始攻击实体 | 分析员提供的 seed/POI |
| Attack sequence lemmatization | 攻击序列抽象化 | 将具体路径/进程归并为语义类别 |

## 8. 优点

- 关系预测任务、关系类别和写回图流程定义清楚。
- 不只报告最终检测，还给出关系模块替换、无补边和无抽象化消融。
- 显式测试 seed 数量与 seed 质量，承认调查起点对结果的影响。
- 使用多个 campaign，并给出留一 campaign 结果和人工抽查。

## 9. 局限

- 输入是已构造审计 provenance graph，没有独立 PCAP/流量子图，也未解决 raw record 生成与跨源配对。
- 随机序列切分可能让相同 campaign、实体或模式同时进入训练和测试；论文未给出严格的实体/campaign 隔离关系评测。
- 关系类别高度不平衡，却只报告总体 P/R/F1，未给 macro-F1 和每类表现。
- 图补边概率未校准，且没有假设边的拒绝、冲突和来源等级。
- 主表 `FP=0` 与 100 节点专家复核中的 3 个明确误报、5 个不确定并不一致。
- 需要高质量标注攻击序列和至少一个正确 seed；新型行为与错误 seed 会明显退化。
- 无 chain edge、stage、intent、claim-to-record replay 和 missing-source 评价。

## 10. 对我选题的启发

- 不能用“LLM/BERT 预测关系补全攻击图”作为新贡献；必须限定为**跨源 observation relation**。
- 流量侧和日志侧先各自形成可复核子图，跨源层预测的是“这些具体 raw records 是否描述同一行为/因果交互”，而不是任意实体语义关系。
- 候选边必须保留 `candidate/verified/rejected/conflict` 状态及 packet/log 原始锚点；LLM/ATT&CK 边单列为 hypothesis layer。
- 对跨源边应使用 campaign-disjoint split、hard negatives、Brier/ECE 和 risk-coverage，避免 APMP 式总体 F1 即“可靠”的跳跃。

## 11. 可转化的研究问题

1. 双源 observation pair 的校准后验能否优于 APMP 式图内关系分类和 BotFence 的确定性 5-tuple？
2. 将预测边与观测边分层，能否降低错误补边对攻击链和 LLM 结论的级联污染？
3. 在错误 seed、缺失流量或缺失日志时，显式 conflict/abstention 是否能改善风险覆盖性能？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| BotFence | BotFence 用 5-tuple 确定性接 host/packet；APMP 学习图内语义边 |
| MPCA | MPCA 对审计事件三元组估计 confidence；APMP 对潜在关系分类，二者均非跨源校准 |
| Integrated Evidence Graphs | 早期工作用专家概率补缺失证据；APMP 改用监督关系预测 |
| HunterAgent | 后者显式验证并可输出证据不足；APMP 将通过过滤的关系直接写回图 |
| Project03 支线 | 迫使“图补边”收紧为 source-preserving、pair-grounded、calibrated cross-source linking |

## 13. 论文写作可引用句式

- 近期工作已利用预训练语言模型从攻击序列预测潜在实体关系并补全审计溯源图，但其分类分数未经过概率校准，推测边也未与观测证据、跨源关联和冲突状态分层。

## 14. 我的批注与疑问

- 论文多次把十个复现场景称作“real APT datasets”，写作时应改为“基于真实报告复现的公开 campaign 数据”。
- 关系预测 80/20 随机切分是否共享 campaign/实体尚不清楚，可能高估泛化。
- `read` 占比超过 60%，总体 F1 不能说明稀有关系是否可靠。
- 专家抽查的“8% FPR”计算口径错误，应在引用时明确为 predicted-positive audit。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：3.5/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是（图内关系补全直接红线）
