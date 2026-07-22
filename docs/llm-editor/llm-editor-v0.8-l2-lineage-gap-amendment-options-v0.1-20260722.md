# LLM Evidence-safe Semantic Editor v0.8：L2 lineage 缺口 amendment 选项 v0.1

**日期**：2026-07-22

**权威基线**：`feat/llm-editor-v0.8 @ 5a2e27e`

**状态**：`options_only_no_role_change`

## 1. 裁断

本文件只列出 BETH、Loghub、Atomic、CAM-LDS、SOCBED 与 Zeek 的 lineage 缺口处置选项，不执行处置。

- 六族当前 candidate role 全部保持不变；
- 未读取 payload、private gold 或模型输出；
- 未批准任何 bounded payload audit；
- 未把历史 1,500 pairs 继承为 v0.8 样本；
- train、development、test 与 L2 Gate 继续为 `false`；
- baseline 与微调继续禁止。

机器可检矩阵见 `llm-editor-v0.8-l2-lineage-gap-amendment-options-v0.1-20260722.json`。

## 2. 共同判断规则

文件、目录、技术编号、运行视图、日志行和 prompt view 都不能自动算独立 lineage。任何 `future_bounded_payload_lineage_audit` 都是未来选项，必须另行授权，并在读取前冻结目标字段、最大读取范围和 grouping rule；其目的只能是核验数据血缘，不能读取标签来制造监督。

三个处置类别的含义是：

| 选项 | 含义 | 对当前角色的影响 |
|---|---|---|
| `replace_family` | 调研并逐族批准具有独立 run/capture 血缘的新来源 | 本轮无变化 |
| `downgrade_to_inactive` | 不再让该族计入科学配额，可保留工程用途 | 本轮无变化 |
| `future_bounded_payload_lineage_audit` | 未来只核验 source-native run/session/host/time grouping | 本轮未授权 |

## 3. 逐族选项

### 3.1 BETH（当前：train candidate）

**缺口**：一个文件、一个主机范围，文件级只有一个可辩护 lineage；409,931 行不能替代独立运行。

| 选项 | 优点 | 代价 / 风险 | 建议 |
|---|---|---|---|
| 换族 | 直接消除最明确的伪重复；可引入独立主机或运行 | 需重新过 license/revision/source gate | **首选** |
| 降为 inactive | 不再夸大行级样本量 | train active family 从 4 降为 3，Gate 继续失败 | 无替代时可接受 |
| 未来有界审计 | 可检查是否存在 source-native session/time cluster | 任意切时间窗不能把单主机变成独立执行；成功概率低 | 低收益，须另授权 |

### 3.2 Loghub Linux（当前：development candidate）

**缺口**：归档内只有一个 `Linux.log`；行或窗口不能证明至少四个独立 lineage。

| 选项 | 优点 | 代价 / 风险 | 建议 |
|---|---|---|---|
| 换族 | 可获得明确 session/run 的 development 来源 | 需新 source gate，transport 覆盖可能变化 | **首选** |
| 降为 inactive | 避免把行级变化当重复 | development active family 从 2 降为 1 | 无替代时可接受 |
| 未来有界审计 | 可寻找原生 boot/session/collection 边界 | 文件内切窗本身不构成独立采集；成功概率低 | 低收益，须另授权 |

### 3.3 Atomic Red Team（当前：train candidate）

**缺口**：technique/YAML 数量代表程序库覆盖，不代表独立执行日志。

| 选项 | 优点 | 代价 / 风险 | 建议 |
|---|---|---|---|
| 换为实际执行日志 | 更贴近 evidence editor，避免把 technique 广度当重复 | 需找到可许可、可回指的执行来源 | **科学主张首选** |
| 降为 inactive/engineering-only | 仍可作格式与文字编译夹具 | train active family 降为 3 | 无执行 artifact 时可接受 |
| 未来有界审计 | 若存在外部 run artifact，可把 specification 与 run 绑定 | YAML 本身无法证明执行独立；没有外部 run 就修不了 | 仅外部 run 元数据存在时考虑 |

