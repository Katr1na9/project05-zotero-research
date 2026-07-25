# Project05 observation compiler：train-null 替代来源快速证据审查协议

日期：2026-07-18  
审查类型：目标明确的 rapid evidence review（非效果量 meta-analysis）  
状态：`frozen_before_external_search`  
冻结时点：本文件写入后、首次本轮 Parallel Web 外部检索前

## 1. 研究问题

### RQ1：完整传感器覆盖的良性时间窗

公开主机审计、provenance 或网络安全数据集中，是否存在由论文或采集协议明确保证的时间窗，使得：

1. 传感器覆盖范围、启停时间和丢失事件处理可审计；
2. 时间窗内没有目标事件/关系不是由“没有告警”“normal 文件名”或未标注推断；
3. 该真值单位与 Project05 的案件级、来源可回指 `process/file/network/system` observation 相同；
4. 可在许可和来源独立性约束下提供至少 478 条正式 train-null 的数量潜力。

### RQ2：显式 non-entailment / no-relation 的安全语义数据

是否存在安全领域 NLI、事件抽取或关系抽取数据，显式标注某段可见证据不蕴含候选事件/关系，并且：

1. 负例不是由知识库缺失、未标注实体对或远程监督缺失自动生成；
2. 标签协议与标注一致性可核验；
3. 任务单位和输出能映射到 Project05 observation contract；
4. 数据与许可允许本地 QLoRA 研究训练。

### RQ3：可证明不相容的受控反事实

关系抽取、事件抽取、NLI 和 provenance 建图文献是否支持从正例构造以下负例：

- 实体类型不相容；
- 时间窗不相容；
- 来源指针与候选关系不相容；
- 在同一封闭记录内可机械证明的 subject/object/predicate 不匹配。

重点区分两种任务：

1. **无条件抽取**：给定 packet，输出所有可支撑 observation；
2. **候选条件验证**：给定 packet 与 candidate relation，只判断该 candidate 是否被来源支撑。

若受控负例只对第 2 类任务成立，则不得把它静默计入现有无条件 compiler 的 `null`；只能提出单独 amendment。

## 2. 冻结的 Project05 判定合同

### 2.1 当前正式 null

当前定义保持不变：`No author-acceptable target SPO observation exists in the visible packet.`

禁止用下列捷径制造正式 null：

- benign、normal、routine 或 outside attack window；
- 没有告警、没有 TTP、没有 extractor 输出；
- 文件名、目录名、scenario/path 标签；
- 未进入知识库或未被标注；
- validation null 迁入 train；
- 放宽 CAM-LDS 禁令。

### 2.2 正式来源必须同时通过

| Gate | 最低要求 |
|---|---|
| 真值 | 论文/协议直接说明负例如何成为负例，且统计单位匹配 |
| 许可 | 根许可与 nested notices 清楚，允许当前研究处理；不作法律意见 |
| 独立性 | 不属于 C07–C12、E3/E5、OpTC、OTRF、WitFoo，也不与已用家族重复凑数 |
| 泄漏 | 下载前只做元数据；下载后仍须 exact/hash/5-gram exclusion scan |
| 数量 | 至少有 478 条合格 train-null 的现实潜力；不足者只能辅助或诊断 |
| 模态 | 不得靠与正例完全不同的文件类型让模型学习 source-format shortcut |

## 3. 预注册裁决类别

| 类别 | 含义 |
|---|---|
| `formal_train_null_candidate` | 真值单位、许可、独立性和数量潜力均通过；可进入新的 metadata-only V3-B 子闸门 |
| `amendment_candidate` | 科学上只对候选条件验证/显式非蕴含成立；必须先修改任务合同，不能计入现有 Gate |
| `smoke_only` | 标签合理但数量、许可范围或代表性不足，只能做系统冒烟 |
| `diagnostic_only` | 可作为挑战集衡量越界/弃权，但不得训练、选 checkpoint 或计 Gate |
| `reject` | 真值、许可、泄漏或单位至少一项不成立 |

不得因为正式 Gate 尚缺 478 条而降低判定阈值。

## 4. 数据库与冻结检索式

检索日期：2026-07-18；英文为主；不限起始年份；截至检索日。每个主题至少执行学术聚焦和通用搜索各一组，所有 Parallel Web JSON 原样保存在 `sources/search/`。

### A. 主机审计/provenance 数据与良性窗口

- `host audit provenance dataset benign time windows complete sensor coverage ground truth`
- `cybersecurity provenance dataset attack ground truth benign events auditd sensor coverage`
- `LID-DS AIT-LDS BETH dataset benign labels ground truth collection protocol`
- `DARPA transparent computing benign background ground truth provenance limitations`

### B. 安全领域显式 non-entailment/no-relation

- `cybersecurity natural language inference dataset non entailment relation extraction no relation`
- `cyber threat intelligence relation extraction dataset negative examples annotation protocol`
- `security event extraction dataset explicit negative no event labels`
- `CTI claim verification evidence entailment dataset`

### C. 受控反事实与负样本构造

- `relation extraction controlled counterfactual negative sampling entity swap false negatives`
- `event extraction hard negative generation type constraint counterfactual`
- `natural language inference hard negatives lexical overlap adversarial annotation`
- `knowledge graph negative sampling typed temporal constraints false negative`

### D. 候选的官方材料

对入围候选再检索原论文、数据卡/README、固定版本、许可文本、nested notices、记录数和标签协议。搜索摘要只用于定位，不直接支持最终裁决。

## 5. 纳入与排除

纳入：

- 公开原论文、同行评审会议/期刊论文或可核验技术报告；
- 数据发布方的官方协议、数据卡、固定仓库/归档和许可；
- 对负例构造、闭世界边界、标注一致性和 false-negative 风险有直接方法说明的文献；
- 能核验标题、作者、年份、venue、DOI/稳定 URL 及相关原文。

排除：

- 仅凭数据集名字含 benign/normal 判真；
- 仅用于入侵检测分类而不提供事件/关系负真值；
- 从未标注实体对、知识库缺失或模型未检出自动生成的 `no_relation`；
- 许可、来源或下载工件无法固定；
- 与冻结测试家族重合或包含测试原文；
- 仅有二手博客或无全文支持的搜索摘要。

## 6. 证据分级

| 等级 | 含义 |
|---|---|
| A | 同任务或同统计单位的官方协议/同行评审直接证据，真值过程完整 |
| B | 相邻任务的高质量同行评审证据，可支持方法原则但不能直接外推 |
| C | 预印本、数据卡、仓库说明或许可元数据 |
| D | 搜索摘要/二手材料，仅用于定位 |

## 7. 防止结论漂移

1. 攻击窗口之外不自动等于没有 observation。
2. benign 事件仍可能是合法 process/file/network/system SPO。
3. 显式 non-entailment 只证明候选 claim 不被文本支撑，不证明世界中事件未发生。
4. 受控实体交换若仍留下其他可抽取关系，不能作为无条件 compiler 的空输出样本。
5. 找到高质量 `no_relation` 数据也必须检查它是否由不完整标注派生。
6. 未找到合格来源时，应裁决现有 40%–60% 无条件 packet-null Gate 与通用日志抽取任务不相容，而不是请求用户补主观标签。
7. 本轮不下载语料、tokenizer 或模型，不安装环境，不训练，不运行正式推理。
