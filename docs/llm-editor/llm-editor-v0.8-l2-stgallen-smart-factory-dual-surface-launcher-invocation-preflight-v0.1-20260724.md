# St.Gallen 双表面 launcher / invocation + 非网络 preflight v0.1

日期：2026-07-24

Authority base：`8440035aae0d4763f120cb4fd8a9a291b869ece8`

状态：`frozen_launcher_invocation_and_non_network_preflight_pass_activation_absent_acquisition_not_authorized`

## 裁断

St.Gallen 双表面的 launcher、调用面、可执行文件身份和非网络 preflight 已冻结。当前仍是：

- activation 文件不存在；
- 每个 surface 的已授权 attempt 为 `0`；
- launcher 与 curl 均未执行；
- 未发 HTTP 请求；
- 未创建 acquisition 目录或目标文件；
- 未打开或解析任何 payload；
- 未启动 audit。

本轮只建立技术入口，不授予 acquisition 权。下一步必须由新的显式授权**同时点名两个 target**，并且每面最多激活一次 initial attempt。

## Authority chain

| 对象 | Commit / SHA-256 |
|---|---|
| Exact dual-surface contract | commit `90a3610`; SHA-256 `f7a794e0774ecd1df58da98d487369892109644c706728cc23bc9ccf2b12af20` |
| 未激活 execution authority | commit `8440035`; SHA-256 `b8ab19fe2f46990ef617123a073419394f40a771064e067be2996f879b1ea7d8` |
| Launcher | local frozen source; SHA-256 `0d2ead3b5fcba69d57ed1251ee336600f929fffe7560dc03cd3c67d638bc32ed` |
| Windows PowerShell | version `10.0.26100.8875 (WinBuild.160101.0800)`; SHA-256 `7600ffe12da441fe89d035b13801e8e91d064bc544a27b19a5cf49f6ab8b18f5` |
| curl | version `8.21.0`; SHA-256 `73d24149ff289afc49ec41f08918ef9faa727d39ad993e929757dc2ddafab805` |

Launcher：

`datasets/llm/download_stgallen_smart_factory_dual_surface_v0_1.ps1`

PowerShell parser 静态检查错误数为 `0`。脚本只被解析和哈希，没有执行。

## 冻结目标与顺序

| 顺序 | Target ID | 隔离面 | Exact bytes | MD5 |
|---|---|---|---:|---|
| 1 | `stgallen_camunda_process_manifest_surface` | protected manifest | 111,548 | `a56fb7b92ad99a8106ff3c75a2d94c6f` |
| 2 | `stgallen_training_sensor_log_surface` | model-candidate sensor | 59,901,231 | `1b310fe1bbbbe53511db015375df8a41` |

执行语义是“原子授权、串行执行”：未来 activation 必须一次同时点名两面，但 launcher 必须先获取 protected manifest。只有 manifest 的 curl exit code、exact size 和 MD5 全部通过后，才允许创建 sensor 目录并启动 sensor 的唯一一次 attempt。

任一面失败都硬停。manifest 失败时 sensor attempt 不会启动；sensor 失败时不重试，也不得打开已经校验通过的 manifest。

## 冻结调用面

工作目录必须是该 worktree 根：

```text
C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe
-NoLogo
-NoProfile
-NonInteractive
-ExecutionPolicy RemoteSigned
-File datasets/llm/download_stgallen_smart_factory_dual_surface_v0_1.ps1
-ActivationJson docs/llm-editor/llm-editor-v0.8-l2-stgallen-smart-factory-dual-surface-acquisition-activation-v0.1-20260724.json
```

该 activation 文件当前不存在，也未获创建或激活授权。launcher 在任何网络动作前要求它：

1. 状态为 `activated_dual_surface_initial_attempts_authorized`；
2. 同时、按冻结顺序点名两个 target；
3. 每个 target 的 `initial_attempts=1`，每面上限为 1、总上限为 2；
4. 钉住 contract、execution-authority、launcher、curl 和 PowerShell SHA-256；
5. 重核 record `14441997` revision `8`、两目标仍不存在、容量及隔离路径；
6. 明确禁止自动 retry、resume、其他 target/source、payload read/parse 和 audit。

preflight、文件存在或 Git commit 都不能自动激活 attempt。

## curl 参数

两面都使用 PowerShell argument array 直接调用，不拼 shell string：

```text
--fail
--location
--silent
--show-error
--retry 0
--connect-timeout 60
--max-filesize <该面的 exact bytes>
--output <该面的冻结隔离路径>
--url <该面的冻结 Zenodo URL>
```

其中：

- 禁止 `--continue-at`；
- 禁止 `--range`；
- 禁止歧义 `--write-out`；
- response body 只能写到该面的唯一冻结目标；
- exact size 通过后才能计算 MD5；
- 成功输出仅含脱敏状态，不含 payload、member、字段或原始标识；
- 脚本不打开、不解析两份 surface，也不调用 audit。

## 非网络 preflight

| 检查 | 结果 |
|---|---|
| Contract SHA 匹配 | 通过 |
| Execution-authority SHA 匹配 | 通过 |
| Launcher PowerShell parse errors | `0` |
| Launcher SHA 已记录 | 通过 |
| curl / PowerShell identity 与 SHA | 通过 |
| Protected manifest 目标存在 | 否 |
| Sensor 目标存在 | 否 |
| St.Gallen acquisition raw root 存在 | 否 |
| 两条目标路径的现有 ancestor reparse points | `0` |
| Available bytes | `650,419,748,864` |
| Required bytes | `120,025,558` |
| Capacity Gate | 通过 |
| Fresh registry revision recheck | 未做；本轮明确为非网络 preflight |
| Launcher / curl executed | 否 |
| HTTP/network request | 否 |
| Attempt consumed | 每面 `0` |

当前只从已提交合同复核 record ID 与 revision。未来 activation 仍须在不访问 payload 的前提下闭合“revision 未变化”证明；本轮没有用网络请求假装完成该项。

## 失败与成功后的硬停

失败时只允许记录 target ID、surface class、observed bytes、process exit status 和脱敏 stderr 摘要。禁止自动 retry、resume、换源、换 revision、换对象、打开 surface、改 role/credit 或启动 audit。

成功时两面都必须先 exact size、再 MD5；只有两组校验均通过才能报告 `dual_surface_verified=true`，随后立即硬停。成功 acquisition 仍不等于 source role、train admission、lineage、sample 或 quota。

## 当前权限边界

| 权限或 credit | 当前状态 |
|---|---|
| Launcher / invocation freeze | 已完成 |
| Launcher / curl execution | 未授权 |
| Activation creation / activation | 未授权 |
| Network / download | 未授权 |
| Initial attempts | 每面 `0` |
| Surface open/read/parse | 未授权 |
| Privacy/notice/schema/manifest/lineage/binding/pointer audit | 未授权 |
| Catalog / source role / train admission | 未授权 |
| Family / lineage / sample / quota credit | `0 / 0 / 0 / 0` |
| L2 Gate | `false` |
| Commit / push 本轮三个冻结工件 | 未执行 |
