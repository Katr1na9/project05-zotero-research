# Portfolio A 停损与换族执行计划 v0.1

**Authority base**: `feat/llm-editor-v0.8` @ `c85c2cdd781d62e54386acacd1778a21930fabe6`

**Date**: 2026-07-22

**Status**: role amendment applied; L2 remains blocked

## 1. 处置结论

CAM-LDS 与 SOCBED 退出科学 train 候选，状态改为：

```yaml
effective_catalog_role: inactive_engineering_only
scientific_use_status: lineage_failed_pending_replace
counts_toward_l2_family_quota: false
counts_toward_l2_lineage_quota: false
```

二者可以在未来单独授权下保留 parser/contract 工程用途，但不能进入训练、development、模型比较或论文效果统计。

BETH、Atomic、Loghub Linux 与 Zeek 保留原 split 意图，但状态统一变为 `*_candidate_pending_replacement`，科学配额信用为 0。不再尝试用单文件切窗、technique 数、fixture 目录或日志行数修复 lineage。

## 2. 为什么现在必须停损

- CAM-LDS：冻结 audit 将 1,061 个 step 归入 1 个 collection candidate；重切 step 只会制造伪重复。
- SOCBED：10 个 suffix 虽全部满足四视图结构，但冻结时间 Gate 为 0/10；事后放宽只是在洗结果。
- BETH：一个 host/file 不能靠切窗成为四个独立运行。
- Atomic：technique YAML 是执行说明，不是执行证据。
- Loghub Linux：一个 archive/log 的行数不是独立 collection。
- Zeek：软件测试 fixture 文件不是独立真实 capture。

这次 role amendment 不修改原始历史审计；它以追加 catalog snapshot 覆盖后续角色解释。

## 3. Amendment 后的真实缺口

| Split | 冻结最低要求 | 当前 quota-eligible | 已知候选 | 尚缺 |
|---|---:|---:|---|---:|
| train | 4 independent families | 0 | ProvSec、LID-DS | 即使两者都闭合仍缺 2 个独立 train family |
| development | 2 independent families | 0 | HDFS-v1、LANL reserve | 2 个候选均未取得 lineage/完整 source Gate |
| test | 2 independent families | 0 materialized | CERT、IoT-23 metadata candidates | 下载与 payload 继续暂停 |

因此 Portfolio A 不是“换掉两个坏族就能开模型”。CAM/SOCBED 退出后，train 必须最终拥有四个真正独立且逐族过 Gate 的来源。

## 4. BETH 替代优先级

### 4.1 ProvSec——科学首选，但 artifact Gate 仍未闭合

2026-07-22 官方元数据复核：

