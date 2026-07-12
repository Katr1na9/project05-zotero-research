# 科研决策日志

## 目的

记录影响研究边界、数据、评价和下一阶段 Gate 的冻结决策。这里记录“为什么这样做”，不替代实验协议、结果文件或进度看板。

### 2026-07-12：盲标范围升级为 C07-C11 v0.2，并设置来源访问 Gate

- 决策：旧 `c07_c10_v0.1` 保留为历史；新建 `c07_c11_v0.2`，不复用 blind ID，不覆盖任何潜在人工输入。
- 范围：27 claim、27 public intent、60 granularity states，共 114 items；C11 作为一个仿真案例计入，但不与自然事件等同。
- 分析顺序：A/B 独立一致性 → 第三人只裁决分歧 → 管理员隔离比较最终人工标签与 compiled intended/G0-G3。
- 来源决策：项目 notes 不是独立证据。C07-C10 的 19 条精确记录恢复前，完整 Claim 任务保持 blocked；C11 的 8 条可回查记录不替代其余来源。
- 通过标准：粒度 proxy 与最终人工标签 weighted kappa 至少 0.70，且 compiled over-granularity rate 不高于 0.10；未通过则收缩主张或调整规则，不删困难 item。
- 当前状态：所有模板为空，`awaiting_annotations`；不使用 Codex、LLM 或代码标签代填。
- 关联文件：`08-writing/human-annotation-evaluation-protocol-v0.2-20260712.md`、`09-experiments/annotation/c07_c11_v0.2/`。

### 2026-07-12：将 OTRF APT29 Day 1 定为 C11 补充案例

- 决策：使用 OTRF APT29 Day 1 Host JSONL 作为 C11 主来源，以 Zeek 作为不同 replay 的场景级诊断；不下载 PCAP 补救预注册节点。
- 理由：它提供相对 DARPA TC/OpTC 不同的 Windows JSONL、多 provider 数据封装，体量可控，并允许在固定来源上检验多 claim AND 语义。
- 冻结边界：APT29 是 adversary-emulation 标签，不是待预测 actor；C11 是一个独立仿真攻击链，不是自然运营事件。
- 结果：D1-D5 全部通过；5 个关键节点中 4 个通过，8 条 event-backed claims；N01 自然缺口使 G3→G2。
- 方法判断：AND 为主分析，OR 仅作敏感性；M2 在 C11 上不具成本优势，因此只保留为透明冻结部署策略，不升级性能主张。
- 汇总规则：C11 单独报告，不与 C07-C10 的 G3 成本求总均值，不把 45 个重复条件计为独立攻击。
- 下一 Gate：双人盲标优先；之后才考虑自然发生或更接近运营现场的第三方 engagement、官方 AFA 映射和论文 v0.5 合并。
- 关联文件：`08-writing/third-data-family-screening-v0.1-20260712.md`、`08-writing/c11-otrf-apt29-day1-results-v0.1-20260712.md`。
