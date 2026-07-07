# APT-ATT: An efficient APT attribution model based on heterogeneous threat intelligence representation and CTGAN

## 1. 基本信息

- 英文题名：APT-ATT: An efficient APT attribution model based on heterogeneous threat intelligence representation and CTGAN
- 中文译名：APT-ATT：基于异构威胁情报表示与 CTGAN 的高效 APT 归因模型
- 作者：Saihua Cai, Gang Wang, Jinfu Chen, Shengran Wang, Kun Wang
- 年份：2025
- Venue：Computer Networks, 270, 111511
- DOI / URL：https://doi.org/10.1016/j.comnet.2025.111511
- PDF 来源：`C:/Users/35393/Downloads/1-s2.0-S1389128625004785-main(科研通-ablesci.com) (1).pdf`
- Zotero key：待补
- 阅读日期：2026-07-07
- 阅读优先级：必读 / 红线精读
- 所属主题：CTI-based APT attribution / Heterogeneous CTI representation / CTGAN / Ensemble learning
- 阅读状态：正文 PDF 已获取并完成 Project05 精读；由原“高风险占位”升级

## 2. 一句话总结

APT-ATT 是一个闭集 APT 组织多分类归因模型：它用 N-Gram + TF-IDF + 卡方特征选择表示异构 CTI 文本，用 CTGAN 生成少数类特征向量缓解类别不平衡，再用 KNN、RF、XGBoost 和逻辑回归 stacking 完成 APT 组织归因。

## 3. 研究问题

- 现有 APT 归因模型在异构长文本 CTI 表示上效率不足。
- APT 组织样本分布不平衡，少数类组织识别效果差。
- 单一分类模型在小规模 CTI 数据和多类别归因任务中稳定性不足。
- 论文目标是提高闭集 APT 组织分类准确率、稳定性和实时性，而不是处理证据不完整、拒答或主动取证。

## 4. 核心贡献

1. 提出适用于长异构威胁情报的轻量文本表示方法：N-Gram 捕获局部语义，TF-IDF 向量化，卡方统计进行特征选择。
2. 引入 CTGAN 生成少数类 APT 组织的 realistic feature vectors，缓解 CTI 类别不平衡。
3. 构造 stacking ensemble attribution model，以 KNN、RF、XGBoost 为 base learners，以优化逻辑回归为 meta learner。
4. 在 AADM 和 AADM+ 两个 CTI 数据集上验证，报告 AADM+ accuracy 达到 94.91%，并给出时间成本和消融实验。

## 5. 方法框架

### 输入

- 非结构化 / 异构 CTI 文本报告。
- 12 类 APT 组织标签。
- 训练阶段使用人工/安全专家已归因的公开 CTI 标签。

### 输出

- APT organization label。
- 多分类预测结果和常规分类指标。

### 关键模块

| 模块 | 作用 | 对 Project05 的意义 |
|---|---|---|
| CTI preprocessing | 小写化、去标点、分词、去停用词、stemming | 基础 NLP 预处理，不是创新空间 |
| N-Gram + TF-IDF | 快速表示 CTI 局部语义和词项重要性 | 证明“异构 CTI 文本快速表示”已被覆盖 |
| Chi-square feature selection | 降维并选择与组织标签相关的特征 | 不能把简单特征选择作为主创新 |
| CTGAN augmentation | 对少数类生成特征向量 | 数据增强 + APT attribution 已被覆盖 |
| Stacking ensemble | KNN/RF/XGBoost + logistic regression 归因分类 | 可作为闭集 actor attribution baseline |

### 方法流程

```text
raw heterogeneous CTI
  -> preprocessing
  -> N-Gram local semantic features
  -> TF-IDF vectorization
  -> chi-square feature selection
  -> CTGAN minority-class augmentation
  -> KNN / RF / XGBoost base predictions
  -> logistic regression meta learner
  -> APT organization attribution label
```

## 6. 数据集与实验

- 数据集：
  - AADM：Attack Attributing Dataset-Master，来自 Perry et al. 2019。
  - AADM+：作者在 AADM 基础上做 back translation，并从 MITRE / Mandiant / ATT&CK 等来源收集仍活跃 APT 组织相关 CTI 构建。
