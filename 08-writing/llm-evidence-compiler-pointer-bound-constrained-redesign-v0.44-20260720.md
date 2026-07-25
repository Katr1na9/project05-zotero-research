# Project05 LLM 证据编译器：程序化 pointer 绑定与约束解码修订 v0.44

日期：2026-07-20

状态：`model_free_implementation_complete_execution_closed`

## 1. 修订原因

v0.43 的 General/Adapted 配对原子评测是已完成且不可覆盖的负结果：General 的 16 条输出全部在顶层 schema 失败；Adapted 仅学会了 unsupported 短路径，8 条 supported 输出全部因 `invalid_edge_source_pointer` 被拒绝。表面 `+0.50` macro-F1 完全来自负类，supported-class F1 在两个来源族均为 0。

本修订不重算、不修复、不重新解释 v0.43。它建立一个新的、仅限 training-validation 的诊断问题：

> 当 evidence pointer 从模型生成目标中移除、由可信程序绑定，并用 token 级 JSON Schema 约束保证模型输出键、层级和类型后，General 或既有 Adapted 条件能否产生严格可接受的 supported 正路径？

## 2. 职责重新分配

旧路径：

```text
LLM → decision + 顶层 pointer + edge 五字段 + edge.source_pointer
```

v0.44 路径：

```text
可见 payload + candidate + bound_pointer
              ↓
同一 Qwen（adapter off/on）
              ↓ token 级 JSON Schema 约束
decision + pointer-free edge_fields
              ↓ 可信 binder
顶层 pointer := deepcopy(bound_pointer)
edge.source_pointer := deepcopy(bound_pointer)
              ↓
严格 scorer / 正例生成 Gate
```

LLM 不再生成、复制、修改或发明 pointer。pointer 是输入合同中已经存在的证据地址，不是需要语言模型推断的语义。模型仍负责判断候选边是否被当前记录支持，并在 supported 分支输出五个语义边字段。

## 3. 约束输出合同

模型输出只允许两个 JSON Schema 分支。

Supported：

```json
{
  "support_decision": "supported",
  "edge_fields": {
    "subject_type": "process",
    "subject_value": "powershell.exe",
    "predicate": "connected_to",
    "object_type": "network_endpoint",
    "object_value": "example.org:443"
  }
}
```

Unsupported：

```json
{
  "support_decision": "unsupported_by_bound_pointer",
  "edge_fields": null
}
```

以下行为一律失败，不做 repair 或 coercion：

- 模型输出任何 `pointer`、`source_pointer` 或 `normalized_edge` 字段；
- supported 缺少任一五字段、出现额外字段、空字符串或非字符串；
- unsupported 携带非空 edge；
- bound pointer 不是精确的三字符串键集合；
- constrained decoder 未启用、失败后退回自由生成、输出未 EOS 终止；
- binder 后顶层 pointer 与 edge pointer 的 canonical SHA-256 不同。

## 4. Constrained decoding

实现采用 `lm-format-enforcer==0.10.6` 的 Transformers `prefix_allowed_tokens_fn` 集成。选择该接口的原因是它能在现有同一已加载 Qwen/PEFT 进程中对 token 进行 JSON Schema 过滤，不要求另行加载一个模型，因此 General 与 Adapted 的唯一模型差异仍是 adapter state。

执行前必须另做隔离依赖兼容预检，至少验证：

1. Python 3.11.9、Transformers 4.45.2 与当前 tokenizer 兼容；
2. 冻结的 two-branch schema 能建立 parser；
3. 合法 token 集不会为空；
4. supported 与 unsupported fixture 均能完成 EOS；
5. 无约束 fallback、自动 retry 和 parser repair 均保持关闭。

v0.44 不授权安装该依赖，也不授权运行模型。依赖预检和一次模型执行必须由后续独立 authority 开启。

## 5. Pointer binder

可信 binder 的输入只有：

- constrained model output；
- 公开请求中已经提供给模型的 `bound_pointer`。

它不得读取：

- `support_decision` gold；
- `normalized_edge` gold；
- development/test；
- C07–C12；
- M3 状态或控制器输出。

绑定规则写死为：

```text
result.pointer = deepcopy(bound_pointer)

if decision == supported:
    result.normalized_edge = edge_fields
    result.normalized_edge.source_pointer = deepcopy(bound_pointer)
else:
    result.normalized_edge = null
```

