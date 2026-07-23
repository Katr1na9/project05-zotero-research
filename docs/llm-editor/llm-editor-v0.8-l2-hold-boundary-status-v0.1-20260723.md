# L2 hold boundary status v0.1

日期：2026-07-23  
authority base：`456b129bd98a317c3de85e78274b11e28ff61a41`

## 裁断

本文件只整理已经提交的边界，不重新评审来源。四项全部保持 hold；没有 source role、train admission、lineage 或 quota credit，也没有改变 L2 Gate。

| 候选 | 当前状态 | 能否进入下一道 | 仍缺什么 | Hold |
|---|---|---|---|---|
| HDFS-v1 | 已是 metadata candidate；未批准替换或 lineage | 可以，但只能另开正式 replacement review；其后仍须 bounded lineage audit | 独立 collection/run 边界；block-ID 独立性；与 Loghub Linux 同 curator/record 风险；标签物理隔离 | 是 |
| ProvSec | 科学上优先，但 artifact Gate 未闭合 | 不能进入 source-role review；只能继续补 artifact metadata | 数据 artifact license、immutable revision、bytes、checksum；contact-form delivery 不足 | 是 |
| LID-DS | dataset license 声明已见；artifact identity 未闭合 | 不能进入 source-role review；只能继续补 artifact metadata | Proton artifact immutable revision、bytes、checksum；repo 无 release/tag 绑定 | 是 |
| N-BaIoT | artifact 与跨 split 边界未闭合 | 不能进入 candidate/source-role review；只能先补 metadata 与 overlap 证据 | artifact license/checksum、source-native run lineage、与 IoT-23 重叠/相关性 | 是 |

## 不允许的推断

- HDFS-v1 的独立文件或 block ID 不等于独立科学 lineage。
- ProvSec 的论文或 OSTI full text 不等于数据 artifact release。
- LID-DS 仓库 fixture 不得替代 Proton 上的 2021 数据 artifact。
- N-BaIoT 的九个设备不等于九次独立执行或采集。

## 权威边界

本整理引用：

- `llm-editor-v0.8-l2-hdfs-v1-pending-replacement-candidate-review-v0.1-20260722.json`
- `llm-editor-v0.8-l2-portfolio-a-replacement-candidates-metadata-only-v0.1-20260722.json`
- `llm-editor-v0.8-l2-train-executed-evidence-candidates-metadata-only-v0.1-20260722.json`
- `llm-editor-v0.8-l2-endpoint-provenance-independent-run-search-v0.1-20260723.json`

本轮未读 `datasets/**`、cache、launcher、archive、进程或 acquisition 日志；未下载；未安装或执行 reader；未写 effective catalog；未改 role/quota/L2；未运行 baseline、微调或样本生成；未 commit、未 push。所有产出仅位于 `docs/llm-editor/`。
