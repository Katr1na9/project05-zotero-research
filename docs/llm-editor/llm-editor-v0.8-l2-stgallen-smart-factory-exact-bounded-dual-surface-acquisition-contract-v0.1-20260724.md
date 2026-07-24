# St.Gallen exact bounded dual-surface acquisition contract v0.1

日期：2026-07-24  
Authority base：`00513fac3a72e765161de79674cf3e3d0acaf73a`

## 状态

`frozen_contract_only_acquisition_not_authorized`

本合同只冻结对象身份和未来执行边界，不授权：

- HTTP request 或下载；
- launcher / invocation / execution-authority；
- retry 或 resume；
- 打开、stream、parse、grep、count 或 preview；
- reader、notice、privacy、schema、manifest、lineage、binding 或 pointer audit；
- catalog、role、credit、样本、baseline、微调或 L2。

## 为什么必须是双表面

St.Gallen 候选的两个必要信息面必须永久分离：

```text
model-candidate surface
  training sensor log
  仅可能提供可见 sensor/actuator evidence

protected manifest surface
  Camunda process-instance ground truth
  仅可能供程序 binder/lineage audit 使用
  永不进入模型视图
```

Sensor log 单独存在时无法证明 source-native process-instance boundary；Camunda manifest 单独存在时又只有受保护 ground truth，不是可供模型读取的 evidence surface。因此未来若执行，必须按本合同的两个 target 共同核验身份，同时保持物理路径隔离。

## 冻结 target 1：protected manifest

| 项 | 值 |
|---|---|
| Target ID | `stgallen_camunda_process_manifest_surface` |
| Source key | `camunda-process.json` |
| Record | Zenodo `14441997`, revision 8 |
| URL | `https://zenodo.org/api/records/14441997/files/camunda-process.json/content` |
| Expected bytes | 111,548 |
| Expected MD5 | `a56fb7b92ad99a8106ff3c75a2d94c6f` |
| Future relative path | `protected_manifest/camunda-process.json` |
| Model visibility | **forbidden** |

它只允许在未来另授权后作为 sealed protected manifest 接受身份校验。即使 MD5 通过，也不得进入 input、prompt、target、pointer suggestion 或 supervision。

## 冻结 target 2：model-candidate sensor surface

| 项 | 值 |
|---|---|
| Target ID | `stgallen_training_sensor_log_surface` |
| Source key | `training_tenhertz_log_20230411-095748.txt` |
| Record | Zenodo `14441997`, revision 8 |
| URL | `https://zenodo.org/api/records/14441997/files/training_tenhertz_log_20230411-095748.txt/content` |
| Expected bytes | 59,901,231 |
| Expected MD5 | `1b310fe1bbbbe53511db015375df8a41` |
| Future relative path | `model_candidate/training_tenhertz_log_20230411-095748.txt` |
| Model visibility | **forbidden until later isolation/source-role review** |

这是唯一具有 curator 明示 10 次 process executions 的 sensor surface。文件名中的 `training` 只是来源方命名，不赋予 Project05 train role。

## 总容量与未来 preflight

- Target count：2
- Combined exact bytes：60,012,779
- 约 0.0559 GiB
- Future activation 前目标卷可用空间必须至少为 120,025,558 bytes，即 payload 总量的两倍。
- 两个 frozen target 必须都不存在。
- 任何 partial、complete、oversized 或未知旧文件都必须 fail-closed；不得 overwrite、reuse、resume、move 或 rename。

本轮没有创建这些目录或文件。

## 物理隔离

未来根目录被预先分为：

```text
raw/model_candidate/
raw/protected_manifest/
```

硬规则：

- protected manifest 不得进入 model-candidate 路径；
- sensor log 不得进入 protected-manifest 路径；
- 两个表面不得 merge、join、concatenate、annotate、repack 或 rearchive；
- 不得创建 hardlink、symlink 或其他跨表面引用；
- process-instance ID 不得写入 model-visible 文件；
- 未来 binder 只能输出另合同允许的不透明、核验过的 token。

Curator description 中的 `camunda_process-instance.json` 与实际 key `camunda-process.json` 不能静默等同；未来 audit 必须先证明映射。

## 未来执行控制（当前未授权）

任何未来 acquisition 必须另行创建并批准 execution authority，并且：

1. 同时点名两个 target ID；
2. 钉死本合同 commit 与 SHA-256；
3. 钉死 launcher/invocation 及 SHA-256；
4. 钉死两个隔离 local roots；
5. 每个 target 最多一次 initial attempt；
6. 禁止自动 retry、resume、换源或降级到单表面；
7. 先获取并校验小型 protected manifest；
8. 只有 manifest exact size + MD5 通过后，sensor attempt 才可启动；
9. 任一失败都终止双表面 acquisition。

## Integrity 顺序

每个 target 都必须：

```text
frozen path
  -> exact size
  -> MD5
  -> target_verified
```

双表面状态必须：

```text
manifest_verified
  AND sensor_verified
  -> dual_surface_verified
  -> hard stop
```

单个 target 通过不得写成双表面通过；size-only、partial 或 MD5 mismatch 均不得写成 verified。

## 明确排除

第一次 acquisition 不得获取：

- `camunda-activity.json`；
- `storage_process.bpmn`；
- `production_process.bpmn`；
- `test_tenhertz_log_20230411-103455.txt`；
- concept-record object、其他 revision、mirror、cache、byte range、renamed object 或 local slice。

其中 activity-level ground truth 会扩大 protected task/stage 暴露；两个 BPMN 是 configuration；外部 test-named sensor log 没有 exact execution count。

## 即使双 MD5 通过，仍不成立的事项

双对象 verified 只证明本地字节身份，不证明：

- Camunda 文件确含十个稳定完整 process instances；
- process instance 与 sensor interval 一一对应；
- completion、retry、partial、abort、reset、duplicate 或 interleaving 已处理；
- sensor surface 不含 process、activity、station、stage、completion 或 ground-truth leakage；
- privacy、secret、notice 或第三方权利已通过；
- pointer 可以 round trip；
- 十次执行是十条独立 lineage 或十个样本；
- LLM 比 JSON parser + Rule/Reuse compiler 更有价值；
- source role、train admission 或 L2 已通过。

## 后续硬停

若未来两个对象均完成 size + MD5 校验，也必须停止。下一阶段需要另行冻结并授权：

`dual_reader_privacy_notice_schema_ground_truth_exclusion_manifest_lineage_binding_semantic_fit_and_pointer_contract`

该合同至少要钉死：

- sensor 与 protected-manifest reader 身份和 hash；
- 各自 byte/line/record/field/token/depth/time caps；
- ground-truth、process/activity/station/stage 字段隔离；
- privacy、secret 和 notice 探针；
- 十个 process-instance manifest、duplicate/reset policy；
- process-to-sensor interval binding；
- opaque pointer binder 与 normalization round trip；
- LLM 相对 Rule/Reuse 的增量 Gate。

## 当前权限确认

- Acquisition / HTTP：`false`
- Launcher / execution authority：`false`
- File open / content read：`false`
- Reader / audit：`false`
- Effective catalog：未写
- Source role：未批准
- Family / lineage / sample / quota credit：全部 `0`
- L2 Gate：`false`
- 本合同工件：暂未 commit
- Git push：未执行