- 类别：两个数据集均包含 12 类 APT 组织。
- 划分：8:2 train/test。
- 运行环境：Windows 11，Intel i5-13400，NLTK，sklearn。
- Baseline：
  - Embedding：SMOBI、BERT、Doc2Vec、FastText。
  - Augmentation：SMOTE、VAE。
  - Classifier：SVM、XGBoost、RF、RGensemble、AdaBoost、CatBoost、ExtraTrees、GBDT、LightGBM。
- 指标：Accuracy、Weighted Precision、Weighted Recall、Weighted F1、Macro Precision、Macro Recall、Macro F1。

### 主要结果

- Embedding 模块：
  - AADM：作者方法 accuracy 83.47%，高于 SMOBI 78.06%。
  - AADM+：作者方法 accuracy 85.57%，高于 SMOBI 80.24%。
  - 时间成本约 2.40s / 2.53s，明显低于 BERT 和 SMOBI。
- CTGAN 模块：
  - 在作者 embedding 下，AADM accuracy 85.28%，高于 VAE 84.58% 和 SMOTE 84.17%。
  - AADM+ accuracy 87.76%，高于 VAE 86.18% 和 SMOTE 85.82%。
- Ensemble attribution：
  - AADM：APT-ATT accuracy 90.56%，weighted F1 90.07%。
  - AADM+：APT-ATT accuracy 94.91%，weighted F1 94.76%，macro F1 94.63%。
- 消融：
  - AADM 去掉 CTGAN：accuracy 降至 88.89%。
  - AADM 去掉 base learners：accuracy 降至 83.89%。
  - AADM+ 去掉 CTGAN：accuracy 降至 93.70%。
  - AADM+ 去掉 base learners：accuracy 降至 89.82%。

## 7. 关键知识点

### 概念

- APT-ATT 的“异构威胁情报表示”实质是 CTI 文本的轻量 NLP 表示，不是多源日志/样本/网络/CTI 证据融合。
- CTGAN 在这里生成的是特征向量，不是生成新 CTI 报告或新攻击图。
- 模型输出是闭集 APT 组织标签，不做 open-set、不做 abstention、不做证据不足降级。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| heterogeneous threat intelligence representation | 异构威胁情报表示 | 本文主要指 CTI 文本表示 |
| conditional tabular GAN | 条件表格生成对抗网络 | CTGAN |
| stacking strategy | 堆叠集成策略 | base learners + meta learner |
| class imbalance | 类别不平衡 | APT 组织样本数不均 |

## 8. 优点

- 把 CTI 文本表示、数据增强和归因分类做成了完整轻量 pipeline。
- 对类别不平衡问题给出明确处理，并通过 CTGAN/SMOTE/VAE 对比验证。
- 实验有 embedding、augmentation、classifier、ablation 四组问题设置，结构清楚。
- 提供 AADM+ 数据集 GitHub 入口，有一定复现价值。

## 9. 局限

- 闭集多分类设定：默认待归因样本属于已知 12 个 APT 组织之一。
- 不处理 open-set、unknown actor、false flag、mimicry。
- 不处理 evidence sufficiency、confidence calibration、refusal、granularity gate。
- 不做多源取证动作规划，也没有对“缺什么证据才能提升归因粒度”建模。
- CTI 标签来自公开专家归因，论文不验证标签争议和多源情报冲突。
- AADM/AADM+ 仍然规模有限，作者也承认未覆盖全部 APT 组织和更多真实场景。

## 10. 对我选题的启发

- 强红线：不能把 Project05 写成“异构威胁情报表示 + 数据增强 + APT 组织分类”。
- 强红线：不能主张“用 CTGAN 解决 APT 归因数据不平衡”。
- 可作为 baseline：APT-ATT 可作为闭集 actor attribution baseline，用来对比 Project05 的“粒度受控/证据不足时不强行归因”。
- 留出的空间：Project05 关注不完整证据下的 attribution granularity、evidence state 和 next evidence action planning。APT-ATT 没有解决“当前证据不够时怎么办”，只是在给定 CTI 文本向量后输出组织标签。

## 11. 可转化的研究问题

