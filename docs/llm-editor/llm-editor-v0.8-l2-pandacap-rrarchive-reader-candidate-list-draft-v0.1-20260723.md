# PANDAcap RRArchive reader candidate list draft v0.1

日期：2026-07-23  
authority base：`456b129bd98a317c3de85e78274b11e28ff61a41`

## 裁断

本清单只有候选，没有 reader 选择或执行权。公开元数据中可见 PANDA `v1.8.85` 与 PyPI `pandare 1.8.85`，但这些只是观察到的上游版本，**不是 pin**。

| 候选 | 观察版本 | 用途候选 | 主要限制 | 状态 |
|---|---|---|---|---|
| PANDA `rrunpack.py` | upstream `v1.8.85` | RRArchive unpack/兼容性候选 | 是 unpack utility，不是已证明的 no-extract bounded reader；可能违反首道审计边界 | `not_pinned / not_installed / not_authorized` |
| PANDA native replay runtime | upstream `v1.8.85` | 格式参考实现 | replay 是主动执行；可能暴露命令、凭据、payload、隐私和恶意行为；不适合首道 CD/notice 审计 | `not_pinned / not_installed / not_authorized` |
| PANDA `rr_print` | upstream `v1.8.85` | 低层 RR log parser 候选 | 公开的是源码而非 pinned executable；可能输出 ordinary replay content；并非已证实的外层 archive reader | `not_pinned / not_installed / not_authorized` |
| `pandare` Python interface | PyPI `1.8.85` | PANDA controller 候选 | 不是已证明的 standalone passive reader；可能依赖 native PANDA 并启动 replay | `not_pinned / not_installed / not_authorized` |

## 后续 reader amendment 必须冻结

- reader 名称、精确版本或 commit；
- executable/package/dependency identity 与 SHA-256；
- invocation 与 parser；
- member、token、per-member、total-byte、time、output caps；
- no-extract、no ordinary content、隐私/secret/identifier/malware/raw-path redaction；
- unsupported format 或超限时 fail closed。

优先顺序是先寻找被动、bounded、no-extract 的 RRArchive metadata parser。`rrunpack.py` 只有在能证明不落盘、不展开 ordinary content 的受限路径时才值得继续；native replay、`rr_print` 与 `pandare` 至多是后续兼容性候选。

## 自检

本轮只读取 `docs/llm-editor/` 中的已提交材料和 GitHub/PyPI 公开元数据。未检查本机 reader；未安装或执行 reader；未读源码 blob 内容；未读 archive、central directory 或 member；未触碰 acquisition、cache、launcher、PID 或日志；未写 effective catalog；未改 role/quota/L2；未运行 baseline、微调或训练样本；未 commit、未 push。
