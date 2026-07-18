# Project05 LLM evidence compiler：候选边验证训练修订 v0.1

状态：`approved_dependency_free_implementation_only`  
日期：2026-07-18  
上游草案：`llm-evidence-compiler-candidate-verification-amendment-draft-v0.1-20260718.md`  
实施计划：`llm-evidence-compiler-candidate-verification-implementation-plan-v0.1-20260718.md`

## 1. 裁决

批准把 QLoRA 的监督单位从无条件 `observation/null packet` 改为：

```text
source record + exact source pointer + candidate SPO/time
→ supported | unsupported_by_bound_pointer | abstain
```

当前批准只覆盖依赖无关的 schema、字段映射、N1–N4 机械负例函数、proof 校验、单元测试和只读数量审计。它不批准构造正式 candidate-pair 数据集，也不批准安装环境、下载 tokenizer/Qwen 权重、训练、正式推理或接入 M3 运行时。

## 2. 负标签的精确含义

`unsupported_by_bound_pointer` 只表示绑定的这一条 source record 不能逐字段支持给定 candidate。它不表示：

- 该事件在真实世界不存在；
- 当前主机或时间窗是良性的；
- 整个 packet 没有其他 observation；
- 未标注或未入库的关系为假。

旧 `packet_role=null` 与 `null_eligible_candidate=true` 行不得迁移、改名或计入本合同的负例数量。

## 3. G0 正例

G0 正例的 subject、predicate、object 和可选 time 必须由 source-specific field map 绑定到显式 record field，或绑定到已命名、冻结且可逆核查的纯机械变换。来源指针、record SHA-256、来源家族和许可 provenance 必须存在。

禁止使用目录/文件路径、ATT&CK/TTP、actor、scenario、模型输出、人工语义补全或 validation/test gold 生成训练 target。固定占位主语（例如没有显式 host 实例却输出 `system/host`）不得作为 G0 正例。

## 4. 机械负例

批准实现但尚不批准批量运行以下四个显式函数：

1. N1：同 packet、同 object type 的 object swap；
2. N2：保持 candidate，仅把 pointer 换为同 packet 的另一条不支持记录；
3. N3：使用冻结 field-map incompatibility 表替换 predicate；
4. N4：仅在两条记录都有显式且不同时间时进行 time mismatch。

所有负例必须保存独立 proof。proof validator 必须重新核查绑定记录确实不支持变更后的 candidate，而不能信任 generator 自报结果。

## 5. 非 token data-gate

只读审计使用以下硬门槛：

| 项目 | 门槛 |
|---|---:|
| train candidate pairs | ≥1200 |
| training-validation candidate pairs | ≥300 |
| train G0-positive families | ≥4 |
| validation G0-positive families | ≥2，且与 train family-disjoint |
| supported 比例 | 40%–60% |
| negative generator families | ≥3 |
| 单一 generator 占比 | ≤50% |
| same-packet negative | ≥75% |
| source-modality match | 100% |
| proof validator pass | 100% |

本轮没有 tokenizer 权限，因此 token p50/p95/max 保持 `not_measured_not_authorized`；它不能被当作已通过。

## 6. 当前预期失败

历史提案分布只有三个 train observation 来源族，其中 CAM-LDS 使用未绑定的 `system/host` 占位主语。Splunk 与 Loghub 只有旧 packet-null 行，不能救来源族 Gate。因此即使 Atomic、SOCBED 和 Zeek 有足够逐字段正例，当前 non-token Gate 仍可能因 train/validation 正例来源族不足而失败。

失败是预注册结果，不允许通过降低家族门槛、迁移旧 null、用 validation 充 train 或放宽 G0 mapping 修复。后续只能另行批准独立同模态正例来源，或把 adapter 降级为 smoke-only；Qwen-General 与 Reuse-Hybrid 保持可用回退路线。

## 7. 论文主张边界

若后续另行授权并完成对照，QLoRA 只可被称为 `task/schema-adapted observation compiler`。本修订不证明幻觉减少、真实世界事件不存在、APT-domain model、actor attribution 或端到端 SOTA。

