# L2 vacant 04 独立 metadata-only 搜索 v0.8

日期：2026-07-24  
Authority base：`b4b9a7606f626cb33f99515bbbd5721089897aec`

## 裁断

本轮找到一个满足搜索门槛的新方向：

`stgallen_smart_factory_process_execution_sensor_traces_2024`

最高裁断为：

`approve_for_separate_metadata_candidate_review_not_source_role`

它现在只占据“待逐族 metadata review”的第 4 个方向，不代表 source role、train admission、lineage、sample、quota 或 L2 Gate 已通过。

## 为什么通过搜索门槛

Zenodo curator 明确声明：

- `training_tenhertz_log_20230411-095748.txt` 包含 storage process 的 5 次执行；
- 同一文件包含 production process 的 5 次执行；
- 合计 10 次 process executions；
- Camunda 还生成 process-instance 与 activity-instance execution event logs。

这里的候选 group 是一个 Camunda 控制的 process-instance execution。`5 + 5 = 10` 是 curator 明示的执行次数，不是从 file、directory、row、host、sensor view、date window、scenario、class 或 verdict 数量推导。

## 身份与权利

| 项 | metadata 结论 |
|---|---|
| Zenodo record | `14441997`, revision 8 |
| Dataset DOI | `10.5281/zenodo.14441997` |
| Dataset license | CC-BY-4.0 |
| DataCite state | findable |
| Paper DOI | `10.1016/j.procs.2025.03.110` |
| Paper | *A semi-automated approach to detecting process-level activities from sensor data* |
| Venue | Procedia Computer Science, 2025 |
| Paper VOR license | CC-BY-4.0 |
| Curator | Ronny Seiger |
| Facility | University of St.Gallen Fischertechnik Industry 9.0V smart factory |
| Collection | Camunda + Python/Flask + 10 Hz sensors |

Zenodo、DataCite 与论文 version-of-record 的 CC-BY-4.0 信号一致。

## 六个官方对象（本轮未下载）

| Key | Bytes | MD5 | 当前边界 |
|---|---:|---|---|
| `camunda-activity.json` | 1,382,197 | `6ec66ad7eddba76c7dedf28a86afb170` | curator 明示 ground truth，模型视图禁入 |
| `camunda-process.json` | 111,548 | `a56fb7b92ad99a8106ff3c75a2d94c6f` | curator 明示 ground truth；只能在另授权后作为 protected manifest 候选 |
| `storage_process.bpmn` | 10,597 | `135657b8811c65e0472463abc6ae19af` | process definition，不是 execution evidence |
| `test_tenhertz_log_20230411-103455.txt` | 115,149,795 | `fe0af3675a35156a25c37c18d5e1d2c3` | 只写 several executions，无 exact count，保持 hold |
| `production_process.bpmn` | 15,949 | `52991ff8d58878d6ef1ae94a9c8d3bf3` | process definition，不是 execution evidence |
| `training_tenhertz_log_20230411-095748.txt` | 59,901,231 | `1b310fe1bbbbe53511db015375df8a41` | 唯一明确闭合 10 executions 的最窄未来 review surface；未授权获取 |

总计 176,571,317 bytes；六个对象均有 MD5。

## 必须保持的保护边界

### 1. Ground truth 不能进入模型视图

Curator 明确把两个 Camunda event logs 称为 ground truth。它们不得：

- 进入模型 input、prompt 或 target；
- 生成 Project05 supervision；
- 被当作 candidate claim；
- 给模型暴露 process/activity identity。

后续若要核验 source-native process-instance boundary，只能另行授权 protected manifest audit，并且输出必须是脱敏计数、哈希或不透明 ID。

### 2. 外部的 training/test 名称不是 Project05 角色

Curator 的文件名中含 `training` 与 `test`，但本项目不能自动继承：

- 外部 `training` 不等于 Project05 train；
- 外部 `test` 不等于 Project05 development/test；
- 不允许按 sensor row、timestamp、activity 或 station 重切；
- 未来只能按完整 process instance 分组。

### 3. 10 次执行还不是 10 个可用样本

Metadata 已闭合数量门槛，但尚未证明：

