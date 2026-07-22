# 模态安全、范围有界、证书驱动的主动攻击归因：Kernel Implementation Specification v0.8

> 状态：`implementation_ready_spec_pending_p0_artifacts`  
> 日期：2026-07-21  
> 前身：v0.7（`active_attribution_experiment_revision_plan_v0.7_implementation_ready.md`）  
> 本版相对 v0.7（按评审 Mandatory/Should Fix）：  
> **(1)** 修正 `A6.5` 重号（Scope Contract → **A6.6**）；  
> **(2)** Kernel 结果域强制**有限**，禁止无界 `plus_external` 却宣称 `solver_complete`；  
> **(3)** 状态改为「规格可拆任务，P0 产物齐后方可编码」；  
> **(4)** Kernel **仅确定性** observation model；TV/随机可分 → Part B optional；  
> **(5)** 澄清 CONTINUE vs 三态不可解决、层级扫描 break 规则；  
> **(6)** Promote 后 `reported` 仍须可解析 pointer；  
> **(7)** Kernel solver 钉为有限域枚举/小型 CSP；  
> **(8)** 附录补最小 `gamma` 与 `TWIN-COUNTEREXAMPLE-001` fixture 骨架；  
> **(9)** 明确：本规格 ≠ 仓库 authority-lock 已授权实现。

---

## 0. 文档用途与硬门禁

本文件是 **Part A Counterexample Kernel 的实现规格**。  
**可拆 sprint / 可写测试清单；在 P0 产物提交并获用户显式授权前，不得开始主代码实现。**

| 分区 | 当前是否可编码 | 内容 |
|---|---:|---|
| **P0 Artifacts** | **须先完成** | JSON Schema、一份 `gamma-kernel-v0.8.yaml`、至少一个 Twin fixture |
| **Part A · Kernel** | **仅 P0 齐 + 用户授权后** | IR、Γ、双查询、MinDiff、确定性 observation、K-E/K-N |
| **Part B · Full** | **仅 A16 Go 后** | 广域联邦、随机 observation、完整 cost、M3\* 闭环、全基线 |
| **附录** | 参考 | 最小 Γ/fixture 骨架、目录、样例 |

### 0.1 禁止事项（继承并加强）

Kernel Go 前禁止：云/K8s/CI/供应链/沙箱/工单全文/被动 DNS 全量连接器；「支持 N 类日志」当贡献；B0–B9 全基线；机会约束规划；LLM/M3\*/概率/人工宣布 `CERTIFIED_STOP`；事后改 Γ/policy/catalog/closed-world 解释结果。

### 0.2 贡献层级（冻结，不增条）

1. No Evidence Laundering / Epistemic Firewall  
2. Scope-bounded Counterexample Certification  
3. Counterexample-guided Acquisition  
4. Evidence-safe Heterogeneous Semantic Compilation（基础设施）  
5. M3\*（求解器）  
6. 广域输入（Part B 压力测试）

```text
防洗白 → 双查询判充分性 → 反例/MinDiff → final-blind 消歧 action → 回流再认证
```

### 0.3 授权声明

本文件 **不构成** 训练、推理、C07–C12 或 M3 接线授权。Part A 编码须另有用户明确授权，并与仓库 authority-lock 一致。

---

# Part A — Counterexample Kernel Implementation

## A1. 科学问题与边界

在预注册 \(\Gamma\) 下 Kernel 须回答：

1. \(q\) 在 \(\ell\) 上是否自身可行（support SAT）？  
2. 是否存在异结论反例（alternative SAT）？  
3. 认证是 **candidate-level** 还是 **level-level**？  
4. 无新 \(E_{case}\)/合法 Promote 时 CTI/模型能否抬高 \(\ell_{cert}\)？  
5. MinDiff 差异与可区分 action？  
6. 不可解决属于：形式 catalog 下界 / 未知区分动作 / 当前不可执行 / UNKNOWN / SCOPE_MISMATCH？

**非主问题：** 路径 F1、actor、最少 action、最多数据源、复杂 LLM/GNN、完整机会约束。

---

## A2. 贡献表述（冻结）

### C1 — Firewall / Non-Amplification

无新案件观测或预注册 promotion 时，不得提高 \(\ell_{cert}\) 或改已认证结论。Promote **不改变 modality**。

