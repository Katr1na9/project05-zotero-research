# PANDAcap RR acquisition failure v0.1

日期：2026-07-23

## 终态

唯一获授权的 PANDAcap RR acquisition attempt 已失败并硬停。

| 检查项 | 结果 |
|---|---:|
| launcher 仍运行 | 否 |
| transfer process 仍运行 | 否 |
| 冻结 expected bytes | 14,897,472,844 |
| 实际 bytes | 4,930,532,296 |
| 完成比例 | 33.0964% |
| exact-size Gate | 失败 |
| stderr | 存在但为空（0 bytes） |
| MD5 | 未计算；exact-size Gate 未通过 |

不完整对象不得视为已获取或已验证的 archive。

## 硬停确认

- 未自动重试、未 resume、未重新调用 launcher、未换源。
- 未打开、列出或解压 archive。
- 未下载 QCOW、PCAP、mirror 或 individual samples。
- 未冻结 reader，未启动 central-directory、notice、manifest 或 payload audit。
- 未写 effective catalog，未改 role、lineage、sample、quota 或 L2 Gate。
- 未生成训练样本，未运行 baseline、微调、Kernel、Γ 或 M3*。
- 本报告不包含 payload、member 或本地 raw path。

任何后续动作都需要新的显式授权。
