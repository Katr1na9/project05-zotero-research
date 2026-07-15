# An End-to-End Framework for Functionality-Embedded Provenance Graph Construction and Threat Interpretation

## 1. 基本信息

- 系统名：Auto-Prov
- 中文译名：面向功能语义增强的溯源图自动构建与威胁解释端到端框架
- 作者：Kushankur Ghosh; Mehar Klair; Kian Kyars; Euijin Choo; Jorg Sander
- 年份：2026
- Venue：arXiv preprint
- arXiv：https://arxiv.org/abs/2603.17100
- 代码：https://github.com/intelligenceafa-cloud/Auto-Prov
- 阅读日期：2026-07-13
- 阅读优先级：必读
- 所属主题：LLM Graph Construction / Heterogeneous Logs / Provenance / Attack Interpretation

## 2. 一句话总结

Auto-Prov 用流式聚类发现异构日志格式，以 GPT-4o 抽取候选 provenance 关系，再让较小 LLM 生成可扩展 regex 规则，并用 LLM/行为相似度补充节点功能标签、解释攻击图；它已直接占据“LLM 自动异构日志建图+攻击摘要”，但没有独立原始 PCAP 与日志的证据级双线融合，也未保留可核验的 packet/log 原始锚点。

## 3. 研究问题

- 如何摆脱为每类日志手写 regex 的 provenance graph 构建方式？
- 如何为图节点补充“实体功能”而不只使用名称或粗粒度类型？
- 如何把检测后的攻击图转化为可供分析员使用的自然语言摘要和 tactic 映射？
- 威胁模型信任日志基础设施，排除日志删除、篡改、检测器投毒与日志 prompt injection。

## 4. 核心贡献

1. RoBERTa embedding + farthest-point sampling + DBStream 在线发现日志类型。
2. GPT-4o Candidate Provenance Extractor 分步抽取实体、类型、方向、交互和时间。
3. LLaMA-3 将候选抽取蒸馏为可复用 regex，流式构建 provenance graph。
4. LLM 名称推断与一跳行为相似分类器共同生成节点 functionality label。
5. 在四种 provenance anomaly detector 上验证自动构图/功能标签的下游增益，并以 LLM 解释攻击图。

## 5. 方法框架

- 每个日志类型仅选代表样本交给 LLM，随后规则应用于全量日志。
- CPE 将复杂任务拆为 log summarization、entity type、interacting entity、edge direction/type 四个子任务；边方向运行 7 次多数投票。
- 单条 provenance record 为 `{Sid, Stype, Sname, Did, Dtype, Dname, Itype, time}`。
- Rule Generator 对每个字段生成 regex，规则库随新日志类型增量更新。
- Node Enricher 先根据名称/路径用 LLaMA-3 推断功能；无法识别时，按一跳行为签名最近邻继承功能标签。
- Graph Assistant 是检测后模块：将攻击图边按时间线性化，生成摘要并映射 APT tactics。

## 6. 数据集与实验

- THEIA：Ubuntu 12.04，结构化 JSON 系统事件，含 FBI、BED 两个攻击。
- ATLAS S1-S4：Windows 10 audit、Firefox 与 DNS logs，含 WEB、MAD、SPAM、PONY 四个攻击。
- 下游检测器：Flash、MAGIC、OCR-APT、Kairos。
- Auto-Prov 相对人工构图的平均 AUC-ROC 在 THEIA 提升 0.23、ATLAS 提升 0.15；AUC-PR 绝对值仍非常低。
- 组件消融表明自动图与 functionality label 均有贡献；仅给不完整基线图增加功能标签可能降低结果。
- GPT-4o 能跨 Windows audit、DNS、Firefox 产生关系；较小模型多停留在 audit 层，Qwen-2/DeepSeek-R1 对部分日志无法生成候选。
- Assistant 使用 3 个独立 LLM 投票判断 tactic reasoning，并以实体名投毒测试鲁棒性；多数攻击的 tactic correctness 高于 0.8。