1. APT-ATT 在证据遮蔽或 CTI 不完整时是否会过度自信地输出 actor label？
2. Project05 是否可以把 APT-ATT 的 softmax / classifier confidence 作为 baseline evidence score，再证明其不能替代 evidence sufficiency gate？
3. 当 APT-ATT 输出 actor label 但 alignment state 缺少关键 provenance/log 证据时，Project05 如何正确降级到 campaign/technique 粒度？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| APT-MMF | 同样压缩多模态/多层特征融合 APT attribution 空间 |
| Au HKG | 多源特征融合 + HKG + APT attribution，与 APT-ATT 共同压住“多源融合归因” |
| LLMAPT / TAA-EPLMR | 这些更偏 LLM/证据路径归因；APT-ATT 是非 LLM 轻量分类路线 |
| Project05 | APT-ATT 是被避让的闭集 actor classifier，不覆盖主动取证规划 |

## 13. 论文写作可引用句式

- Existing CTI-based attribution models can already classify known APT organizations from heterogeneous intelligence text using lightweight representations, data augmentation, and ensemble learning; however, they assume a closed-set attribution setting and do not decide whether the currently observed evidence is sufficient for a target attribution granularity.

## 14. 我的批注与疑问

- 这篇拿到后，原来的“APT-ATT 未获取风险”可以降级为“已确认红线”。
- 它没有杀死 Project05 新主线，反而帮我们把边界说清楚：我们的目标不是更高 actor classification accuracy，而是证据不完整时如何不乱归因，并以成本约束规划补证。
- 写专利时不要出现“CTGAN”“异构情报表示”“stacking 归因分类器”作为核心限定。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：3/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：4/5
- 是否进入核心文献：是

## 16. 逐节精读

### 16.1 Abstract / Introduction：它把问题定义在哪里

论文的起点是三个传统 CTI-based APT attribution 痛点：长异构 CTI 嵌入效率低、APT 组织类别不平衡、单一分类器稳定性不足。作者把 APT attribution 明确收缩成一个监督式多分类任务：给定 CTI 文本，预测其对应的 APT 组织标签。

这里的关键不是“多源安全证据融合”，也不是“证据链归因”，而是“文本情报分类”。论文反复强调的是 fast vectorization、minority-class augmentation、ensemble stability。它的 attribution 是 closed-set actor classification，不涉及当前证据是否足够、是否应输出 unknown、是否应降级到 campaign/technique。

对 Project05 的直接含义：如果我们说“解决 APT 归因中异构威胁情报表示效率低和类别不平衡”，会撞；如果我们说“在不完整证据下判断当前最高可支撑归因粒度并规划补证动作”，则不在它的任务边界内。

### 16.2 Related Work：作者怎样给自己找位置

作者把相关工作分成三组：

1. Malware-based APT attribution：基于恶意软件行为、二进制、代码相似度等。
2. CTI-based APT attribution：进一步分 NLP-based、graph-based、multidimensional feature analysis。
3. Multidimensional feature / graph / KG 类方法：作者主要批评这些方法计算复杂、依赖高质量结构化数据、实时性较差。

表 1 的定位很重要：APT-ATT 被作者列为 NLP-based，并标注为包含 CTI 信息、不依赖外部威胁知识、可自动处理 CTI、时间成本低、处理类别不平衡。也就是说，它自己没有把方法宣传成多源证据图、provenance alignment、取证系统或 LLM 归因框架。

对 Project05 的直接含义：APT-ATT 压住的是“轻量 CTI 文本归因分类”方向，而不是“CTI-local evidence alignment 之后的证据状态与取证规划”方向。

### 16.3 Methodology：三个模块到底做了什么

APT-ATT 的方法是三段式。

第一段是 feature representation。输入是 raw heterogeneous CTI，先做 lowercase、punctuation removal、tokenization、stop-word removal、stemming；然后用 unigram/bigram N-Gram 抽局部语义，用 TF-IDF 向量化，再用 chi-square statistics 根据组织标签相关性筛特征。这里所谓 heterogeneous 主要指 CTI 文本格式和长度不一致，不是日志、样本、网络、基础设施、provenance 多模态证据共建模。

第二段是 CTGAN data augmentation。作者统计每类 APT 组织样本数，低于平均样本量的类别被视为 minority class。每个 minority class 单独训练 CTGAN，并生成同类 feature vectors，再与原训练集合并。这个 CTGAN 生成的是特征空间中的 tabular vectors，而不是新 CTI 报告、攻击图、证据链或取证路径。

