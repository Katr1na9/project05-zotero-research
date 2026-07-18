# Paper B Phase 1 train-null 来源闸门 v0.1

状态：`superseded_by_cisa_kev_literature_audit_20260718`

日期：2026-07-17

## 1. 结论先行

> 2026-07-18 终态：本文件保留为 V3-BN-01 提案历史。后续官方来源与同行文献审查
> 已否决 CISA KEV 的正式 train-null 资格，并取消 50 条单人 feasibility 审核；KEV
> 仅可作为隔离的 `non_entailing_contract_negative` 诊断集，正式训练 Gate 计数为 0。
> 权威结论见 `cisa-kev-hard-negative-literature-audit-v0.1-20260718/`。

目前没有一个 routine/status 日志来源可以直接、诚实地批准为正式
train-null 族。原因不是许可或数量，而是语义：常规主机、Windows、OpenStack
或审计日志通常本身就能表达 process/file/network/system 的 SPO。仅因它们是
“正常”“良性”或不带告警，就把它们标为 null，会违反已经冻结的 null 定义。

本轮得到两个不同性质的可选项：

- `omerbenamram/evtx` 的 `security.evtx` 是唯一值得做小规模可行性抽查的
  routine-log 候选，但现在不能批准为正式来源；
- CISA KEV 是更有科学意义的“静态安全参考负例”：它说明漏洞能力和缓解措施，
  但不证明某台主机发生了执行、访问或连接。它可以训练模型区分“背景知识/可能性”
  与“已观察事实”，但不属于原 Option B 写死的 routine/status 日志，必须显式修订
  后才能使用。

## 2. 候选裁决

| 候选 | 元数据 | 裁决 | 原因 |
|---|---|---|---|
| CISA KEV | CC0；commit `87ba74fc…`; 1,647 条；JSON 1,552,342 bytes | **建议作为修订候选** | 静态参考条目不证明案例内行为，适合做 source-grounding hard negative；但改变了 Option B 的来源类型，且需限制占比，防止模型只学会识别来源格式。 |
| `omerbenamram/evtx` `security.evtx` | MIT/Apache-2.0；release 0.12.2 commit `99a6def7…`; README 称 30 MB | **仅保留 50 条 feasibility** | 许可清楚、来源独立，但样本来源说明不足；Windows Security 事件很可能仍是合法 observation，无法预先保证 240 条 null。 |
| OpenStack Nova logs | GPL-3.0；100k normal logs | **拒绝** | VM 创建/销毁/配置日志本身支持系统、进程或网络 SPO；normal/abnormal 文件名不能作监督。 |
| AECID anomaly-log aggregate | GPL-3.0 仓库，底层多来源 | **拒绝** | 含 Loghub 派生来源，与现有族不独立；依赖 normal/abnormal split，且底层许可各异。 |
| EVTX ATT&CK samples | GPL-3.0；200 个 EVTX | **硬拒绝** | 明确按 ATT&CK/TTP 和路径组织，违反 no-TTP/no-path-supervision；事件本身也偏正 observation。 |

原始元数据证据保存在：

- `sources/research_llm-train-null-source-candidates-metadata-20260717.json`
- `09-experiments/llm_finetuning_v0.3/generated/train-null-source-candidate-review.csv`

两份文件的用户决策栏均为空，`download_authorized=false`。

CISA 固定版本的精确元数据为：JSON blob
`8bf66834de2ae94decf5958426a49791ac1e7`，schema 3,407 bytes / blob
`3d49b7270847e6088d8e49f5087ef5562e7917c9`，CC0 LICENSE 7,469 bytes / SHA-256
`8DFCF2D0CBA33BEDE386EB470DAF2AC08CAF6540FC2516BAAB10DD546F90938A`。

## 3. 推荐修订：CISA KEV 只做受限 hard negative

若批准，应新增一个小修订，而不是把 KEV 偷换成 routine/status 日志：

1. 来源名称写为 `static-security-reference hard negatives`，不写 benign log；
2. 只使用 KEV JSON/CSV 自身字段，不抓取或复制第三方链接内容；
3. 每个 packet 明确标注来源类型为 reference，而不是 host/provenance event；
4. null 理由只能是“没有案例内已观察行为”，不能是“漏洞不存在”或“没有攻击”；
5. 屏蔽 actor、TTP、campaign、ransomware 标签；`knownRansomwareCampaignUse`、
   `notes`、第三方 URL 和 remediation prose 默认不进入模型输入；
6. 先做不超过 50 条作者 feasibility，逐条确认没有可接受目标 SPO；
7. 若 50 条接受率不足以投影到至少 240 条最终 null，立即否决，不改规则追数量；
8. 即使可行，KEV hard negatives 在最终 200 个 train-null 中最多占 50%，其余来源
   仍需不同模态，避免模型靠 source type 机械弃权；
9. 仍需 blocked-family、exact、5-gram exclusion、1024-token Gate 和确定性抽样；
10. 对外措辞保持 `task/schema-adapted observation compiler`，不得称 APT-domain
    fine-tuning。

上述条件已固化为不具授权效力的机器可读草案
`V3-BN-01`：`09-experiments/llm_finetuning_v0.3/generated/train-null-source-decision-contract-draft.json`。
它进一步写死：只选 JSON、不重复获取 CSV；50 条按
`SHA256(source_id|cveID)` 升序确定；若接受比例的 95% Wilson 下界乘以排除后总体
不足 240，则直接否决该来源，不得换抽样规则追数量。若总体仍为 1,647 且抽满 50
条，对应最低为 13 条通过。

## 4. 若坚持 routine/status 日志

只建议批准一个非常小的 `security.evtx` 可行性步骤：最多解析并抽取 50 条，
不进入训练目录、不构建 Task 7、不改现有队列。每条仍须按 frozen contract 审核。
若 Windows 事件中的主体、动作和对象足以形成合法 SPO，该条必须判 observation，
不能因为 Event ID 常见或行为正常而判 null。

这一步只能回答“该来源是否值得继续”，不能授权完整语料获取或正式 packet 构建。

## 5. 当前硬停

在你明确选择并批准前，以下动作仍禁止：候选语料下载、Task 7 packet 构建、
tokenizer/Qwen 下载、环境安装、训练和正式推理。

建议决策：优先审阅并批准/拒绝“CISA KEV 受限 hard-negative 修订”；如果你坚持
只用 routine/status 日志，再考虑 50 条 EVTX feasibility。两条路径都不能直接跳过
小规模语义审计。
