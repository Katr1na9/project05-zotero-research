# LLM 证据编译层主线融合 M1 接口审阅包

日期：2026-07-17  
状态：`ready_for_user_interface_review`  
范围：WP0–WP1  
下一授权：无；M1 审阅通过前不进入 WP2

## 1. 已完成

1. 路线替代记录已生效：独立 Paper B/QLoRA 默认路线暂停，LLM 改为主线前端。
2. 权威设计、prior-art review、`run_mvp.py`、`EvidenceClaim` schema 和 alignment schema 已做 SHA-256 锁定。
3. 新增 6 个合同：public request、candidate envelope、entity binding、claim-node link、admission decision、run manifest。
4. 实现 dependency-free public request builder、机械准入器和确定性 stub。
5. 准入器只读取 public request 和 candidate output，不读取 private reference 或作者 gold。
6. 旧 `run_mvp.py`、C07–C12、冻结结果和旧 schema 未修改。

## 2. 机械准入目前保证什么

controller-eligible claim 必须同时满足：

- schema 合法；
- request、artifact 和 record 哈希未被篡改；
- pointer 指向当前可见 record；
- claim pointer 与 candidate envelope 一致；
- subject/object surface 可在来源字段中机械复现；
- predicate 位于 source-specific allowlist；
- actor/campaign 结论实体不能作为 observation 进入；
- host/process/tenant scope 不与来源冲突；
- claim time window 不越过来源窗口；
- target node 存在且 claim type/predicate 满足公开资格合同。

未知或不合格 target link 不会增加 coverage，但其 observation claim 可作为 unlinked evidence 保留。所有拒收、弃权和 link rejection 均有原因码，不静默丢弃。

“通过机械准入”不等于语义真值或人类确认；private reference 只允许用于后续 scorer。

## 3. 信息边界证据

定向测试覆盖：

- 修改 private 内容不改变 public request 及其 hash；
- 递归阻断 `required_claim_ids`、`recoverable_claim_ids`、oracle 等字段；
- 即使藏在普通文本中，也拒绝 canonical `Cxx-EC-xxx` 标识；
- runner/path guard 不能读取 `private/`；
- candidate run ID 必须与 bundle/run 一致；
- 篡改 public payload 后，即使旧 hash 仍在也会硬停；
- stub 不导入 torch、transformers 或 bitsandbytes；
- authority lock 自动复核 legacy 文件字节。

## 4. 验证终态

| 验证 | 结果 |
|---|---|
| 新接口定向测试 | `25 passed` |
| Python 编译检查 | `passed` |
| 全仓库 unittest | `460 passed, 6 skipped` |
| `run_mvp.py` SHA-256 | `A7EBCF2739B7CD708011DB378D0F18AF3EB970C6236813BE7F8258D5394A952E`，与 WP1 前一致 |
| EvidenceClaim schema SHA-256 | `5FCA1B77512C5C966860781214DCB83BEE76CFECA56B9E4AE3B91657D73CA63A`，一致 |
| AlignmentState schema SHA-256 | `462C8E5F657A4467FC4B945FBAB60A2FF86D1D1470DBA8D5C3937F46E14EA61E`，一致 |

首次全仓库 verbose 运行因 120 秒工具上限在测试仍通过时被中止；随后以 300 秒上限从头安静模式重跑，129.126 秒得到完整 `OK` 终态。未把第一次不完整运行算作通过证据。

机器可读证据：`09-experiments/llm_evidence_compiler_mainline/m1-interface-readiness.json`。

## 5. 尚未完成

- 尚未建立 C04–C12 的真实 artifact catalog；
- 尚未验证 32 条冻结 reference pointer 是否全部能回指本地原始工件；
- 尚未建立 public target-node catalog 与 artifact-action visibility manifest；
- 尚未实现 `RULE-STRONG`；
- 尚未接入 CTINexus/OntoLogX 等第三方组件；
- 尚无模型、训练或正式推理；
- 尚未构造临时 controller case view；
- 尚无任何正向 LLM 或端到端实验结果。

## 6. M1 通过后的下一步

进入 WP2，但范围仍只到数据和基线：

1. 盘点 C04–C12 可访问的原始工件与 pointer；
2. 建 public artifact/target-node/action-visibility manifests；
3. 对不可解析 pointer fail closed，不用手写摘要补齐；
4. 整理并冻结 `RULE-STRONG` development snapshot；
5. 形成 M2 数据与基线审阅包。

WP2 仍不需要安装模型、下载权重、训练或双人审计。

