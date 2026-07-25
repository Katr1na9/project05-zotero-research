# PANDAcap 逐族 Metadata Candidate Review v0.1

**裁断：`approve_as_metadata_candidate_not_source_role`。**

PANDAcap 可以保留为独立的 endpoint/provenance metadata candidate。官方 Zenodo revision 4 与固定 curator 文档共同声明了 63 条 PANDA full-system traces，并把来源原生边界定义为：每个 root SSH session 触发一次 30 秒 recording。该分组声明不依赖 attack class、verdict、目录类别或人为切窗，因此通过“值得单独保留为 metadata candidate”的最低门槛。

这不是 source-role 批准。63 条是 **candidate capture groups**，不是 63 个已经核验的独立 lineage。当前不写 effective catalog，不分配 family、lineage、sample 或 quota credit，不填补 train slot，也不通过 L2 Gate。

本轮默认只评：

`eurosec2020-pandacap-rr.zip`

QCOW、PCAP、Academic Torrents mirror 和 individual samples 均未纳入默认表面；本轮没有下载、打开或列举任何 archive，也没有读取 trace、payload、label、ground truth 或模型输出。

## 1. 逐族结论

| 项 | PANDAcap 结论 |
|---|---|
| Dataset identity | pass |
| Zenodo revision / version | `3759652 / revision 4 / version 1.0` |
| DOI / concept DOI | `10.5281/zenodo.3759652` / `10.5281/zenodo.3759651` |
| Record-scope license | CC-BY-4.0；nested notice 未审 |
| 默认对象 | `eurosec2020-pandacap-rr.zip` |
| 默认对象 bytes | `14,897,472,844` |
| 默认对象 MD5 | `1624d475a6bb337451f0ce201fb17456` |
| 官方 trace 声明 | 63 |
| 来源原生 capture boundary | 每个 root SSH session 触发一次 30 秒 recording |
| `>=4` label-independent capture 声明 | pass |
| 一 trace ↔ 一唯一 SSH session manifest | 未发布 / 未核 |
| VM reset / snapshot restore | 未声明 |
| duplicate / repeat session policy | 未声明 |
| RR ↔ QCOW ↔ PCAP session binding | 未核 |
| RRArchive reader identity | 未钉 |
| Privacy / secrets / malware isolation | 未核 |
| Pointer recoverability | 未核 |
| Protected exact/near exclusion | 未执行 |
| Benign/null capacity | 0 |
| Metadata candidate | **approved** |
| Train source role | **false** |
| Catalog write | **false** |
| Download / archive audit | **false / false** |
| Family / lineage / sample / quota credit | `0 / 0 / 0 / 0` |
| Replacement slot | vacant |
| L2 Gate | false |

因此当前状态是：

`approved_metadata_candidate_pending_separate_exact_bounded_acquisition_contract_and_reader_privacy_manifest_audit`

## 2. 为什么可以保留

### 2.1 身份和 artifact 可复核

Zenodo revision 4 固定：

- Dataset DOI：`10.5281/zenodo.3759652`
- Concept DOI：`10.5281/zenodo.3759651`
- Version：`1.0`
- License：`CC-BY-4.0`
- 四个对象总字节：`22,433,496,290`
- 每个对象均有 MD5

DataCite 对 title、creator、version、Dataset 类型和 rights 的记录相符。Crossref 验证了 EuroSec 2020 论文 `10.1145/3380786.3391396`，Zenodo 将数据集标为该论文的 supplement。

### 2.2 分组声明来自采集过程

Zenodo 与固定的 `vusec/pandacap` 数据集文档都声明：

- 采集期为 2020-02-21 至 2020-02-23；
- 共 63 条 PANDA traces；
- root SSH session 开始时，`recctrl` 启动一次 30 秒 recording。

因此候选 grouping key 来自 source-native session/capture，而不是：

- attack family；
- technique 或 verdict；
- 文件所在 class path；
- 为满足配额而事后切出的时间窗。

这足以支持 metadata candidacy，但不足以支持 lineage credit。

### 2.3 endpoint/provenance 相关性强

PANDA full-system record/replay trace 与 endpoint execution/provenance 任务直接相关。若后续所有 Gate 均通过，候选用途可能包括：

- 从可见 replay event 产生 Candidate Claim IR；
- 给出 unbound/ambiguous pointer suggestion；
- entity、time 或 pointer 不可靠时 abstain；
- 从可见 endpoint evidence 提出 candidate q。

