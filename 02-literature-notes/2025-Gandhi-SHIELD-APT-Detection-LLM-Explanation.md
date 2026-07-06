# SHIELD: APT Detection and Intelligent Explanation Using LLM

## 基本信息

- 作者：Parth Atulbhai Gandhi, Prasanna N. Wudali, Yonatan Amaru, Yuval Elovici, Asaf Shabtai
- 年份：2025
- arXiv：https://arxiv.org/abs/2502.02342
- HTML：https://arxiv.org/html/2502.02342v1
- 当前状态：纳入 Project05 二次深扫高风险补充材料。

## 它在研究什么

SHIELD 面向 APT detection and investigation，不是 actor attribution。它把统计异常检测、provenance graph 分析和 LLM contextual analysis 结合起来，用于降低误报、生成可解释攻击描述和攻击摘要。

## 方法核心

SHIELD 的流程包括：

```text
system logs
  -> statistical anomaly detection
  -> provenance graph construction
  -> benign activity pruning
  -> suspicious event community detection
  -> LLM multi-stage reasoning
  -> confidence score
  -> temporal correlation engine
  -> interpretable attack summary / kill-chain mapping
```

关键机制包括：

- deviation analyzer：识别异常事件；
- graph analyzer：构造、剪枝和聚类 provenance graph；
- LLM analyzer：对可疑社区做多阶段 CoT reasoning，输出攻击判断、置信度和 kill-chain 映射；
- temporal correlation engine：跨时间窗口维护攻击集，并使用 confidence decay / reinforcement 机制动态更新置信度。

## 对 Project05 的撞题影响

SHIELD 压缩以下空间：

1. provenance graph + LLM 分析；
2. LLM 对 APT 攻击过程做可解释摘要；
3. LLM 对可疑日志/图社区做多阶段推理；
4. 动态 confidence scoring；
5. confidence threshold 和队列优先级；
6. 攻击阶段 / kill-chain 映射。

Project05 如果引入日志/provenance evidence，不能把“LLM 解释日志证据并输出攻击摘要”作为核心创新。

## 与 Project05 当前方向的区别

SHIELD 主要解决 detection and investigation，不解决 actor attribution 的可判定性问题。Project05 可避让空间是：

- 不做 APT detection；
- 不把日志图解释当核心；
- 把 provenance 作为证据通道之一；
- 判断这些证据是否足以把结论从 attack investigation 升级到 actor/campaign attribution；
- 当日志证据只支持攻击阶段或 intent 时，禁止输出 actor-level 归因；
- 输出缺失证据采集建议。

## 精读结论

SHIELD 让 Project05 的“LLM 受控解释”边界更窄：不能只写“LLM 解释攻击链/日志图”，必须写“LLM 解释归因门控结果和缺失证据原因”。否则会与 SHIELD、AARGS、TAA-EPLMR 等工作形成连续撞题。

