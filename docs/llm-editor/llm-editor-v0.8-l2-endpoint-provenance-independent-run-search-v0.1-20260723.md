# L2 Endpoint / Provenance 独立运行来源检索 v0.1

**Authority base**：`ea349632aeeabe59056558e94f1d5925031b041e`

**范围**：metadata-only；未下载或打开 payload/archive；未改 family role、quota 或 L2 Gate

## 1. 裁断

本轮找到两个值得后续处理的方向，但**没有填补 train slot**：

| 方向 | 官方 run/capture 证据 | Artifact Gate | 本轮裁断 |
|---|---|---|---|
| [Dynamic Malware Analysis kernel and user-level calls](https://zenodo.org/records/1203289) | 官方说明 1,000 malicious + 1,000 clean sample runs；编号目录代表不同样本的一次 run | CC-BY-4.0；固定 Zenodo revision；两个 archive 均有 bytes + MD5 | **可另开逐族 metadata candidate review**；不是 source approval |
| [AIT Log Data Set](https://zenodo.org/records/4264796) | V1.1 明说 4 个 independent testbeds；[V2.1](https://zenodo.org/records/19483937)列出 8 个独立命名的 testbed/simulation group | CC-BY-NC-SA-4.0；固定 revision；files 均有 bytes + MD5 | **hold**：与已淘汰 CAM-LDS 共用 AIT curator 与 model-driven testbed 范式，family distinctness 未闭合 |

因此，Liwa replacement slot 继续 `vacant`，quota 仍为 `0`。下一步若用户愿意，应只对 `dynamic_malware_kernel_user_calls_2018` 另开逐族 metadata candidate review；仍不得下载。

## 2. 检索规则

纳入方向必须同时具备：

1. endpoint、host audit、system call 或 provenance evidence；
2. 官方记录级 license、immutable revision、byte size 与 checksum；
3. curator 在 metadata 中声明至少 4 个 run/capture/execution/simulation/testbed 单元；
4. raw evidence 与 label/answer/ground truth 有可物理隔离的可能；
5. 没有已知 active train/dev/test artifact 重用。

行数、文件数、目录数、technique 数、host/sensor view、device 数、日期或任意时间窗均不得替代 run/capture。E3、E5、OpTC、OTRF、WitFoo 继续 protected；AInception、Liwa 与 EVTX 继续 failed/inactive。

N-BaIoT 本轮**没有抢跑**：没有重新查询、登记或提升。其 artifact license、immutable checksum、source-native run lineage 以及与 IoT-23 的跨 split 重叠未同时闭合前，保持 hold。

## 3. 优先方向：Dynamic Malware Analysis kernel/user-level calls

官方 Zenodo record `1203289` 提供：

- DOI `10.5281/zenodo.1203289`，record revision `5`；
- license `CC-BY-4.0`；
- `KernelDriver.7z`：434,907,463 bytes，MD5 `d4e4abb2d37353d22f80662864e03ea4`；
- `Cuckoo.7z`：14,638,588,754 bytes，MD5 `070528130fc81478a77c763558530f6b`；
- 1,000 malicious 与 1,000 clean samples 已执行；
- 官方描述明确说明，编号目录中的每个编号代表“running of a different sample”，并将该单元称为 run；
- endpoint 证据包含 kernel-driver system-call logs 与 Cuckoo dynamic-analysis reports。

它比 EVTX 样本仓库强的关键不是“文件更多”，而是 curator 给出了**不同样本运行 → 编号目录**的 source-native 映射。

仍未闭合：

- 官方 metadata 没有提供 VM snapshot/reset manifest；
- KernelDriver 与 Cuckoo 可能是同一 executed sample 的两种 sensor view，禁止双算 lineage；
- `Clean` / `VirusShare` 路径、Cuckoo signatures/verdicts 与 detector outputs 都是 supervision leakage，未来必须隔离；
- 仍需 nested notice、run/hash 对齐、duplicate/reset、pointer recoverability 与 protected exclusion audit。

所以本轮只给：

```yaml
search_verdict: approve_for_separate_metadata_candidate_review_not_source_role
download: false
family_credit: 0
lineage_credit: 0
sample_credit: 0
```

## 4. AIT-LDS：分组证据强，但 distinctness 不够

### V1.1

[AIT-LDS V1.1](https://zenodo.org/records/4264796) 的官方描述精确写明：日志来自 **four independent testbeds**。应只钉 `AIT-LDS-v1_1.zip`：

- 3,404,722,917 bytes；
- MD5 `4573b78ca4909c259632a49a3a34211e`。

同 record 中的 `v1_0` 与 `v1_1` 是同一四-testbed collection 的版本，不能当两个 family 或两个 run。

### V2.1

[AIT-LDS V2.1](https://zenodo.org/records/19483937) 官方列出 8 个 testbed/dataset：`fox`、`harrison`、`russellmitchell`、`santos`、`shaw`、`wardbeck`、`wheeler`、`wilson`；每个都有自己的 simulation/attack 时间与固定 archive。每个 full archive 又有一个 `no-pcaps` derivative；两者只是同一 testbed 的两种 view，只能算一个 lineage candidate。

阻塞点不是 run 数，而是 portfolio distinctness：AIT-LDS 与 CAM-LDS 共享 Landauer、Skopik、Hotwagner、Wurzenberger，均来自 AIT 的 synthetic small-enterprise/model-driven testbed 路线。CAM-LDS 虽已 inactive，但当前授权要求找“新且 distinct”的 family；不能仅因旧来源退出就忽略 curator/generator nuisance。

因此 AIT-LDS 保持：

```yaml
status: hold_for_distinctness_and_curator_overlap_review
download: false
quota: 0
```

## 5. 已筛但未推进

| 来源 | 结论 | 原因 |
|---|---|---|
| [WinMET](https://zenodo.org/records/16414116) | hold | 31,844 个 SHA-named CAPE execution traces、GPL-3.0-or-later、bytes/MD5 都齐；但 metadata 没有 reset/non-duplicate manifest，也没有 benign pool。trace count 不自动等于 independent lineage。 |
| [API traces for malware detection](https://zenodo.org/records/11079764) | hold | 约 330k traces，CC-BY-4.0、archive bytes/MD5 齐；但每个 SHA trace 是否来自 separately reset execution 未声明。 |
| [DYNAMISM 2018](https://zenodo.org/records/1296278) | hold | lineage 证据很强：2,386 benign + 2,495 malicious apps，且每个 app 前重置 Android；但当前 record API 不提供 artifact license、files、bytes 或 checksums。 |
| [DYNAMISM 2016–2023](https://zenodo.org/records/21280255) | hold | 声明 controlled execution、23,266 个有效 first runs 与 1,821 second runs；但 record 当前没有 files/bytes/checksums。 |
| [SAPPAN Combined Network and Host Data](https://zenodo.org/records/4159878) | reject | 只有两个 attack scenarios；Samba 的四个 dataset 是同一 scenario 的 phase/failed attempt，不能当四个 independent runs。 |
| [DongTing](https://zenodo.org/records/6627050) | hold | 12,116 attack sequences 与 17,855 bug-triggering programs 不能替代 reset/run manifest；而且主要是 kernel-bug anomaly corpus，语义范围过窄。 |
| [Hands-on Cybersecurity Training Behavior](https://zenodo.org/records/10298187) | reject | participant/session 数不是 endpoint capture run；training definition 与 hints 还是 protected supervision。 |
| [Node-Level Intrusion Logs](https://zenodo.org/records/18997859) | reject | 官方 record 无 files、run、size 或 checksum。 |

## 6. Evidence / Inference / Recommendation

**Evidence**

- Zenodo `1203289` 同时闭合 license、record revision、bytes、MD5，并把不同 sample 的 numbered directory 定义为 run。
- AIT-LDS V1.1 明示 4 个 independent testbeds；V2.1 有 8 个 source-native testbed/simulation groups。
- 其余来源至少缺 run/reset 合同、artifact identity 或 evidence fit 中的一项。

**Inference**

- `1203289` 是本轮最“新且 distinct”的方向，但只能进入下一轮 metadata candidate review；统计独立性和双传感器 view 绑定尚未核验。
- AIT-LDS 的 run metadata 更强，但 same-curator/testbed nuisance 使它暂时不能被称为 distinct replacement family。

**Recommendation**

1. 下一授权只开 `dynamic_malware_kernel_user_calls_2018` 逐族 metadata candidate review；
2. AIT-LDS 先停在 distinctness/overlap amendment；
3. 不下载任何候选，不改 effective catalog role，不给 quota；
4. N-BaIoT、WinMET、DYNAMISM、SAPPAN、DongTing 与 API-traces 均不在本轮前进。

机器可检 companion：`llm-editor-v0.8-l2-endpoint-provenance-independent-run-search-v0.1-20260723.json`。
