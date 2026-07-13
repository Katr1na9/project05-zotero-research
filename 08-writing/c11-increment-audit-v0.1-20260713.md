# C11 论文增量复核 v0.1

日期：2026-07-13

复核对象：远端提交 `90ac1c3` 中的 OTRF APT29 Day 1 接入、C11 案例、冻结结果、OR 敏感性、标注包和回归测试。

## 1. 复核结论

C11 是当前论文的有效增量，但它加强的是**外部效度边界与代理敏感性**，不是算法性能或 actor attribution accuracy。它可进入论文 v0.5 的独立小节，不应与 C07-C10 的 G3 主结果求总均值。

一句话论点：C11 证明同一调查控制接口能够接入第三种 Windows JSONL/多 provider 封装并保留自然 G3→G2 降级，同时反证 M2 跨场景最低成本和 OR/AND 可互换这两个更强外推。

## 2. 已验证事实

| 项目 | 复核结果 |
|---|---|
| 固定来源 | OTRF Security-Datasets commit `d9d40ef123d2c87d5d3df28c96bcab4f0faccc87` |
| 主机归档 | 13,944,973 bytes；SHA-256 `98A073140860560D70080ACE9142961BE4F64B4862BAE892D62D0F254D0FDBE5` |
| 原始回查 | 本机重新下载固定归档，8 条 claim 的行号、RecordNumber 和锚点测试全部通过 |
| 解析规模 | 196,081 host rows，0 malformed；Zeek 2,140 rows，但与 Host 不同窗 |
| 自然缺口 | N01 固定 `3aka3.doc` 锚点 0 命中，未用其他步骤替换 |
| 多 claim | N02-N05 各两条 claim，来自 PowerShell+Sysmon 或 PowerShell+Security provider family |
| 主结果 | AND 下 M2 success 1.0000、mean cost 3.6667；Coverage/M1 为 3.2444 |
| 语义敏感性 | 只改 AND→OR 后 M2 mean cost 1.0222，变化 -2.6445 |
| 可复现性 | 当前代码重跑的 C11 summary SHA-256 与冻结结果一致 |
| 信息边界 | 非 Oracle planner 的 action/state 公开视图均排除模拟器隐藏答案 |

## 3. 发现并修复的工程问题

C07-C11 标注包的公开 JSONL 内容可重现，但 `packet_manifest.json` 中 C07-C10 来源文件哈希与当前 LF checkout 不一致。原因是提交新增 `.gitattributes` 后，旧文件行尾被规范化，而标注包仍保留规范化前的字节哈希。已用冻结生成器、相同 seed、相同 case 顺序和相同版本重新生成包；仅 manifest 中受行尾影响的来源 SHA-256 改变，114 个公开 item 与空白标注模板保持不变。

## 4. 必须收紧的科学表述

### 4.1 内部冻结不等于外部 preregistration

协议、内部时间戳记录和结果在同一 Git 提交中公开。它们支持“事件读取前建立了内部冻结记录”的研究过程声明，但不能像 OSF、注册报告或先行 Git commit 那样向外部读者独立证明先后顺序。论文使用“内部冻结”“预先指定”或“参数锁定”，不使用未经限定的“预注册”。

### 4.2 多 provider 不等于独立传感器

C11 的 claim 对来自同一主机事件归档中的不同 Windows provider family。它们比同一事件字段拆分更强，但弱于 Host+Zeek、EDR+NDR 或独立设备的跨传感器 corroboration。Host 与 Zeek 不同窗，后者未进入事件级 claim。

### 4.3 collection claim 不等于 exfiltration claim

N02 与 N05 的历史节点标识包含 `exfil`，但当前 claim 对只回指压缩命令和归档文件创建。它们支持 collection/archiving，不单独支持网络外传。论文保留 node ID 以维持冻结结果，但明确限制语义，不把这两对 claims 写成外传已证实。

### 4.4 C11 未覆盖全部策略族

C11 v0.1 运行的是 `run_mvp.py` 的 14 个内置策略和消融。XGBoost、AFA-VOI 与 Depth-2 没有在 C11 上运行，因此不能写成“所有冻结方法都完成 C11 评估”。这些方法的比较结论仍限 C07-C10。

## 5. 对论文结构的处理

1. 保留 C07-C10 为 G3 主分析，主图 1-3 和聚合数字不改。
2. 在实验设计中把 C11 定义为一个 G2、APT29 emulation、第三封装外部效度压力。
3. 在结果新增独立表格，不与 C07-C10 混合平均。
4. 在讨论中把 M2 从“当前部署锚点”进一步限定为“C07-C10 内的透明部署锚点”。
5. 在局限性中同时写明内部冻结、多 provider、compound node 语义和未运行策略。

## 6. 尚未关闭

双人盲标包仍是 `awaiting_annotations`。C11 增加了 8 个 claim、5 个公开意图和 12 个粒度状态，使 C07-C11 总包达到 114 个 item，但没有产生任何人工一致性或粒度校准结果。C11 不能替代这项 A 级门槛。
