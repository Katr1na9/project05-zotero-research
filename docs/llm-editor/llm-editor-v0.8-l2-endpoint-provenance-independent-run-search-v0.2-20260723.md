# L2 Endpoint / Provenance 独立执行来源检索 v0.2

**Authority base**：`3190555e25f21df38eafe01d6c9067623e1a054d`

**范围**：metadata-only；未下载或打开 payload/archive，未读论文全文、模型输出或 private gold；未改 family role、quota 或 L2 Gate。

## 1. 裁断

本轮找到一个可以进入下一道“逐族 metadata candidate review”的方向：**REPROD**。它还不是 train candidate，更没有配额。

| 方向 | curator 声明 | Artifact Gate | 本轮裁断 |
|---|---|---|---|
| [REPROD](https://zenodo.org/records/8123115) | 405 次 ransomware binary executions；原始 PML 以 MalwareBazaar SHA-256 命名；861 个 DOT 是同批执行的派生视图 | CC-BY-4.0；固定 Zenodo record/revision；15 个文件全部有 bytes+MD5 | **可另开逐族 metadata candidate review**；不得自动写 catalog、下载或计配额 |
| [EN2025](https://zenodo.org/records/18218588) | 3,260 个样本各带 endpoint API-call logs | MIT；4 个 archive 有 bytes+MD5 | **hold**：顶层 archive 是 class label；未声明 label-blind run key 或 reset |
| [Android ransomware execution traces](https://zenodo.org/records/1420449) | 666 次执行；明确每次运行前重置 Android | 当前 API 无 files/bytes/checksum/license | **hold**：lineage 强，但 artifact Gate 失败 |
| [TwinDroid](https://zenodo.org/records/6464808) | benign/infected app syscall traces | CC-BY-4.0；877 个 checksummed files | **hold**：未声明 reset 与一 trace 一独立 execution；文件数不能当 run 数 |
| [SILRAD](https://zenodo.org/records/17104902) | benign + ransomware Sysmon logs | CC-BY-4.0；单 archive 有 bytes+MD5 | **hold**：未声明 ≥4 个 run，也没有 label-blind group key |

Liwa replacement slot 继续 `vacant`，quota 仍为 `0`，L2 仍为 `false`。

## 2. 为什么 REPROD 值得继续

### Evidence

1. [Zenodo record 8123115](https://zenodo.org/records/8123115) 明确说 PML 来自 ransomware binaries 的 executions，archive 中保留 `n=405` 次 PML 执行；全部获得的 `n=861` 个 DOT 是这些 PML 经 SPADE 处理和查询后的 subgraphs。
2. 同一记录明确说 PML 文件以 MalwareBazaar 的 SHA-256 命名。因此候选 lineage key 是 opaque sample hash，不依赖 family、attack、technique 或 verdict 标签。
3. 记录固定为 revision 2、version 1.0、CC-BY-4.0；15 个对象合计 `144,708,035,023` bytes，全部有官方 MD5。
4. [DataCite](https://api.datacite.org/dois/10.5281/zenodo.8123115) 交叉确认 DOI、标题、作者、版本和权利信息；数据 DOI 解析到当前 Zenodo record。
5. Crossref 确认同一作者组的 ACM CSET 2023 论文 [Towards Reproducible Ransomware Analysis](https://doi.org/10.1145/3607505.3607510)，且论文元数据的参考文献明确引用 REPROD concept DOI `10.5281/zenodo.7933806`。
6. 论文声明的 [REPROD-prov GitHub organization](https://github.com/REPROD-prov) 存在两个公开仓库；本轮只读了 repository metadata，没有读代码内容。

### Inference

- REPROD 满足本轮检索门槛：来源方声明的执行数远大于 4，候选 group key 不由标签产生，artifact 身份可钉。
- `405 PML` 是候选执行组；`861 DOT` 只是派生视图，**不能**再算 861 个独立 lineage。
- 目前仍不能把 405 写成“已核独立 lineage”：官方 metadata 没有声明每次执行之间恢复 VM snapshot，也未给出可在不读 `summary.csv` 情况下验证的一一映射 manifest。
- 数据全是 ransomware executions，metadata 阶段的 benign/null capacity 为 `0`。即便以后通过，也只能补 executed supported evidence，不能单独修复类别平衡。

### Recommendation

下一步只应另开 `reprod_ransomware_execution_provenance_2023` 的逐族 metadata candidate review。若该 review 通过，仍须再开 exact bounded acquisition contract；当前约 144.7 GB 的对象没有下载授权。

## 3. 后续必须冻结的边界

若未来另行授权 audit：

1. lineage 候选键只能是 opaque SHA-256，禁止 class/family/path/verdict 参与；
2. 同一 SHA 的 PML 与 DOT 必须合并为一个 lineage；
3. `summary.csv` 默认全部排除，不进入 prompt、pointer、target 或 supervision；
4. 先 central directory/manifest，验证至少 4 个唯一 SHA 与 PML member 的一一关系；
5. VM reset、重复执行、同 binary 多次执行与缺失 PML 的状态必须 fail-closed；
6. nested notices、pointer recoverability 和 protected exact/near exclusion 必须另行通过；
7. 不得把 `dots.zip` 静默当作 raw PML 的等价替代。

## 4. 未推进方向

- **EN2025**：官方说每个样本有 traffic + endpoint API-call logs，但四个 artifact 本身按 benign/spyware/ransomware/RAT 分类。class archive 不能充当 lineage；未见 reset 或 label-blind member key 声明。
- **Android Extinguishing Ransomware**：执行和 reset 声明最强，但当前 Zenodo API 没有 artifact files、checksum 或 license，故 fail-closed。
- **TwinDroid**：官方记录有大量 SHA-like trace 文件，但没有 metadata-level reset 和一 trace 一 execution 合同，不能从 877 个文件反推 877 个 runs。
- **SILRAD**：Sysmon 模态合适，但官方说明未给 run 数或 group key。
- **AU-PEMal-2025**：只发布两个带标签的 flattened feature CSV，不是 pointer-recoverable raw endpoint evidence。
- **Ranflood**：78 个 benchmark scenarios 是结果记录，不是可恢复 pointer 的 endpoint/provenance capture。

AIT-LDS 没有抢跑；N-BaIoT 没有推进；Cuckoo 没有下载或重新纳入；KernelDriver 的 class-path lineage 没有重开。

## 5. 来源核验

| 来源 | 核验用途 | 结果 |
|---|---|---|
| Zenodo record/API | artifact identity、license、revision、bytes、MD5、execution 声明 | **VERIFIED** |
| DataCite DOI API | DOI、权利、作者、version、concept relation | **VERIFIED** |
| Crossref DOI API | ACM 论文存在、作者组、venue、REPROD DOI citation | **VERIFIED** |
| GitHub organization API | curator workflow organization identity | **VERIFIED（metadata only）** |
| Semantic Scholar | 论文存在性第二交叉检查 | `HTTP 429`，未用于结论 |
| OpenAlex exact DOI | 论文存在性第二交叉检查 | `NOT_FOUND`，未用于结论 |

Crossref、DataCite、Zenodo 与 DOI resolution 已独立闭合关键身份；Semantic Scholar 限流和 OpenAlex 缺项不改变 artifact identity，但已保留为核验限制。资金信息为 Office of Naval Research grant `N00014-21-1-2754`，未发现它影响 artifact identity 的具体冲突。

## 6. Gate

- metadata search：`complete`
- reviewable direction：`reprod_ransomware_execution_provenance_2023`
- effective catalog change：`false`
- download / payload audit：`false`
- role / lineage / sample / quota credit：`0`
- baseline / fine-tuning / Kernel / M3*：`false`
- L2 Gate：`false`
- git push：`false`

本报告由 AI 辅助完成；所有纳入结论均以官方 registry/repository metadata 为证据，未把搜索摘要、文件数或推断性 run 数写成已核 lineage。
