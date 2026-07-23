# COW160x4 metadata candidate review v0.1

日期：2026-07-23  
authority base：`89e1c3c06930b21ad53bcab3804a87ef4c61b2b9`

## 裁断

`cow160x4_cowrie_ssh_session_provenance_2026`：

**`approve_as_metadata_candidate_not_source_role`**

这只表示 metadata identity 与 source-native session grouping 候选成立；不表示 source role、train admission、lineage、sample、quota 或 L2 Gate 通过。

## 已闭合

| 项目 | 结论 |
|---|---|
| Zenodo record | revision 6，DOI `10.5281/zenodo.21260400` |
| License | record-scope `CC-BY-4.0` |
| Artifact identity | 5 个对象均有 bytes 与 MD5 |
| Session declaration | curator 声明约 3,800 万 SSH sessions |
| Grouping key | Cowrie 为每次 SSH connection 分配唯一 `session` ID |
| ≥4 source-native group Gate | 通过 |

160 hosts、4 configurations、14 countries、50 days、51 files 和约 2.11 亿 events 均不算 lineage；唯一 grouping candidate 是 opaque Cowrie `session`。

## 唯一可考虑的未来 review surface

`session_aggregation.jsonl.gz`

- bytes：`1,328,104,319`
- MD5：`1f3897650fb420c97c14ff452398c3f8`
- 性质：curator 描述的 session-level derived aggregation

它至多可以支持未来 lineage manifest/schema probe，不能自动视为训练证据。

以下对象默认 fail-closed：

- `data_all.zip`
- `transferred_files.zip`
- `transferred_files_metadata.csv`
- `malformed.txt`

raw object 明确涉及 username、password、command、URL、network/geolocation identifiers、fingerprints、filenames 与潜在恶意 payload。本评审不允许静默放开。

## 为什么不能给 source role

1. 约 3,800 万 sessions 的 exact non-empty unique cardinality 未核。
2. reconnect、duplicate、retry 与同一 bot campaign 的相关性未核。
3. `session_aggregation` 是 derived gzip surface，不是 raw endpoint execution。
4. Cowrie 是 emulated shell；command 不得写成真实 OS 执行，emulated response 不得写成真实 host state。
5. 字段物理隔离、privacy、secret、malware、nested notice 与 protected overlap 未过。
6. gzip 缺少天然随机访问；`artifact checksum + session + decompressed ordinal` pointer 尚未证明可 round trip。
7. 与 PANDAcap 是不同 curator/artifact/technology，但共享 SSH honeypot modality，不能自动跨 split。
8. 没有 curator-bound peer-reviewed publication。

## 未来必须另行授权的顺序

1. 只为 `session_aggregation.jsonl.gz` 冻结 exact bounded acquisition contract。
2. 冻结 gzip reader、hash、invocation、compressed/decompressed byte caps、line cap 与 parser。
3. 先做 bounded notice/schema/manifest probe。
4. 验证至少四个 non-empty unique sessions，以及 duplicate/reconnect/campaign grouping。
5. 冻结字段 allowlist，并排除 identifier、credential、command、URL、filename、fingerprint、geolocation、payload 和 event-type target。
6. 验证 deterministic pointer round trip。
7. 完成 PANDAcap nuisance 与 protected overlap review。

## 权限与自检

- effective catalog：未写。
- source role / train admission：否。
- family / lineage / sample / quota credit：全部 `0`。
- 下载、archive/payload audit、训练样本、baseline、微调：均未授权、未执行。
- 未触碰 `datasets/**`、cache、ZIP/archive 或 launcher。
- 未 commit、未 push。
