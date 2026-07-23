# PANDAcap RR Acquisition Execution Authority v0.1

**状态：`frozen_one_initial_attempt_authorized`**

用户点名授权：

> `pandacap_eurosec2020_rr_archive` 一次获取 → exact size + MD5 硬停 → 成功后冻结 reader + privacy/CD/notice/manifest 合同。

本执行权只允许一次 initial attempt，不允许自动 retry、resume、换源、下载 QCOW/PCAP 或打开 archive。

## Frozen target

| 字段 | 值 |
|---|---|
| Target ID | `pandacap_eurosec2020_rr_archive` |
| Record / revision | `3759652 / 4` |
| Key | `eurosec2020-pandacap-rr.zip` |
| Exact bytes | `14,897,472,844` |
| MD5 | `1624d475a6bb337451f0ce201fb17456` |
| URL | `https://zenodo.org/api/records/3759652/files/eurosec2020-pandacap-rr.zip/content` |
| Maximum attempts | 1 |
| Automatic retry | false |
| Resume | false |

## Frozen launcher

| 字段 | 值 |
|---|---|
| Script | `datasets/llm/download_pandacap_rr_v0_1.ps1` |
| SHA-256 | `7d912856fdeea0d55d849130d76cbfe84c43c8a5af3960bb8bcb88c8e6419dbf` |
| PowerShell parse errors | 0 |
| curl | `C:\WINDOWS\system32\curl.exe` |
| `--retry` | `0` |
| `--continue-at` | absent |
| `--write-out` | absent |
| Pre-existing target | absent |
| Available bytes | `659,282,071,552` |

Launcher 直接以 PowerShell argument array 调用 curl。HTTP body 只能写入冻结 target；stdout 不得承载 payload。

## Terminal behavior

成功路径：

1. curl exit code 必须为 0；
2. 先核 exact size；
3. exact size 通过后才计算 MD5；
4. 两者都通过才记录 `verified`；
5. 硬停，不打开 archive；
6. 冻结现有 reader identity 与 privacy/CD/notice/manifest 合同及未执行脚本；
7. 再次硬停，等待 audit execution 独立授权。

失败路径：

1. 只记录脱敏 target、实际 bytes、exit status 和 stderr 摘要；
2. 不自动 retry；
3. 不 resume；
4. 不换 revision、mirror 或 artifact；
5. 不下载 QCOW/PCAP；
6. 不打开或复用 partial object；
7. 不冻结 reader，不执行 archive audit。

## Unchanged prohibitions

- 不读取 archive、central directory、member、trace 或 payload；
- 不读取 credential、secret、attacker command、downloaded payload、PII、network content、label 或 ground truth；
- 不写 effective catalog；
- 不改 source role、family、lineage、sample 或 quota；
- 不生成训练样本；
- 不跑 baseline 或微调；
- 不碰 Kernel、Γ 或 M3*；
- 不标 L2 通过；
- 不 git push。
