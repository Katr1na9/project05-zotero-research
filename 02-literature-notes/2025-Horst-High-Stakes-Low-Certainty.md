# High Stakes, Low Certainty: Evaluating the Efficacy of High-Level Indicators of Compromise in Ransomware Attribution

## 1. 基本信息

- 英文题名：High Stakes, Low Certainty: Evaluating the Efficacy of High-Level Indicators of Compromise in Ransomware Attribution
- 中文译名：高风险、低确定性：评估高层失陷指标在勒索软件归因中的有效性
- 作者：Max van der Horst; Ricky Kho; Olga Gadyatskaya; Michel Mollema; Michel van Eeten; Yury Zhauniarovich
- 年份：2025
- Venue：USENIX Security 2025
- DOI / arXiv / URL：https://www.usenix.org/conference/usenixsecurity25/presentation/van-der-horst；补充材料 DOI: 10.5281/zenodo.14732550
- Zotero key：待核验
- 阅读日期：2026-07-04
- 阅读优先级：必读
- 所属主题：Trustworthy Attribution / Ransomware Attribution / Evidence Reliability / Sanction Screening

## 2. 一句话总结

这篇论文用 20 位专家访谈和 27 份真实勒索软件事件报告，实证检验高层 IoC/TTP 是否真的适合勒索软件归因。结论很锋利：TTP 这类高层指标太泛、组内不稳定、组间重叠明显，而从业者实际更依赖赎金信、通信渠道、泄露站点等低层或勒索软件特定指标；但这些低层指标又高度易变，因此勒索软件归因和制裁筛查天然处在“高风险、低确定性”的状态。

## 3. 研究问题

- 论文要解决的核心问题是什么？
  - 勒索软件受害者在支付赎金前需要做 sanction screening，确认收款方是否为受制裁实体。
  - 这个过程依赖 cyber threat actor attribution，但归因证据是否足够可靠并不清楚。
  - 传统 Pyramid of Pain / Q-model 通常认为 TTP 等高层 IoC 比 IP、hash、域名等低层 IoC 更稳定、更有归因价值；本文检验这个假设在勒索软件场景是否成立。
- 这个问题为什么重要？
  - 勒索软件归因错误会带来法律、财务和声誉风险。
  - Ransomware-as-a-Service, rebranding, affiliate turnover 和 false flag 会削弱“某组有稳定 TTP 签名”的假设。
  - 如果制裁筛查要求高确定性，而证据本身无法支撑高确定性，受害组织会被夹在业务恢复、法律风险和证据不充分之间。
- 之前方法哪里不够？
  - 许多归因框架默认高层 IoC 更有价值，但缺少勒索软件实证验证。
  - TTP 抽取/ATT&CK 映射研究通常把 TTP 当作上层推理的稳定输入，却较少量化其归因区分度。
  - 自动化归因方法往往给出 actor label 或 score，但没有充分处理证据含糊、证据重叠和法律确定性要求。
- 它和威胁归因、攻击链、意图识别、CTI、ATT&CK、RAG、Agent 的关系是什么？
  - 与威胁归因：直接研究 ransomware threat actor attribution。
  - 与 ATT&CK/TTP：用 MITRE ATT&CK Enterprise v14.1 将事件报告映射为 tactic/technique/sub-technique 组合，并分析 TTP 相似度。
  - 与可信归因：说明 TTP 证据不能直接等价为高置信归因证据。
  - 与 LLM/RAG：后续 LLM/RAG 系统不能只检索 TTP 后生成归因解释，必须判断证据区分度、不确定性和拒答条件。

## 4. 核心贡献

