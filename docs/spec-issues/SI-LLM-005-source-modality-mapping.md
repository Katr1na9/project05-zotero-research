# SI-LLM-005：source_modality 与 epistemic modality/source_family 语义混淆

**Owner**：Kernel/M3* 会话
**LLM 轨道状态**：阻塞真实 source-family mapping；不阻塞拒绝越权测试

## 当前字段

Legacy 数据的 `source_modality` 值为 `endpoint_event|network_event|security_text`，表示数据载体/来源形态。v0.8 的：

- `modality` 表示认识论来源：`observed|derived|reported|hypothesized|unknown`；
- `source_family` 表示语义来源族：execution、identity、communication、data_access、control_plane、system_provenance、software_supply_chain、external_intel、human_investigation。

## 阻塞案例

`security_text` 可能是 reported CTI，也可能是人工调查记录；`endpoint_event` 通常是 observed，但也可能是 derived alert。若简单映射，reported CTI 可能被“洗白”为 observed case evidence。

## 建议变更

Kernel 发布版本化 source semantics mapping contract：

1. modality 必须来自受信 ingestion metadata，而非 LLM 推断；
2. 每个 source family 的默认 modality 与允许例外；
3. derived alert、reported CTI、human investigation 的明确规则；
4. 不确定时固定为 `unknown` 并 abstain；
5. Promote 永不改变 modality。

## 兼容性影响

旧 `source_modality` 保留为 transport metadata，不能重命名为 `modality`。转换器需要同时输出 transport/source schema 与 epistemic modality。

## 对认证安全的影响

高。错误映射是 evidence laundering 的直接入口，会破坏 Modality Leakage Rate=0 和 Non-Amplification。
