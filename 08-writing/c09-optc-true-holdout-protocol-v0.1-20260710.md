# C09 OpTC 第三真留出协议 v0.1

日期：2026-07-10  
状态：**预登记 / 未编译**（M3a 公式已冻结；C07/C08 已完成）  
前置：`contribution-boundary-and-results-brief-v0.1.md`；C07/C08 结果 README

## 1. 目的

在 **E5 THEIA（C07）+ E5 ClearScope（C08）** 之外，增加一条**企业遥测风格、独立 engagement 家族**的真留出，检验冻结 M3a 是否仍能：

- 达标且不越 `support_ceiling`；
- 在 intended≠OR + 通道门控下可跑通；
- **不要求**成本优于 M2（预登记：主终点是 paired regret 汇总，不是打赢）。

预登记主对比：

| 终点 | 定义 |
|---|---|
| 主 | C07+C08+C09 上 M3a vs M2 的 mean cost / regret 方向是否一致 |
| 次 | 网络/主机通道失效时是否仍有可靠回退；良性/噪声动作是否不被当成攻击缺口 |
| 禁止事后改 | `m3a_gap_compat_score` 权重、STOP 语义、通道先验表 |

## 2. 硬约束

| 禁止 | 原因 |
|---|---|
| 为让 M3a 更好看而调权 / 改 STOP | 污染真留出 |
| 下载全量 ~TB 后再“挑好看的一天”当 holdout | 必须先锁 ground-truth 窗口 |
| 把 OpTC 编成检测分类器评测 | 本项目评的是主动取证规划，不是 IDS |
| 用 Inria corrected 全集替代前不写 manifest 差异 | 来源边界必须可审计 |
| 宣称“跨数据集泛化”仅凭 C07+C08 | 缺第三来源前最多写“双 E5 异构复现” |

## 3. 数据边界（先文档、后子集）

### 3.1 官方入口

- 索引：https://github.com/FiveDirections/OpTC-data  
- Ground truth：`OpTCRedTeamGroundTruth.pdf`  
- 模式：`ecar.md`；已知问题：`errata.md`  
- 大数据：Google Drive（README 中的 `ecar/`、`ecar-bro/`、`bro/`）  
- 可选质量补丁：Inria corrected OpTC（https://doi.org/10.57745/UXCWOC）——**仅当官方 eCAR 主键/关联明显坏掉时再换**；默认先官方子集。

### 3.2 子集策略（必须，禁止全量）

目标体量：能锁 **1 个红队活动日 × 少量被攻击主机** 的 eCAR 窗口，而不是 500 主机 × 多天。

推荐下载顺序：

1. **必下（小）**：`OpTCRedTeamGroundTruth.pdf`、`ecar.md`、`errata.md`  
2. **必下（中）**：ground truth 锁定后的 **evaluation 日目录** 中、与目标主机相关的 eCAR 分片（优先 `ecar/evaluation/`；若需网络枢轴再补对应 `ecar-bro` / `bro`）  
3. **不下**：benign 全量、无关主机、全 evaluation 全机

IEEE DataPort / 文献常见划分：红队活动约在 **2019-09-23 / 09-24 / 09-25**；具体主机与 IOC **以 GT PDF 为准，在读事件前写入 `ground_truth/R06.json`**。

### 3.3 本地目录

```text
09-experiments/real_data/darpa_optc/
  manifest.json
  README.md
  docs/                  # GT PDF + ecar/errata（可进 git 若体积小）
  ground_truth/R06.json  # 锁窗后写；未锁前不要编 motif
  raw/                   # gitignore
  extracted/             # gitignore
  derived/               # 抽取摘要；可进 git
```

案例目录（编译后）：`09-experiments/real_cases/C09-darpa-optc-<slug>/`

## 4. 编译清单（与 C07/C08 同构）

1. `case_config.json` — `holdout_role: true_cross_engagement_third_holdout`；`channel_reliability`；`cti_nodes/edges`；mask 协议与 C07/C08 同形。  
2. `evidence_claims.json` — 每条 claim 回指 eCAR `id`（或等价主键）；`hideable`；自然缺失不伪造。  
3. `acquisition_actions.json` — **intended≠OR(recoverable)**；不可靠通道 + 可靠回退；至少一条良性/噪声审查动作（若 GT 有 interleaved benign）。  
4. `motif_spec.json` + 编译报告 — 事件级匹配可审计。  
5. 冻结评估：`run_mvp.py --case-dir ... --output-dir results/c09_holdout_m3a/`（**不改** M3a）。

企业遥测与 PGDMP 不同：需要一条 **eCAR 窗口抽取/motif 编译** 小脚本（新建，不复用 `stream_pgdump_*`）。预登记：脚本只服务锁定窗口，不做全库特征挖掘来“找能赢的 claim”。

## 5. 预登记成功/失败判据

| 结果 | 写法 |
|---|---|
| M3a success≈M2，成本不优于 M2 | 与 C07/C08 同向 → 写“三来源工程可复现；成本优势未成立” |
| M3a success 明显崩 | 主线回到表示/动作空间假设，**禁止**调权抢救 |
| 窗口内关键 IOC 大量缺失 | 降级 `support_ceiling` 或换 GT 中另一活动日；记录为数据质量，不调 M3a |

## 6. 并行可做的次级硬度（不替代 C09）

在等 OpTC 下载时，可在 **开发集 C01–C06** 上预登记并做：

- 噪声/误导 acquisition action 鲁棒性（附录）；  
- 仍 **不得** 用其结果回头改 C07/C08/C09 公式。

## 7. 当前阻塞

- [ ] 本机取得 GT PDF 并锁定 R06 窗口/主机  
- [ ] 下载对应 eCAR 子集并登记 SHA-256  
- [ ] eCAR 抽取脚本 + motif 编译  
- [ ] C09 案例编译与冻结评估  
- [ ] 更新 contribution brief：C07+C08+C09 paired regret 表
