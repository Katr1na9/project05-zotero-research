# CN119766567B：基于 TTP 描述相似度匹配的威胁归因方法

## 基本信息

- 类型：中文专利
- 专利号：CN119766567B
- 题名线索：基于 TTP 描述相似度匹配的威胁归因方法
- 来源：https://patents.google.com/patent/CN119766567B/zh
- 当前状态：纳入 Project05 二次深扫高风险材料。

## 它在做什么

该专利围绕 TTP 描述进行相似度匹配，并用于威胁归因。其核心链路可以概括为：

```text
TTP 描述
  -> 文本/语义相似度匹配
  -> 威胁行为体或攻击活动归因
```

## 对 Project05 的撞题影响

它会压缩：

1. 基于 TTP 描述相似度的威胁归因。
2. 基于 ATT&CK technique/procedure 文本匹配的 actor attribution。
3. 使用语义匹配把待分析行为映射到已知组织 TTP profile。

Project05 不能把“更好地匹配 TTP 描述以完成归因”作为创新点。

## 与 Project05 当前方向的区别

Project05 可以继续使用 TTP，但必须把 TTP 放在证据强度较低、可共享、可模仿的证据通道中，而不是默认高权重归因依据。

更安全的表述是：

- TTP 证据用于支持 technique/intent 层；
- 只有当 TTP 与高区分度样本、基础设施、时间线或 provenance 证据一致时，才允许升级到 actor-level；
- TTP 共享或可模仿时触发降级或拒答。

## 风险等级

橙色。

它不一定堵死 Project05，但明确堵住“TTP 相似度归因”这条路。

