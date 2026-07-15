# Creating Integrated Evidence Graphs for Network Forensics

## 1. 基本信息

- 中文译名：为网络取证构建集成证据图
- 作者：Changwei Liu; Anoop Singhal; Duminda Wijesekera
- 年份：2013
- Venue：Advances in Digital Forensics IX, IFIP AICT 410, pp. 227-241
- DOI：https://doi.org/10.1007/978-3-642-41148-9_16
- NIST 页面：https://www.nist.gov/publications/creating-integrated-evidence-graphs-network-forensics
- 阅读日期：2026-07-14
- 阅读优先级：重点读（概率证据图历史红线）
- 所属主题：Probabilistic Evidence Graph / Attack Graph / Network Forensics

## 2. 一句话总结

本文给出在证据完整时直接合并多个概率证据图、在证据缺失/被篡改时借助 MulVAL attack graph 补全路径的两种算法，并用 primary/secondary/expert evidence 系数及概率并集公式更新主机和证据边概率；它占据“概率证据图 + 缺失证据 + 攻击路径”的宽泛表述，但概率来自专家类别、relevancy/importance 和图合并假设，不是数据驱动的 packet-log 跨源关系校准。

## 3. 研究问题

- 多个局部攻击/受害主机的 evidence graph 如何合并成全局网络取证图？
- 相同主机、相同漏洞、相似攻击路径合并时，节点与证据概率如何更新？
- 反取证造成证据边缺失时，能否借助全网 attack graph 找到可能的中间路径？

## 4. 核心贡献

1. 定义带节点/边属性和概率赋值的 evidence graph。
2. 提出不依赖 attack graph 的 DFS 合并算法，对相同主机/证据更新概率。
3. 提出借助 logical attack graph 的缺失证据图合并算法。
4. 讨论按相同配置/漏洞分组和按 reachability/CVSS 剪枝 attack graph 的复杂度控制。
5. 在文件服务器、数据库服务器和工作站组成的实验室场景中展示全局图合并。

## 5. 方法框架

### 输入

- 已由取证员构造的多个 sub-evidence graphs。
- 每条 evidence 的 impact weight、attack relevancy、host importance 与类别系数。
- 可选：由 MulVAL 和漏洞/网络配置产生的 probabilistic attack graph。

### 输出

- 合并后的 integrated probabilistic evidence graph。
- 更新后的 host/evidence probability。
- 在缺失证据时由 attack graph 补入的候选路径。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Evidence normalization | 把证据归一为 id/source/destination/content/time | 是来源保持 schema 的历史基础 |
| Direct merge | 合并相同节点/证据并更新概率 | 可作为简单概率图合并基线 |
| Attack-graph-assisted merge | 用潜在攻击路径填补缺失边 | 可作为缺失证据推理 baseline，但必须标为假设 |

### 方法流程

```text
局部概率证据图
  -> 证据完整：DFS 识别相同主机/边并直接合并
  -> 证据缺失：映射至裁剪后的 MulVAL attack graph 补候选路径
  -> 更新 host/evidence probability -> 全局集成证据图
```

## 6. 数据集与实验

- 实验为小型 lab network：Apache Tomcat file server、database server、workstations 等，攻击与漏洞路径由作者配置。
- 证据向量为 `(id, source, destination, content, timestamp)`，以时间依赖和网络配置构图。
- primary/secondary/expert knowledge 系数示例分别为 1、0.8、0.5。
- 两张局部图合并时，用 `p'=p1+p2-p1*p2` 更新相同主机或相同证据边概率。
- 缺失边实验人为移除一段证据，再从 MulVAL attack graph 的对应路径补回。
- 评价为算法与案例可行性，没有真实大规模数据、边级准确率、校准误差、统计检验或反取证强度变化实验。

## 7. 关键知识点

- 概率证据图在 2013 年已经显式区分 primary、secondary 和 expert hypothesis；“给证据加权”不是新贡献。
- 边概率由 `coefficient * impact * relevancy * importance` 形成，依赖专家量表，并未通过观测频率或独立 calibration set 学习。
- 合并公式隐含证据独立性/概率并集假设；相关证据重复计数会导致过度自信。
- 用 attack graph 补“缺失证据”只能产生结构假设，不能把潜在路径写成已观察事实。
- 本文节点是 host、边是预处理取证 evidence，不是 packet/log observation 对的关系分类。

## 8. 优点

- 很早就将证据不完整、被篡改和全局多攻击图合并作为核心问题。
- 区分观察证据与专家假设，并给出不同的权重系数。
- 明确讨论相同节点/证据合并和概率更新，而非只做图拼接。
- 给出两套伪代码与复杂度分析，适合作为历史 baseline。

## 9. 局限

- 证据图本身由调查员/规则预先构造，未解决原始 packet-log 记录如何生成候选边。
- 概率不是经过 Brier/ECE/reliability 验证的校准后验，且独立性假设未检验。
- attack graph 补边会把可行路径混入观察证据，若不分层可能制造虚假证据链。
- 场景规模小、漏洞与攻击已知，没有现代 APT、并发路径和异构遥测。
- 没有图边、链、意图、拒答和 claim replay 的定量评价。

## 10. 对我选题的启发

- 不能声称首次概率证据图、首次缺失证据推理或首次全局 evidence graph 合并。
- 我们应把 `observed`、`cross-source candidate`、`verified/rejected/conflict` 和 `knowledge-prior hypothesis` 分层，避免 attack graph/LLM 先验冒充证据。
- 跨源边后验必须在独立标注 packet-log pairs 上校准，并与专家权重/简单概率并集 baseline 比较。
- 缺失/冲突实验应报告 risk-coverage、safe abstention 和链置信传播，而不只是补出一条完整路径。

## 11. 可转化的研究问题

1. 数据驱动且可校准的跨源关系是否优于固定 primary/secondary 系数和独立性合并公式？
2. 如何把 attack graph/ATT&CK 先验作为 hypothesis edge，而不污染 observed evidence layer？
3. 在证据缺失或相互矛盾时，何时补候选路径，何时必须拒答？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| He et al. 2016 | 后者直接把 packet/log EV 构成 evidence graph；本文更早聚焦多个概率图合并和缺失边 |
| M-DUCAG | 两者均用概率攻击/因果图处理告警与路径不确定性，概率主要来自模型和专家参数 |
| MPCA | 后者从审计日志估计事件 confidence；仍未解决 packet-log relation calibration |
| BotFence | BotFence 显式做 host-packet join，但为确定性 5-tuple；本文提供旧概率合并基线 |
| Project03 支线 | 限制“概率证据图”宽泛主张，保留跨源边监督校准与证据层/假设层分离空间 |

## 13. 论文写作可引用句式

- 概率证据图早已用于合并多条攻击证据路径，并借助攻击图处理缺失证据；然而，既有概率通常源于预设证据类别和专家权重，不能等同于对原始异构遥测关联的经验校准。

## 14. 我的批注与疑问

- NIST/Crossref 的正式题名为 `Creating Integrated Evidence Graphs for Network Forensics`，获取到的作者稿首页题名为 `Merging Sub Evidence Graphs to an Integrated Evidence Graph`；引用采用正式出版题名。
- `p1+p2-p1*p2` 只有在特定独立性语义下合理；同一传感链产生的重复 evidence 不应直接这样增强置信。
- “缺失 evidence 由 attack graph path 补入”必须在我们的图中标作 hypothesis，不可计入 source-grounded coverage。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：4/5
- 实验可复现性：3/5
- 作为硕士论文基础价值：4.5/5
- 是否进入核心文献：是（概率证据图历史红线）