1. 任务贡献：提出并实证分析勒索软件归因服务于 sanction screening 时的证据可靠性问题。
2. 数据贡献：结合 20 位专家半结构化访谈和 27 份真实勒索软件事件报告，另参考 13 份 CISA #StopRansomware 报告。
3. 方法贡献：将事件报告映射为 ATT&CK tactic/technique/sub-technique 组合，用 overlap similarity、containment similarity 和 silhouette score 分析 TTP 区分度。
4. 经验贡献：挑战“高层 IoC 更适合归因”的通用假设，指出勒索软件场景中 TTP 过于泛化且跨组重叠明显。
5. 实务贡献：提出改进数据共享、标准化报告、归因框架和制裁违规政策的建议。
6. 理论贡献：扩展 Pyramid of Pain，使其考虑勒索软件特定 IoC，如 ransom note、communication channel、leak site 等。

## 5. 方法框架

### 输入

- 数据类型：
  - 专家访谈文本；
  - 勒索软件事件调查报告；
  - CISA #StopRansomware 报告；
  - MITRE ATT&CK Enterprise v14.1。
- 输入格式：
  - 半结构化访谈录音与转写；
  - 事件报告中的 root cause analysis、ransomware strain、TTP、工具和 IoC；
  - CISA 报告中聚合的 ransomware actor TTP。
- 先验知识：
  - Pyramid of Pain；
  - Q-model；
  - MITRE ATT&CK；
  - OFAC / cyber sanctions / sanction screening 背景。

### 输出

- 预测结果：本文不训练分类器，输出实证发现。
- 图结构：无正式图结构。
- 标签：
  - RTA 名称；
  - ATT&CK tactic/technique/sub-technique 组合。
- 报告：
  - 勒索软件归因流程；
  - IoC 使用方式；
  - TTP 相似度和聚类分析；
  - sanction screening 风险。
- 证据链：
  - 访谈主题；
  - 事件报告中提取的 TTP；
  - RTA 名称映射；
  - TTP overlap / containment / silhouette 指标。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Expert Interview Study | 了解从业者如何做 ransomware attribution 与 sanction screening | 可作为论文动机：真实归因流程依赖多证据且存在不确定性 |
| Thematic Analysis | 对访谈转写做编码和主题归纳 | 可借鉴到后续人工访谈或专家评审设计 |
| Incident Report Analysis | 从真实勒索软件报告中抽取 RTA 与 ATT&CK TTP | 可作为 TTP 区分度评估方法 |
| RTA Mapping | 对齐公司报告和 CISA 报告中的 actor 命名 | 提醒 actor alias / rebranding 是归因评价难点 |
| TTP Binary Vectorization | 将每份报告编码为 887 维 ATT&CK tactic/technique/sub-technique 二值向量 | 可用于后续 TTP similarity、actor profile 和 attribution baseline |
| Overlap / Containment Similarity | 衡量同组和跨组 TTP 重叠 | 比单纯 Jaccard 更适合 TTP 集大小不同的报告 |
| Silhouette Score | 检查 TTP 是否能形成 actor 可分簇 | 可用于检验 TTP 是否足以支撑 actor attribution |

### 方法流程

```text
专家访谈
  -> 转写
  -> 主题分析
  -> 从业者归因流程与 IoC 使用偏好

公司事件报告 + CISA 报告
  -> RTA 名称映射
  -> ATT&CK tactic/technique/sub-technique 提取
  -> 887 维 TTP 二值向量
  -> overlap / containment / silhouette 分析
  -> 判断 TTP 对勒索软件归因的区分度

访谈结果 + 报告分析
  -> 综合判断高层 IoC 是否可靠
  -> sanction screening 风险与改进建议
```

## 6. 数据集与实验

- 数据集：
  - 20 位专家访谈：15 位来自合作安全公司，5 位来自其他类似公司。
  - 27 份可分析的真实勒索软件事件报告。
  - 13 份 CISA #StopRansomware 报告，均为 2023 年发布。