第三段是 ensemble attribution。第一层 base learners 是 XGBoost、RF、KNN；第二层 meta learner 是 logistic regression。XGBoost 用于复杂非线性边界，RF 用类别权重缓解不平衡，KNN 用距离加权处理局部相似。三者输出概率向量后拼接成新特征，逻辑回归学习各 base learner 权重并输出最终组织标签。

对 Project05 的直接含义：如果将来做 baseline，可以把 APT-ATT 看作“闭集 CTI actor classifier”。它可以回答“像哪个已知 APT 组织”，但不能回答“这个结论需要哪些本地证据支撑”“是否证据不足”“下一步应取什么证据”。

### 16.4 Experimental Setup：实验环境与评价对象

实验用两个 CTI 数据集：

- AADM：Attack Attributing Dataset-Master，Perry et al. 2019 发布。
- AADM+：作者在 AADM 基础上做 back translation，并补充 MITRE、Mandiant、ATT&CK 等来源中仍活跃 APT 组织的 CTI。

两个数据集都包含 12 类 APT 组织，按 8:2 划分训练集和测试集。作者强调标签来自公开高质量情报源和安全专家归因，没有使用自动推理工具生成标签。

实验设置四个 RQ：

| RQ | 问题 | 对应模块 |
|---|---|---|
| RQ1 | 文本表示是否比其他 embedding 方法更好 | N-Gram + TF-IDF + chi-square |
| RQ2 | CTGAN 是否比 SMOTE/VAE 更好 | 数据增强 |
| RQ3 | stacking ensemble 是否优于其他分类器 | 归因分类 |
| RQ4 | 各模块贡献如何 | 消融实验 |

评价指标全部是分类指标：accuracy、weighted precision/recall/F1、macro precision/recall/F1。没有 calibration error、unknown rejection、evidence completeness、cost-to-attribution、next-best-evidence rank 等指标。

### 16.5 Results：结果应该怎么读

RQ1 显示作者的轻量文本表示在 AADM 上 accuracy 83.47%，AADM+ 上 85.57%，高于 SMOBI、BERT、Doc2Vec、FastText。更关键的是时间成本：作者方法约 2.40s / 2.53s，BERT 接近 90-100s，SMOBI 更高。这个结果说明 APT-ATT 的优势主要是“快且足够准”，不一定是语义理解最强。

RQ2 显示 CTGAN 在作者 embedding 上把 AADM accuracy 推到 85.28%，AADM+ 推到 87.76%，略高于 VAE 和 SMOTE。作者还用 UMAP 可视化证明生成样本与原样本有重叠，没有明显 mode collapse。这里的提升幅度不算巨大，但足够支撑“CTGAN 比简单插值更适合高维 CTI feature vectors”的论点。

RQ3 是主结果：完整 APT-ATT 在 AADM 上 accuracy 90.56%，在 AADM+ 上 94.91%。AADM+ 上第二名 ExtraTrees 为 92.24%，所以完整模型领先约 2.67 个百分点。作者还强调标准差更低，说明 30 次重复实验下更稳定。

RQ4 的消融说明 CTGAN 和 base learners 都有用。AADM+ 中去掉 CTGAN 后 accuracy 从 94.91% 降到 93.70%，去掉 base learners 降到 89.82%，两者都去掉降到 83.88%。这表明 stacking ensemble 对最终性能的贡献比 CTGAN 更大。

### 16.6 Threats to Validity：作者自己承认的薄弱点

作者承认三类关键限制：

- 参数没有充分验证，例如 retained features 设置为类别数的 25 倍、CTGAN 训练 100 次，这些设定不一定最优。
- 对非开源 comparison methods 的复现可能有实现偏差。
- 数据集只覆盖两个 CTI 数据集和有限 APT 组织，不能证明泛化到所有 APT 组织和真实场景。

此外，作者专门讨论 chi-square 在高度稀疏特征空间可能有偏。表 10 显示特征维度从 159,563 / 178,168 降到 300，稀疏度从约 99% 降到约 96%。这有利于效率和分类，但也意味着模型高度依赖词项统计相关性，不具备对证据因果链、攻击过程、证据冲突的显式建模能力。

### 16.7 Conclusion / Future Work：它未来想做什么

