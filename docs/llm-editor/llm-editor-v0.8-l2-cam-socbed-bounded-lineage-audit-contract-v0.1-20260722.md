# CAM-LDS + SOCBED 有界 lineage-only audit 合同 v0.1

**Authority base**: `feat/llm-editor-v0.8` @ `a96730b5f7caf05a46e4198ab23c0281c7c3e273`

**冻结日期**: 2026-07-22

**状态**: `frozen_before_payload_lineage_audit`

## 1. 目的与边界

本审计只回答一个问题：CAM-LDS 与 SOCBED 是否存在可重复、可审计的 source-native grouping，可以作为未来 lineage 设计的候选。

本审计不构造训练样本，不读取或使用 label，不生成监督，不改变 family role 或配额，不运行 baseline/微调，也不推进 HDFS 正式替换或 CERT/IoT-23 下载。

## 2. 全局字段白名单

允许读取：

- ZIP central directory 的 member path、目录标志、压缩/解压大小、CRC32；
- 时间字段：`@timestamp`、`timestamp`、`ts`；
- 主机字段：`host.name`、`hostname`、`host`、`agent.hostname`、`agent.name`、`observer.hostname`；
- 纯文本日志仅允许解析时间前缀与 hostname token。

禁止读取或保留：

- label/class/target/gold/answer/ground-truth；
- attack/technique/tactic/actor/malware；
- message、event text/code、process/command、IP、文件、注册表、用户字段；
- observation/null proposal、模型输出、private gold。

禁止项优先于白名单。缺字段时不得临时扩表，只能报告 missing。

输出中不保留原始路径、hostname、事件文本或亚日级时间；只保留哈希 group ID、计数、日期级时间摘要与结构性判断。

## 3. CAM-LDS 冻结规则

归档固定为：

- `manifestations_filtered.zip`；
- SHA-256 `BA824F500AF6D64925792D6A693E54AFB761D1CFB5FE515EFB2206035772BADE`；
- 最大归档大小 213,771,977 bytes。

仅允许同时位于 `/steps/` 与 `/logs/` 下的 `.log/.json/.jsonl/.txt`。`techniques`、`sequences`、`configs`、`attacker`、`facts.json`、`eve.json` 全部排除。

Grouping：

- `collection_anchor`：第一个 `/steps/` 之前的完整前缀；
- `step_anchor`：第一个 `/logs/` 之前的完整前缀；
- `host_scope`：`/logs/` 后第一个目录组件；
- lineage candidate = `collection_anchor`；
- 同一 collection 下的多个 step/host 是 repeated views，不是独立重复。

每个 step 最多读取字典序首尾两个 member、每个 member 最多 256 行；全族最多 2,000 个 member、128 MiB payload。超过上限即 fail-closed。

即使结构一致，本审计也不得把 CAM-LDS collection 直接标成 statistically independent run；缺少外部 run/reset metadata 时只能输出 candidate grouping。

## 4. SOCBED 冻结规则

归档固定为：

- `dataset.zip`；
- SHA-256 `7EDA65F08BBE6F274C1FEFF178AE132CFD0E8EDBDF0A10EF08321259B6FACC54`；
- 最大归档大小 77,984,817 bytes。

只允许路径匹配 `winlogbeat_<数字>.jsonl` 的 40 个候选文件；每文件最多读取前 512 行，仅提取白名单时间/host 字段。

Grouping：

- 数字 suffix 是 `run_key`；
- parent directory 是一个 view；
- 同一 suffix 的所有 view 合并为一个 run candidate；
- 四个文件不能算四次独立运行。

结构 Gate：每个 run suffix 在每个 parent view 中恰有一个文件，不得路径重复或内容哈希重复。时间 Gate：每个 view 至少一个可解析时间，同一 run 的 sampled day set 必须相交。不同 suffix 若内容哈希或时间签名相同，必须标记，不得独立计数。

通过结构与时间 Gate 只说明 source-native run grouping 成立；共享 testbed 状态下的统计独立性仍未得到证明，因此本审计不改 independent-lineage quota。

## 5. 硬停

- archive hash 漂移：停止该族审计；
- 路径不在白名单：不打开；
- label/sequence/technique 路径：不打开；
- 字段缺失：不扩白名单；
- 达到 member/byte/line 上限：停止并报告 truncated；
- 任何审计结果：不得自动改变 role、quota 或 L2 Gate。

机器可检合同见同名 JSON。合同必须先于 payload audit 单独提交，以证明 grouping 规则不是看过结果后修改。