- [UCO Cyber research page](https://uco-cyber.github.io/research/)仍指向 Springer 论文与 Google Form；
- [Crossref DOI metadata](https://api.crossref.org/works/10.1007/s44227-023-00014-9)确认论文版本为 CC BY 4.0；
- 官方表单只说明提交联系信息后另行分享下载链接；
- 公开表单没有 dataset-specific license、artifact version、byte size 或 checksum。

因此状态保持 `hold_artifact_gate_unclosed`。论文的 CC BY 4.0 不能自动替代数据 artifact 许可。

闭合条件必须同时满足：

1. 数据集本身的明确许可；
2. immutable artifact/release identity；
3. byte size；
4. SHA-256 或等价不可变 checksum；
5. label/path 隔离合同可执行。

### 4.2 LID-DS 2021——许可声明部分闭合，artifact identity 仍阻塞

[官方仓库固定 commit](https://github.com/LID-DS/LID-DS/commit/587d15870843961acb78fbb4b8fcd0ede28eabcc)的 README 在 LID-DS 2021/2019 下载链接后，明确把 “Leipzig Intrusion Detection Dataset” 置于 GPL version 3 or later。对应：

- README git blob：`600f5aabf3297b955a77106d7dbeefdb8ba23902`；
- LICENSE git blob：`608ad4ba70e32efdc7a6204ddc9b37a6ebfb7d94`；
- dataset-level license statement：`GPL-3.0-or-later`，metadata 层已验证。

但[官方 Proton 分享页](https://drive.proton.me/urls/BWKRGQK994#fCK9JKL93Sjm)没有公开 immutable revision、文件大小或 checksum，[GitHub Releases](https://github.com/LID-DS/LID-DS/releases)与[Tags](https://github.com/LID-DS/LID-DS/tags)也为空。因此状态为：

```yaml
status: partial_license_closed_checksum_and_revision_open
immutable_artifact_revision_verified: false
artifact_checksum_verified: false
```

仓库里的 `lid_ds/sim/datasets/Archiv.zip` 是一个固定 repo blob，但没有证据证明它等同于 Proton 提供的 LID-DS 2021 正式数据，禁止拿它偷换 artifact Gate。

### 4.3 BETH 分配规则

1. ProvSec artifact Gate 全闭合时优先替代 BETH；
2. ProvSec 长期阻塞时，LID-DS artifact Gate 全闭合后作为 BETH 备选；
3. 同一 artifact 只能占一个 family/split，不能同时替代 BETH 与 Atomic。

## 5. Atomic 替代

Atomic 优先使用 BETH 未占用的 ProvSec/LID-DS 候选，因为二者至少包含实际采集的系统调用/运行证据，而 Atomic 只有 YAML 过程定义。

若 ProvSec/LID-DS 只有一个闭合，优先保证 BETH；Atomic 必须继续寻找另一个独立 executed endpoint/provenance family，不得重复使用同一 artifact，也不得把 Atomic technique 拆成多个 family。

## 6. CAM-LDS / SOCBED 空出的两个 train slot

两族降为 inactive 后，仍需新找 **两个额外独立 train families**。最低元数据条件：

- artifact 级许可明确；
- revision、size、checksum 可冻结；
- 至少四个 source-native run/capture lineage 可在下载前由 manifest 元数据提出，并在未来有界 audit 中核验；
- label、scenario、attack name 与 hidden answer 可物理隔离；
- 与 ProvSec/LID-DS、development/test family 不重叠。

没有这两个来源时，即使 ProvSec 与 LID-DS 都通过，train 也只有 2/4 family，不得启动 baseline。

## 7. Development 换族

### 7.1 Loghub → HDFS-v1

HDFS-v1 当前只是 `approved_as_metadata_candidate`，不是正式 replacement。若以后单独批准替换，授权文字必须同时写明：

```yaml
replacement_approved: true
lineage_quota_credit: false_until_separate_frozen_audit
development_gate_passes_on_replacement_alone: false
```

block ID 只能先作 trace/grouping candidate。没有后续 lineage 核验，development 仍然失败；不能为纸面完整而先批准替换。

### 7.2 Zeek → LANL reserve

Zeek 更适合由同时含 host/network evidence 的 LANL source 替代，而不是为了凑 family 数硬塞纯 host-system-call corpus。LANL Comprehensive/Unified 在 per-file checksum、登记和 overlap 条件闭合前只保留 reserve：

- 一个 LANL corpus 最多占一个 split role；
- daily files 是同一企业内相关观测，不能自动当独立企业；
- red-team event/identity/time hints 必须与 model view 物理隔离。

## 8. 固定执行顺序

1. **已完成**：CAM-LDS、SOCBED → `inactive_engineering_only`；其余四族 → pending replacement。
2. 关闭 ProvSec/LID-DS 的 artifact license/revision/size/checksum Gate；未闭合则不下载。
3. 为 CAM/SOCBED 空出的两个 train slot 调研新的独立 executed evidence families。
4. 冻结四个 train replacement 的互斥 portfolio 分配；同一来源不得占两族或跨 split。
5. 单独评审 HDFS-v1 正式替换；批准替换也不自动给 lineage credit。
6. 关闭 LANL checksum/登记条件并只选一个 development role。
7. train/development portfolio 全部冻结后，才重新决定是否授权 CERT/IoT-23 下载。
8. 全部来源依次通过 payload、notice、exclusion、lineage、sample-kind、modality Gate 后，才可申请 baseline。

## 9. 明确禁止

- 第二轮 CAM/SOCBED lineage audit；
- 放宽 SOCBED 已冻结时间 Gate；
- 重切 CAM step 或任意时间窗；
- 用 HDFS metadata candidate 身份冒充 development lineage 通过；
- 在 train/development 方案未定前下载 CERT/IoT-23；
- baseline、微调、Kernel/Gamma/M3*；
- 把历史 1,500 pairs 自动继承为 v0.8；
- 标记 L2 通过。

## 10. 当前 Gate

```yaml
role_amendment_applied: true
cam_inactive_engineering_only: true
socbed_inactive_engineering_only: true
train_quota_passed: false
development_quota_passed: false
test_quota_passed: false
hdfs_formal_replacement_approved: false
cert_iot23_download_authorized: false
baseline_authorized: false
fine_tuning_authorized: false
l2_gate_passed: false
```

机器可检 catalog snapshot 见 `llm-editor-v0.8-l2-effective-source-catalog-role-amendment-v0.3-20260722.json`。

## 11. Sources

Academic / peer-reviewed metadata:

- [Shrestha et al. (2023), ProvSec DOI metadata](https://doi.org/10.1007/s44227-023-00014-9)
- [Crossref record for ProvSec](https://api.crossref.org/works/10.1007/s44227-023-00014-9)
- [LANL Comprehensive Cyber Events dataset DOI](https://doi.org/10.17021/1179829)

Official dataset/repository metadata:

- [UCO Cyber research page](https://uco-cyber.github.io/research/)
- [ProvSec official contact/download form](https://docs.google.com/forms/d/e/1FAIpQLSfCSGWDW2oUx5YYFoUZ0HWCSRDg-bIbhdkb16pwKL0GGlcCfQ/viewform?usp=send_form)
- [LID-DS official repository at pinned commit](https://github.com/LID-DS/LID-DS/tree/587d15870843961acb78fbb4b8fcd0ede28eabcc)
- [LID-DS pinned README](https://github.com/LID-DS/LID-DS/blob/587d15870843961acb78fbb4b8fcd0ede28eabcc/README.md)
- [LID-DS pinned LICENSE](https://github.com/LID-DS/LID-DS/blob/587d15870843961acb78fbb4b8fcd0ede28eabcc/LICENSE)
- [LID-DS 2021 official Proton share page](https://drive.proton.me/urls/BWKRGQK994#fCK9JKL93Sjm)
- [LANL Comprehensive Cyber Events official page](https://csr.lanl.gov/data/cyber1/)
- [LANL Unified Host and Network Dataset official page](https://csr.lanl.gov/data/2017/)
