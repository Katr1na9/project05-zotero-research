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