作者未来方向包括：

1. 融合 text、images、network traffic 等多模态特征提高 APT 归因准确性和鲁棒性。
2. 探索更高效的特征抽取和数据增强模型以满足实时归因。
3. 构建覆盖更多 APT 类别的大规模数据集。

这对 Project05 有一个重要提醒：APT-ATT 未来会往 multimodal feature fusion 走，所以我们也不能把“多模态特征融合提高 actor classification accuracy”作为主线。我们的多模态如果要保留，只能作为 evidence source 类型或 action space 类型，而不是做分类器精度堆叠。

## 17. 红线矩阵

| 方向 | APT-ATT 是否覆盖 | Project05 处理方式 |
|---|---:|---|
| 异构 CTI 文本表示 | 是 | 不作为创新；最多作为 baseline 输入表征 |
| N-Gram / TF-IDF / chi-square 轻量表示 | 是 | 不碰 |
| CTGAN 缓解 APT 类别不平衡 | 是 | 不碰；专利权利要求避免 CTGAN / 生成少数类特征 |
| stacking ensemble actor classifier | 是 | 可作为闭集 actor baseline，不作为主贡献 |
| 多源安全证据融合 | 部分相关但未覆盖 | 不能写宽泛“多源融合归因”；应限定为 evidence state / acquisition planning |
| provenance/log 与 CTI 对齐 | 否 | 仍由 POIROT/DeepHunter/MEGR-APT/CLIProv/APT-CGLP 谱系覆盖 |
| 证据充分性 / 粒度门控 | 否 | Project05 保留空间 |
| 缺失证据需求生成 | 否 | 可以作为 planner explanation，但不能只产 list |
| 主动取证规划 | 否 | Project05 核心空间 |
| open-set / unknown / refusal | 否 | Project05 可用作差异点 |
| false flag / mimicry | 否 | 可作为后续扩展，不建议 MVP 强行覆盖 |

## 18. 如果作为 baseline，应该怎样用

APT-ATT 不适合作为 Project05 的主方法，但适合作为一个“会过度闭集归因”的 baseline：

```text
输入：被遮蔽后的 CTI 文本 / 当前可见情报片段
APT-ATT baseline：直接输出 12 类已知 APT 组织之一
Project05：先判断当前证据可支撑粒度，再决定输出 actor / campaign / technique / unknown，或规划下一步取证动作
```

可设计的对比指标：

| 指标 | APT-ATT 可能表现 | Project05 希望表现 |
|---|---|---|
| Actor accuracy | 完整 CTI 下较强 | 不以闭集 actor accuracy 为唯一目标 |
| Over-attribution rate | 证据缺失时可能偏高 | 降低 |
| Correct downgrade | 不支持 | 支持 |
| Cost to target granularity | 不支持 | 支持 |
| Next evidence ranking | 不支持 | 支持 |
| Evidence grounding | 弱，主要是特征词统计 | 强，回指 evidence state / alignment gap |

## 19. 对当前专利/论文题名的具体影响

不能写：

- “一种基于异构威胁情报表示与数据增强的 APT 归因方法”
- “一种基于 CTGAN 的 APT 归因样本不平衡处理方法”
- “一种基于多模型集成学习的 APT 组织归因方法”
- “一种融合多源特征提高 APT actor 分类准确率的方法”

可以写得更安全：

- “一种面向证据不完整场景的 APT 归因粒度判定与主动取证规划方法”
- “一种基于对齐证据状态的 APT 归因可支撑性评估与证据获取动作排序方法”
- “一种面向归因粒度提升的安全证据获取决策方法”

关键是：APT-ATT 追求的是“给定 CTI 文本后更准更快地分到已知组织”；Project05 追求的是“证据不完整时，当前能不能归到某一粒度，以及下一步取什么证据最值”。

## 20. 最终判断

APT-ATT 对旧的宽题是红色警报，对新主线是可控红线。它基本堵死了“异构 CTI 文本表示 + CTGAN + 集成学习归因分类”的路，但没有碰到 Project05 当前最核心的四件事：证据状态、归因粒度、取证动作价值、成本约束闭环。

因此，APT-ATT 不会推翻当前主线，反而帮助我们更清楚地把 Project05 从“又一个 actor classifier”里切出来。