- 数据规模：
  - 访谈对象覆盖数字取证、CTI、逆向工程、安全运营和管理岗位。
  - 公司报告原始集合中有 12 份因日志不完整、攻击者删除日志或无法重构 kill chain 被排除。
  - 事件报告中的 RTA 包括 Blackcat、Lockbit、Play、Black Basta、Royal、Phobos 等。
  - 每份报告被编码为 887 维 tactic/technique/sub-technique 组合二值向量。
- 标注方式：
  - 访谈使用 thematic analysis，两名编码者，Krippendorff's Alpha 为 0.872。
  - 事件报告由一名研究者手工提取 RTA、ransomware strain 和 TTP；受保密限制，不能独立复核。
  - 公司 RTA 名称与 CISA RTA 名称通过人工调研映射，例如 Blackcat -> ALPHV，Black Basta -> Black Basta，BlackSuit -> Royal。
- Baseline：
  - 本文不是模型评测，无传统 baseline。
  - 隐含对照是 Pyramid of Pain / Q-model 中对高层 IoC 归因价值的默认假设。
- 指标：
  - overlap similarity；
  - containment similarity；
  - silhouette score；
  - 同一 RTA 内部 TTP overlap；
  - 不同 RTA 之间 TTP overlap。
- 主要结果：
  - 从业者实际主要依赖低层或勒索软件特定指标：ransom note、communication channel、leak site、network IoC 等。
  - TTP 被认为适合画像和概念化行为，但不足以做高置信、细粒度的勒索软件 actor 归因。
  - 同一 RTA 的事件报告平均 TTP overlap 只有 0.37，说明同组内部 TTP 也不稳定。
  - 不同 RTA 的聚合 TTP 平均 overlap 为 0.21，说明跨组也存在明显共享。
  - silhouette score 为负值，欧氏距离约 -0.0864，余弦距离约 -0.0873，说明按 TTP 很难形成清晰 actor cluster。
  - Rebranding、RaaS affiliate、共享工具链和可能的 false flag 会进一步削弱 TTP 的归因区分度。
- 消融实验：
  - 无机器学习消融；主要是不同相似度指标和报告来源的比较。
- Case study：
  - CISA 和公司报告中的 actor 命名需要映射，显示 rebranding 与 alias 本身就是归因障碍。
  - Phobos / Carver Phobos / 8Base、Blackcat / ALPHV、BlackSuit / Royal 等映射体现了勒索软件生态的名称混乱和品牌迁移。

## 7. 关键知识点

### 概念

- **RTA**：Ransomware Threat Actor，勒索软件威胁行为体。
- **Sanction screening**：制裁筛查，判断赎金支付对象是否为受制裁实体。
- **High-level IoC**：高层失陷指标，如 TTP、行为模式、modus operandi。
- **Low-level IoC**：低层失陷指标，如 hash、IP、域名、注册表键、具体通信渠道。
- **Ransomware-specific IoC**：勒索软件特定指标，如 ransom note、leak site、payment/communication channel。
- **RaaS**：Ransomware-as-a-Service，勒索软件即服务，会导致品牌、工具、affiliate 和行为模式分离。
- **Rebranding**：勒索软件组织更名或品牌迁移，削弱历史 actor profile 的连续性。
- **Relative attribution**：相对归因，将事件关联到历史活动簇，而不必声称识别真实幕后主体。
- **Absolute attribution**：绝对归因，声称识别实际 actor 或实体，风险更高。

### 技术路线

- 本文不是要替代 TTP 抽取，而是提醒：TTP 抽取后的 actor attribution 仍然很难。
- 它把“证据可靠性”从抽象口号落到可检验问题：
  - 同一个 actor 的 TTP 是否稳定？
  - 不同 actor 的 TTP 是否可分？
  - 报告来源和命名是否一致？
  - legal certainty 要求和 technical evidence uncertainty 是否匹配？
