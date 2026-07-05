# MM-AttacKG: A Multimodal Approach to Attack Graph Construction with Large Language Models

## 1. 基本信息

- 英文题名：MM-AttacKG: A Multimodal Approach to Attack Graph Construction with Large Language Models
- 中文译名：MM-AttacKG：基于大语言模型的多模态攻击图构建方法
- 作者：Yongheng Zhang; Xinyun Zhao; Yunshan Ma; Haokai Ma; Yingxiao Guan; Guozheng Yang; Yuliang Lu; Xiang Wang
- 年份：2025
- Venue：arXiv preprint
- DOI / arXiv / URL：https://arxiv.org/abs/2506.16968
- 本地 PDF：`../07-zotero-exports/pdfs_20260705/MM_AttacKG_2025.pdf`
- 本地文本：`../07-zotero-exports/pdf_text_20260705/MM_AttacKG_2025.txt`
- 阅读日期：2026-07-05
- 阅读优先级：重点
- 所属主题：Multimodal CTI / Attack Graph Construction / MLLM / Threat Image Parsing

## 2. 一句话总结

MM-AttacKG 在 AttacKG+ 的基础上把 CTI 报告中的图像、流程图、代码截图、表格、时间线等 threat images 纳入 attack graph construction，通过 brainstorming、extraction、verification、integration 多阶段 prompt 从图像中补充 entity、relation 和 technique；它进一步说明“多模态 CTI 构图”也已经有人做了，Project05 应避免把多模态构图作为主创新。

## 3. 研究问题

- 论文要解决什么？
  - 现有 attack graph construction 主要依赖 CTI 文本。
  - 但真实 CTI 报告包含大量图片：attack flow chart、code、table、screenshot、timeline 等。
  - 这些图像包含关键威胁信息，忽略它们会导致 attack graph 不完整。
- 为什么重要？
  - 图片可能包含文本中没有明确写出的攻击流程、实体关系和技术细节。
  - 多模态 CTI 可以提高攻击链理解的完整性。
- 和 Project05 的关系是什么？
  - 它把“CTI 多模态证据补全 attack graph”做成了一个完整框架。
  - Project05 如果要写“多源证据融合”，必须避开“图文 CTI 融合构图”这个已覆盖点。

## 4. 核心贡献

1. 首次系统探索 CTI image 在 attack graph construction 中的作用。
2. 提出 MM-AttacKG，多模态攻击图构建框架。
3. 使用 AttacKG+ 构建 text-based attack graph，再用 MLLM 解析 threat images。
4. 设计多阶段 prompt pipeline：
   - Brainstorming；
   - Extraction；
   - Verification；
   - Integration。
5. 构建 AG-LLM-mm 多模态 CTI 数据集。
6. 实验证明图像信息可以补充 entity、relation、technique，提高 attack graph 完整性。

## 5. 方法框架

### 输入

- CTI text；
- CTI images：
  - attack process；
  - flow chart；
  - code；
  - table；
  - screenshot；
  - file info；
  - timeline；
  - case display 等。
- text-based attack graph；
- image-aware context；
- global context。

### 输出

- image-enhanced multimodal attack graph；
- 新增 entity；
- 新增 relation；
- 新增 MITRE technique。

### 方法流程

```text
CTI text + CTI images
  -> AttacKG+ text-based attack graph
  -> image-aware/global context extraction
  -> brainstorming: generate image questions
  -> extraction: answer questions from image
  -> verification: filter questions and refine answers
  -> integration: add node / relation / technique
  -> multimodal attack graph
```

## 6. 数据集与实验

- 数据集：
  - AG-LLM-mm。
- 评估任务：
  - multimodal threat information extraction；
  - attack graph integration；
  - ablation study；
  - key module analysis。
- 对比：
  - text-based AttacKG+；
  - ICL；
  - CoT；
  - MM-AttacKG。
- 模型：
  - Qwen-VL-72B；
  - Qwen2.5-VL-32B；
  - Qwen2.5-VL-7B。

### 主要结果

MM-AttacKG 在 entity、relation、technique 三个维度优于简单 ICL / CoT 和 text-only 方法。消融表给出的完整模型表现：

| 任务 | Precision | Recall | F1 |
|---|---:|---:|---:|
| Entity | 0.7224 | 0.8280 | 0.7716 |
| Relation | 0.7460 | 0.8973 | 0.8147 |
| Technique | 0.5256 | 0.6232 | 0.5703 |

去掉 Image-Aware-Context 和 Global-Context 后，entity F1 从 0.7716 降到 0.7022，technique F1 从 0.5703 降到 0.5093。说明上下文支撑对图像威胁信息抽取有效。

## 7. 关键发现

- CTI image 可以显著补充 text-based attack graph 中缺失的实体、关系和 technique。
- 直接 ICL / CoT 不如专门设计的 brainstorming + verification pipeline。
- technique identification 仍然比 entity/relation extraction 更难。
- 作者在 Stuxnet case 中显示，融合图像后可新增 T1003、T1107、T1546 等 technique 相关信息。

## 8. 局限

- 仍然是 attack graph construction，不是 APT actor attribution。
- 图像解析和文本解析是分阶段完成，不是端到端跨模态联合推理。
- 没有处理多篇 threat reports 之间的冲突和证据不一致。
- 没有 confidence calibration、evidence sufficiency、refusal。
- 没有日志/provenance 证据。
- 数据集和代码声称 acceptance 后释放，复现性需后续确认。

## 9. 对 Project05 的影响

### 撞掉的方向

- “多模态 CTI + LLM 构建攻击图”已经被 MM-AttacKG 覆盖。
- “用 CTI 报告图像补全 TTP/attack graph”不能作为主创新。

### 留下的空间

1. 把 MM-AttacKG 的 multimodal attack graph 作为证据来源，而不是最终系统目标。
2. 研究图文证据不一致时如何加权和拒答。
3. 研究 attack graph evidence 是否足以支持 intent / actor attribution。
4. 与 provenance/log evidence 对齐，这是 MM-AttacKG 没有做的。
5. 把 image-derived evidence 纳入 evidence sufficiency scoring。

## 10. 可转化的选题问题

> 当 CTI 文本和图像可以共同构建 attack graph 后，如何判断这些多模态图证据对 actor attribution 的支持程度，并在图文证据冲突或不足时输出低置信/拒答？

## 11. 相关工作位置

| 相关文献 | 关系 |
|---|---|
| AttacKG+ | MM-AttacKG 直接以 AttacKG+ 作为 text-based graph constructor |
| AURA | AURA 做 RAG/multi-agent attribution，MM-AttacKG 做上游多模态 attack graph |
| APT-MMF | APT-MMF 是 report-IOC graph actor classifier，MM-AttacKG 是 graph construction |
| Project05 | MM-AttacKG 可作为 multimodal CTI evidence source |