### C2 — Scope-bounded Certification

base/support/alternative；candidate vs level-level；coverage mode；UNKNOWN 不得冒充认证。

### C3 — Counterexample-guided Acquisition

Action = 观测划分；Kernel 用**确定性** observation model；M3\* 无 STOP 权。

### 基础设施一句

Evidence-safe Claim IR 保持 pointer、modality、truth_status、authority，避免角色坍缩。

---

## A3. 四个核心对象

1. Scope Contract \(\Gamma\)（可哈希、测试前冻结）  
2. Firewall + Promotion/Revocation Audit  
3. Checker（候选、双查询、level 认证、反例）  
4. Acquisition（确定性 observation、可行性、资源轨迹）

---

## A4. 场景、模态、动作

**场景：** 被盗凭据直接登录 vs 已控主机横向移动（Twins）；分歧在 `compromised_host` / `initial_foothold`（可选 `account_origin`）。

**模态 ≤3：** 端点；身份；可选粗网络摘要。

**Action 6–10：** 须含：可区分命中、zero-hit 可排除、高成本低区分、理论可分但不可执行、形式观测等价、真实空结果。

---

## A5. 角色 / 模态 / 权限三分

| 角色 | 默认权限 |
|---|---|
| \(E_{case}\) | 排除世界、witness、证书 |
| \(K_{mech}\) | 白名单派生 only |
| \(K_{CTI}\) | 排序；枚举 Promote 获有限 authority |
| \(H_{model}\) | 提候选/action；不直接认证 |

禁止单一 `trust_score` 代替：`modality` / `truth_status` / `certification_authority`。

---

## A5.5 Claim IR Kernel Schema

### 最小字段

```yaml
claim_id: string
subject: { entity_id: string, entity_type: string }
predicate: string
object: { entity_id: string|null, literal: string|number|boolean|null, entity_type: string|null }
time: { start: timestamp|null, end: timestamp|null, precision: exact|bounded|approximate|unknown }
location: { host: string|null, tenant: string|null, zone: string|null }
polarity: positive|negative|unknown
modality: observed|derived|reported|hypothesized|unknown
truth_status: unassessed|supported|contradicted|conflicted|retracted
epistemic_role: case_evidence|mechanism_knowledge|background_intelligence|model_hypothesis|analyst_hypothesis|unknown
certification_authority:
  allowed: boolean
  levels: [string]
  basis_rule_id: string|null
  policy_hash: string|null
source_family: execution|identity|communication|data_access|control_plane|system_provenance|software_supply_chain|external_intel|human_investigation
source_schema: string
pointer:
  source_id: string|null
  record_id: string|null
  byte_or_row_range: [integer, integer]|null
  content_hash: string|null
compiler: { parser_id: string, parser_version: string, model_id: string|null, prompt_or_rule_hash: string }
binding_status: unbound|bound|ambiguous|failed
admission_status: candidate|admitted|rejected|abstained
promotion_status: none|eligible|promoted|revoked
admissible_levels: [string]
support_claim_ids: [string]
contradict_claim_ids: [string]
rule_trace: [string]
confidence: { extraction: float|null, source: float|null, model: float|null }
lifecycle_state: generated|bound|admitted|promoted|revoked|rejected|abstained  # 只读派生
```

### 不变量

**I1 Pointer：** `modality=observed` ∧ `role=case_evidence` ∧ `authority.allowed` ⇒ pointer 可解析可复验。  
**I1b Promoted reported：** `promotion_status=promoted` ∧ `modality=reported` ⇒ **仍须**可解析外部/情报 pointer（source_id+record 或 content_hash）；禁止无 pointer 却 `authority.allowed=true`。  
**I2 Modality：** Promote/Revoke **不得**改 modality；`derived`↛`observed`。  
**I3 Derivation monotonicity：** \(A(c_d)\subseteq\bigcap A(c_i)\cap A(r)\)。  
**I4 No silent promotion：** 须 `promotion_event_id`。  
**I5 Abstention：** 禁填最可能实体进 \(E_{case}\)。  
**I6 Contradiction：** 冲突并存，`truth_status=conflicted`。

**LLM：** 可提候选/对齐/条件解释；不可改 authority、Promote、自验证书、伪造绑定、宣布 CERTIFIED_STOP。

---

