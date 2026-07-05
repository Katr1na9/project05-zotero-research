# 2026 H1 补读后的 Project05 选题决策

## 当前判断

2026 年上半年不是空白，而且推进得很快：

- TTPrint 已经做了 evidence-grounded TTP extraction；
- CTI-Thinker 已经做了 LLM + CTI KG + GraphRAG attack reasoning；
- Minerva 已经做了 CTI LLM 的可验证奖励/RLVR；
- OpenSec 已经把安全 agent 评价推进到 evidence-gated action；
- High-Precision APT Malware Attribution 已经做了 APT malware attribution 的 open-set / OOS abstention；
- Synthetic APTs 直接质疑 TTP-based attribution；
- ARCANE 说明跨 campaign 累积证据仍可能低置信。

所以，Project05 不能再把创新写成宽泛的：

> 多源证据融合 + LLM 辅助 APT 归因解释

这个题目会被 AURA、CTI-Thinker、APT-MMF、TAA-EPLMR 和一批 2026 工作压得很紧。

## 推荐方向

建议收窄为：

> 一种面向证据不完整与开放集行为体场景的证据充分性感知、分层降级与可拒答大语言模型辅助 APT 归因解释方法

如果想更像专利题名，可以写成：

> 一种基于证据可用性画像和充分性门控的大语言模型辅助 APT 分层归因解释方法

## 关键技术方案

系统不要默认输出 actor，而是按以下流程：

```text

输入案件证据
  -> 证据可用性画像
  -> 多通道证据结构化
  -> 候选 actor/campaign/intent/technique 生成
  -> 证据充分性评分
  -> 分层门控
      sufficient for actor    -> actor attribution + explanation
      sufficient for campaign -> campaign-level hypothesis
      sufficient for intent   -> intent-level explanation
      only TTP-level          -> technique-level summary
      insufficient/conflict/OOS -> abstain/refusal
  -> LLM 生成证据引用、缺失证据说明、补充取证建议

```

## 专利可保护点

1. 证据可用性画像：识别当前案件有/缺哪些证据类型，如 CTI sentence、IOC、malware feature、infrastructure、timeline、provenance path。
2. 证据充分性门控：根据证据数量、类型、区分度、可靠性、冲突程度和时效性，判断是否允许输出 actor。
3. 自适应归因粒度：证据不足时，从 actor 降级到 campaign、intent 或 technique。
4. 可拒答机制：unknown actor、OOS、false flag、TTP mimicry、候选 actor 过近时，拒绝高置信归因。
5. LLM 解释模板：输出支持证据、反证/冲突证据、缺失证据和下一步取证建议。

## 论文实验建议

实验不能只比较 actor accuracy。建议指标：

- actor accuracy / top-k accuracy；
- selective accuracy；
- coverage；
- over-attribution rate；
- correct abstention rate；
- out-of-scope rejection rate；
- confidence calibration / ECE / Brier score；
- evidence citation precision；
- missing-evidence diagnosis accuracy。

需要构造的测试场景：

1. 完整证据；
2. 缺少 malware / infrastructure / timeline / provenance 中的一类或多类；
3. known actor 间 TTP 高重叠；
4. unknown actor / OOS；
5. false flag / TTP mimicry；
6. 证据冲突。

## LLM 在其中的作用

LLM 不应被设计为唯一归因裁判。更稳的角色是：

1. 读 CTI 文本，抽取候选行为、TTP、IOC、时间线；
2. 把异构证据翻译成可比较的自然语言 evidence cards；
3. 对候选结论做证据充分性解释；
4. 在拒答时说明为什么不能归因；
5. 给出补充取证建议；
6. 把结构化评分结果转化为分析师可读的报告。

这样才能避开 “LLM 幻觉式归因” 的风险，也能回应 AURA 没有 evidence weighting / confidence scoring 的缺口。

