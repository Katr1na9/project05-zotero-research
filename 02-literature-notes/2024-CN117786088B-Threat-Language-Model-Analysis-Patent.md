# CN117786088B：威胁情报分析方法、装置、设备、介质及程序产品

## 基本信息

- 类型：中文专利
- 专利号：CN117786088B
- 题名：威胁情报分析方法、装置、设备、介质及程序产品
- 来源：https://patents.google.com/patent/CN117786088B/zh
- 当前状态：纳入 Project05 二次深扫高风险材料。

## 它在做什么

该专利并非只做传统威胁情报检索，而是涉及：

```text
威胁情报
  -> 大语言模型/语言模型分析
  -> 威胁知识抽取或结构化
  -> 威胁情报分析结果
```

它会与 Project05 中“LLM 读取 CTI、抽取证据、构建证据账本”的底层能力发生接近。

## 对 Project05 的撞题影响

该专利会压缩：

1. 使用大语言模型抽取威胁情报要素。
2. 使用语言模型进行威胁情报结构化分析。
3. 把威胁情报文本转成可供分析的实体、关系或图。

Project05 不能把“LLM 抽取 CTI 证据并结构化”写成独立创新。

## 与 Project05 当前方向的区别

Project05 应把 LLM CTI 抽取能力降级为前置模块，真正的核心放在：

- evidence sufficiency；
- attribution granularity gate；
- refusal / abstention；
- missing evidence request；
- grounded explanation verification。

换言之，Project05 不是“LLM 威胁情报分析系统”，而是“威胁归因证据是否足以支持某层结论的控制系统”。

## 风险等级

橙色到红色。

该专利提醒 Project05 后续说明书中不能把 LLM 抽取、LLM 分析、LLM 生成威胁情报结果写得太宽。