- process-instance ID 的不可变 manifest；
- complete/reset/retry/partial/duplicate policy；
- 十次执行的统计独立性；
- ground-truth process boundary 与 sensor message range 的可靠绑定；
- sensor 字段是否泄漏 process stage、station、component 或 task identity；
- pointer 能否从 normalization 回到允许的 sensor surface。

因此 family、lineage、sample、quota credit 仍全部为 `0`。

## 科学价值与限制

这个方向提供的是工业 cyber-physical process execution provenance：

```text
Camunda process instance
    -> Python/Flask-controlled smart-factory actions
    -> 10 Hz sensor and actuator messages
```

它在 curator、facility、execution engine、collection technology 与 modality 上均区别于：

- REPROD 的 ransomware provenance；
- PANDAcap 的 SSH full-system replay traces；
- LogChunks 的 CI build/job logs。

但它不是 malware、APT、honeypot 或 host-forensics 数据，而是 process-mining/activity-detection benchmark。能否成为科学上有价值的第四个 executed-evidence family，必须由下一道逐族 review 单独裁断。

## 本轮未晋级方向

| Candidate | 处置 | 理由 |
|---|---|---|
| EU-TEACHING avionics traces | reject | 四个目录对应 DDoS-L2、CPU theft、Spectre、branch-predictor anomaly 条件；scenario/attack count 不是独立 run count。Zenodo CC-BY-4.0 与 curator BY-NC-SA 信号也冲突 |
| Ethereum DApp execution traces | hold | registry 未给 exact source-native transaction count；是否属于 endpoint/provenance family 未闭合 |
| Time-synchronized energy harvesting traces | reject | 五个 scenario 与多个 sensor views 不能替代 endpoint execution groups |
| DtTsa | reject | 仅软件 release，未发布 immutable execution dataset 或 run count |
| CPM RO-Crate AI pipeline example | reject | 只声明一次 pipeline execution；内部 steps 不等于四次独立执行 |

## Portfolio 状态

| 位置 | 状态 |
|---|---|
| 01 | `reprod_ransomware_execution_provenance_2023` |
| 02 | `pandacap_ssh_honeypot_full_system_traces_2020` |
| 03 | `logchunks_travis_ci_build_log_captures_2020` |
| 04 | `stgallen_smart_factory_process_execution_sensor_traces_2024` — pending separate metadata candidate review |

本轮：

- 未下载或打开任何 artifact/payload；
- 未写 effective catalog；
- 未授 source role 或 train/development admission；
- family / lineage / sample / quota credit 全部为 `0`；
- L2 Gate 仍为 `false`；
- 未跑 baseline、微调或生成训练样本；
- v0.8 工件未 commit、未 push。

## 下一道合规入口

若继续，必须另行授权 **St. Gallen Smart Factory 逐族 metadata candidate review**。该 review 应优先裁断：

1. industrial operational provenance 的科学适配性；
2. 两个 Camunda ground-truth 文件的物理排除合同；
3. 外部 training/test 名称不继承合同；
4. protected process-instance manifest 与 sensor-range binding 的未来可行性；
5. duplicate/retry/partial/reset/repeated-system nuisance；
6. privacy、nested notice 与 pointer round trip。

该搜索不授权 acquisition、payload audit、catalog write、role 或 credit。

## Sources

### Academic / peer-reviewed

- [García-Bañuelos et al., 2025 — A semi-automated approach to detecting process-level activities from sensor data](https://doi.org/10.1016/j.procs.2025.03.110)

### Official registry and curator metadata

- [Zenodo record 14441997 — Smart Factory sensor and process dataset](https://zenodo.org/records/14441997)
- [DataCite DOI metadata — 10.5281/zenodo.14441997](https://api.datacite.org/dois/10.5281/zenodo.14441997)
- [Zenodo record 8289079 — EU-TEACHING avionics dataset](https://zenodo.org/records/8289079)
- [EU-TEACHING curator repository](https://github.com/EU-TEACHING/teaching-avionics-dataset)
- [Zenodo record 14228751 — Ethereum DApp execution data](https://zenodo.org/records/14228751)
- [Zenodo record 6383042 — Time-synchronized energy harvesting traces](https://zenodo.org/records/6383042)
- [Zenodo record 19634159 — DtTsa](https://zenodo.org/records/19634159)
- [Zenodo record 10245846 — CPM RO-Crate AI pipeline execution](https://zenodo.org/records/10245846)
