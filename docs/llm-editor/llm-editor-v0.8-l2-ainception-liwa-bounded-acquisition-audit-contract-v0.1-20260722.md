# AInception + Liwa 有界 acquisition / manifest-lineage audit 合同 v0.1

**Branch / authority base**：`feat/llm-editor-v0.8` @ `8d090a6c54a2251328e37bcf76097e79a2627116`

**冻结日期**：2026-07-22

**状态**：`frozen_before_payload_acquisition`

## 1. 本次授权的精确含义

本合同只允许下载五个精确对象：四个 AInception ZIP 和 Liwa revision 7 的唯一 ZIP。下载后只执行 manifest-first、nested-notice、lineage grouping 与 evidence-shape/pointer 的有界探针。

以下仍未授权：

- 采用为 train source 或改变 family role；
- 授予 family、lineage、sample、modality 配额；
- 生成训练监督、Candidate Claim IR 或 normalization；
- 读取 label/ground truth；
- baseline、微调、正式评测；
- CERT、IoT-23、protected family、Kernel、Gamma 或 M3*；
- Git push 或 L2 Gate 状态变化。

## 2. 冻结的 AInception 子集

| ZIP | Bytes | MD5 | 选择层 |
|---|---:|---|---|
| `SL100.zip` | 31,592,162 | `3d7841d3eaf6d4e297cc75aa9a33fe3d` | SL100 唯一 simulation |
| `SL300_variant_7.zip` | 9,735,245,693 | `13a2fcba6a4690ca514278ce6ad2d4cf` | 先锁 SL300 覆盖，再选该层较小 archive |
| `SL700_variant_f_a.zip` | 3,358,489,764 | `8852767f1bc07b4f308483c448a31849` | 第一 distinct declared variant |
| `SL700_variant_b_a.zip` | 3,639,281,826 | `e81e2819cbb1ccda76fda080293385be` | 第二 distinct declared variant |

合计 `16,764,609,445` bytes，约 `15.61 GiB`。

选择规则先要求覆盖官方 metadata 声明的 SL100、SL300、SL700 三个 storyline，再在已锁 strata 内控制容量，并增加第二个 SL700 declared variant。它不是“四个最小 ZIP”的 size-only 选择。

选择标签只用于 acquisition stratification，不得进入 model view、supervision、pointer 或未来 target。看见 archive 内容后禁止替换未选 ZIP。

## 3. 冻结的 Liwa archive

仅允许：

| Artifact | Bytes | MD5 |
|---|---:|---|
| `Forensic Value of Enhanced Endpoint Telemetry in Active Directory Attack Detection A Controlled Co.zip` | 7,357,185 | `94f2af6a756a0841126d51a55bd8fe85` |

本授权不扩展到 Liwa 的其他 record、revision、附件或相关材料。AInception + Liwa 的下载总上限为 `16,771,966,630` bytes，约 `15.62 GiB`。

## 4. Manifest-first 规则

每个 archive 必须先通过 byte size 与 MD5，之后才能读取 central directory。禁止 extract-to-disk，只能流式查看授权 archive。

可持久化的信息仅包括：

- member/directory 数量与压缩、解压总字节数；
- suffix 和排除类别计数；
- manifest/CRC aggregate hash；
- 最多 64 个不可逆 member-path hash；
- notice、raw-evidence candidate、schema/pointer 类别计数；
- day-level timestamp range 与 hashed host/run cardinality；
- raw-vs-summary、lineage、失败 Gate 与理由。

不得持久化 raw member path、hostname、timestamp 细粒度值、IP、user、command、file/registry 值、event message、CSV row、JSON object 或 payload excerpt。

## 5. 排除和 bounded probe

路径含 label、answer、ground truth、AttackMate、timeline、ATT&CK/technique/tactic/actor、STIX/IOC、graph、BloodHound、screenshot、statistics、rule 或 config 的成员不进入 evidence probe。PCAP、图片、PDF 和 Office 文件也不得打开。

例外仅是 basename 命中 README/LICENSE/NOTICE/COPYING 的 bounded notice scan，用于检查 nested rights conflict；每成员最多 128 KiB，不保留文本。

对非禁止的 CSV/JSON/JSONL/NDJSON/LOG/TXT/XML：

- 每成员最多读取 2 MiB、128 records；
- 每个 AInception ZIP 最多 8 个文本成员、总 16 MiB；
- Liwa 最多 40 个文本成员、总 80 MiB；
- 只保留 schema-category booleans、计数、day-level summary 与不可逆 hash；
- forbidden supervision 字段优先于所有 allowlist。

成员选择算法同样在下载前冻结：AInception 对每个 eligible text suffix 取 normalized path 字典序首尾，去重后再按字典序补足至 8 个；Liwa 对所有 eligible CSV 按 normalized path 字典序读取，若超过 40 个则 fail closed。

## 6. Lineage Gate

### AInception

一个精确 ZIP 最多是一个 lineage candidate。通过条件：checksum 正确、archive path 安全、至少存在一个非禁止 raw-evidence member、四个 archive 无相同 archive hash 或完全相同 manifest signature。官方 record 的“complete simulation”声明可支持 `source-native lineage candidate`，但不能支持 statistical independence 声称。

### Liwa

从 CSV member 的 source-native run token 构造 group，删除 native/Sysmon/Wazuh/enhanced 等 logging-view token 后，同一 run 的多视图仍属于同一 lineage。必须至少有四个稳定 run group，且每组至少一个 CSV 呈现 raw-event schema；detector-only summary、重复 content/signature 或无稳定 run token 的 CSV 不计。

Liwa 不能贡献 null/benign lineage。row、attack type、view、path 和任意时间窗都不能补 lineage 数。

## 7. Fail-closed

以下任一情况不得放宽合同：

- size/MD5 漂移；
- archive path traversal 或损坏；
- nested notice 与 record-level CC-BY-4.0 冲突；
- raw evidence 只存在于被禁止或未授权的成员类型；
- 预注册 probe 无法判断 pointer/schema；
- AInception 不足四个 source-native lineage candidate；
- Liwa CSV 是 detector/statistical summary 或不足四个稳定 execution groups。

失败时只报告失败，不自动换 archive、扩大 suffix/field allowlist、增加读取上限、放宽 lineage 规则或重新下载其他来源。

## 8. 终点

完成 audit 后，即使 lineage/evidence-shape 通过，也只可产生下一道 source-role review 的证据；不得直接进入 train。L2 Gate、baseline 与微调继续关闭，Git 保持未推送。

机器可检合同见 `llm-editor-v0.8-l2-ainception-liwa-bounded-acquisition-audit-contract-v0.1-20260722.json`。