### 3.4 CAM-LDS（当前：train candidate）

**缺口**：step 目录是可能的 grouping key，但 sequence、host state 与时间依赖未核。

| 选项 | 优点 | 代价 / 风险 | 建议 |
|---|---|---|---|
| 换族 | 消除 scenario/run 相关性歧义 | 会损失当前最接近 endpoint/audit 的候选 | 审计失败后的备选 |
| 降为 inactive | 最保守地消除共享 sequence 风险 | train 降为 3，且损失审计日志覆盖 | 仅审计失败后 |
| 未来有界审计 | 现有 step/host 结构最可能支持 run-level grouping | 需另授权；sequence/technique 标签仍须隔离 | **优先审计候选** |

### 3.5 SOCBED（当前：train candidate）

**缺口**：40 个文件实际对应 10 个 run suffix × 4 个 host/config；同 suffix 四文件最多算一个 run。

| 选项 | 优点 | 代价 / 风险 | 建议 |
|---|---|---|---|
| 换族 | 可降低 testbed/synthetic 域依赖 | 新 source gate；损失 Windows event 覆盖 | 审计失败后的备选 |
| 降为 inactive | 避免预先把 10 个 suffix 当独立 | train 降为 3 | 仅审计失败后 |
| 未来有界审计 | 10 个显式 suffix 使 run-level 核验较可行 | 需 nested notice 与共享 testbed 状态核验 | **优先审计候选** |

### 3.6 Zeek non-PCAP tests（当前：development candidate）

**缺口**：软件测试 fixture 与 parent directory 不是独立真实采集；共享 blob 和生成链未核。

| 选项 | 优点 | 代价 / 风险 | 建议 |
|---|---|---|---|
| 换族 | 获得 capture-level provenance；减少与 IoT-23 的 Zeek 格式相关 | 需新 source gate；parser 覆盖可能下降 | **科学 development 首选** |
| 降为 inactive/engineering-only | 保留 parser fixture 价值但不计科学重复 | development 只剩一个 active candidate | 可接受工程姿态 |
| 未来有界审计 | 可去重 blob、归并同一 btest artifact | 无法把 fixture 变成真实 capture；可能只够工程用途 | 诊断用途，须另授权 |

## 4. 组合 amendment 方案

### 方案 A：替换明确失败族，再审计有希望族（推荐）

1. 替换 BETH 与 Loghub；
2. 对 CAM-LDS 与 SOCBED 另开 bounded lineage audit；
3. Atomic 若无执行 artifact 则替换/降级；
4. Zeek 仅保留工程用途或换成独立 capture 来源。

优点是科学独立性最强，且把 payload 审计投入集中在最可能成功的两个来源；代价是来源调研和逐族 Gate 工作量最大。

### 方案 B：全部弱族降级，接受 Gate 失败

把无法从 metadata 证明独立性的来源降为 inactive 或 engineering-only，L2 保持失败或 `smoke_only`，不降低 quota。

这是最干净的停损方案，但不能开启 baseline、微调或完整 L2 评测。

### 方案 C：先做有界 lineage 审计，再决定角色

优先审计 CAM-LDS/SOCBED；BETH、Loghub、Atomic、Zeek 只检查 source-native lineage 元数据，不读取标签或构造监督。结果冻结后再选择 replace/inactive。

该方案最少预先改角色，但成本高，而且仍可能得到 Gate 失败的结论。

## 5. Gate 保持

```yaml
family_roles_changed: false
test_candidates_approved: false
bounded_payload_audit_authorized: false
train_lineage_quota_passed: false
development_lineage_quota_passed: false
test_lineage_quota_passed: false
l2_gate_passed: false
baseline_authorized: false
fine_tuning_authorized: false
```

下一步若要执行任何 replace、inactive 或 payload lineage audit，必须以新的明确授权和版本化 amendment 开始；本文件本身不触发任何动作。
