# Project05 当前权威文件索引

**状态日期**：2026-07-15

**本次变更**：用户已明确授权在自动化实验贯通后开始论文与专利撰写。该授权解除“暂不写正文”的工作流暂停，但不把仍开放的人工、运营测量或外部真值 Gate 视为已完成，也不授权把草稿标记为投稿或申请就绪。

## 1. 唯一写作入口

| 类型 | 当前权威文件 | 状态与边界 |
|---|---|---|
| 论文主稿 | `paper-main-draft-v1.0-parameter-governance-20260715.md` | 完整参数治理整合稿；不是投稿就绪稿 |
| 论文格式工作稿 | `paper-package-v1.0-parameter-governance/Project05_不完整证据下的可审计APT调查控制-完整工作稿.docx` | 通用中文学术版式；11 页、4 表、1 图、20 项编号参考文献；已逐页视觉复核，目标期刊未定，仍非投稿就绪稿 |
| 论文参考文献 | `paper-main-references-v0.3.bib` | 已补 Turney、Saar-Tsechansky、Howard、RFC 3227、NIST SP 800-86；投稿前回原文复核 |
| 专利主稿 | `patent-main-draft-v0.9-parameter-governance-20260715.md` | 仅方法权利要求；供发明人及中国专利代理师复核 |
| 专利干净申请文本 | `patent-application-text-v0.9-zju-reference-20260715.md` | 已移出证据矩阵、提交红线、内部路径和研发状态；约 6,324 个汉字 |
| 专利格式稿 | `patent-package-v0.9-zju-reference/Project05_调查取证动作规划方法-浙大参考格式.docx` | 参照两份浙大已审稿构建；四个新页 section、11 项方法权利要求、5 幅自有附图；Word 导出 18 页并逐页视觉复核 |
| 专利权利要求证据映射 | `patent-work/05-claim-evidence-map-v0.9.json` | 11 项方法权利要求逐项映射 P/E/F/C source ID |
| 方法学治理母本 | `methodological-parameter-governance-v0.1-20260714.md` | cost、阈值、corroboration、奖励、先验、构念与终点的治理起点 |
| 成本标准 | `cost-assignment-standard-v0.1-20260714.md` | 规定 E/V/D/A/R 分解与 legacy/uniform/rubric/measured 边界 |

`paper-main-draft-v0.9-route-b-positioning-20260714.md`、`patent-main-draft-v0.8-route-b-20260714.md` 及更早稿继续作为过程档案保留，不删除、不改写，但不再承担当前母本功能。

## 2. 当前实验权威入口

| 事项 | 权威位置 | 冻结事实 |
|---|---|---|
| 自动化完成审计 | `../09-experiments/results/nonhuman_completion_audit_v0.1/completion_manifest.json` | 15 个正式输出重新验证；411 passed、6 skipped、0 failed；`all_experiments_complete=false` |
| Cost profile | `../09-experiments/cost_profiles/`、`../09-experiments/data_schema/cost_profile.schema.json` | legacy/uniform 完成；rubric 360 分量待评分；measured 72 动作待测 |
| 参数治理 | `../09-experiments/results/parameter_governance_v0.1/` | 40 阈值组合、6 k-of-n 配置、7 个 M2 alpha、legacy/uniform 对照 |
| W6 修正 | `../09-experiments/results/parameter_governance_w6_v0.2/`、`../09-experiments/results/parameter_governance_audit_v0.1/` | planner belief 与执行可靠性分离；旧混杂结论不得复用 |
| Planner prior | `../09-experiments/results/policy_prior_sensitivity_audit_v0.2/` | ×0.75 改变 AFA/Depth-2；×1.25 无动作或结果变化 |
| Runtime contract | `../09-experiments/governance/contracts/planner-runtime-contract-v0.1.json` 及 AFA endpoint contract | AFA、Depth-2、XGBoost、Logistic 正式入口受公开视图和隐藏结果不变性约束 |
| External GT | `../09-experiments/results/external_ground_truth_interface_v0.1/` | 可接受记录 0；actor accuracy 与 analyst utility 不可识别 |
| 人工 Round 1 | `human-annotation-round1-results-v0.2-route-b-correction-20260714.md` | Claim κ=-0.1455；Intent Jaccard=0.3673、micro-F1=0.4878；粒度任务作废 |

