# 踩坑日志：科研版

## 目的

记录所有浪费过时间的问题，避免重复踩坑。

## 记录格式

### YYYY-MM-DD：问题标题

- 场景：
- 表现：
- 原因：
- 解决：
- 预防：
- 影响：

## 初始记录

### 2026-07-12：编译 claim 时未同步保存最小来源 excerpt

- 场景：C07-C10 从超大 PIDSMaker/OpTC 数据中编译 evidence claims，之后原始窗口未保留在当前工作区。
- 表现：claim 留有 UUID/event ID 和详细 notes，但新标注者无法独立打开对应原始记录验证 pointer 与语义。
- 原因：早期流程把“案例可重跑”和“人工可核验”混为一件事，只保存抽取摘要，没有为每条最终 claim 固化 canonical excerpt。
- 解决：C07-C11 v0.2 增加来源访问 Gate 和专门台账；C11 可直接回查，C07-C10 标为 BLOCKED，待恢复记录或重新抽取 excerpt。
- 预防：每条新 claim 必须同时保存 source hash、record locator、最小原始字段 excerpt、excerpt hash 和抽取命令，并用一对一测试校验。
- 影响：高——在补源前，27 条 Claim 任务不能完整启动，人工效度主张仍为空。

### 2026-07-12：同一数据集目录不等于同一次事件窗口

- 场景：OTRF APT29 Day 1 同时提供 Host ZIP 与 `combined_zeek.log`。
- 表现：两者都带 Day 1/Apt29 标签，直觉上容易作为双模态 corroboration 拼接。
- 原因：Host 覆盖 `2020-05-02`，Zeek 覆盖 `2020-04-30`，属于不同 replay 窗口。
- 解决：结构扫描阶段先比较 UTC 范围；Zeek 降为 scenario-level diagnostic，不生成事件级 claim。
- 预防：任何跨文件证据融合必须先通过时间重叠、主机/实体和执行实例三项校验；目录名或场景标签不算对齐证据。
- 影响：高——错误拼接会制造不存在的跨源证据链。

### 2026-07-12：PowerShell JSON 校验会误报大小写重复键

- 场景：用 `ConvertFrom-Json` 批量校验实验 JSON。
- 表现：包含 `Security` 与 `security` 等大小写不同键名时，PowerShell 按大小写不敏感规则拒绝解析，而标准 JSON 解析器可正常读取。
- 原因：工具语义差异，不是文件本身 malformed。
- 解决：仓库 JSON 完整性统一使用 Python 标准库 `json.load`；PowerShell 只做文件枚举和文本查看。
- 预防：验证工具必须与运行时解析器一致；不要把 shell 特有解析错误计入数据坏行。
- 影响：中——会产生错误的数据质量告警并干扰批量验证。

### 2026-07-12：检索首条命中不等于正确事件语义

- 场景：从 PowerShell/Sysmon/Security 事件中为冻结 motif 选择 claim。
- 表现：同一关键词可能同时出现在查询、只读检查、命令构造和实际写入/执行记录中。
- 原因：字符串命中只证明词项出现，不证明行为语义或因果角色。
- 解决：逐条核对 provider、EventID、命令语义、目标对象和记录定位；只保留可描述具体行为的 event-backed claim。
- 预防：motif probe 负责召回，claim selection 负责语义判定；两步产物分开并保留 exact locator。
- 影响：高——错误事件语义会让 evidence claim 看似可回查但无法支撑节点。

### 2026-07-10：从 recoverable 抄 intended 造成答案键

- 场景：为 M3a 增加公开 `intended_cti_node_ids`。
- 表现：通道在线时 M3a 近乎 Oracle；`intended` 与 `OR(recoverable)` 节点集完全一致（C01–C06）。
- 原因：编译时用隐藏恢复集合反推公开意图；通道门控只覆盖离线 seed。
- 解决：P0-#1 通道门控 + `intended≠OR` 标注规范与 CI；C01–C07 均已过宽意图合规（allowlist 已清零）。
- 预防：禁止脚本从 `recoverable_claim_ids` 生成 `intended`；新案例必须过 `test_intended_not_recoverable_or`。
- 影响：高——直接威胁“表示假设”实验的可辩护性。

### 2026-06-30：Zotero 翻译源 CNKI 证书错误

- 场景：Zotero Reader 中选中文本，Translate for Zotero 调用 CNKI 翻译。
- 表现：`SSL_ERROR_BAD_CERT_DOMAIN`，无法翻译。
- 原因：CNKI/dict.cnki.net 安全连接证书问题，不是 PDF 或 Zotero 本体损坏。
- 解决：将翻译源切换为 Bing，并开启自动划词翻译与弹窗。
- 预防：后续优先使用 GPT/Gemini/DeepL，并配置网络安全术语 prompt。
- 影响：通用翻译术语质量仍可能不稳定。

### 2026-06-30：RIS 导入 Zotero 只生成链接而非 PDF 附件

- 场景：导入 RIS/BibTeX 后，Zotero 条目只有 URL，需要手动找 PDF。
- 表现：不能直接在 Zotero Reader 中批注。
- 原因：普通 RIS 只包含元数据和 URL，不包含本地 PDF 附件字段。
- 解决：生成带 `L1 - file:///...pdf` 的 RIS，并下载公开可获取 PDF。
- 预防：以后导入前优先生成 `with_PDF` RIS。
- 影响：付费墙或无开放 PDF 的论文仍需手动获取。
