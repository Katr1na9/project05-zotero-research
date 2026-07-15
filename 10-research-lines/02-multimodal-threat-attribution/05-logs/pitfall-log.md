# P05-L2 Pitfall Log

## 记录模板

### YYYY-MM-DD：问题

- 场景：
- 表现：
- 原因：
- 解决：
- 预防：
- 影响：

## 2026-07-12：把“多模态”当作研究问题

- 场景：新支线只有技术方向，没有明确任务。
- 表现：容易直接搜索 VLM、设计融合模型或起论文题目。
- 原因：把技术手段误当成可回答问题。
- 解决：工作区停在 Stage 0，先完成 Socratic RQ Scoping。
- 预防：G1 前禁止创建模型代码和论文正文。
- 影响：高，决定是否会形成宽泛且高撞题的论文。

## 2026-07-12：把文件名前缀当作真实网络模态

- 场景：bridge 为避免 Scapy 误识别，使用文件名前缀覆盖抓包判定。
- 表现：`scion_*` 可在 API 中显示 SCION，但 wire 实际为 IPv4/UDP。
- 原因：实验意图、控制配置和观测事实没有分字段保存。
- 解决：拆分 configured/intended/observed/resolved modality，并保存逐跳证据。
- 预防：文件名只用于 manifest lookup，禁止作为 wire ground truth 或模型特征。
- 影响：高，会造成模态性能、行为追溯和意图解释的循环自证。

## 2026-07-12：混淆网络 operator intent 与攻击者 intent

- 场景：检索 intended/observed behavior 时，RFC 9315 等 intent-based networking 工作大量出现。
- 表现：容易把“网络是否执行运营者意图”误写成“是否识别攻击者意图”。
- 原因：两个领域都使用 `intent`，语义完全不同。
- 解决：本线固定使用 `network intent/compliance` 与 `attack stage/TTP/intent candidate` 两套术语。
- 预防：检索矩阵和论文定义中必须分别列出主体、观测和真值。
- 影响：高，会导致错误撞题判断和错误贡献表述。

## 2026-07-15：把网络字段当作独立流量证据

- 场景：论文同时包含 IP/port/netflow 节点和系统日志。
- 表现：容易称为 traffic+log 双模态图。
- 原因：没有检查网络信息是否来自独立 PCAP/传感器，还是同一 audit event 的字段。
- 解决：只有独立 source lineage、raw anchor 和单独子图才计为流量证据线。
- 预防：功能矩阵固定列 Input、Anchor、X-edge。
- 影响：高，会误判 SAURONEYES、ProHunter 等 audit-only 工作。

## 2026-07-15：把 Softmax/专家权重称为校准概率

- 场景：APMP、MPCA、M-DUCAG 和早期 evidence graph 都带 confidence/probability。
- 表现：误以为 R2 已完全撞题，或反过来把普通分数包装成 calibration novelty。
- 原因：混淆 ranking/discrimination 与 probability calibration。
- 解决：要求独立 calibration set、Brier/ECE/reliability diagram 和 risk-coverage。
- 预防：所有“可信/置信度”主张逐项审计概率含义与样本独立性。
- 影响：高，直接决定核心创新是否成立。

## 2026-07-15：让确定性 join 生成训练真值

- 场景：用时间/五元组/PID 自动生成 packet-log 正样本，再训练模型超越同一规则。
- 表现：模型获得漂亮结果，但只复现标注规则。
- 原因：标签与 baseline 同源，形成循环验证。
- 解决：基于场景/raw evidence 定义独立关系语义，双人标注歧义样本并构造 hard negatives。
- 预防：pilot 先计算标注一致性，campaign-disjoint 切分后才训练。
- 影响：致命，若不解决会使 R2 无效。

## 2026-07-15：把访问受限摘要写成全文精读

- 场景：T-Trace、Citar、ANTEATER 等只有出版页/索引内容。
- 表现：容易复述搜索索引中的表格或方法细节。
- 原因：检索工具暴露长摘要片段，看起来像全文。
- 解决：使用 `extended-indexed-read` / `metadata-abstract-only` 状态并限制可用 claim。
- 预防：每篇笔记顶部记录合法全文来源和允许用途。
- 影响：高，关系到综述证据可信度。
