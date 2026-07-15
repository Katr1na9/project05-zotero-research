# Project05 LLM 编译 Phase 1（v0.2）

## 当前状态

本目录只承载 Paper B 的 Phase 1：来源约束的 observation compiler，以及同一通用模型下的 structured/direct 对照。授权范围为 RQ1 与 RQ5；RQ3 端到端传导、RQ4 selector、Phase 2/3、强化学习、微调和多模态均未授权。

截至 2026-07-15，dependency-free 基础设施、public/private ID 隔离、真实来源 context-packet 草案、G0 admission、Rule 实现、G1 多 gold scorer、stub backend、四组 prompts、structured 七段哈希链与 prompt/config lock 已实现。尚无任何模型输出，也未安装或下载 `jsonschema`、PyTorch、Transformers、Accelerate、bitsandbytes 或模型权重。

双人 null 构造审计与 Rule development snapshot 已完成：

- development null 构造审计：26/26 双人确认，SHA-256 `8D8649384C0829DB5C33D6817D48DC1F1B3E85608ECAAD16E0903682A2EBBD53`；
- test null 构造审计：32/32 双人确认，SHA-256 `6DD8D97B87FCDC73824DA1A2991FD6F64232CD538A3B00D1BAF7D343D0C2E5ED`；
- Rule snapshot：`baseline_strength_gate=passed`，52 个 development packets，schema-valid rate 1.0，abstain rate 0.2308，project-gold agreement 0.2692。Rule 对 26/26 positive 产生 claim，12/26 null abstain；该偏弱分布已冻结，禁止在看到 LLM 输出后增强。

审计前的历史证据保留在 `generated/pre-model-readiness.json`。当前权威机器证据为 `generated/pre-model-readiness-post-audit.json`：60 项定向测试通过，test bundle 为 64 packets / 6 cases，public/private 扫描无泄漏，prompt/config lock 与 Rule snapshot 有效，推理依赖、本地模型缓存及模型输出均不存在，禁改文件差异为空。当前状态为 `ready_to_request_model_authorization`，但这不是模型授权本身。

## 数据与边界

- `generated/development/`：C04–C06，26 positive + 26 null 草案，仅用于 Rule 开发校准。
- `generated/test/`：C07–C12，32 positive + 32 null 草案，冻结测试形状为 64 packets / 6 独立案例。
- `generated/*/public/`：唯一允许进入推理进程的数据。
- `generated/*/private/`：G1 scorer-only gold，永不进入 validator、runner 或 structured 第二阶段。
- `generated/null-construction-audit/`：模型前 null 构造审计模板，不是模型后 G2 输出评分。
- C12 null 草案含 aggregate observation 的 constituent records，必须由两名独立审阅者逐项确认；不得以程序默认值代替人工判断。

旧目录 `09-experiments/llm_compiler/` 与旧 14-row pilot 只保留为历史 smoke test，不构成本 Phase 1 的科学结果，也不得把旧 `claim_id` 逻辑带入 v0.2。

## Gate 与声明纪律

1. development/test null 构造审计与 private manifest 冻结已完成。
2. development-only Rule snapshot 已冻结；不得查看任何 LLM 输出后再调规则。
3. readiness 已给出 `ready_to_request_model_authorization=true`；下一步必须由用户另行授权依赖安装与模型 revision 解析，不能把 readiness 视作自动授权。
4. Gates 9.1–9.3 未全部通过前，Paper B 标题、摘要和核心贡献不得写入正向 LLM 效果声明；Paper A 继续保持调查控制/参数治理叙事，不得混写本支线未出结果。
5. 若 G2 的 κ `<0.70` 或 unassessable `>20%`，论文形态预注册为 `negative_evaluation_or_interface_pilot`；不得使用“减少幻觉”“降低无支撑断言”等人类验证措辞，也不得用 Phase 2/3 事后救场。

无合格 G2 时，只能报告 `project_gold_packet_agreement`、`ceiling_violation_rate` 与 `invalid_pointer_rate`，不能使用 GPS/UCR 名称。

## 预模型验证命令

```powershell
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest 09-experiments.tests.test_llm_packet_separation 09-experiments.tests.test_llm_phase1_contract 09-experiments.tests.test_llm_phase1_validation 09-experiments.tests.test_llm_phase1_scoring 09-experiments.tests.test_llm_compiler_pilot -v

& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m py_compile 09-experiments\scripts\build_llm_evaluation_packets.py 09-experiments\scripts\run_llm_phase1.py 09-experiments\scripts\validate_llm_phase1_output.py 09-experiments\scripts\score_llm_phase1.py

& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 09-experiments\scripts\run_llm_phase1.py --pre-model-readiness 09-experiments\llm_compiler_v0.2\generated\pre-model-readiness-post-audit.json
```

readiness 证据拒绝覆盖已有文件。需要重新生成时，应在新审计状态下写入新的审阅路径或经明确审阅后归档旧证据，不得原地改写 JSON。

## HARD STOP A

在用户对新的 readiness 报告作出单独授权之前，禁止安装推理依赖、解析或下载模型 revision/权重、运行 atomic pilot、生成正式模型输出，或启动 Phase 2/3。本文档及所有结果均保持 Markdown/JSON；不生成 DOCX、PPT 或 PDF。
