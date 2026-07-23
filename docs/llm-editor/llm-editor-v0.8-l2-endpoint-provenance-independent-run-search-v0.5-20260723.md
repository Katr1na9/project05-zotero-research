# Endpoint/provenance independent-run search v0.5

日期：2026-07-23  
authority base：`89e1c3c06930b21ad53bcab3804a87ef4c61b2b9`

## 裁断

第 4 个可单独逐族评审的方向为：

`cow160x4_cowrie_ssh_session_provenance_2026`

裁断严格停在：

**`approve_for_separate_metadata_candidate_review_not_source_role`**

没有 catalog write、source role、train admission、family/lineage/sample/quota credit 或 L2 Gate 变化。

## 为什么没有用 host、configuration 或 file count 凑数

Zenodo revision 6 的 curator 声明：

- 约 3,800 万个 SSH sessions；
- Cowrie 为每次 SSH connection 分配唯一 `session` identifier；
- 160 个 honeypot instances、4 个 configurations、14 个 countries、50 days 和 51 个 daily files 都只是环境或包装信息。

本搜索只把一个 opaque Cowrie SSH connection session 视为 candidate group。host、configuration、country、sensor、day、file、event type、attack 或 verdict 均不得形成 lineage。

## Metadata identity

| 项目 | 值 |
|---|---|
| Zenodo DOI | `10.5281/zenodo.21260400` |
| Concept DOI | `10.5281/zenodo.21260399` |
| Record revision | 6 |
| License | `CC-BY-4.0` |
| Resource type | Dataset |
| Preferred future review surface | `session_aggregation.jsonl.gz` |
| Bytes | `1,328,104,319` |
| MD5 | `1f3897650fb420c97c14ff452398c3f8` |

`session_aggregation.jsonl.gz` 只是未来逐族 metadata review 的最窄候选面，并未获下载或 audit 权。

## 高风险对象默认排除

- `data_all.zip`：curator schema 明确包含 command、username、password、URL、environment value、filename、fingerprint、network/geolocation identifiers。
- `transferred_files.zip`：curator 明确警告包含潜在恶意攻击者 payload。
- `transferred_files_metadata.csv`：不是建立 session grouping 所需对象。
- `malformed.txt`：不能建立稳定 session 或 pointer。

## 仍未闭合

1. 约 3,800 万 sessions 的 exact non-empty unique cardinality、reconnect、duplicate 和 bot-campaign correlation 未核。
2. session aggregation 是 derived surface，未证明足以形成 Candidate Claim IR。
3. privacy、credential、command、identifier、malware、nested notice 与 field allowlist 未过 Gate。
4. pointer round trip 与 protected exact/near overlap 未核。
5. 与 PANDAcap 不同 artifact、curator 和 capture technology，但同属 SSH honeypot 模态，cross-family nuisance independence 未核。
6. Zenodo/DataCite 未绑定关联论文；Crossref 没有找到 curator-bound exact publication。

## 本轮筛除的其他方向

| 候选 | 处置理由 |
|---|---|
| Orthogonal Syscall Attack Captures | 十个 archive 以 attack family 命名；无 label-independent run count |
| Miningbeat | 单一 timestamped/labeled CSV；无 source-native run/session |
| Mendeley SysCall | registry 未闭合 immutable files、bytes、checksums 和 execution mapping |
| 4-Month SSH Botnet Dataset | 28 个 interactive sessions 是 outcome-filtered subset；敏感字段边界未闭合 |
| Honey for the Agent | 声明 sessions，但官方 record 无 files/bytes/checksums |
| Multi-Regional Cloud Honeynet | 只有 event、host、sensor 和 72-hour counts；无 session/run contract |
| Cardiff Bane or Boon | 与已处置 dynamic-malware Kernel Driver/Cuckoo family 同源，不是新 family |

## 自检

- 启动 HEAD 精确匹配 authority。
- 未读取或触碰 `datasets/**`、`local_audit_cache`、ZIP/archive 或 `download_*.ps1`。
- 未下载 payload/archive。
- 未重晋 REPROD、PANDAcap、LogChunks、StreamSpot 或任何既有 hold/reject。
- 未降低 ≥4 source-native label-independent group 门槛。
- 未写 catalog，未授 credit，未 commit、未 push。