## A6. Firewall 与 Promote/Revoke

### A6.1 Promote 语义

\[
PromoteRole(c,\ell):\ A(c)\leftarrow A(c)\cup\{\ell\}
\]

`modality` 不变；`epistemic_role` 可→`case_evidence`；须满足 I1b。

### A6.2 条件（全部 AND，无开放例外）

```text
source_provenance_valid ∧ case_entity_binding_valid ∧ temporal_validity
∧ not_mere_historical_tendency ∧ listed_rule_id ∈ Γ
∧ admissible_for_level(ℓ) ∧ policy_version matches Γ
∧ pointer_resolvable_for_promoted_claim
```

### A6.3 Audit / A6.4 Revoke

审计须 `modality_before == modality_after`。撤销 → authority 收回、依赖证书 invalidated、强制重跑 checker。

### A6.5 Non-Amplification

\(E_{case}'=E_{case}\) 且无新/撤 Promote ⇒ \(\ell_{cert}'=\ell_{cert}\)；\(P(q)\)/排序可变。

---

## A6.6 Scope Contract \(\Gamma\) Machine Schema

```yaml
gamma_id: string
gamma_version: string
entity_types: [string]
event_types: [string]
relation_types: [string]
attribution_levels: [string]

# Kernel：结果域必须有限
result_domains:
  compromised_host:
    type: host_id
    generator: from_case_entities          # 仅案件实体闭包
    finite_candidates: null                # 或显式列表
    coverage_mode: exhaustive              # Kernel 允许 exhaustive | solver_complete
  initial_foothold:
    type: host_id
    generator: from_finite_candidate_list  # 禁止无界 plus_external
    finite_candidates: [H1, H3]            # 必须进 hash 的有限集
    coverage_mode: exhaustive

mechanism_rules: [rule_id]
temporal_constraints: object
sensor_coverage:
  - sensor_id: string
    observable_id: string
    entities: [string]
    time_windows: [interval]
    absence_semantics: closed_world|open_world|bounded_completeness|unknown
    completeness_conditions: [string]
retention_assumptions: [object]
missingness_assumptions: [object]
threat_assumptions:
  log_deletion: none|bounded|unmodeled
  log_forgery: none|bounded|unmodeled
  sensor_compromise: none|bounded|unmodeled
admission_policy: { version: string, rules: [rule_id] }
promotion_policy: { version: string, rules: [rule_id] }
action_catalog: { version: string, actions: [action_id] }
candidate_protocol:
  proposer_ids: [string]
  solver_seed_enabled: boolean
  coverage_reporting_required: true
min_diff:
  config_version: string
  lambda_event: float
  lambda_entity: float
  lambda_assumption: float
  tie_break: lexicographic
  timeout_ms: integer
solver_semantics:
  engine: finite_domain_enumerator|small_csp   # Kernel 钉死；禁止未声明 SMT 冒充 complete
  engine_version: string
  timeout_ms: integer
  incomplete_search_policy: UNKNOWN_NOT_CERTIFIED
  proof_policy: reproducible_run|solver_proof|independently_checked
closed_world_fields: [observable_id]
open_world_fields: [observable_id]
hash: sha256:...
```

### A6.6.1 有限域硬约束（Kernel）

| 禁止 | 要求 |
|---|---|
| `generator: from_case_entities_plus_external` 且 external 无界 | external 必须是 `finite_candidates` 预注册列表 |
| `coverage_mode: solver_complete` 配无限域 | 无限域只能 `heuristic`，**不得** level-level CERTIFIED_STOP |
| 测试中临时扩大 candidates | 新 `gamma_version` + 重评 |

### A6.6.2 absence_semantics

| 值 | 空结果 |
|---|---|
| `closed_world` / 满足条件的 `bounded_completeness` | 可排除「若世界成立必有记录」 |
| `open_world` / `unknown` | 不排除；unknown 不计 zero-hit 消歧价值 |

CTI/WHOIS 等默认 `open_world`。证书须列出 critical scope assumptions。

---

## A7. 候选 \(q\) 与认证层级

### A7.1–A7.2 发现与 coverage

Propose ∪ SolverSeed；每 \(q\) 属有限 `result_domains`；报告：

```yaml
candidate_coverage: { level, mode: exhaustive|solver_complete|heuristic, ... }
```

