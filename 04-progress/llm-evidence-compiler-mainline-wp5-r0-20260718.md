# Project05 主线 LLM 证据编译层：WP5 / CTINexus Gate R0

日期：2026-07-18  
终态：`passed_r0_minimal_import_full_runtime_blocked`  
准确结论：CTINexus 固定 wheel 的最小 import 与 CLI help 通过；完整 pipeline runtime 尚不可用、未授权、未执行。

## 1. 本轮完成了什么

- 下载并校验 `ctinexus==0.2.1` wheel；
- SHA-256 精确匹配：`EE45EEF7D719B5EDA187455DDC9262967A36A1595785F190E9062080D4A1C003`；
- METADATA 显示 MIT License，Python 范围为 `>=3.10,<3.14`；
- wheel 共 333 个条目，无原生二进制、无加密条目、无路径穿越；
- 创建 Python 3.11.15 隔离环境；
- 仅安装 CTINexus wheel 与 `python-dotenv==1.2.1`，环境约 26.9 MB；
- 从空工作目录执行受网络保护的 import 与 CLI help；
- 冻结最小环境锁、依赖缺口和独立 readiness。

本轮没有安装 Gradio、LiteLLM、Hydra、pandas/scipy/sklearn 等完整运行依赖，没有下载模型或 embedding，没有运行任何 CTI 输入。

## 2. 隔离 smoke 结果

| 项目 | 结果 |
|---|---:|
| `import ctinexus` | 通过 |
| CLI help | 通过 |
| provider 凭据发现 | 0 |
| 注册 provider | 0 |
| 网络连接尝试 | 0 |
| model / embedding load | 0 |
| pipeline runtime | 0 |
| CTI 输入 | 0 |
| 第三方 demo/annotation 数据读取 | 0 |
| Gradio/LiteLLM/科学计算模块加载 | 0 |

隔离措施包括 Python `-I`、`PYTHONNOUSERSITE=1`、禁用 dotenv、空工作目录、移除 provider 环境变量以及 socket 网络拦截。

## 3. 第三方内置数据风险

wheel 自带：

- annotation 文件 149 个；
- demo 文件 148 个；
- 其中 30 个文件名包含 APT/actor/campaign 类词。

这些内容没有进入 Project05 输入，也没有在 smoke 中读取。`downloads/`、`venv/` 和 `sandbox/` 已由本地 `.gitignore` 排除，第三方 wheel、示例数据与隔离环境不会推送到仓库。正式工件只保存哈希、数量、依赖清单与审计结果。

## 4. 完整 runtime 阻塞

CTINexus 声明 13 个当前未安装的 runtime 依赖：

```text
gradio, hydra-core, jinja2, litellm, networkx, nltk, omegaconf,
pandas, pyvis, scikit-learn, scipy, tld, trafilatura
```

一次 `pip --dry-run` 完整闭包解析在 `litellm 1.92.0` 的 Windows sdist metadata 阶段失败，并意外尝试在 AppData 临时缓存获取 Rust 工具链。Project05 venv 未被修改；本次新建的 `cargo/rustup/rustup-init` 临时目录已在核对绝对路径后清理。

因此不能声称：

- CTINexus pipeline 已可运行；
- CTINexus 已在 Project05 CTI 上产生 triplet；
- LLM 编译性能已被验证；
- 完整依赖安装已通过。

## 5. 关键工件

- `09-experiments/llm_evidence_compiler_mainline/wp5/r0/r0-readiness.json`
- `09-experiments/llm_evidence_compiler_mainline/wp5/r0/wheel-static-audit.json`
- `09-experiments/llm_evidence_compiler_mainline/wp5/r0/r0-import-smoke-v0.1.1.json`
- `09-experiments/llm_evidence_compiler_mainline/wp5/r0/minimal-environment-lock-v0.1.1.json`
- `09-experiments/llm_evidence_compiler_mainline/wp5/r0/r0-dependency-resolution-observation.json`
- `09-experiments/scripts/audit_ctinexus_r0_wheel.py`
- `09-experiments/scripts/run_ctinexus_r0_smoke.py`
- `09-experiments/scripts/validate_ctinexus_r0.py`

首次 smoke 因本地 wheel 的 `pip freeze` 使用 `name @ file://...` 形式而 fail closed；该失败工件被保留。v0.1.1 改用 `pip list --format=json` 校验实际版本后通过，没有覆盖或删除失败记录。

## 6. 验证

- 全部 compiler tests：80 passed；
- 全实验测试：522 passed，6 skipped，346 subtests passed，0 failed；
- M3 脚本、M3 结果、C07–C12、旧 EvidenceClaim/alignment schemas 均未修改。

## 7. 下一步建议

> 2026-07-18 路线更新：用户已否决 Qwen。下列建议以 `llm-evidence-compiler-open-base-finetuning-amendment-v0.1-20260718.md` 为准；Qwen 不再具有任何执行授权。

不建议在当前 Windows 环境直接重试 CTINexus 全依赖安装。更新后的建议为：

1. 主方法评估非营利研究机构发布、开放权重的 OLMo 2 本地编译器，以文献复现式 QLoRA 学习 Project05 的 pointer/SPO/link/abstention 合同，再经过 Project05 source-span Gate；
2. CTINexus 完整上游 runtime 降为可选复用基线，后续若需要可在 WSL/Linux 或单独兼容锁中复现；
3. 两者都不直接进入 M3，sidecar 继续保持 `controller_eligible=false`。

当前仍不需要双人审计。R0 没有产生语义输出。
