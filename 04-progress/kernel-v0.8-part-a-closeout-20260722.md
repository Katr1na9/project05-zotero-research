# Kernel v0.8 Part A 收口纪要

**日期：** 2026-07-22
**分支：** `feat/kernel-v0.8`
**本地 HEAD：** `93af889`
**工程状态：** `PART_A_IMPLEMENTED_PENDING_A16_REVIEW`
**A16 状态：** `PENDING_HUMAN_REVIEW`，在明确 Go 裁定前按 `NO-GO` 处理

## 1. 本轮结果

Part A Counterexample Kernel 已按用户逐切片授权完成 P0–P10。本轮最后的
P10 没有增加规划算法，而是把既有组件串为一条确定性 Twin 主链：

```text
Checker
→ MinDiff
→ Counterexample Artifact
→ Distinguishing Action Selection
→ Deterministic Observation Executor
→ optional explicit feedback
→ Recertification
→ System State
```

默认 Twin 路径从代码得到：

- 初始 `checker_status=COUNTEREXAMPLE_FOUND`；
- `allowed_actions` / `forbidden_actions` 与冻结 fixture 一致；
- 不自动选择回流观测；
- 最终 `system_status=CONTINUE`，不签发证书。

显式回流单个有效 hit 的补充路径从代码得到
`checker_status=CANDIDATE_CERTIFIED`，但系统仍为 `CONTINUE`；candidate-level
结果没有被洗成 level-complete `CERTIFIED_STOP`。

## 2. 实施切片与提交

| 切片 | 交付内容 | 本地提交 |
|---|---|---|
| P0 | Schema、Γ、action catalog、Twin fixture、合同测试 | `3b34f3e` |
| P0 rulings | canonical hash、promotion/event 与命名裁定收口 | `43ba22a` |
| P1 | finite-domain Checker | `0e72757` |
| P2 | deterministic finite-witness MinDiff | `54174e3` |
| P3 | counterexample artifact assembler | `1ebbf91` |
| P4 | distinguishing action selection | `ede7b30` |
| P5 | deterministic observation executor | `1bae135` |
| P6 | world elimination + recertification | `4da8d2a` |
| P7 | epistemic Firewall admission | `ee06f37` |
| P8 | Promote/Revoke append-only audit lifecycle | `5d678bf` |
| P9 | system state + level-certificate gate | `441c7c4` |
| P10 | deterministic Kernel E2E driver | `93af889` |

从 P0 的父提交 `d156b68` 到 P10，共 12 个提交、69 个文件、10,194 行新增。
该计数描述本地 Kernel 实施切片，不代表已经合并、推送或发布。

## 3. 验证记录

2026-07-22 在 `feat/kernel-v0.8 @ 93af889` 复跑：

| 校验 | 命令 | 结果 |
|---|---|---|
| P10 定向 | `python -m unittest tests.integration.test_twin_kernel_e2e_p10 -v` | 4/4 passed |
| Kernel 全回归 | `python -m unittest discover -s tests -p "test_*.py" -v` | 100/100 passed |
| Python 编译 | `python -m compileall -q src tests` | passed |
| 补丁格式 | `git diff --check`、`git diff --cached --check` | passed |
| 越界导入 | 扫描 P10 的 Planner/compiler/training/LLM 导入 | no hit |

测试通过只证明冻结合同及 Twin 实现当前一致，不等价于外部有效性、完整 Part B
评估或 A16 Go。

## 4. 明确未做

- 没有实现 Part B、广域连接器或随机 observation；
- 没有接入 Planner、M3*、概率阈值、LLM 或训练；
- 没有改变冻结 Γ、canonical hash、action catalog 或 fixture expected；
- 没有允许人工、LLM、M3* 或 candidate-only 结果宣布 STOP；
- 没有 push，也没有创建 PR。

P7/P8 observation-to-Claim IR 的生产适配器没有在 P10 中擅自发明；P10 的
Firewall/Admit 是可选边，当前确定性主链以显式 observation feedback 接入 P6。

## 5. 当前门禁与下一决定

Part A 的**工程主链**可以视为闭合，但 A16 的**权威裁定**尚未闭合。当前只允许
文档收口、代码评审和准备合并材料。以下事项仍需新的明确授权：

1. 裁定 A16 Go / No-Go；
2. 替换 SI-010 的 fixture policy-hash 占位并形成正式认证材料；
3. push `feat/kernel-v0.8`；
4. 创建 PR 或合并；
5. 开始任何 Part B、Planner/M3*、LLM、训练或实验切片。

轨道 authority 状态以
`08-writing/KERNEL-V0.8-AUTHORITY-STATUS-20260722.md` 为当前入口。

## 6. 人工批准的收口债务修复

用户于 2026-07-22 明确批准以下三个窄修复；它们不构成新的 Part A 算法：

1. Firewall 将缺 observation context 保留为
   `FW-016_OBSERVATION_CONTEXT_REQUIRED`，不支持的 observation kind 拆为
   `FW-017_OBSERVATION_KIND_UNSUPPORTED`；
2. 新增 `EvidenceGammaFiniteProblemCompiler`，P1/P2/P3/P9/P10 的 Twin
   `FiniteDomainProblem` 从冻结 Γ 与 admitted case evidence 重算，不再在测试里
   手写 H1/H3 世界约束；
3. 新增 `PredicateProjectionContract`，调用方通过 action ID 提供变量绑定，
   predicate 只能解析自冻结 catalog 的唯一 `world_dependencies`；MinDiff 拒绝
   裸 mapping 和 ghost predicate。

本切片 RED 为 5 个预期失败；实现和迁移后全套为 105/105 passed。静态扫描确认
Twin 集成测试中无 H1/H3 手写世界约束、无两个历史 ghost predicate 字面量。
Γ、canonical hash、action catalog 与 fixture expected 均未修改。该切片仍等待
人工 diff 评审，不改变 A16 `PENDING_HUMAN_REVIEW` / `NO-GO` 状态。