**仅** `exhaustive` 或（有限域上的）`solver_complete` ⇒ 可声称 **level-level**。

### A7.3 双查询

```text
base = solve(Γ ∧ E_case)
support = solve(Γ ∧ E_case ∧ Q_ℓ = q)
alternative = solve(Γ ∧ E_case ∧ Q_ℓ ≠ q)
```

真值表同 v0.7（UNSAT base→SCOPE；support UNSAT→REJECT；双 SAT→COUNTEREXAMPLE；support SAT∧alt UNSAT→CANDIDATE_CERTIFIED；任超时→UNKNOWN）。

### A7.4 Candidate vs Level

- **Candidate-level：** 对当前 \(q\) 唯一可行；heuristic 时不得抬 \(\ell_{cert}\)。  
- **Level-level：** 有限域覆盖完备 + 恰一可行 + alternative UNSAT + 无 UNKNOWN → 可更新 \(\ell_{cert}\)。

### A7.5 最高层扫描（写死 break）

```text
highest = NONE
for level in low_to_high:
    if coverage not in {exhaustive, solver_complete}:
        mark CONDITIONAL/UNCERTIFIED for this and higher; break
    if not exactly_one_level_certified(level):
        mark CONDITIONAL if candidates exist; break   # 不得继续给更高层 CERTIFIED_STOP
    highest = level
# 更高层可并行输出概率，一律 UNCERTIFIED
```

Kernel 只承诺到 `compromised_host` / `initial_foothold`。

---

## A8. Checker

输出：`CERTIFIED` | `COUNTEREXAMPLE_FOUND` | `SCOPE_MISMATCH_SUSPECTED` | `UNKNOWN`（及候选 `REJECT_CANDIDATE`）。

Witness 仅：\(E_{case}\)、允许 \(K_{mech}\)、合法 promoted（含 audit）、pointer/rule_trace。

---

## A9. MinDiff（与 checker 解耦）

```yaml
checker_status: COUNTEREXAMPLE_FOUND
minimization_status: OPTIMAL|BEST_EFFORT|TIMEOUT|NOT_REQUESTED
```

MinDiff 超时 ⇒ 仍 `COUNTEREXAMPLE_FOUND`，**不得** UNKNOWN/CERTIFIED。一屏 Shared/A-only/B-only/Disagreement/Predicates/absence/minimization_status。

---

## A10. 证书

含 `certification_scope: candidate_level|level_complete`、`proof_level`、`critical_scope_assumptions`、promotion 依赖。  
表述：`reproducible_run`≠`independently_checked`。Γ/E/Promote/域/开闭世界变化 ⇒ 失效。

---

## A11. Action 与 Observation（Kernel=确定性）

### A11.0 Kernel 范围

- **强制** `noise_model: deterministic` 且定义 \(O_a(\omega)\)。  
- \(D_{TV}\ge\delta\) **不在 Kernel**；列入 Part B optional。  
- 无 observation model 的 action：可执行/记资源，**不得**用于 catalog ceiling。

### A11.1–A11.3

确定性可分：\(O_a(\omega_1)\neq O_a(\omega_2)\)。  
完全等价：对 catalog 内**全部带 formal model 的** action 均 \(O_a(\omega_1)=O_a(\omega_2)\) ⇒ 可 `UNRESOLVABLE_UNDER_CATALOG`。

### A11.4 三态

| 状态 | 定义 |
|---|---|
| `UNRESOLVABLE_UNDER_CATALOG` | 形式完全观测等价 |
| `NO_KNOWN_DISTINGUISHING_ACTION` | 未找到区分动作，无形式下界 |
| `DISTINGUISHABLE_BUT_INFEASIBLE` | 形式可分但权限/保留/传感器不可用 |

### A11.5 Zero-hit

须同时：模型声明必现记录、coverage、closed/bounded 完整、retention/权限无缺口、无相关 deletion/forgery 假设。

---

## A12. Acquisition / M3\*

\(V(a)=\mathbb E[|\mathcal U|-|\mathcal U_o|]\)；深度仅 `M3-KERNEL-D1` / `M3-KERNEL-D3`；无 planning-confidence 门；无 STOP 权；无 hidden GT。

---

## A13. Cost / 计数

三种计数；Kernel 记 wall/records/bytes（可选 CPU/analyst）。不做机会约束与 E/D/A/R 正式 burden；不可行≠高 cost。