## 3. 当前冻结写作判断

1. 主线是“不完整证据下、信息边界约束的 APT 调查控制”，不是新的 actor attribution classifier。
2. 独立评估单位为 C07–C12 六个案例或攻击链；每例 45 个 mask/intensity/seed 条件是配对重复，合计 270 条，不能写成 270 个独立攻击。
3. Legacy ML 结果为：XGBoost 270/270、mean cost 3.8926；M2 270/270、3.8704；Logistic/M3b 267/270、4.0000。
4. Uniform 结果只表示动作数：AFA 入口中 M2/Myopic/Rollout-H3/Oracle 为 1.7296/1.7333/1.7778/1.4852；Depth-2 入口中 M2/Depth-2/Oracle 为 1.7296/1.8963/1.4852；ML 入口中 XGBoost/Logistic/M2/M3a/Oracle 为 1.6852/1.6630/1.7296/1.7333/1.4852，均为 270/270。
5. M2 在 40 个阈值组合、6 个 k-of-n 配置和 7 个 alpha 上保持内部 success=1 且零粒度越界；动作序列并非完全稳定，故不得升级为全局最优或参数无关。
6. AFA 与 Depth-2 是领域适配，不是 AFABench、AACO、NOCTA 或 WinRegRL 官方同任务复现。
7. Uniform 排序变化只能证明成本口径敏感性，不能替代真实 measured cost；legacy 也不得称为真实运营成本。
8. Actor/campaign accuracy、跨组织泛化、SOTA 和普遍成本降低均无证据支撑。
9. Claim、Intent 与粒度仍是待验证工程构念；第三人裁决不能改写 Round 1 一致性。
10. C11 的冻结保守主端点为 AND，OR 为乐观敏感性端点；新稿统一写成 k-of-n 两端，不再颠倒。
11. C12 是一个 G1 生产 SOC 衍生 incident；厂商投影、自动标签和 `Disrupted` 均不是 actor truth。
12. 专利只保护计算机实现的方法；系统、设备和存储介质权利要求保持删除。
13. 专利中的 cost profile、k-of-n、runtime allowlist、先验分离和来源 Gate 均为从属特征或实施方式，不把未完成人工/测量结果写成技术效果。

## 4. 开放 Gate

| Gate | 当前状态 | 关闭条件 |
|---|---|---|
| Cost rubric | 360 个分量待真实独立评分 | 两名评分者、冻结规则、一致性与裁决流程完成 |
| Measured cost | 72/72 动作待运营测量 | 动作级记录完整、归一化方案冻结并通过正式校验 |
| 人工构念 Round 2 | 未启动 | 独立分发、回收、聚合和预注册门槛判定完成 |
| 外部 actor/campaign GT | 0 条可接受记录 | 完整可核验真值进入 external GT bundle |
| Analyst utility | 不可识别 | 预注册效用终点和有效记录完成 |
| 论文投稿 | 未就绪 | 作者信息、引用复核、图表更新和目标期刊格式完成；开放科学 Gate 如未关闭须保留限制 |
| 专利提交 | 未就绪 | 发明人/权属/公开日确认，中国专利检索和代理师逐项审查完成 |

## 5. 版本和仓库纪律

- 默认写作交付物为 Markdown 审阅稿；论文、专利、报告和演示文稿均先完成 `.md` 内容审阅。
- 只有在用户明确确认 Markdown 内容通过或明确要求转换后，才生成 DOCX、PPTX 或 PDF 等排版派生文件。
- 后续内容修改以 Markdown 母本为唯一入口；已有 DOCX/PPTX/PDF 不直接承担反复改稿功能，待母本再次确认后统一重建。
- 不覆盖冻结实验、旧论文/专利母本或用户已有修改。
- profile、输入、正式输出和运行契约均以版本与 SHA-256 关联。
- 当前仅存在本地 `main`；没有可供合并的功能分支，本轮不得写成“已合并各分支”。
- 本轮文稿和证据映射未擅自 stage、commit 或 push。
- 现有 `figures/main-v0.4/` 不能完整表示新增 cost/prior 治理结果；投稿前需另立新版图表，不覆盖旧图。
