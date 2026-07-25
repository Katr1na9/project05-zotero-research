# LogChunks metadata candidate review v0.1

日期：2026-07-23  
实际 authority base：`5fa2b6bd1eb4f8a3864425828d9ba1dcfaaa79ed`

> 用户给出的 HEAD 提示约为 `8e4a7c2`，但启动时实际 HEAD 为 `5fa2b6bd…`。本授权以“当前 HEAD”为 authority，因此采用实际值；未 checkout、reset、merge 或改分支。

## 裁断

`logchunks_travis_ci_build_log_captures_2020`：

**`approve_as_metadata_candidate_not_source_role`**

这是 metadata candidate，不是 source role、train admission、lineage credit 或 L2 Gate 通过。

## 为什么可以保留为 metadata candidate

| 项目 | 结果 |
|---|---|
| Zenodo record | revision 3，DOI `10.5281/zenodo.3632351` |
| Version / type | `1.0.0` / Dataset |
| License | record-scope `CC-BY-4.0` |
| Artifact | `LogChunks.zip` |
| Bytes | `24,108,826` |
| MD5 | `aafa45079bdae44e340f4474ca5c4340` |
| Curator capture declaration | 797 Travis CI logs、80 repositories、29 main languages |
| ≥4 metadata capture Gate | 通过 |
| Associated publication | ACM MSR 2020，DOI `10.1145/3379597.3387485` |

797 是 curator 声明的 log capture 数，不是由 archive file、class、attack、technique 或人为时间窗推出来的，因此足以进入 metadata candidate 层。

## 为什么不能给 source role

1. 官方元数据没有证明一份 log 对应一个唯一 Travis job 或 build。
2. 没有 stable build/job ID、build-matrix parent/child、retry、rerun、duplicate 或 truncation 合同。
3. repository、language、file、directory、row 和 date window 均不能充当独立 lineage。
4. 同一 archive 明确包含人工 failure chunks、搜索 keywords、结构类别及 repository-level annotation XML；这些对象必须物理隔离，不能进入输入、target、pointer 或 grouping。
5. archive member、record position、pointer round trip、nested notices、第三方日志权利、secret/privacy 和 protected overlap 均未核。
6. CI build logs 是条件性的 execution provenance，不是 security incident telemetry；即使未来 audit 通过，也只能讨论狭窄的 CI-provenance 角色。

## 未来若另行授权，必须先过的 Gate

- exact bounded acquisition contract；
- central-directory 与 nested-notice；
- annotation XML、manual span、keyword、category 和 label-bearing path 的物理隔离；
- 至少四个稳定、opaque、label-independent 的 source-native build/job groups；
- matrix/retry/rerun/duplicate grouping；
- privacy、token、URL、environment value 和 secret exclusion；
- immutable member + build/job ID + record-position pointer round trip；
- protected exact/near overlap。

任一项无法闭合时 fail closed；claim 必须 abstain 或保持 unbound。

## 权限与自检

- metadata candidate：是。
- effective catalog：未写。
- source role / train admission：否。
- family / lineage / sample / quota credit：全部 `0`。
- 下载、archive/payload audit、训练样本、baseline、微调：均未授权、未执行。
- 未触碰 PANDAcap/REPROD cache、zip、launcher 或 acquisition。
- 未 commit、未 push。
