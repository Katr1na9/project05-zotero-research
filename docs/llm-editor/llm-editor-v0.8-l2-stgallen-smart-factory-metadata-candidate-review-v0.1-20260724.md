# St.Gallen Smart Factory 逐族 metadata candidate review v0.1

日期：2026-07-24  
Authority base：`a2a9204b8e40338d45f357aec999f4c767115550`

## 裁断

`stgallen_smart_factory_process_execution_sensor_traces_2024`

裁断：

`approve_as_metadata_candidate_not_source_role`

它可以保留为 metadata candidate，但当前不能：

- 写入 effective catalog；
- 获得 source role 或 train/development admission；
- 获得 family、lineage、sample 或 quota credit；
- 下载或打开任何对象；
- 生成训练样本；
- 进入 baseline、微调或 L2 Gate。

## 通过了什么

根据 [Zenodo record 14441997](https://zenodo.org/records/14441997)，curator 明确声明较窄的 sensor log 包含 storage process 5 次执行和 production process 5 次执行，共 10 次 process executions。这不是从行数、文件数、日期窗、sensor view、process type 或 scenario 数量推断。

同时：

- Zenodo version chain 只返回一个发布 DOI version；
- 六个顶层对象均有 exact bytes 与 MD5；
- [DataCite](https://api.datacite.org/dois/10.5281/zenodo.14441997) 和 Zenodo 均声明 CC-BY-4.0；
- [García-Bañuelos et al., 2025](https://doi.org/10.1016/j.procs.2025.03.110) 的 version-of-record 也是 CC-BY-4.0；
- Zenodo curator description 直接绑定该论文 DOI。

因此 metadata identity、single release、artifact identity、record-scope rights、publication binding 和 `>=4` curator execution count Gate 通过。

## 六个对象与边界

| Key | Bytes | MD5 | 评审边界 |
|---|---:|---|---|
| `camunda-activity.json` | 1,382,197 | `6ec66ad7eddba76c7dedf28a86afb170` | activity ground truth；模型视图禁入 |
| `camunda-process.json` | 111,548 | `a56fb7b92ad99a8106ff3c75a2d94c6f` | process-instance ground truth；只可作为未来 protected manifest 候选 |
| `storage_process.bpmn` | 10,597 | `135657b8811c65e0472463abc6ae19af` | process definition，不是 execution evidence |
| `test_tenhertz_log_20230411-103455.txt` | 115,149,795 | `fe0af3675a35156a25c37c18d5e1d2c3` | 只声明 several executions，无 exact count；保持 hold |
| `production_process.bpmn` | 15,949 | `52991ff8d58878d6ef1ae94a9c8d3bf3` | process definition，不是 execution evidence |
| `training_tenhertz_log_20230411-095748.txt` | 59,901,231 | `1b310fe1bbbbe53511db015375df8a41` | 唯一闭合 10 executions 的未来 model-surface 候选；当前未授权 |

六个对象合计 176,571,317 bytes。

另有一个必须前置核验的命名问题：curator description 使用 `camunda_process-instance.json` 与 `camunda_activity-instance.json`，而不可变 artifact keys 是 `camunda-process.json` 与 `camunda-activity.json`。未来不能靠名字相似静默等同，必须在 bounded audit 中证明映射。

## 为什么还不能成为 source

### 1. “十次执行”还不是十条 lineage

当前只知道 curator 声明 10 次执行，尚未核验：

- 稳定的 source-native Camunda process-instance ID；
- 每个 process instance 是否对应一个完整、非重叠 sensor interval；
- completion、abort、retry、partial、duplicate 和 reset 规则；
- storage 与 production 是否交错；
- 同一 factory 重复执行带来的 nuisance；
- 十次执行是否可视为统计独立 lineage。

因此 verified lineage count 仍是未知，lineage credit 为 `0`。

### 2. Ground truth 必须与模型物理隔离

Curator 明确将两个 Camunda event logs 称为 ground truth。它们不得进入：

- LLM input、prompt 或 target；
- training supervision；
- candidate claim；
- pointer suggestion；
- Project05 split key。

顶层文件分离说明物理隔离“可能可做”，但 sensor log 是否仍含 process、activity、station、stage、completion 或其他 protected identity 尚未核验。因此 isolation Gate 不能预先判过。

### 3. 外部 `training/test` 名称没有 Project05 权力

外部文件名不能自动继承为本项目角色：

- `training_*` 不等于 Project05 train；
- `test_*` 不等于 Project05 development/test；
- 不得按 row、timestamp、station、activity、component 或 process type 重切；
- 若未来通过，只能按完整且核验过的 process instance 分组。

### 4. Pointer 必须由 protected binder 注入

候选 pointer 形状只能是：

```text
record DOI
+ immutable sensor artifact identity
+ opaque verified process-instance ID
+ recoverable sensor-record locator
```

LLM 不得读取、复制或发明 Camunda process-instance ID。未来 binder 必须从受保护 manifest 注入 opaque ID，并证明 normalization 后仍能恢复到允许的 sensor record。

## LLM 科学适配性

声明的 model-surface 是 10 Hz 结构化 sensor/actuator messages。潜在 Candidate Claim IR 可以表达：

- component reported sensor state；
- component reported actuator state；
- sensor reported value at time；
- candidate process-activity hypothesis。

但必须区分：

- 直接 sensor reading 的 modality 只能由 trusted source metadata 指定；
- process-activity interpretation 只能是 candidate q / conditional hypothesis；
- LLM 不得把推断活动提升为 observed evidence。

更重要的是，这种输入已经高度结构化。未来必须证明 LLM 能提供规则编译器没有的 evidence-safe semantic normalization 或 candidate-q 价值。如果确定性 JSON parser + Rule/Reuse compiler 已经足够，St.Gallen 应保持 engineering-only 或直接交给规则路线，不能为了填第四族强行使用 LLM。

## 科学角色限制

该来源是 controlled industrial cyber-physical process execution provenance，不是：

- malware execution；
- APT investigation；
- honeypot interaction；
- host-forensics；
- security incident ground truth。

它与 REPROD、PANDAcap 和 LogChunks 在 curator、facility、execution engine 与 collection technology 上明显不同，但“不同”不自动等于“适合安全证据编译”。下一道 source-role review 必须单独证明它对 executed-evidence 科学问题的贡献。

## 当前 Gate

| Gate | 状态 |
|---|---|
| Metadata identity | pass |
| Single release | pass |
| Artifact identity | pass |
| Record-scope CC-BY-4.0 | pass |
| Publication binding | pass |
| Curator-declared executions ≥4 | pass（10） |
| Stable process-instance identity | fail-closed |
| Lineage independence | fail-closed |
| Duplicate/retry/partial/reset policy | fail-closed |
| Ground-truth physical isolation | fail-closed |
| Sensor-field label isolation | fail-closed |
| Candidate Claim IR semantic fit | fail-closed |
| LLM increment over Rule/Reuse | fail-closed |
| Pointer recoverability | fail-closed |
| Notice/privacy/secret | fail-closed |
| Protected overlap | fail-closed |
| Security evidence role fit | fail-closed |
| Source role / L2 | false |

## 推荐的下一道入口

本评审不授权 acquisition。若另获授权，建议先冻结 **exact bounded dual-surface acquisition contract**：

1. Model candidate surface：
   - `training_tenhertz_log_20230411-095748.txt`
   - 59,901,231 bytes
   - MD5 `1b310fe1bbbbe53511db015375df8a41`
2. Protected manifest surface：
   - `camunda-process.json`
   - 111,548 bytes
   - MD5 `a56fb7b92ad99a8106ff3c75a2d94c6f`

第一次 acquisition 应明确排除：

- `camunda-activity.json`；
- 两个 BPMN；
- 外部 `test_*` sensor log。

即使未来 acquisition 校验成功，也只证明对象身份；不授权打开文件、读取内容、授 role/credit 或生成样本。

## 本轮权限确认

- 未下载或打开 sensor、ground truth、BPMN 或其他 artifact；
- 未读 publication full text；
- 未写 effective catalog；
- 未修改 role、quota 或 L2；
- 未生成训练样本；
- 未跑 baseline 或微调；
- 未修改 Kernel schema、Γ 或 M3*；
- 未 commit、未 push。

## Sources

### Academic / peer-reviewed

- [García-Bañuelos et al., 2025 — A semi-automated approach to detecting process-level activities from sensor data](https://doi.org/10.1016/j.procs.2025.03.110)

### Official registry metadata

- [Zenodo record 14441997 — Smart Factory dataset](https://zenodo.org/records/14441997)
- [Zenodo API record 14441997](https://zenodo.org/api/records/14441997)
- [DataCite DOI metadata — 10.5281/zenodo.14441997](https://api.datacite.org/dois/10.5281/zenodo.14441997)
