# Project05 constrained decoder 隔离依赖兼容预检修订 v0.45

日期：2026-07-20

状态：`single_dependency_install_and_zero_model_call_preflight_authorized`

## 1. 目的

v0.44 已完成 pointer-free JSON Schema、程序化 pointer binder、正例硬 Gate 和模型惰性 runner，但服务器既有 runtime 不包含 constrained-decoding 包。v0.45 只回答一个工程前置问题：

> `lm-format-enforcer==0.10.6` 能否在现有 Python 3.11.9、Transformers 4.45.2 和冻结 Qwen2.5 tokenizer 上解析 two-branch JSON Schema，并允许 supported/unsupported 两条 canonical token 路径正常 EOS？

本阶段不加载 Qwen 权重、不加载 adapter、不读取 training-validation payload，模型调用数必须为 0。

## 2. 唯一服务器边界

只允许访问：

```text
/home/myy/project05-qwen25-4090-v0.1
```

依赖必须安装到：

```text
/home/myy/project05-qwen25-4090-v0.1/local-runtime/constrained-v0.1
```

部署包、pip cache、临时目录和输出审计也必须位于该根目录内。禁止列举、读取、创建、移动或删除服务器其他目录。

## 3. 隔离安装规则

- 固定 requirement：`lm-format-enforcer==0.10.6`；
- 使用现有 venv 的 `pip --target`，不修改现有 venv site-packages；
- 首先安装到 `.installing` 临时目标，成功且容量过 Gate 后原子改名；
- target、`.installing`、成功审计或失败审计任一已存在时拒绝覆盖；
- 最大依赖目标容量 100,000,000 bytes；
- pip cache 和 TMP 均重定向到授权根目录；
- 安装失败只写一次脱敏 failure audit，不自动重试；
- 不把 pip stdout/stderr、下载 URL 或环境秘密写入 Git 工件。

## 4. 兼容预检

安装成功后执行以下零模型调用检查：

1. distribution 版本精确为 0.10.6；
2. 实际导入模块位于隔离 target 内；
3. Draft 2020-12 Schema 自身合法；
4. `JsonSchemaParser` 能构建 two-branch grammar；
5. 使用冻结 Qwen tokenizer 和真实 chat prompt 前缀；
6. supported canonical JSON 的每一个目标 token 都在 grammar 允许集合内；
7. unsupported canonical JSON 的每一个目标 token都在 grammar 允许集合内；
8. 两条完整路径结束后 EOS 均被允许；
9. 每一步允许 token 集均非空；
10. 记录包版本、token 数、允许集合范围和哈希，不记录 prompt/payload 原文。

fixture 只使用合成的 `preflight.exe`、`/tmp/preflight.bin` 与虚构 pointer，不使用任何训练、验证或测试数据。

## 5. 明确禁止

v0.45 不授权：

- `AutoModelForCausalLM`、PEFT adapter 或任何权重加载；
- `model.generate` 或其他模型调用；
- 读取 training-validation、train、development/test 或 C07–C12；
- M3、控制器、`run_mvp.py` 或 Paper A 修改；
- 自动 retry、schema 降级、自由生成 fallback 或 parser repair；
- 下载新模型、tokenizer、adapter 或 checkpoint；
- 访问 `/home/myy/project05-qwen25-4090-v0.1` 之外的路径。

## 6. 结果分支

通过：只允许回收脱敏 preflight audit，然后建立新的、哈希锁定的一次性 16 条/32 调用 execution authority。通过本身不授权模型执行。

失败：保留失败审计并停止。不得更换 constrained-decoder 包、版本或 schema 后自动重试；任何替代方案需要新 amendment。

## 7. 产物

- dependency/preflight 脚本；
- 4090 零模型调用 launcher；
- v0.45 authority；
- 模型无关测试；
- 成功时一个脱敏 JSON audit，失败时一个脱敏 failure JSON。

raw generation 在本阶段不存在，adapter 与训练数据均不被读取。