---

## A14. 系统状态机

```text
CERTIFIED_STOP | CONDITIONAL | CONTINUE
UNRESOLVABLE_UNDER_CATALOG | NO_KNOWN_DISTINGUISHING_ACTION | DISTINGUISHABLE_BUT_INFEASIBLE
SCOPE_MISMATCH_SUSPECTED | UNKNOWN | BUDGET_EXHAUSTED
```

### A14.1 主状态判定序（写死）

```text
1. SCOPE_MISMATCH_SUSPECTED
2. UNKNOWN                         # 压过一切认证/消歧结论
3. 若 level-level 认证成立 → CERTIFIED_STOP
4. 若存在反例：
     若存在 formal 可分且 feasible 的 action → CONTINUE
     elif 存在 formal 可分但均 infeasible → DISTINGUISHABLE_BUT_INFEASIBLE
     elif 已证明 catalog 完全等价 → UNRESOLVABLE_UNDER_CATALOG
     else → NO_KNOWN_DISTINGUISHING_ACTION
5. BUDGET_EXHAUSTED（闭环阶段）
6. CONDITIONAL 仅为并行标签，不覆盖主状态
```

---

## A15. 实验与负向测试

**K-E1–E4 / K-N1–N6：** 同 v0.7（Swap、Laundering、Twins、Ceiling；Omission、Revoke、Closed-world misconfig、MinDiff timeout、Missing obs model、Modality preservation）。

**固定案例 ID：** 同 v0.7 九个 TWIN-* ；每个须含 raw、claims、Γ、catalog、预期状态、允许/禁止 action、资源样例。

---

## A16. Go / No-Go

Go 须全过：Schema 校验；Promote 不变 modality；真值表；candidate≠level；heuristic 不抬 \(\ell_{cert}\)；MinDiff 超时不影响不充分；确定性 obs 可复现区分；zero-hit 合法；K-E/K-N；checker≠生成 LLM；预冻 hash；一屏反例；真实形式 ceiling；**Go 条件均有自动测试**。

No-Go：手写反例；假认证；超时当 UNSAT；heuristic 当完备域；reported→observed；无 obs model 证 ceiling；三态冒充；MinDiff 导致错 STOP；hidden ID；玩具 Γ；靠扩输入掩盖失败。

---

## A17. 实施阶段

| Phase | 内容 | 退出 |
|---|---|---|
| **P0** | Schema JSON + `gamma-kernel-v0.8.yaml` + ≥1 Twin fixture + 状态机测试骨架 | 产物齐、有限域目检通过 |
| P1 | base/support/alternative | 真值表自动测 |
| P1a | candidate vs level | coverage 测 |
| P1b | Firewall / Promote / Revoke | K-E1/2、K-N2/6 |
| P1c | Counterexample + MinDiff | K-E3、K-N4 |
| P1d | 确定性 observation + 可分性 | K-E4、K-N5 |
| P1e | 资源轨迹 + D1 planner | 固定案例闭环 |
| Gate | A16 | Go 后才 Part B |

**P0 未完成 ⇒ 禁止合并主实现 PR。**

---

# Part B — Full（Kernel Go 后）

继承 v0.7：语义族扩展、三平面图、编译指标（含 AuthorityLeakage）、基线、完整 \(\mathbf B\)、M3\* 闭环。

**新增：** 随机 observation / \(D_{TV}\ge\delta_a\) 仅 Part B；须预注册 \(\delta_a\) 进 catalog hash。

---

# 共享规范