这些用途目前都只是 fit 判断，不是 sample 或 source-role 批准。

## 3. 为什么仍不能算 train family

### 3.1 63 条声明不等于独立 lineage

还没有机器可检证据证明：

- 一条 trace 对应一个唯一、非空 SSH session；
- session 之间执行了 VM reset、snapshot restore 或等价 reinitialization；
- 没有 duplicate/repeat capture；
- 63 条在统计上相互独立；
- RR、QCOW、PCAP 的同-session 绑定完整且无漂移。

所以 lineage credit 必须保持 0。

### 3.2 多视图不得重复计数

RR、QCOW disk delta 和 PCAP 是同一批 63 sessions 的不同视图：

```text
one SSH session
  ├─ RR full-system trace
  ├─ QCOW disk-delta view
  └─ PCAP network view
```

它们必须进入同一个 lineage group 和同一个 split。三个视图不能算三个 family，也不能把一个 session 扩成三条 lineage。

### 3.3 RRArchive reader 尚未闭合

2020 年的 curator 文档把 RRArchive 描述为 upcoming，并说明 PANDA support 仍在进行中。当前没有冻结：

- reader 名称与版本；
- executable/package identity；
- SHA-256；
- invocation；
- parser；
- fail-closed 行为。

因此即使未来另行批准 acquisition，也不能直接打开 archive。

### 3.4 隐私、秘密与恶意内容风险高

真实 SSH honeypot 的 full-system trace 可能包含：

- credentials 或 secrets；
- attacker commands；
- downloaded payload；
- personal/network identifiers；
- 恶意或 dual-use 内容。

QCOW 可能包含敏感或恶意文件，PCAP 可能包含网络标识和 session content。Record-scope CC-BY-4.0 不自动证明 archive 内第三方权利、隐私处置或训练安全已经闭合。

### 3.5 没有 benign/null 容量

该集合是 SSH honeypot/brute-force 场景，官方 metadata 没有声明可独立使用的 benign/null execution pool，不能单独修复 class balance。

## 4. 默认 artifact 边界

未来若另行授权 exact bounded acquisition contract，只允许默认考虑：

| 字段 | 冻结候选值 |
|---|---|
| Record | Zenodo `3759652`, revision 4 |
| Key | `eurosec2020-pandacap-rr.zip` |
| Bytes | `14897472844` |
| MD5 | `1624d475a6bb337451f0ce201fb17456` |
| Official URL | `https://zenodo.org/api/records/3759652/files/eurosec2020-pandacap-rr.zip/content` |

这张表不是下载授权。正式 acquisition contract 仍须另行写死 byte ceiling、resume policy 与 retry ceiling。

默认排除：

- `eurosec2020-pandacap-qcow.zip`；
- `eurosec2020-pandacap-pcap.zip`；
- Academic Torrents mirrors；
- standalone VM images；
- individual samples；
- 未钉死的替代源。

`ubuntu16-planb-kernelinfo.conf` 只是 supporting profile，不能计 lineage 或 sample。

## 5. 下一道 Gate

若以后继续，必须逐道、独立授权：

1. 为 `eurosec2020-pandacap-rr.zip` 冻结 exact bounded acquisition contract；
2. 在任何 archive inspection 前冻结 reader/tool amendment；
3. 冻结 central-directory、nested-notice、member、per-member bytes、total bytes 和输出脱敏上限；
4. 不读 ordinary trace content，先验证是否存在至少 4 个稳定、非空、label-independent trace/session identifiers；
5. 核 session manifest、duplicate/repeat、reset/reinitialization 与同-session multi-view binding；
6. 冻结 privacy-safe field allowlist，排除 credential、command、payload bytes、secret、PII 与 raw network content；
7. 验证 pointer recoverability；
8. 执行 protected exact/near exclusion；
9. 最后才可开独立 source-role review。

任何一步不能在不读取 label、敏感内容或 hidden ground truth 的前提下闭合，都应 fail closed。

## 6. 权限边界

本评审明确没有授权：

- 下载 PANDAcap；
- 打开 archive、central directory 或 member；
- 读取 RR、QCOW、PCAP、label、ground truth 或模型输出；
- 写 effective catalog；
- 改 family role 或 quota；
- 计 family、lineage 或 sample；
- 生成训练样本；
- baseline 或微调；
- Kernel、Γ 或 M3*；
- CERT / IoT-23 下载；
- 操作正在进行的 REPROD acquisition；
- 标 L2 通过；
- git push。

机器可检依据见同名 JSON。