这不是对 v0.43 输出的事后修复。v0.43 原始输出及其负结果哈希保持不变；v0.44 使用新 prompt、新输出 schema、新面板 seed、新 scorer 和新 authority。

## 6. 小型 training-validation 面板

只允许从冻结的 300 条 training-validation 中按新 seed `2026072002` 无放回选取 16 条：

| 来源族 | supported | unsupported | 合计 |
|---|---:|---:|---:|
| Loghub Linux | 4 | 4 | 8 |
| Zeek non-PCAP | 4 | 4 | 8 |
| 合计 | 8 | 8 | 16 |

General/Adapted 每条各一次，共 32 次生成；每个来源族×决策区组内首运行顺序 2/2 平衡。两条件共享：base、tokenizer、NF4、prompt、schema、decoder、greedy 配置、硬件、binder 和 scorer。唯一模型差异仍为 adapter off/on。

面板 seed 必须与 v0.41 的 `2026072001` 不同。面板身份只在服务器保存，不把原始 training-validation payload 下载到本地。

## 7. 正例生成硬 Gate

Gate 逐条件计算，macro-F1 永远不能覆盖任一正例失败项。

必须同时满足：

1. overall `supported_schema_valid_rate >= 0.50`；
2. Loghub 与 Zeek 各自 `supported_schema_valid_rate >= 0.50`；
3. overall supported-class F1 严格大于 0；
4. 两个来源族各自 supported-class F1 严格大于 0；
5. overall unsupported-class F1 严格大于 0；
6. 两个来源族各自 unsupported-class F1 严格大于 0；
7. 至少产生一条 predicted-supported，且其程序化 pointer binding integrity rate 等于 1.0。

`supported_edge_exact_rate` 作为语义诊断报告，但本原子 Gate 的首要问题是先证明“正例路径可生成且结构可接纳”。未来 S3 联合训练或主线接入必须另设 edge semantic Gate，不能只凭 schema 通过进入正式测试。

## 8. Checkpoint 选择规则前移

未来若建立新 S0–S3 数据并重新训练，checkpoint 选择必须先做 eligibility，再排序：

```text
eligible = supported-schema overall/each-family 过线
           AND supported-F1 overall/each-family > 0
           AND unsupported guardrail 过线
           AND pointer binding integrity == 1

if no eligible checkpoint:
    STOP；不得选择“相对最好”的拒答 checkpoint
else:
    只在 eligible 集合内排序
```

合格集合内的排序顺序为：supported-schema、supported-F1、supported edge exact、unsupported-F1、family macro-F1、assistant-token NLL、较早 epoch。macro-F1 从主选择指标降为后置排序项。

## 9. 结果分支

### 9.1 至少一个条件通过正例 Gate

只允许得出：新架构在 training-validation 小面板上具有继续研究正路径的资格。随后可以提出 S0–S3 数据设计 amendment，但仍不自动授权：

- 构造或下载新训练数据；
- 重新 QLoRA；
- 选择新 checkpoint；
- development/test、C07–C12 或 M3 运行；
- Paper A 或正向论文结果措辞。

### 9.2 两个条件均失败

LLM 当前路线停止，不再通过换 checkpoint、新 seed、宽松 parser 或正式测试补救。主线保留 `RULE-STRONG` / `REUSE-HYBRID` 编译器，并如实记录约束解码和程序化 pointer 绑定仍未打破 supported collapse。

## 10. 当前授权边界

本次仅授权并已实现：

- pointer-free JSON Schema；
- pointer binder；
- 模型惰性 runner；
- server-side scorer；
- 正例硬 Gate 与未来 checkpoint eligibility；
- 新面板选择和模型无关测试；
- v0.44 哈希合同与 authority。

仍未授权：

- 安装 `lm-format-enforcer` 或改变服务器 runtime；
- 新模型、tokenizer、adapter 或权重下载；
- 4090 模型调用；
- 第二次 v0.43 运行或旧输出重算；
- S0–S3 数据构造或 QLoRA；
- development/test、C07–C12、M3、`run_mvp.py` 或 Paper A 修改；
- raw generation、checkpoint 或 adapter 下载。

## 11. 实施结论

v0.44 已把本轮负结果暴露的两个合同错误同时消除：

1. pointer 从概率生成目标改为确定性证据绑定；
2. supported-schema 与 supported-F1 从结果解释项前移为执行和 checkpoint 选择硬门槛。

下一安全动作是形成并审核 constrained-decoding 依赖兼容预检 authority；在该 authority 通过前，模型调用数保持为 0。
