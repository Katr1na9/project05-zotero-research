# Project05 主线 LLM 证据编译层：WP4 CTI 检索与排除审计

日期：2026-07-17  
状态：`passed_s2_s3_ready_for_runtime_gate_review`  
范围：固定来源检索、逐文档来源核验、规范化、protected-family payload exclusion scan  
未授权：组件 runtime、模型/embedding、训练、正式推理、C07–C12、M3 controller integration

## 1. 结论

M3 系列与 LLM 编译层继续保持并行隔离。WP4 已将来源约束的 CTI 文本准备为 compiler component bench 输入，但尚未运行任何第三方组件或 LLM。

```text
固定 CTI 来源
→ license / origin / revision 验证
→ 只保留获批记录
→ protected-family exact + 5-gram scan
→ controller_eligible=false 的 component-bench records
```

S2/S3 独立校验终态为 `passed_s2_s3_ready_for_runtime_gate_review`，没有自动打开下一阶段权限。

## 2. 来源与记录

| 角色 | 来源 | 上游独立文档单位 | 准入记录 |
|---|---|---:|---:|
| `unit` | CTID Blueprints Intrusion Analysis JSON | 1 | 1 |
| `development` | MITRE ATT&CK malware/tool procedure text | 1 | 11,189 |
| `component_validation` | CISA 第一方安全通告 | 7 | 7 |
| 合计 | 3 个 publisher families | 9 | 11,197 |

MITRE 的 11,189 条 procedure 是同一个 STIX 文件中的重复测量，不能作为 11,189 个统计独立样本。它们只能用于开发、接口调试和确定性抽样，不能扩大论文中的有效样本量。

## 3. 许可与来源验证

- CTID Blueprints Apache-2.0 LICENSE 的实际 git blob SHA-1 与 catalog 固定值一致；
- MITRE ATT&CK 自定义宽松许可证的实际 git blob SHA-1 与固定值一致，必须保留 MITRE attribution；
- 7/7 个 TRAM 候选均包含原始 CISA URL；
- 7/7 个原始 URL 均返回 HTTP 200，最终地址仍位于 `cisa.gov`；
- 只保留通告纯文本，不复制网页 HTML、图片、脚本或第三方嵌入媒体；
- 原始上游大文件未保留在正式输出中，只记录 revision、URL、字节数和 SHA-256。

## 4. 泄漏排除审计

保护锁只包含 hash 与 5-gram hash，不包含原始测试 payload 或 private gold。

| 检查 | 结果 |
|---|---:|
| normalized exact | 0 |
| normalized 5-gram near duplicate | 0 |
| APT29 / OTRF / C07–C12 / DARPA / WitFoo 等禁止字面量 | 0 |
| `private/gold/oracle` 禁止字段 | 0 |
| 最大 Jaccard | 0.12 |
| 冻结阈值 | 0.85 |
| 排除记录 | 0 |

终态为 `passed_clean`。这只表示没有发现与保护集合的 exact/near 重合，不表示 CTI 语义已经正确或模型不会产生幻觉。

## 5. 关键工件

- `09-experiments/llm_evidence_compiler_mainline/wp4/generated/retrieval-v0.1/retrieval-manifest.json`
- `09-experiments/llm_evidence_compiler_mainline/wp4/generated/retrieval-v0.1/source-origin-audit.json`
- `09-experiments/llm_evidence_compiler_mainline/wp4/generated/retrieval-v0.1/payload-exclusion-audit.json`
- `09-experiments/llm_evidence_compiler_mainline/wp4/generated/retrieval-v0.1/admitted-records.jsonl`
- `09-experiments/llm_evidence_compiler_mainline/wp4/generated/retrieval-v0.1/s2-s3-readiness.json`
- `09-experiments/scripts/retrieve_compiler_cti_sources.py`
- `09-experiments/scripts/validate_compiler_cti_retrieval.py`

readiness 已记录所有正式工件的 SHA-256。输出中的每条记录均为 `controller_eligible=false`。

## 6. 验证

- WP4 source Gate tests：7 passed
- WP4 retrieval tests：7 passed
- WP4 independent readiness tests：6 passed
- 全部 compiler tests：67 passed
- 全实验测试：506 passed，6 skipped，346 subtests passed，0 failed

本轮没有修改 `run_mvp.py`、`run_m3star*.py`、M3Star results、C07–C12 real cases 或旧 EvidenceClaim/alignment schemas。

## 7. 下一 Gate

下一步是单独审阅 component bench 计划。即使批准，也应分开授权：

1. 固定 revision 的 CTINexus 代码获取与隔离环境 import smoke；
2. 本地模型/embedding 的具体选择与下载；
3. 仅 CTID unit 的 runtime smoke；
4. smoke 通过后才允许 development / 7-document component validation。

当前仍不需要双人语义审计。只有未来采用“语义关系正确”“无支撑断言减少”等人类语义结论时，才触发最小人工审计。