- 对 LLM/RAG 威胁归因的关键启示：
  - 不能把 ATT&CK/TTP 命中当作高置信 actor 归因依据。
  - 需要 evidence sufficiency、actor alias/rebranding 处理、confidence calibration 和 refusal。
  - 对勒索软件归因尤其要区分 group brand、affiliate、tooling、payment infrastructure 和 actual sanctioned entity。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| ransomware threat actor | 勒索软件威胁行为体 | RTA |
| sanction screening | 制裁筛查 | 支付赎金前的合规检查 |
| high-level IoC | 高层失陷指标 | TTP / 行为模式 |
| low-level IoC | 低层失陷指标 | hash / IP / 域名等 |
| ransom note | 赎金信 | 勒索软件特定 IoC |
| leak site | 泄露站点 | 勒索组织公开施压渠道 |
| communication channel | 通信渠道 | 与攻击者联系的渠道 |
| rebranding | 更名 / 品牌迁移 | 勒索团伙常见 |
| Ransomware-as-a-Service | 勒索软件即服务 | RaaS |
| relative attribution | 相对归因 | 关联到历史活动簇 |
| absolute attribution | 绝对归因 | 识别实际行为体 |
| overlap similarity | 重叠相似度 | 适合比较不同大小 TTP 集 |
| containment similarity | 包含相似度 | 衡量一个集合被另一个集合覆盖 |

## 8. 优点

- 直接研究真实勒索软件归因和 sanction screening，比纯 benchmark 更贴近高风险实务。
- 用专家访谈和事件报告分析互相验证，不只停留在理论批判。
- 明确挑战“高层 IoC/TTP 天然更可靠”的常识，对当前 TTP/RAG 研究很有纠偏价值。
- 给出了可复用的 TTP 区分度评估方式：overlap、containment、silhouette。
- 对 false attribution、legal ambiguity、confidence level 和 intelligence pollution 的讨论很适合支撑可信归因选题。

## 9. 局限

- 数据主要来自欧洲安全公司和相关从业者，地域和行业覆盖可能有限。
- 27 份可分析事件报告规模不大，且 11 个 actor 只出现一次。
- 事件报告中 TTP 提取受保密限制，只能由一名研究者完成，无法独立复核。
- 公司报告和 CISA 报告的粒度、目的、数据来源不同，比较时存在不可避免偏差。
- 本文聚焦勒索软件，不一定能直接推广到国家级 APT、供应链攻击或非勒索场景。
- 它批判 TTP 归因价值，但没有提出自动化归因模型或新的概率融合方法。

## 10. 对我选题的启发

- 可以直接借鉴：
  - 用 TTP overlap / containment / silhouette 检验 TTP 对 actor attribution 的区分度。
  - 在威胁归因输出中区分 relative attribution 与 absolute attribution。
  - 把 legal / operational risk 纳入可信归因动机，而不是只谈模型幻觉。
  - 将 ransom note、leak site、communication channel 作为 ransomware-specific evidence。
- 可以改进：
  - 将 Opinion Pools 的 attributor 权重与证据类型可靠性结合：TTP attributor 不应默认高权重。
  - 用 LLM/RAG 对证据进行解释时，增加 evidence sufficiency gate。
  - 对 actor alias、rebranding、RaaS affiliate 做专门建模。
  - 将 provenance evidence 用作本地行为证据，但仍不能直接跳到 actor 结论。
- 可以作为 baseline：
  - TTP-only attribution baseline；
  - low-level IoC-only baseline；
  - TTP + low-level IoC + provenance evidence 的多证据融合 baseline；
  - monolithic LLM attribution vs modular evidence attribution。
- 可以用于研究动机：
  - 高层 TTP 证据并非天然可靠，尤其在 RaaS 生态下存在组内不稳定和组间重叠。
  - 归因系统必须表达不确定性和证据不足，不能只给单一 actor label。
  - 制裁筛查等高风险场景要求可解释、可审计、可拒答的归因系统。
