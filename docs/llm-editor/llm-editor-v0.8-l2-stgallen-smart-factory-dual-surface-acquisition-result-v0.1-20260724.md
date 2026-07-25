# St.Gallen 双表面 acquisition result v0.1

日期：2026-07-24

Authority base：`6c542ea32a58397d9e6436328c40a64c4e653afa`

状态：`verified_dual_surface_acquisition_complete_hard_stopped`

## 结果

冻结 launcher 只执行了一次并正常退出。manifest 先行且通过身份校验后，sensor 才启动：

| Target | Attempt | Exact bytes | MD5 | 结果 |
|---|---:|---:|---|---|
| `stgallen_camunda_process_manifest_surface` | `1/1`，已消耗 | `111,548 / 111,548` | 通过 | verified |
| `stgallen_training_sensor_log_surface` | `1/1`，已消耗 | `59,901,231 / 59,901,231` | 通过 | verified |

合计 expected/actual bytes 均为 `60,012,779`，因此：

`dual_surface_verified=true`

没有自动 retry、resume、换源、换 revision 或换对象。

## 内容访问边界

本轮 acquisition 只进行了 launcher 内冻结的 exact-size 与 MD5 身份校验：

- 未打开、解析、预览、抽样或读取任一 surface 的普通内容；
- 未再次哈希；
- 未执行 reader；
- 未启动 privacy、notice、schema、manifest、lineage、binding、semantic-fit、LLM-increment 或 pointer audit；
- protected manifest 仍禁止进入模型可见面；
- sensor surface 在独立隔离和 source-role review 前仍禁止模型可见。

## 科学与权限结论

获取和身份校验成功不证明 source-role、独立 lineage、pointer 可恢复性或 LLM 增益，也不产生训练资格。

当前仍为：

- family / lineage / sample / quota credit：`0 / 0 / 0 / 0`；
- source role：未改变；
- effective catalog：未写；
- L2 Gate：`false`；
- baseline / fine-tuning / Kernel / Γ / M3*：未授权；
- 两面的 remaining attempt：均为 `0`。

已按合同硬停。任何 reader 或数据审计都需要新的冻结合同和独立 execution authority。
