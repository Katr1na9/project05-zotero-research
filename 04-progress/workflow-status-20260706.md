# Project05 Workflow Status

日期：2026-07-06

## 当前所处阶段

当前处于：

> Stage 6：Collision Matrix 功能级撞题  
> 正在向 Stage 7：Patent Due Diligence 过渡，但尚未通过 G4。

## 已完成

- 主线文献第一轮沉淀。
- 2026 H1 补读。
- TAA-EPLMR / LLMAPT 已纳入精读。
- 二次深度撞题扫描。
- 新增 13 份精读/风险精读笔记。
- `patent-claims-draft-v0.1` 已标记为偏宽草案。

## 当前红线

以下方向不得作为 Project05 主创新：

1. 多源证据融合 APT 归因。
2. LLM-based APT attribution framework。
3. KG/RAG/GraphRAG 归因。
4. IOC/KG/HIN/GNN/RGCN 图归因。
5. TTP 相似度/加权归因。
6. open-set / abstention 单点创新。
7. provenance graph + LLM 攻击摘要。
8. confidence score / information gap / hunting recommendation。

## 当前白名单

仍可推进的组合：

```text
证据充分性画像
  + 归因粒度门控
  + 可拒答解释
  + 缺失证据生成
  + LLM 受控表达
```

必须注意：每个单点都不新，只有组合成“归因控制层”才可能保留空间。

## 未通过的 Gate

### G4：专利权利要求可防守性

未通过原因：

- v0.1 题名仍含“多源安全证据自适应融合”，太宽；
- 独立权利要求仍容易被 US12368730B2、TAA-EPLMR、TRAIL、APT-scope、HG-CTA、AARGS 等压缩；
- 需要把“多源融合”降级为输入条件。

### G5：实验可执行性

未通过原因：

- 数据集未最终确定；
- baseline 未最终确定；
- 缺失证据生成的评价方式未确定；
- APT-ATT、APTChaser、GAPT、AARGS 全文仍需补齐。

## 下一步任务

1. 导入 `07-zotero-exports/zotero-import-candidates-20260706-deep-scan.ris`。
2. 获取 APT-ATT、APTChaser、GAPT、AARGS 正文。
3. 把摘要级风险精读升级为全文精读。
4. 重写 `patent-claims-draft-v0.2`。
5. 起草 `experiment-plan-v0.1`。

