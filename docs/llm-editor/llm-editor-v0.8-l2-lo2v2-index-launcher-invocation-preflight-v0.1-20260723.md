# LO2v2 index launcher / invocation freeze + preflight v0.1

日期：2026-07-23  
Authority base：`26a3b3f0fa73bf94495b86ca47e74e865aafe39c`  
状态：`frozen_launcher_invocation_and_preflight_pass_download_not_authorized`

## 结论

`lo2v2_index_json` 的 launcher、curl executable identity、exact argv 与本地非网络 preflight 已冻结。

**当前仍未激活 execution-authority：initial attempts=`0`，download=`false`。**

只有后续新的用户授权明确点名 `lo2v2_index_json`，并在执行前重新核对全部 hash、目标不存在和容量，才可激活唯一一次 initial attempt。

## Authority chain

| 对象 | Commit / SHA-256 |
|---|---|
| Exact acquisition contract | commit `4231a2e`; SHA-256 `30e736a454ae5513591872bf8e3aa63372a51225db34f51436a8750d11c9374d` |
| 未激活 execution-authority | commit `26a3b3f`; SHA-256 `ec883c941ba583c44948921f86bc134f94ac49b3067d51f741f6b6c324ccc97f` |
| Launcher | local frozen source; SHA-256 `2a91304d96c1271a5a1943f137f42151836131259786e073a330893bd8b8fbb7` |
| curl executable | `C:\WINDOWS\system32\curl.exe`; version `8.21.0`; SHA-256 `73d24149ff289afc49ec41f08918ef9faa727d39ad993e929757dc2ddafab805` |

Launcher：

`datasets/llm/download_lo2v2_index_v0_1.ps1`

该脚本本轮只被静态解析和哈希，没有执行。

## 冻结 invocation

```text
--fail
--location
--silent
--show-error
--retry 0
--connect-timeout 60
--max-filesize 31028530
--output datasets/llm/local_audit_cache/lo2v2-bounded-v0.1/raw/LO2v2_index.json
--url https://zenodo.org/api/records/18937117/files/LO2v2_index.json/content
```

冻结属性：

- PowerShell argument array 直接调用，不使用拼接 shell string；
- `--retry 0`；
- 无 `--continue-at`；
- 无 `--range`；
- 无 `--write-out`；
- response body 只能写入唯一冻结目标；
- exact size `31,028,530` 通过后才计算 MD5；
- MD5 必须为 `2efcff67820ba1df40fae362919271eb`；
- 成功输出只含脱敏状态，不含 payload 或 raw JSON；
- 脚本不打开、不解析 JSON，也不启动 audit。

## Preflight

| 检查 | 结果 |
|---|---|
| Contract SHA 匹配 | 通过 |
| Execution-authority SHA 匹配 | 通过 |
| Launcher PowerShell parse errors | `0` |
| curl 存在且已哈希 | 通过 |
| Frozen target 已存在 | 否 |
| Available bytes | `651,846,590,464` |
| Required bytes | `31,028,530` |
| Capacity Gate | 通过 |
| Launcher / curl executed | 否 |
| HTTP/network request | 否 |
| Attempt consumed | 否 |

preflight 只检查 identity、脚本语法、目标不存在和容量；没有创建 target parent、cache 或目标文件。

## 激活边界

当前：

- `execution_authority_activated=false`
- `initial_attempts_authorized_now=0`
- `download_authorized_now=false`
- `automatic_retry=false`
- `resume=false`

后续明确点名 `lo2v2_index_json` 时，最多只能激活一次 initial attempt。preflight 通过、文件存在或 commit 存在都不能自动激活。

激活前还必须重新检查：

1. contract SHA；
2. execution-authority SHA；
3. launcher SHA；
4. curl executable SHA；
5. frozen target 仍不存在；
6. available capacity 仍超过 exact bytes。

## 成功或失败后的硬停

失败：只记录脱敏 failure，禁止 retry、resume、换源、换 revision、换对象、打开 JSON 或改 role/credit。

成功：必须先 exact size，再 MD5；两者通过后只记录脱敏 verified result，并立即硬停。不得自动打开或解析 JSON，不得启动 notice/schema/manifest/lineage/label/overlap/pointer audit。

## 权限

| 权限或 credit | 当前状态 |
|---|---|
| Launcher creation | 已完成 |
| Launcher / curl execution | 未授权 |
| Network / download | 未授权 |
| Initial attempts | `0` |
| JSON open/read/parse | 未授权 |
| Audit / runtime archive | 未授权 |
| Catalog / source role / train admission | 未授权 |
| Family / lineage / sample / quota credit | `0 / 0 / 0 / 0` |
| L2 Gate | `false` |
| Commit / push of launcher and preflight | 未授权 |