## 7. 关键知识点

- LLM 直接逐日志推理不具备规模性，把少量高能力抽取蒸馏成确定性规则是更现实的构图路线。
- “图构建质量”不能只用解析 F1 衡量；Auto-Prov 用多个下游检测器的 AUC/ADP 间接评估结构价值。
- 结构缺失会放大语义标签噪声，因此先保证证据边，再做功能/意图语义增强。
- DNS/Firefox/audit 的跨日志关系是多源日志图，不自动等于原始 PCAP+日志的双侧证据图。

## 8. 优点

- 自动适应日志格式演化，减少手写解析器成本。
- 将强模型用于少量候选、弱模型生成规则，兼顾推理能力和吞吐量。
- 跨四个图检测器做下游验证，避免结果只绑定单个 detector。
- 明确发现小模型难以恢复跨日志关系，为模型选择和人工核验提供依据。

## 9. 局限

- 输入虽含 DNS/Firefox/网络连接日志，但没有独立原始 PCAP、packet/flow evidence 与日志双侧对齐。
- provenance record 无 source-record ID、packet index、hash、解析版本或多候选边状态，难以做原始证据回放。
- GPT-4o 抽取被当作候选真值再生成规则，可能把错误稳定地蒸馏进全量图。
- 图构建主要用下游检测效果间接评价，缺少节点/边级 precision、recall、direction error 和 cross-source link accuracy。
- Assistant 的正确性依赖 LLM-as-judge 与 ATT&CK tactic 描述，没有人类事件级证据审计或意图 ground truth。
- 排除日志篡改与 prompt injection，弱化了对抗性场景。

## 10. 对我选题的启发

- “LLM 自动建图”已经不能作为宽泛主创新，但可把 Auto-Prov 作为日志侧解析 baseline。
- Project03 的 TrafficObservation 可补上 Auto-Prov 未处理的原始 PCAP/flow 证据，并与 HFish/system logs 在统一 evidence record 中保留双向来源。
- 应把图构建评价提升为四层：抽取正确性、跨源边正确性、原始证据可回放性、下游链/意图增益。
- 对 LLM 产生的边采用 candidate/verified/rejected 状态，并用确定性 packet/log 查询器验证，避免错误蒸馏。

## 11. 可转化的研究问题

1. 如何将 LLM 候选关系与 PCAP/日志确定性证据核验组合，构建可审计双源图？
2. graph edge uncertainty 与 source completeness 能否预测攻击链/意图结论何时应拒答？
3. 在 parser drift、time drift、NAT 与共享实体下，双源边的校准准确率如何变化？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| UTLParser | 都处理异构日志构图；Auto-Prov 用 LLM 自动生成抽取规则，UTLParser 依赖 parser/POI |
| MOLE | 同属 LLM 生成 provenance 抽取模板；Auto-Prov 更完整并提供下游检测/解释评估 |
| SHIELD | 后者使用既有 provenance 图做 LLM 攻击链分析；Auto-Prov 更侧重图自动构建 |
| Project03 | TrafficObservation 与 HFish LogObservation 可补充原始双侧证据及可回放锚点 |

## 13. 论文写作可引用句式

- 最新工作已证明大模型可以从异构日志中归纳 provenance 抽取规则并改善下游检测，但跨源关系仍主要由模型候选与日志字段推断产生，缺乏面向原始网络包和日志记录的证据级验证与不确定性表达。

## 14. 我的批注与疑问

- ADP 关注“每个攻击至少命中一个节点”，不能代替完整攻击链覆盖。
- AUC-PR 接近零说明事件级误报仍很严峻，摘要质量不应掩盖这一点。
- LLM 多数投票只能降低随机方向翻转，不能发现系统性错误。
- 需要检查公开代码是否保留 log offset；论文方法描述未将其列入 provenance record。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4.5/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是（直接碰撞，主线必读）
