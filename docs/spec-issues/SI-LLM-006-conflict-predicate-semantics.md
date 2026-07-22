# SI-LLM-006：对象冲突依赖 canonical predicate 互斥语义

**Owner**：Kernel/M3* 会话  
**LLM 轨道状态**：不阻塞 polarity 冲突保留；阻塞对象值冲突的真实集成

## 当前字段

本地 Candidate Claim IR projection 只有 `claim.subject/predicate/object/polarity`。v0.8 规定冲突来源应并存并标记 `truth_status=conflicted`，但当前共享工件没有说明哪些 predicate 是单值、互斥或允许多值。

## 阻塞案例

同一进程同时 `connected_to` 两个地址通常不是冲突；同一进程在同一时刻有两个不同 `parent_process` 则可能冲突。若仅以“subject/predicate 相同、object 不同”判断，会把合法多值关系误标为冲突；若完全忽略 object 差异，又会漏掉功能性关系的冲突。

## 建议变更

Kernel 发布只读 canonical predicate 语义表，至少声明：

1. predicate 是否允许多 object；
2. 互斥判断是否需要时间窗、实体 scope 或 polarity；
3. 语义表的版本与 hash；
4. 未登记 predicate 的默认策略（建议仅保留候选，不推断对象冲突）。

L1 本地实现只接受外部传入的 `exclusive_object_predicates`，不自行扩写 Γ 或猜测 predicate 语义。相反 polarity 仍可机械识别为冲突。

## 兼容性影响

共享语义表发布后，本地参数应替换为版本化、只读 Kernel contract。历史输出缺少该 contract hash 时，不得追溯性宣称对象冲突已完整识别。

## 对认证安全的影响

中高。过度标记会制造伪冲突并改变调查优先级；漏标会掩盖来源分歧。两者都不应由 LLM 自行裁定，更不能直接影响认证或 STOP。