- 可以用于实验设计：
  - 增加 false attribution / rebranding / alias confusion 样本。
  - 报告 top-k actor candidates、confidence、evidence sources 和 abstention。
  - 用 TTP cluster separability 作为某类证据能否用于归因的先验检查。
  - 比较不同证据源对 calibration 和 top-k attribution 的贡献。

## 11. 可转化的研究问题

1. 在 RaaS 和 rebranding 场景下，如何构建 uncertainty-aware ransomware attribution，使系统输出 actor candidate distribution 而不是硬归因？
2. TTP overlap / containment / silhouette 能否作为证据可靠性先验，用于调整 Opinion Pools 中 TTP attributor 的权重？
3. 能否将 ransom note、leak site、communication channel、ATT&CK TTP 和 provenance InfoPath 分别建模为 attributor，并输出 calibrated actor PMF？
4. 当 TTP 证据组内不稳定、组间重叠时，LLM/RAG 如何可靠拒答并指出缺失证据？
5. 能否构建一个小规模 evidence sufficiency benchmark：给定 CTI + IoC + provenance evidence，判断是否足以支持 relative attribution / absolute attribution / sanction screening？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| A survey of cyber threat attribution | 综述提供归因层级和挑战，本文提供勒索软件场景的实证证据可靠性 |
| TTPXHunter | TTPXHunter 抽取 TTP，本文提醒 TTP 抽取不等于 actor attribution |
| TechniqueRAG | TechniqueRAG 做 ATT&CK 标注，本文说明 ATT&CK 标注后的归因区分度需要额外验证 |
| CTIBench | CTIBench 的 CTI-TAA 可测 actor attribution，本文提示应加入 evidence sufficiency 和 rebranding/alias 处理 |
| LLMs are Unreliable for CTI | LLM unreliable 说明模型不可靠，本文说明归因证据本身也不可靠 |
| Opinion Pools | Opinion Pools 提供多证据概率融合架构，本文提供证据权重和可靠性判断的现实依据 |
| Beyond RAG for CTI | Beyond RAG 讨论检索结构性幻觉，本文讨论 TTP/IoC 证据不能支撑高确定性归因 |
| LocalIntel | LocalIntel 强调本地上下文，本文说明 ransomware attribution 还需要具体低层和组织/案件证据 |
| Kairos / DEPCOMM | 二者提供日志侧行为证据，但本文提醒即使有行为/TTP，也仍要区分 evidence of attack 与 evidence of actor |

## 13. 论文写作可引用句式

- 高层 TTP 指标虽然比低层 IoC 更难被攻击者随意改变，但在勒索软件生态中并不必然具备足够的 actor 区分度。
- 勒索软件归因需要同时面对低层指标易变、高层指标泛化、RaaS affiliate 共享工具链和组织更名带来的不确定性。
- 对高风险 sanction screening 场景而言，归因系统不仅要输出候选行为体，还必须说明证据充分性、置信度和可能的误归因风险。
- TTP 抽取和 ATT&CK 标注只能提供攻击行为语义层，不应被直接等同为威胁行为体级归因证据。

## 14. 我的批注与疑问

- 这篇补齐了 Opinion Pools 之后最关键的一环：不是所有 attributor 都同等可靠，尤其 TTP attributor 可能在 ransomware 场景中区分度不足。
- 它把我的方向从“证据越多越好”推进到“证据是否足以支撑某一级别的归因”。
- 后续如果做 `CTI + provenance evidence -> actor PMF`，必须把输出分成：
  - no attribution / insufficient evidence；
  - relative attribution to known cluster；
  - candidate actor PMF；
  - high-risk sanction screening warning。
- 需要继续查：是否已有论文把 TTP separability、evidence sufficiency、opinion pool weights 和 LLM/RAG 结合起来。
- 如果未来使用 ATT&CK/TTP 数据做实验，要避免把 `technique overlap` 误当作 `actor identity`。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：4.5/5
- 实验可复现性：3.5/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是