**层级：** process→…→actor；Kernel 主攻 host/foothold。  
**Final-blind：** 冻 IR/Γ/域/coverage/admission/promotion/catalog/**确定性** obs/MinDiff/solver/M3 深度/STOP。  
**风险表：** 同 v.7，并加上「无界域假完备」「随机可分拖垮 Kernel」。

---

# 一句话

> **规格已可拆任务；先交 P0（有限域 Γ + Schema + Twin fixture），再用确定性双查询与不改 modality 的防火墙做 Kernel；随机可分、广域与完整 cost 一律后置。**

---

# 附录 A — P0 最小 `gamma-kernel-v0.8.yaml` 骨架

```yaml
gamma_id: gamma-kernel-v0.8
gamma_version: "0.8.0"
entity_types: [host, account, process, ip]
event_types: [process_execute, authenticate, network_connect]
relation_types: [executes, authenticates_to, connects_to]
attribution_levels: [compromised_host, initial_foothold]
result_domains:
  compromised_host:
    type: host_id
    generator: from_case_entities
    finite_candidates: null
    coverage_mode: exhaustive
  initial_foothold:
    type: host_id
    generator: from_finite_candidate_list
    finite_candidates: [H1, H3]
    coverage_mode: exhaustive
sensor_coverage:
  - sensor_id: auth-H1
    observable_id: kerberos_auth
    entities: [H1]
    time_windows: ["2026-01-01T10:00:00Z/2026-01-01T10:15:00Z"]
    absence_semantics: bounded_completeness
    completeness_conditions: ["retention_ok", "sensor_up"]
  - sensor_id: auth-H3
    observable_id: logon_origin
    entities: [H3]
    time_windows: ["2026-01-01T10:00:00Z/2026-01-01T10:15:00Z"]
    absence_semantics: bounded_completeness
    completeness_conditions: ["retention_ok"]
threat_assumptions: { log_deletion: none, log_forgery: none, sensor_compromise: none }
admission_policy: { version: adm-0.8, rules: [A001, A002] }
promotion_policy: { version: prom-0.8, rules: [] }   # Kernel Twin 可不启用 Promote
action_catalog: { version: act-0.8, actions: [query_auth_H1_1000_1015, query_logon_origin_H3] }
candidate_protocol: { proposer_ids: [rule_seed], solver_seed_enabled: true, coverage_reporting_required: true }
min_diff: { config_version: md-0.8, lambda_event: 1.0, lambda_entity: 1.0, lambda_assumption: 1.0, tie_break: lexicographic, timeout_ms: 2000 }
solver_semantics:
  engine: finite_domain_enumerator
  engine_version: "0.8.0"
  timeout_ms: 5000
  incomplete_search_policy: UNKNOWN_NOT_CERTIFIED
  proof_policy: reproducible_run
closed_world_fields: []
open_world_fields: [cti_report]
hash: "TO_BE_COMPUTED_AFTER_FREEZE"
```

---

# 附录 B — `TWIN-COUNTEREXAMPLE-001` fixture 骨架

```text
tests/fixtures/TWIN-COUNTEREXAMPLE-001/
  README.md                 # 预期 CONTINUE + COUNTEREXAMPLE_FOUND
  gamma_ref.yaml            # 指向 gamma-kernel-v0.8 hash
  raw/
    endpoint.jsonl
    auth.jsonl
  claims/
    case_evidence.jsonl
    cti_background.jsonl    # 仅排序，不得进 witness
  expected/
    target_level: initial_foothold
    candidate_q: H1
    base: SAT
    support: SAT
    alternative: SAT
    checker_status: COUNTEREXAMPLE_FOUND
    system_status: CONTINUE
    mindiff_disagreement: { A: H1, B: H3 }
    distinguishing_predicates: [auth_origin(H3), credential_activity(H1)]
    allowed_actions: [query_auth_H1_1000_1015]
    forbidden_actions: []    # 依赖 GT 的禁止
```

---

# 附录 C — 建议目录（同 v0.7，略）

`schemas/*.schema.json`、`configs/gamma-kernel-v0.8.yaml`、`configs/action-catalog-kernel-v0.8.yaml`、`src/{ir,firewall,scope,checker,counterexample,actions,planner,executor,cli}/`、`tests/{unit,integration,fixtures}/`。

---

# 附录 D — v0.7 → v0.8

| 评审问题 | v0.8 |
|---|---|
| A6.5 重号 | Scope Contract → **A6.6** |
| 无界域 + solver_complete | **有限 candidates**；禁无界 plus_external |
| implementation_ready 过满 | `…_pending_p0_artifacts`；P0 门禁 |
| TV 过重 | Kernel **仅确定性** |
| CONTINUE vs 三态 | **A14.1 判定序** |
| Promote 无 pointer | **I1b** |
| 层级扫描含糊 | **A7.5 break 写死** |
| solver 过空 | `finite_domain_enumerator\|small_csp` |
| 缺实例 | 附录 A/B 骨架 |
| 规格≠授权 | **0.3** |
