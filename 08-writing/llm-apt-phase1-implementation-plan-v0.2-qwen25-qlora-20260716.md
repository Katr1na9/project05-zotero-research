# Paper B Phase 1 Qwen2.5 同底座 QLoRA 实施计划 v0.2

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development`（仅在用户明确要求子代理时）或 `superpowers:executing-plans`，逐任务实施并在每个硬停点提交用户审核。所有追踪步骤使用 checkbox（`- [ ]`）。

**状态：** `superseded_no_qwen_execution_authority`  
**取代文件：** `llm-evidence-compiler-open-base-finetuning-amendment-v0.1-20260718.md`  
**说明：** 用户于 2026-07-18 明确否决 Qwen；本计划只作历史实施记录，不得用于下载、安装、训练或正式推理授权。

**Goal:** 在不改动 Paper A、Phase 2/3 和 C07–C12 冻结测试字节的前提下，以固定 `Qwen/Qwen2.5-7B-Instruct` 为唯一底座，构建并评估 Project05 observation-compiler QLoRA adapter，完成同底座 General/Adapted、Rule、structured/direct、G2 与负结果回退的可复现实验链。

**Architecture:** 继承已完成的 v0.2 public/private 分包、Rule snapshot、G0/G1 scorer 和 null construction audit；新增独立训练来源治理、来源家族隔离、作者审核训练标签、QLoRA 训练和单底座 adapter 切换。正式推理先运行 General compiler，并将同一次 compiler 结果复用于 structured conclusion，避免重复调用并保持 448-call 预算；测试完成后再构建独立 G2 盲审包和声明 Gate。

**Tech Stack:** Windows 11 / PowerShell、Python 3.11、stdlib-first pre-model tests、JSON/JSONL/GZip/CSV/SHA-256、PyTorch `2.3.1+cu121`、Transformers `4.45.2`、PEFT `0.13.2`、bitsandbytes `0.43.1`、RTX 2080 Ti 11 GB、Hugging Face 本地 cache。

## Global Constraints

- 权威设计：`08-writing/llm-apt-provenance-research-design-v0.3-qwen25-qlora-amendment-20260716.md`。
- 执行工作树：`C:/Users/35393/Desktop/workspace/Project05-Zotero/.worktrees/llm-apt-phase1`；分支 `codex/llm-apt-phase1`；起点 commit `dc9dbc0942fe912df2d57b9c24b2601a9f5ea60a`。
- 主工作区已有用户文件移动和 `docs/superpowers` 安装内容；实施只在上述 feature worktree 中进行，不整理、不暂存、不提交主工作区无关变化。
- v0.2 生成目录当前为未跟踪私有/实验工件；禁止 `git add .`、`git add -A` 或通配暂存。每次提交必须显式列出计划文件，且提交前运行 `git diff --cached --name-only`。
- 不覆盖 `09-experiments/llm_compiler_v0.2/generated/{development,test,null-construction-audit,runs}`；v0.3 只读取并锁定其 hash。
- 不修改 `09-experiments/scripts/run_mvp.py`、`09-experiments/real_cases/`、Paper A、专利文本、成本 profile 或旧结果。
- 不生成 DOCX、PPTX 或 PDF；所有阶段记录先写 Markdown/JSON。
- 只实现 RQ1 与 RQ5；不实现 selector、DQN、RL、actor/campaign 监督或 Phase 2/3。
- 唯一底座：`Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28`；`trust_remote_code=false`；正式运行 `local_files_only=true`。
- General 与 Adapted 条件必须使用同一内存中的底座、同一 tokenizer、同一量化和解码；差异只能是 adapter disabled/enabled。
- QLoRA：NF4 + double quantization、FP16 compute、`r=16`、`alpha=32`、dropout `0.05`、7 个 attention/MLP projection、sequence 1024、micro-batch 1、gradient accumulation 16、最多 3 epochs、LR `2e-4`、primary seed `2026071601`。
- 训练进程不得读取 v0.2 development/test、G2、Paper A 或模型测试输出；训练数据根目录之外的输入必须 fail closed。
- DARPA TC E3 已用于 v0.2 development/Rule/prompt 开发，不进入 QLoRA train/training-validation；DARPA TC E5、DARPA OpTC、OTRF APT29、WitFoo Precinct6 属于 C07–C12 测试家族，同样禁止进入训练。
- 最低数据 Gate：train `>=400` packets / `>=4` 独立来源家族；training-validation `>=100` packets / `>=2` 未进入 train 的来源家族；正/null 各 40%–60%；至少 50% 正 packet 有干扰记录或多记录选择。
- 固定 Qwen2.5 tokenizer 必须对完整 prompt+target 统计 train/validation p50、nearest-rank p95、pre-exclusion max 和 final max；p95 `<=1024`，超长 packet 在冻结前排除并重算全部 Gate，最终 max `<=1024`，全程禁止静默截断。
- 训练标签只需逐项作者审核，不要求双人盲标；它们不能替代 G2，也不能称为人类共识 gold。
- 模型/cache/checkpoint 总量上限 30,000,000,000 bytes；训练或正式推理预计/实际超过 24 GPU 小时则停止；smoke 峰值显存必须 `<=10.5 GiB`。
- 最大正式推理 448 calls；若预计超过 24 GPU 小时，只取消 192-call repeat panel，保留 256-call first-pass。
- 测试独立单位始终是 6 个案例；packet 和重复调用不得伪装成独立样本。
- G2 不实施或 kappa `<0.70` / unassessable `>20%` 时，不输出 GPS/UCR，不声称减少幻觉或提高真实 APT 溯源准确率。
- 任何测试输出不得回流 prompt、Rule、数据、adapter、阈值、matching fields 或 checkpoint 选择。
- 每个任务先写失败测试、确认失败、做最小实现、确认通过、显式暂存、检查 staged diff、再提交。

---

## Inherited Baseline（开始编码前复核）

| 工件 | 当前 SHA-256 |
|---|---|
| `pre-model-readiness-post-audit.json` | `631d367cd63c37b5cbf64d4e343e278cc48e0ca75d9863a3f8c7d8c7111f697b` |
| `frozen/prompt-config-lock.json` | `451ca81133b672cb81bba39626ba20727bd02bb575a16b72bd47b1794ca8a753` |
| `frozen/rule-baseline-development.json` | `ff69476ec63da5d89d332085b9d9ccbf314fdba9383ffbdfb0e88ffd8be0f6d1` |
| test public `input_manifest.json` | `00ef6be1584486a249d396ee6c9f2fa4ff24691f6269db169c55963204abc566` |
| test private `gold_manifest.json` | `4fb476316dda262ba81a2fb0dff35b01b293bda837efb276ccf350cf8358f822` |
| development public `input_manifest.json` | `5361efe4a3ebaf9b14f52c03d0b6ae1bd747cd80adbe5e6e5a29ffa9774a2b61` |
| development private `gold_manifest.json` | `bf4df68d539a30e1bfcb7f5b053238dc7af787957bf4224c87ced6613df5c6f0` |
| test null audit CSV | `6dd8d97b87fcdc73824da1a2991fd6f64232cd538a3b00d1baf7d343d0c2e5ed` |
| development null audit CSV | `8d8649384c0829db5c33d6817d48dc1f1b3e85608ecaad16e0903682a2ebbd53` |

开始时运行：

```powershell
$ProjectPython='C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest `
  09-experiments.tests.test_llm_packet_separation `
  09-experiments.tests.test_llm_phase1_contract `
  09-experiments.tests.test_llm_phase1_validation `
  09-experiments.tests.test_llm_phase1_scoring `
  09-experiments.tests.test_llm_compiler_pilot -q
```

Expected: `Ran 60 tests` and `OK`。若任一 hash 或基线测试不符，停止，不自动重建 v0.2 工件。

---

## File Map

### Tracked files to create

- `09-experiments/llm_compiler_v0.3/README.md` — v0.3 条件、继承边界与运行顺序。
- `09-experiments/llm_compiler_v0.3/experiment_config.json` — General/Adapted/structured/direct、seeds、调用预算和路径。
- `09-experiments/llm_finetuning_v0.3/README.md` — 标准化来源包、作者审核和训练边界。
- `09-experiments/llm_finetuning_v0.3/training_config.json` — QLoRA、checkpoint 选择和资源 Gate。
- `09-experiments/llm_finetuning_v0.3/source_catalog.json` — 只保存用户已审核的来源家族、许可证证据和 split role；未批准行不得进入该文件。
- `09-experiments/data_schema/llm_training_source_catalog.schema.json` — 来源许可和 split schema。
- `09-experiments/data_schema/llm_training_record.schema.json` — 标准化 source record 与 observation candidate schema。
- `09-experiments/data_schema/llm_finetuning_packet.schema.json` — train/training-validation packet schema。
- `09-experiments/data_schema/llm_adapter_manifest.schema.json` — adapter、底座、数据与运行时 provenance。
- `09-experiments/data_schema/llm_model_runtime_lock_v0.3.schema.json` — Qwen commit、文件 hash、依赖、GPU 与授权状态。
- `09-experiments/governance/contracts/llm-compiler-contract-v0.3.json` — v0.3 同底座和训练/test 隔离契约。
- `09-experiments/scripts/freeze_llm_v03_inheritance.py` — v0.2 hash 继承锁。
- `09-experiments/scripts/audit_llm_training_sources.py` — 来源许可、blocked family、exact/near duplicate 和测试标识扫描。
- `09-experiments/scripts/build_llm_finetuning_data.py` — 审核标签导入与确定性 packet 构建。
- `09-experiments/scripts/validate_llm_finetuning_data.py` — 数据充分性和物理隔离 Gate。
- `09-experiments/scripts/lock_qwen_runtime.py` — 无权重元数据 lock、下载后 hash 和磁盘 Gate。
- `09-experiments/scripts/llm_qwen_backend.py` — lazy local-only Qwen/PEFT inference backend。
- `09-experiments/scripts/train_qwen_qlora.py` — assistant-only loss、smoke、primary training、checkpoint selection 和 adapter manifest。
- `09-experiments/scripts/run_llm_phase1.py` — 配置路径解耦、Adapted condition、stage-1 reuse 和正式调度。
- `09-experiments/scripts/score_llm_phase1.py` — Adapted Gate、G2、GPS/UCR 和 publication decision。
- `09-experiments/tests/test_llm_v03_inheritance.py`。
- `09-experiments/tests/test_llm_finetuning_data.py`。
- `09-experiments/tests/test_llm_finetuning_leakage.py`。
- `09-experiments/tests/test_qwen_runtime_lock.py`。
- `09-experiments/tests/test_qwen_qlora.py`。
- `09-experiments/tests/test_llm_phase1_adapter.py`。
- `09-experiments/tests/test_llm_phase1_g2.py`。

### Generated/private files（不得宽泛暂存）

- `09-experiments/llm_compiler_v0.3/generated/frozen/v02-inheritance-lock.json`。
- `09-experiments/llm_compiler_v0.3/generated/frozen/prompt-config-lock.json`。
- `09-experiments/llm_compiler_v0.3/generated/frozen/qwen25-runtime-lock.json`。
- `09-experiments/llm_finetuning_v0.3/generated/source-candidate-review.csv`。
- `09-experiments/llm_finetuning_v0.3/generated/author-review.csv`。
- `09-experiments/llm_finetuning_v0.3/generated/{train,training-validation}/`。
- `09-experiments/llm_finetuning_v0.3/generated/frozen/{test-exclusion-lock,data-gate,adapter-manifest}.json`。
- `09-experiments/llm_finetuning_v0.3/generated/frozen/tokenizer-lock.json` — 固定 Qwen2.5 tokenizer 小文件、chat serialization 与 hash；不含权重。
- `09-experiments/llm_finetuning_v0.3/generated/runs/{smoke,primary}/`。
- `09-experiments/llm_compiler_v0.3/generated/runs/{atomic-pilot,formal}/`。
- `09-experiments/llm_compiler_v0.3/generated/g2-audit/<audit_id>/`。
- `.cache-llm-phase1-qwen25/`、`.venv-llm-phase1-qwen25/`、adapter 与 checkpoint 二进制文件。
- `04-progress/llm-apt-v03-*-20260716.md` 阶段证据记录。

---

### Task 1: Freeze v0.2 inheritance and declare the v0.3 contract/config

**Files:**

- Create: `09-experiments/llm_compiler_v0.3/README.md`
- Create: `09-experiments/llm_compiler_v0.3/experiment_config.json`
- Create: `09-experiments/llm_finetuning_v0.3/training_config.json`
- Create: `09-experiments/governance/contracts/llm-compiler-contract-v0.3.json`
- Create: `09-experiments/scripts/freeze_llm_v03_inheritance.py`
- Create: `09-experiments/tests/test_llm_v03_inheritance.py`

**Interfaces:**

- `build_inheritance_lock(v02_root: Path, expected: dict[str, str]) -> dict[str, Any]`
- `verify_inheritance_lock(lock: dict[str, Any], v02_root: Path) -> None`
- Produces immutable input for all later v0.3 preflights.

- [ ] **Step 1: Write failing inheritance/config tests.**

```python
def test_v03_inherits_exact_v02_assets_without_rebuild(self):
    lock = inheritance.build_inheritance_lock(V02_ROOT, EXPECTED_SHA256)
    self.assertEqual("dc9dbc0942fe912df2d57b9c24b2601a9f5ea60a", lock["code_commit"])
    self.assertEqual(64, lock["test_packet_count"])
    self.assertEqual(6, lock["test_case_count"])
    self.assertEqual(EXPECTED_SHA256, lock["files"])

def test_v03_declares_one_base_and_one_adapter(self):
    config = json.loads(V03_CONFIG.read_text(encoding="utf-8"))
    self.assertEqual("Qwen/Qwen2.5-7B-Instruct", config["models"]["base"]["model_id"])
    self.assertEqual("a09a35458c702b33eeacc393d103063234e8bc28", config["models"]["base"]["resolved_commit"])
    self.assertNotIn("security", config["models"])
    self.assertEqual("base", config["models"]["adapter"]["base_role"])
    self.assertEqual(448, config["call_budget"]["maximum_formal"])

def test_training_config_matches_approved_qwen25_qlora_design(self):
    config = json.loads(TRAINING_CONFIG.read_text(encoding="utf-8"))
    self.assertEqual({"rank": 16, "alpha": 32, "dropout": 0.05}, config["lora"])
    self.assertEqual(1024, config["sequence_length"])
    self.assertEqual(2026071601, config["primary_seed"])
    self.assertEqual(24, config["maximum_gpu_hours"])
```

- [ ] **Step 2: Run tests and confirm failure.**

```powershell
& $ProjectPython -m unittest 09-experiments.tests.test_llm_v03_inheritance -v
```

Expected: import/file failure because v0.3 files do not exist.

- [ ] **Step 3: Implement canonical hash locking.**

```python
def build_inheritance_lock(v02_root: Path, expected: dict[str, str]) -> dict[str, Any]:
    files = {}
    for relative, expected_hash in sorted(expected.items()):
        actual = hashlib.sha256((v02_root / relative).read_bytes()).hexdigest()
        if actual != expected_hash:
            raise ValueError(f"v0.2 inheritance drift: {relative}")
        files[relative] = actual
    return {
        "schema_version": "project05-v02-inheritance-lock-v0.3",
        "code_commit": "dc9dbc0942fe912df2d57b9c24b2601a9f5ea60a",
        "test_packet_count": 64,
        "test_case_count": 6,
        "files": files,
        "mutable": False,
    }
```

The v0.3 config must name conditions exactly: `rule_compiler`, `general_compiler`, `adapted_compiler`, `general_structured`, `general_direct`. Its repeat panel contains the four model modes except Rule, and seeds remain `2026071503/04` for G2/repeat plus `2026071601` for training. `training_config.json` is frozen here so source packet construction and later training cannot use different seeds or QLoRA values.

- [ ] **Step 4: Generate the inheritance lock and rerun old + new tests.**

```powershell
& $ProjectPython 09-experiments/scripts/freeze_llm_v03_inheritance.py `
  --v02-root 09-experiments/llm_compiler_v0.2/generated `
  --output 09-experiments/llm_compiler_v0.3/generated/frozen/v02-inheritance-lock.json
& $ProjectPython -m unittest 09-experiments.tests.test_llm_v03_inheritance -v
& $ProjectPython -m unittest 09-experiments.tests.test_llm_phase1_validation -q
```

Expected: new tests pass; existing v0.2 tests remain `OK`; no v0.2 file hash changes.

- [ ] **Step 5: Commit only tracked config/code/tests.**

```powershell
git add 09-experiments/llm_compiler_v0.3/README.md 09-experiments/llm_compiler_v0.3/experiment_config.json 09-experiments/llm_finetuning_v0.3/training_config.json 09-experiments/governance/contracts/llm-compiler-contract-v0.3.json 09-experiments/scripts/freeze_llm_v03_inheritance.py 09-experiments/tests/test_llm_v03_inheritance.py
git diff --cached --name-only
git commit -m "experiment: declare qwen25 phase1 inheritance"
```

---

### Task 2: Make the runner config-aware and reuse General stage 1

**Files:**

- Modify: `09-experiments/scripts/run_llm_phase1.py`
- Modify: `09-experiments/tests/test_llm_phase1_validation.py`
- Create: `09-experiments/tests/test_llm_phase1_adapter.py`

**Interfaces:**

- `ExperimentPaths.from_config(config_path: Path) -> ExperimentPaths`
- `freeze_prompt_config_lock(output_path: Path, paths: ExperimentPaths) -> dict[str, Any]`
- `run_structured_from_compiler(packet, compiler_result, compiler_manifest, backend, attempt_index, paths) -> tuple[dict, dict]`
- `structured_manifest(compiler_manifest, admission, stage2_input, messages, raw_text, result, telemetry) -> dict[str, Any]`
- `build_formal_plan(config, packets, repeat_packets) -> list[dict[str, Any]]`

- [ ] **Step 1: Write failing path and call-reuse tests.**

```python
def test_structured_reuses_general_compiler_output_without_second_stage1_call(self):
    backend = CountingStubBackend()
    compiler_result, compiler_manifest = runner.run_compiler(
        packet(), "general_compiler", backend, 0, V03_PATHS
    )
    result, manifest = runner.run_structured_from_compiler(
        packet(), compiler_result, compiler_manifest, backend, 0, V03_PATHS
    )
    self.assertEqual(2, backend.call_count)  # one compiler + one conclusion total
    self.assertEqual(
        compiler_manifest["stage_hash_chain"]["stage1_raw_sha256"],
        manifest["stage_hash_chain"]["stage1_raw_sha256"],
    )

def test_formal_plan_has_256_first_pass_and_448_with_repeats(self):
    plan = runner.build_formal_plan(V03_CONFIG, packets(64), packets(12))
    self.assertEqual(448, len(plan))
    self.assertEqual(256, sum(row["attempt_index"] == 0 for row in plan))

def test_v03_prompt_lock_reuses_prompt_bytes_but_hashes_v03_config_contract(self):
    lock = runner.freeze_prompt_config_lock(TEMP_LOCK, V03_PATHS)
    self.assertEqual(V02_PROMPT_HASHES, lock["prompt_sha256"])
    self.assertEqual(sha256_file(V03_CONFIG), lock["config_sha256"])
    self.assertEqual(sha256_file(V03_CONTRACT), lock["contract_sha256"])
```

- [ ] **Step 2: Confirm failures before implementation.**

Run the two named tests with `-v`. Expected: missing `ExperimentPaths` and `run_structured_from_compiler`.

- [ ] **Step 3: Add explicit path resolution and stage-1 reuse.**

```python
@dataclass(frozen=True)
class ExperimentPaths:
    config_path: Path
    prompt_dir: Path
    contract_path: Path
    schema_dir: Path
    generated_root: Path

    @classmethod
    def from_config(cls, config_path: Path) -> "ExperimentPaths":
        config_path = config_path.resolve()
        config = load_json(config_path)
        root = config_path.parent
        return cls(
            config_path=config_path,
            prompt_dir=(EXPERIMENT_ROOT / config["paths"]["prompt_dir"]).resolve(),
            contract_path=(EXPERIMENT_ROOT / config["paths"]["contract"]).resolve(),
            schema_dir=SCHEMA_DIR.resolve(),
            generated_root=(root / "generated").resolve(),
        )

def run_structured_from_compiler(packet, compiler_result, compiler_manifest,
                                 backend, attempt_index, paths):
    admission = _VALIDATOR.admit_candidates(compiler_result, packet)
    stage2_input = _VALIDATOR.build_structured_stage2_input(
        admission, packet["support_ceiling"]
    )
    messages = conclusion_messages(
        "structured", stage2_input, attempt_index, paths.prompt_dir
    )
    raw_text, telemetry = backend.generate(
        messages, generation_for("general_structured", paths.config_path)
    )
    result = conclusion_result_from_raw(
        packet, "general_structured", attempt_index, raw_text
    )
    return result, structured_manifest(
        compiler_manifest, admission, stage2_input, messages, raw_text,
        result, telemetry
    )
```

`build_formal_plan` must emit exactly four calls per packet/attempt: General compiler、Adapted compiler、General structured conclusion、General direct。Structured row references the matching General compiler `call_id`; scheduler refuses to run it until that result/hash exists.

- [ ] **Step 4: Preserve v0.2 behavior and validate 448 arithmetic.**

```powershell
& $ProjectPython 09-experiments/scripts/run_llm_phase1.py --config 09-experiments/llm_compiler_v0.3/experiment_config.json --freeze-prompt-config-lock 09-experiments/llm_compiler_v0.3/generated/frozen/prompt-config-lock.json
& $ProjectPython -m unittest 09-experiments.tests.test_llm_phase1_validation 09-experiments.tests.test_llm_phase1_adapter -v
& $ProjectPython -m unittest 09-experiments.tests.test_llm_compiler_pilot -q
```

Expected: all pass; the old dependency-free runner still imports without torch/Transformers.

- [ ] **Step 5: Commit.**

```powershell
git add 09-experiments/scripts/run_llm_phase1.py 09-experiments/tests/test_llm_phase1_validation.py 09-experiments/tests/test_llm_phase1_adapter.py
git diff --cached --name-only
git commit -m "experiment: reuse structured compiler stage"
```

---

### Task 3: Define source governance and fail-closed catalog validation

**Files:**

- Create: `09-experiments/llm_finetuning_v0.3/README.md`
- Create: `09-experiments/llm_finetuning_v0.3/source_catalog.json`
- Create: `09-experiments/data_schema/llm_training_source_catalog.schema.json`
- Create: `09-experiments/data_schema/llm_training_record.schema.json`
- Create: `09-experiments/scripts/audit_llm_training_sources.py`
- Create: `09-experiments/tests/test_llm_finetuning_leakage.py`

**Interfaces:**

- `validate_source_catalog(catalog: dict[str, Any]) -> dict[str, Any]`
- `approved_families(catalog, split: str) -> set[str]`
- `emit_source_review(candidates, output_csv: Path) -> None`

- [ ] **Step 1: Write failing license/family tests.**

```python
def test_catalog_requires_six_approved_disjoint_families(self):
    report = audit.validate_source_catalog(catalog_fixture())
    self.assertEqual(4, report["train_family_count"])
    self.assertEqual(2, report["validation_family_count"])
    self.assertTrue(report["split_disjoint"])
    self.assertEqual("passed", report["status"])

def test_known_development_and_test_families_are_rejected(self):
    for blocked in (
        "darpa_tc_e3", "darpa_tc_e5", "darpa_optc",
        "otrf_apt29", "witfoo_precinct6",
    ):
        catalog = catalog_fixture(replace_first_family=blocked)
        with self.assertRaisesRegex(ValueError, "blocked source family"):
            audit.validate_source_catalog(catalog)

def test_unresolved_license_or_download_authority_fails_closed(self):
    catalog = catalog_fixture(license_status="unresolved")
    with self.assertRaisesRegex(ValueError, "source is not approved"):
        audit.validate_source_catalog(catalog)
```

- [ ] **Step 2: Run and confirm failure.**

Expected: missing schema/module.

- [ ] **Step 3: Implement exact catalog rules.**

Each production source entry contains: `source_family_id`、`display_name`、`split_role`、`publisher`、`source_url`、`license_id`、`license_url`、`license_sha256`、`license_status="approved"`、`user_reviewed_at`、`download_authorized`、`declared_bytes`、`input_format="normalized-jsonl-v1"`。`source_catalog.json` begins as `{"status":"pending_user_source_review","sources":[]}` and therefore intentionally fails the six-family Gate until Task 5 user review.

```python
BLOCKED_FAMILIES = frozenset({
    "darpa_tc_e3", "darpa_tc_e5", "darpa_optc",
    "otrf_apt29", "witfoo_precinct6",
})

def validate_source_catalog(catalog):
    sources = catalog.get("sources", [])
    if any(row["source_family_id"] in BLOCKED_FAMILIES for row in sources):
        raise ValueError("blocked source family")
    if any(row.get("license_status") != "approved" or
           row.get("download_authorized") is not True for row in sources):
        raise ValueError("source is not approved")
    train = {row["source_family_id"] for row in sources
             if row["split_role"] == "train"}
    valid = {row["source_family_id"] for row in sources
             if row["split_role"] == "training-validation"}
    if train & valid or len(train) < 4 or len(valid) < 2:
        raise ValueError("source-family split gate failed")
    return {"status": "passed", "train_family_count": len(train),
            "validation_family_count": len(valid), "split_disjoint": True}
```

- [ ] **Step 4: Test schema and failure report generation.**

```powershell
& $ProjectPython -m unittest 09-experiments.tests.test_llm_finetuning_leakage -v
& $ProjectPython 09-experiments/scripts/audit_llm_training_sources.py `
  --catalog 09-experiments/llm_finetuning_v0.3/source_catalog.json `
  --emit-review 09-experiments/llm_finetuning_v0.3/generated/source-candidate-review.csv
```

Expected: unit tests pass; production command exits nonzero with `source-family split gate failed` and creates a review CSV, without downloading data.

- [ ] **Step 5: Commit schema, fail-closed catalog and validator.**

```powershell
git add 09-experiments/llm_finetuning_v0.3/README.md 09-experiments/llm_finetuning_v0.3/source_catalog.json 09-experiments/data_schema/llm_training_source_catalog.schema.json 09-experiments/data_schema/llm_training_record.schema.json 09-experiments/scripts/audit_llm_training_sources.py 09-experiments/tests/test_llm_finetuning_leakage.py
git diff --cached --name-only
git commit -m "experiment: gate qlora training sources"
```

---

### Task 4: Build a test-exclusion lock and exact/near-duplicate audit

**Files:**

- Modify: `09-experiments/scripts/audit_llm_training_sources.py`
- Modify: `09-experiments/tests/test_llm_finetuning_leakage.py`
- Generate: `09-experiments/llm_finetuning_v0.3/generated/frozen/test-exclusion-lock.json`

**Interfaces:**

- `build_test_exclusion_lock(v02_public: Path, v02_private: Path) -> dict[str, Any]`
- `normalized_text_hash(value: Any) -> str`
- `character_ngrams(value: str, n: int = 5) -> set[str]`
- `audit_training_records(records, exclusion_lock, threshold=0.85) -> dict[str, Any]`

- [ ] **Step 1: Write failing mutation and near-duplicate tests.**

```python
def test_exclusion_lock_contains_hashes_not_test_payload(self):
    lock = audit.build_test_exclusion_lock(TEST_PUBLIC, TEST_PRIVATE)
    encoded = json.dumps(lock, ensure_ascii=False)
    self.assertNotIn("records", lock)
    self.assertNotIn("candidate_claims", encoded)
    self.assertRegex(lock["lock_sha256"], r"^[A-F0-9]{64}$")

def test_exact_and_near_duplicate_training_record_is_blocked(self):
    lock = exclusion_fixture("powershell.exe -enc AAAA")
    records = [{"payload": "  PowerShell.exe   -ENC aaaa  "}]
    report = audit.audit_training_records(records, lock, threshold=0.85)
    self.assertEqual("failed", report["status"])
    self.assertIn("normalized_exact_match", report["blockers"])
```

- [ ] **Step 2: Confirm failure, then implement deterministic normalization.**

```python
def normalized_text(value):
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    return " ".join(text.split())

def jaccard(a, b):
    union = a | b
    return 1.0 if not union else len(a & b) / len(union)
```

The exclusion lock records only SHA-256、normalized text hashes、5-gram signatures、blocked family IDs and source v0.2 manifest hashes。Raw C07–C12 payload and private gold never enter the training packet directory or trainer process.

- [ ] **Step 3: Generate the lock twice and assert byte identity.**

```powershell
& $ProjectPython 09-experiments/scripts/audit_llm_training_sources.py --build-test-exclusion-lock --v02-root 09-experiments/llm_compiler_v0.2/generated --output 09-experiments/llm_finetuning_v0.3/generated/frozen/test-exclusion-lock.json
Copy-Item 09-experiments/llm_finetuning_v0.3/generated/frozen/test-exclusion-lock.json $env:TEMP\test-exclusion-lock.first.json
& $ProjectPython 09-experiments/scripts/audit_llm_training_sources.py --build-test-exclusion-lock --v02-root 09-experiments/llm_compiler_v0.2/generated --output 09-experiments/llm_finetuning_v0.3/generated/frozen/test-exclusion-lock.json
Compare-Object (Get-Content $env:TEMP\test-exclusion-lock.first.json) (Get-Content 09-experiments/llm_finetuning_v0.3/generated/frozen/test-exclusion-lock.json)
```

Expected: no `Compare-Object` output.

- [ ] **Step 4: Commit code/tests only.**

```powershell
git add 09-experiments/scripts/audit_llm_training_sources.py 09-experiments/tests/test_llm_finetuning_leakage.py
git diff --cached --name-only
git commit -m "experiment: block qlora test leakage"
```

---

### Task 5: Produce an evidence-backed source review and stop for user approval

**Files:**

- Generate: `09-experiments/llm_finetuning_v0.3/generated/source-candidate-review.csv`
- Generate: `04-progress/llm-apt-v03-source-gate-20260716.md`
- Modify only after approval: `09-experiments/llm_finetuning_v0.3/source_catalog.json`

**Interfaces:**

- CSV columns exactly mirror the source catalog fields plus `decision` and `review_note`.
- The Markdown report lists candidate URL、publisher、license evidence/hash、declared download bytes、format、APT relevance、family independence and exclusion scan status.

- [ ] **Step 1: Research source metadata only; do not download corpus payload.**

For every candidate, fetch only landing page/license/manifest metadata. Reject sources that have no explicit reuse terms, require full raw PCAP, belong to the five blocked families, or are mirrors/derivatives of another candidate.

- [ ] **Step 2: Run the catalog validator against the proposed six-or-more rows.**

```powershell
& $ProjectPython 09-experiments/scripts/audit_llm_training_sources.py --review-csv 09-experiments/llm_finetuning_v0.3/generated/source-candidate-review.csv --output-report 04-progress/llm-apt-v03-source-gate-20260716.md
```

Expected before user action: report status `pending_user_source_review`; no download command is emitted.

- [ ] **Step 3: Present the complete source review to the user.**

The user must explicitly approve/reject each source, its license, download size and split role. A family can enter `source_catalog.json` only when both `license_status="approved"` and `download_authorized=true` are present.

- [ ] **Step 4: After approval, import only accepted rows and revalidate.**

```powershell
& $ProjectPython 09-experiments/scripts/audit_llm_training_sources.py --import-approved-review 09-experiments/llm_finetuning_v0.3/generated/source-candidate-review.csv --catalog 09-experiments/llm_finetuning_v0.3/source_catalog.json
& $ProjectPython 09-experiments/scripts/audit_llm_training_sources.py --catalog 09-experiments/llm_finetuning_v0.3/source_catalog.json
```

Expected: `status=passed`, train families `>=4`, training-validation families `>=2`, disjoint `true`.

- [ ] **Step 5: Commit the approved catalog and evidence record only after user review.**

```powershell
git add 09-experiments/llm_finetuning_v0.3/source_catalog.json 04-progress/llm-apt-v03-source-gate-20260716.md
git diff --cached --name-only
git commit -m "docs: approve qlora source catalog"
```

**HARD STOP V3-B:** If the user has not approved at least six independent families, stop here. Do not download training corpora, install the Qwen runtime or download model weights.

---

### Task 6: Normalize approved records and complete author-only label review

**Files:**

- Create: `09-experiments/scripts/build_llm_finetuning_data.py`
- Create: `09-experiments/tests/test_llm_finetuning_data.py`
- Generate: `09-experiments/llm_finetuning_v0.3/public_sources/<family>/records.jsonl.gz`
- Generate: `09-experiments/llm_finetuning_v0.3/generated/author-review.csv`

**Interfaces:**

- `normalize_source_row(row, source_entry) -> dict[str, Any]`
- `build_author_review(records) -> list[dict[str, str]]`
- `import_author_review(records, review_rows) -> list[dict[str, Any]]`

- [ ] **Step 1: Write failing schema/provenance tests.**

```python
def test_normalized_record_binds_source_license_and_hash(self):
    record = builder.normalize_source_row(raw_row(), approved_source())
    self.assertEqual("normalized-jsonl-v1", record["schema_version"])
    self.assertEqual(approved_source()["source_family_id"], record["source_family_id"])
    self.assertRegex(record["provenance"]["source_file_sha256"], r"^[A-F0-9]{64}$")
    self.assertNotIn("actor", json.dumps(record).casefold())

def test_only_author_accepted_observation_or_null_enters_builder(self):
    with self.assertRaisesRegex(ValueError, "review is not accepted"):
        builder.import_author_review([record()], [review(decision="pending")])
```

- [ ] **Step 2: Implement strict normalized input.**

Each row must contain `source_family_id`、`document_id`、`artifact_id`、`record_id`、`source_type`、`payload`、`provenance` and either one or more `observation_candidates` or `null_eligible_candidate=true`。Arbitrary HTML/PDF/PCAP input is rejected; a newly approved format requires a separate adapter task and test before use.

- [ ] **Step 3: Download only approved declared files and verify size/license/hash.**

Use the source-specific URLs already frozen in `source_catalog.json`; write raw material only beneath `llm_finetuning_v0.3/public_sources/<family>/`. Abort if actual bytes exceed the catalog declaration without new user approval. No C07–C12 path may be an input.

- [ ] **Step 4: Generate the author review CSV.**

Required columns: `review_item_id,source_family_id,document_id,record_id,source_excerpt,subject_type,subject_value,predicate,object_type,object_value,artifact_id,pointer_record_id,proposed_role,decision,reviewer,reviewed_at,review_note`。Allowed `decision`: `accept_observation`、`accept_null`、`reject`。One author is sufficient; blank reviewer/time or any other decision is invalid.

Review may be frozen in batches of at most 50 rows, each with an independent batch hash. The expected workload is at least 500 final packets plus rejected drafts; elapsed review time and row counts are recorded per batch. Workload never permits lowering the 400/100 Gate. An optional second reviewer may inspect a deterministic 10% sample selected with seed `2026071605`, stratified by source family and positive/null role; report raw agreement and field corrections as diagnostics only, never as G2.

- [ ] **Step 5: Import reviewed labels and run leakage audit.**

```powershell
& $ProjectPython 09-experiments/scripts/build_llm_finetuning_data.py --import-author-review 09-experiments/llm_finetuning_v0.3/generated/author-review.csv --catalog 09-experiments/llm_finetuning_v0.3/source_catalog.json --output-root 09-experiments/llm_finetuning_v0.3/generated/reviewed-records
& $ProjectPython 09-experiments/scripts/audit_llm_training_sources.py --records-root 09-experiments/llm_finetuning_v0.3/generated/reviewed-records --exclusion-lock 09-experiments/llm_finetuning_v0.3/generated/frozen/test-exclusion-lock.json
```

Expected: zero blocked family/exact/near-duplicate/test identifier matches.

- [ ] **Step 6: Commit code/tests; keep raw/reviewed data private unless license review permits tracking.**

```powershell
git add 09-experiments/scripts/build_llm_finetuning_data.py 09-experiments/tests/test_llm_finetuning_data.py
git diff --cached --name-only
git commit -m "experiment: build reviewed qlora records"
```

---

### Task 7: Build and freeze train/training-validation packets

**Files:**

- Create: `09-experiments/data_schema/llm_finetuning_packet.schema.json`
- Create: `09-experiments/scripts/validate_llm_finetuning_data.py`
- Modify: `09-experiments/scripts/build_llm_finetuning_data.py`
- Modify: `09-experiments/tests/test_llm_finetuning_data.py`
- Generate: `09-experiments/llm_finetuning_v0.3/generated/{train,training-validation}/packets.jsonl.gz`
- Generate: `09-experiments/llm_finetuning_v0.3/generated/frozen/data-gate.json`
- Generate: `04-progress/llm-apt-v03-data-gate-20260716.md`

**Interfaces:**

- `build_training_packets(records, catalog, seed=2026071601) -> dict[str, list[dict]]`
- `serialize_qwen_chat(packet, target) -> str`
- `count_packet_tokens(packet, target, tokenizer) -> int`
- `nearest_rank_percentile(values, probability=0.95) -> int`
- `validate_data_gate(train, validation, catalog, exclusion_report, tokenizer_lock) -> dict[str, Any]`
- `freeze_training_manifests(output_root: Path) -> dict[str, Any]`

- [ ] **Step 1: Write failing split/count/ratio tests.**

```python
def test_split_is_by_source_family_not_packet(self):
    built = builder.build_training_packets(reviewed_records(), catalog_fixture())
    train_families = {row["source_family_id"] for row in built["train"]}
    valid_families = {row["source_family_id"] for row in built["training-validation"]}
    self.assertFalse(train_families & valid_families)

def test_data_gate_requires_counts_balance_and_distractors(self):
    report = validator.validate_data_gate(
        train_packets(400), validation_packets(100), catalog_fixture(), clean_audit()
    )
    self.assertEqual("passed", report["status"])
    self.assertGreaterEqual(report["positive_with_distractor_rate"], 0.50)
    self.assertGreaterEqual(report["train_family_count"], 4)
    self.assertGreaterEqual(report["validation_family_count"], 2)

def test_token_gate_records_distribution_and_never_truncates(self):
    report = validator.validate_data_gate(
        train_packets(400), validation_packets(100), catalog_fixture(),
        clean_audit(), tokenizer_lock_fixture()
    )
    self.assertLessEqual(report["token_distribution"]["train"]["p95"], 1024)
    self.assertLessEqual(report["token_distribution"]["training_validation"]["p95"], 1024)
    self.assertLessEqual(report["token_distribution"]["train"]["final_max"], 1024)
    self.assertFalse(report["tokenizer"]["truncation_enabled"])

def test_overlength_packets_are_removed_before_all_gates_are_recomputed(self):
    report = validator.validate_data_gate(
        train_packets(400, one_packet_tokens=1025), validation_packets(100),
        catalog_fixture(), clean_audit(), tokenizer_lock_fixture()
    )
    self.assertEqual("smoke_only", report["status"])
    self.assertEqual(1, report["token_distribution"]["train"]["excluded_overlength"])
    self.assertEqual(399, report["post_token_filter_counts"]["train"])
```

- [ ] **Step 2: Implement deterministic packet construction.**

Positive packet: one author-accepted target observation plus at least one same-source distractor when available; output is the accepted compiler JSON。Null packet: only author-accepted null records and output exactly `{"status":"abstain","candidate_claims":[]}`。`candidate_claim_id` is omitted from target and remains runner-generated at inference.

Before final manifests, download only `tokenizer.json`、`tokenizer_config.json`、`merges.txt` and `vocab.json` from the fixed Qwen commit after V3-B approval; verify and store their SHA-256 in `tokenizer-lock.json`. Use the already-audited tokenizer-only library to encode the exact frozen Qwen chat serialization without truncation; this does not authorize any safetensors/model weight download. Define p95 as `sorted_values[ceil(0.95*n)-1]`. Record pre-exclusion and post-exclusion distributions separately.

- [ ] **Step 3: Freeze ordering and manifests.**

Sort source families/document IDs before a seeded within-family shuffle。Remove every packet whose full prompt+target count exceeds 1024, then recompute packet counts、source-family counts、positive/null ratios and distractor coverage; never call a tokenizer with `truncation=True`。Manifest records source catalog hash、review CSV hash、tokenizer lock/hash、chat serialization hash、builder hash、schema hash、packet file hash、token distributions、role counts、family counts and seed。Running the same command twice must produce byte-identical gzip (`mtime=0`).

- [ ] **Step 4: Build, validate and emit the Gate record.**

```powershell
& $ProjectPython 09-experiments/scripts/build_llm_finetuning_data.py --reviewed-root 09-experiments/llm_finetuning_v0.3/generated/reviewed-records --catalog 09-experiments/llm_finetuning_v0.3/source_catalog.json --output-root 09-experiments/llm_finetuning_v0.3/generated
& $ProjectPython 09-experiments/scripts/validate_llm_finetuning_data.py --root 09-experiments/llm_finetuning_v0.3/generated --output 09-experiments/llm_finetuning_v0.3/generated/frozen/data-gate.json
```

Expected: all minimum counts/ratios/families pass, exclusion matches equal zero, token p95 `<=1024`, and post-filter max `<=1024`. Otherwise the report status is `smoke_only` and adapter cannot enter Paper B core conditions.

- [ ] **Step 5: Run tests and commit code/schema/report.**

```powershell
& $ProjectPython -m unittest 09-experiments.tests.test_llm_finetuning_data 09-experiments.tests.test_llm_finetuning_leakage -v
git add 09-experiments/data_schema/llm_finetuning_packet.schema.json 09-experiments/scripts/build_llm_finetuning_data.py 09-experiments/scripts/validate_llm_finetuning_data.py 09-experiments/tests/test_llm_finetuning_data.py 04-progress/llm-apt-v03-data-gate-20260716.md
git diff --cached --name-only
git commit -m "experiment: freeze qlora training packets"
```

**HARD STOP V3-C:** Show `data-gate.json`, source/license report, complete diff and disk declaration to the user. Until explicit authorization, do not install the new runtime or download Qwen weights.

---

### Task 8: Freeze offline Qwen metadata, runtime pins and authorization blockers

**Files:**

- Create: `09-experiments/data_schema/llm_model_runtime_lock_v0.3.schema.json`
- Create: `09-experiments/scripts/lock_qwen_runtime.py`
- Create: `09-experiments/tests/test_qwen_runtime_lock.py`
- Generate: `09-experiments/llm_compiler_v0.3/generated/frozen/qwen25-runtime-lock.json`

**Interfaces:**

- `build_offline_runtime_lock(config, authorization) -> dict[str, Any]`
- `verify_snapshot(lock, snapshot_dir: Path) -> dict[str, Any]`
- `measure_disk_gate(paths: list[Path], limit=30_000_000_000) -> dict[str, Any]`

- [ ] **Step 1: Write failing immutable metadata tests.**

```python
def test_offline_lock_pins_qwen25_files_and_stays_blocked(self):
    lock = runtime.build_offline_runtime_lock(CONFIG, authorization={})
    self.assertEqual("a09a35458c702b33eeacc393d103063234e8bc28", lock["model"]["resolved_commit"])
    self.assertEqual(15_242_807_270, lock["model"]["repository_bytes"])
    self.assertEqual(15_231_271_888, lock["model"]["weight_bytes"])
    self.assertEqual(4, len(lock["model"]["weight_files"]))
    self.assertFalse(lock["ready_for_weight_download"])
    self.assertIn("model_download_not_authorized", lock["blockers"])

def test_runtime_package_substitution_is_rejected(self):
    with self.assertRaisesRegex(ValueError, "runtime package mismatch"):
        runtime.verify_package_versions({**EXPECTED_PACKAGES, "peft": "0.14.0"})
```

- [ ] **Step 2: Implement exact metadata.**

Embed the four LFS hashes and sizes from v0.3 design, plus README/LICENSE/config/tokenizer hashes。The training config contains all QLoRA values verbatim and forbids `merge_and_unload`、Hub upload、test path access and more than three epoch checkpoints.

- [ ] **Step 3: Generate blocked lock before any runtime mutation.**

```powershell
& $ProjectPython 09-experiments/scripts/lock_qwen_runtime.py --config 09-experiments/llm_finetuning_v0.3/training_config.json --output 09-experiments/llm_compiler_v0.3/generated/frozen/qwen25-runtime-lock.json
```

Expected: status `blocked_before_runtime_install`, with blockers for install/download/smoke/training authorization.

- [ ] **Step 4: Run tests and commit.**

```powershell
& $ProjectPython -m unittest 09-experiments.tests.test_qwen_runtime_lock -v
git add 09-experiments/data_schema/llm_model_runtime_lock_v0.3.schema.json 09-experiments/scripts/lock_qwen_runtime.py 09-experiments/tests/test_qwen_runtime_lock.py
git diff --cached --name-only
git commit -m "experiment: lock qwen25 runtime metadata"
```

---

### Task 9: Implement lazy Qwen/PEFT backend and QLoRA trainer with fake modules

**Files:**

- Create: `09-experiments/scripts/llm_qwen_backend.py`
- Create: `09-experiments/scripts/train_qwen_qlora.py`
- Create: `09-experiments/data_schema/llm_adapter_manifest.schema.json`
- Create: `09-experiments/tests/test_qwen_qlora.py`
- Modify: `09-experiments/tests/test_llm_phase1_adapter.py`

**Interfaces:**

- `QwenLocalSession(base_path, base_commit, adapter_path, adapter_sha256)` — 只加载一次底座和 adapter；adapter key 固定为 `project05_obs_compiler`。
- `QwenLocalSession.view(adapter_enabled: bool) -> QwenBackendView`
- `QwenBackendView.generate(messages, generation_config) -> tuple[str, dict]` — 保持现有 `InferenceBackend` 两参数接口。
- `build_bnb_config(torch, BitsAndBytesConfig)`
- `build_lora_config(LoraConfig)`
- `assistant_only_labels(tokenizer, messages, max_length=1024) -> dict[str, Tensor]`
- `select_checkpoint(metrics: list[dict]) -> dict`
- `write_adapter_manifest(...) -> dict`

- [ ] **Step 1: Write fake-module tests before importing torch.**

```python
def test_backend_is_lazy_local_only_and_switches_one_adapter(self):
    with fake_hf_modules() as calls:
        session = qwen.QwenLocalSession(BASE_DIR, COMMIT, ADAPTER_DIR, ADAPTER_SHA)
        general = session.view(adapter_enabled=False)
        adapted = session.view(adapter_enabled=True)
        general.generate(messages(), generation())
        adapted.generate(messages(), generation())
    self.assertTrue(calls["model"]["local_files_only"])
    self.assertFalse(calls["model"]["trust_remote_code"])
    self.assertEqual(1, calls["base_load_count"])
    self.assertEqual([False, True], calls["adapter_states"])
    self.assertNotEqual(general.backend_id, adapted.backend_id)

def test_training_masks_all_non_assistant_tokens(self):
    batch = trainer.assistant_only_labels(fake_tokenizer(), messages(), 1024)
    prompt_len = batch["assistant_start"]
    self.assertTrue(all(value == -100 for value in batch["labels"][:prompt_len]))
    self.assertTrue(any(value != -100 for value in batch["labels"][prompt_len:]))

def test_checkpoint_tie_break_is_pre_registered(self):
    selected = trainer.select_checkpoint(metric_rows())
    self.assertEqual("checkpoint-100", selected["checkpoint"])
```

- [ ] **Step 2: Implement lazy imports and quantization.**

```python
def build_bnb_config(torch, BitsAndBytesConfig):
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )

def build_lora_config(LoraConfig):
    return LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    )
```

All torch/transformers/peft imports remain inside runtime functions. Importing either script with the project Python must not load those packages. Backend ID includes base commit、quantization config hash and adapter hash/state。

`QwenBackendView.generate()` acquires the session lock, then uses `model.disable_adapter()` for General or `model.set_adapter("project05_obs_compiler")` for Adapted before generation. It restores the previous state in `finally`; General and Adapted views may not run concurrently on the shared model. Reports call it an “observation-compiler adapter” or “task-adapted adapter”, never a generally capable “APT domain model”.

- [ ] **Step 3: Enforce training root and adapter-only output.**

`train_qwen_qlora.py` resolves every data path beneath `llm_finetuning_v0.3/generated/{train,training-validation}` before importing torch。It rejects any path containing `llm_compiler_v0.2/generated/test`、`development`、`g2-audit` or `real_cases`。After save, it fails if output contains full-model shard names or files above 1 GB.

- [ ] **Step 4: Run fake-module and all pre-model tests.**

```powershell
& $ProjectPython -m unittest 09-experiments.tests.test_qwen_qlora 09-experiments.tests.test_llm_phase1_adapter -v
& $ProjectPython -m unittest 09-experiments.tests.test_llm_packet_separation 09-experiments.tests.test_llm_phase1_contract 09-experiments.tests.test_llm_phase1_validation 09-experiments.tests.test_llm_phase1_scoring 09-experiments.tests.test_llm_compiler_pilot -q
```

Expected: all tests pass without installing/loading model packages in the project interpreter.

- [ ] **Step 5: Commit.**

```powershell
git add 09-experiments/scripts/llm_qwen_backend.py 09-experiments/scripts/train_qwen_qlora.py 09-experiments/data_schema/llm_adapter_manifest.schema.json 09-experiments/tests/test_qwen_qlora.py 09-experiments/tests/test_llm_phase1_adapter.py
git diff --cached --name-only
git commit -m "experiment: add qwen25 qlora backend"
```

---

### Task 10: After authorization, install the isolated runtime and download the fixed snapshot

**Files:**

- Create outside Git: `.venv-llm-phase1-qwen25/`
- Create outside Git: `.cache-llm-phase1-qwen25/huggingface/`
- Update generated: `09-experiments/llm_compiler_v0.3/generated/frozen/qwen25-runtime-lock.json`
- Generate: `04-progress/llm-apt-v03-runtime-gate-20260716.md`

**Interfaces:**

- No API change; resolves Task 8 lock blockers only after explicit user authorization.

- [ ] **Step 1: Confirm authorization and free disk before mutation.**

Record user authorization timestamp in the runtime lock。Measure cache/checkpoint directories and require projected total `<30,000,000,000` bytes。Do not count another `local_dir` copy.

- [ ] **Step 2: Create the isolated environment and install exact pins.**

```powershell
py -3.11 -m venv .venv-llm-phase1-qwen25
& .\.venv-llm-phase1-qwen25\Scripts\python.exe -m pip install --upgrade pip
& .\.venv-llm-phase1-qwen25\Scripts\python.exe -m pip install --index-url https://download.pytorch.org/whl/cu121 torch==2.3.1+cu121
& .\.venv-llm-phase1-qwen25\Scripts\python.exe -m pip install transformers==4.45.2 accelerate==0.34.2 bitsandbytes==0.43.1 peft==0.13.2 datasets==3.0.1 huggingface-hub==0.25.2 safetensors==0.4.5 numpy==1.26.4 jsonschema==4.23.0
```

Expected: resolver reports exactly the pinned direct packages; no old `.venv-llm-phase1` mutation.

- [ ] **Step 3: Run CUDA/NF4/package smoke without model weights.**

```powershell
& .\.venv-llm-phase1-qwen25\Scripts\python.exe 09-experiments/scripts/lock_qwen_runtime.py --probe-runtime --config 09-experiments/llm_finetuning_v0.3/training_config.json --output 09-experiments/llm_compiler_v0.3/generated/frozen/qwen25-runtime-lock.json
```

Expected: CUDA device RTX 2080 Ti、compute capability 7.5、NF4 round-trip finite、NumPy bridge passed、package pins exact。

- [ ] **Step 4: Download only the fixed snapshot into HF cache.**

```powershell
$env:HF_HOME=(Resolve-Path '.cache-llm-phase1-qwen25').Path + '\huggingface'
& .\.venv-llm-phase1-qwen25\Scripts\python.exe 09-experiments/scripts/lock_qwen_runtime.py --download-fixed-snapshot --repo-id Qwen/Qwen2.5-7B-Instruct --revision a09a35458c702b33eeacc393d103063234e8bc28 --output 09-experiments/llm_compiler_v0.3/generated/frozen/qwen25-runtime-lock.json
```

The downloader must use cache snapshot only, reject symlink escape, and never call `snapshot_download` without the 40-hex revision.

- [ ] **Step 5: Verify all four local weight hashes and the disk Gate.**

```powershell
& .\.venv-llm-phase1-qwen25\Scripts\python.exe 09-experiments/scripts/lock_qwen_runtime.py --verify-local-snapshot --lock 09-experiments/llm_compiler_v0.3/generated/frozen/qwen25-runtime-lock.json --output-report 04-progress/llm-apt-v03-runtime-gate-20260716.md
```

Expected: repository bytes 15,242,807,270; all four SHA-256 values match; cache/checkpoint total below 30 GB; no model output exists.

---

### Task 11: Run the 20-packet QLoRA training smoke and stop again

**Files:**

- Generate: `09-experiments/llm_finetuning_v0.3/generated/runs/smoke/`
- Generate: `04-progress/llm-apt-v03-qlora-smoke-20260716.md`

**Interfaces:**

- `run_smoke(..., packet_limit=20) -> dict[str, Any]`
- Output records trainable params、loss、peak VRAM、wall time、adapter save/reload and opened-path audit.

- [ ] **Step 1: Select 20 packets without reading test/development.**

Use 10 positive + 10 null packets, blocked by source family and deterministic seed `2026071601`。The selection manifest contains only training packet IDs/hashes.

- [ ] **Step 2: Run one bounded forward/backward/save/reload cycle.**

```powershell
& .\.venv-llm-phase1-qwen25\Scripts\python.exe 09-experiments/scripts/train_qwen_qlora.py --mode smoke --base-lock 09-experiments/llm_compiler_v0.3/generated/frozen/qwen25-runtime-lock.json --training-config 09-experiments/llm_finetuning_v0.3/training_config.json --data-root 09-experiments/llm_finetuning_v0.3/generated --packet-limit 20 --output 09-experiments/llm_finetuning_v0.3/generated/runs/smoke
```

- [ ] **Step 3: Enforce smoke Gate.**

Pass only if trainable parameters `<1%`（expected near 40.4M）、loss finite、peak VRAM `<=10.5 GiB`、adapter saves/reloads、fixed validation generation completes、opened-path audit contains no v0.2/test/development/G2/Paper A path。

- [ ] **Step 4: Write the Markdown record and run adapter tests in the real environment.**

```powershell
& .\.venv-llm-phase1-qwen25\Scripts\python.exe -m unittest 09-experiments.tests.test_qwen_runtime_lock 09-experiments.tests.test_qwen_qlora 09-experiments.tests.test_llm_phase1_adapter -v
```

Expected: all pass. If OOM or any Gate fails, stop and revise the design; do not silently shorten sequence length or change rank.

**HARD STOP V3-D:** Present runtime lock, exact package list, snapshot hashes, smoke metrics and complete diff. Formal QLoRA training requires a new explicit user authorization.

---

### Task 12: Train the primary adapter and freeze its manifest

**Files:**

- Generate: `09-experiments/llm_finetuning_v0.3/generated/runs/primary/`
- Generate: `09-experiments/llm_finetuning_v0.3/generated/frozen/adapter-manifest.json`
- Generate: `04-progress/llm-apt-v03-primary-training-20260716.md`

**Interfaces:**

- `select_checkpoint(metrics)` uses only training-validation packet agreement, then invalid-pointer/unsupported-proxy, then earlier checkpoint.
- `write_adapter_manifest` binds base commit、adapter SHA、training config、train/validation manifests、runtime lock、seed、GPU and metrics.

- [ ] **Step 1: Revalidate all locks immediately before training.**

Run inheritance、source、exclusion、data、runtime and disk validators。Any drift blocks training.

- [ ] **Step 2: Run the primary seed only.**

```powershell
& .\.venv-llm-phase1-qwen25\Scripts\python.exe 09-experiments/scripts/train_qwen_qlora.py --mode train --base-lock 09-experiments/llm_compiler_v0.3/generated/frozen/qwen25-runtime-lock.json --training-config 09-experiments/llm_finetuning_v0.3/training_config.json --data-root 09-experiments/llm_finetuning_v0.3/generated --seed 2026071601 --output 09-experiments/llm_finetuning_v0.3/generated/runs/primary
```

Stop at 24 GPU hours。Save at most three adapter checkpoints; never save merged full weights。

- [ ] **Step 3: Select checkpoint without test access and freeze manifest.**

```powershell
& .\.venv-llm-phase1-qwen25\Scripts\python.exe 09-experiments/scripts/train_qwen_qlora.py --mode select --run-root 09-experiments/llm_finetuning_v0.3/generated/runs/primary --output-manifest 09-experiments/llm_finetuning_v0.3/generated/frozen/adapter-manifest.json
```

- [ ] **Step 4: Decide optional seeds solely from elapsed primary time.**

If and only if primary elapsed GPU time `<=6` hours, the user may authorize seeds `2026071602/03` as diagnostics。Both must use identical config/data and all results must be reported; test performance cannot select among them。

- [ ] **Step 5: Commit only sanitized provenance/report, not binary adapter/checkpoints.**

Explicitly inspect the manifest for local usernames/absolute cache paths before staging。Record relative artifact IDs and hashes instead。

---

### Task 13: Run a 28-call atomic pilot on training-validation packets

**Files:**

- Modify: `09-experiments/scripts/run_llm_phase1.py`
- Modify: `09-experiments/tests/test_llm_phase1_adapter.py`
- Generate: `09-experiments/llm_compiler_v0.3/generated/runs/atomic-pilot/`
- Generate: `04-progress/llm-apt-v03-atomic-pilot-20260716.md`

**Interfaces:**

- `select_atomic_pilot(training_validation_manifest, seed=2026071601, count=14) -> list[dict]`
- `estimate_formal_runtime(atomic_manifests, config) -> dict[str, Any]`

- [ ] **Step 1: Write the exact panel test.**

```python
def test_atomic_pilot_uses_validation_not_frozen_test(self):
    panel = runner.select_atomic_pilot(TRAINING_VALIDATION_MANIFEST, 2026071601, 14)
    self.assertEqual(14, len(panel))
    self.assertTrue(all(row["split"] == "training-validation" for row in panel))
    self.assertFalse(any(row["case_id"].startswith("C0") for row in panel))

def test_atomic_plan_is_14_base_plus_14_adapter_calls(self):
    plan = runner.build_atomic_plan(panel_fixture())
    self.assertEqual(28, len(plan))
    self.assertEqual({"general_compiler": 14, "adapted_compiler": 14}, counts(plan))
```

- [ ] **Step 2: Implement panel selection and immutable plan.**

Block by source family and packet role; the pilot cannot use v0.2 development/test or old C07/C09 historical pilot rows。Pilot output is a system smoke only and cannot change prompt/training/checkpoint.

- [ ] **Step 3: Run base and adapter with one loaded model.**

```powershell
& .\.venv-llm-phase1-qwen25\Scripts\python.exe 09-experiments/scripts/run_llm_phase1.py --config 09-experiments/llm_compiler_v0.3/experiment_config.json --atomic-pilot --runtime-lock 09-experiments/llm_compiler_v0.3/generated/frozen/qwen25-runtime-lock.json --adapter-manifest 09-experiments/llm_finetuning_v0.3/generated/frozen/adapter-manifest.json --output 09-experiments/llm_compiler_v0.3/generated/runs/atomic-pilot
```

- [ ] **Step 4: Validate completeness and estimate formal wall time.**

Require 28 completed first-pass rows、schema/error telemetry、base/adapted backend hash distinction、peak VRAM、p50/p95 latency and no test path access。Projection uses 448 calls, or 256 if repeat panel would exceed 24 GPU hours.

- [ ] **Step 5: Run tests and commit code/report.**

```powershell
& .\.venv-llm-phase1-qwen25\Scripts\python.exe -m unittest 09-experiments.tests.test_llm_phase1_adapter -v
git add 09-experiments/scripts/run_llm_phase1.py 09-experiments/tests/test_llm_phase1_adapter.py 04-progress/llm-apt-v03-atomic-pilot-20260716.md
git diff --cached --name-only
git commit -m "experiment: validate qwen adapter pilot"
```

**HARD STOP V3-E:** Show pilot outputs, projected time, VRAM and call decision. Formal 64-packet inference requires explicit user authorization.

---

### Task 14: Run the frozen 64-packet Phase 1 and contamination diagnostics

**Files:**

- Modify: `09-experiments/scripts/run_llm_phase1.py`
- Modify: `09-experiments/tests/test_llm_phase1_adapter.py`
- Generate: `09-experiments/llm_compiler_v0.3/generated/runs/formal/`
- Generate: `04-progress/llm-apt-v03-formal-run-20260716.md`

**Interfaces:**

- `execute_formal_plan(plan, backend, inherited_inputs, output_root) -> dict`
- `run_contamination_probes(base_backend, adapter_backend, frozen_probes) -> dict`

- [ ] **Step 1: Preflight immutable inputs.**

Verify v0.2 inheritance、Rule snapshot、v0.3 config/contract/prompt lock、runtime、adapter and test public manifests。Formal runner mounts only test `public/`; private gold remains unavailable.

- [ ] **Step 2: Run 256 first-pass model calls.**

For each 64 packets: General compiler、Adapted compiler、General structured conclusion reusing General compiler output、General direct。Write append-only call manifests and raw first-pass output; invalid JSON remains invalid and is never repaired into first-pass.

- [ ] **Step 3: Run the repeat panel only if predeclared time Gate passes.**

12 packets × 4 conditions × 4 extra attempts = 192 calls。Every structured repeat binds the same-attempt General compiler hash and its own conclusion hash。Technical repeats remain diagnostics.

- [ ] **Step 4: Run frozen contamination/refusal probes outside main scores.**

Probe names、UUID、timestamps、commands and local event strings fixed before the first test call。Report memorization-like exact/near-exact output、empty/refusal/abstain/invalid strata separately。Set contamination to `unknown` unless absence can be demonstrated, which is not expected here。

- [ ] **Step 5: Validate run completeness and forbid feedback.**

```powershell
& .\.venv-llm-phase1-qwen25\Scripts\python.exe 09-experiments/scripts/validate_llm_phase1_output.py --run-root 09-experiments/llm_compiler_v0.3/generated/runs/formal --config 09-experiments/llm_compiler_v0.3/experiment_config.json --public-input 09-experiments/llm_compiler_v0.2/generated/test/public
```

Expected: exact call count 448 or preregistered 256; no private/test-gold read; no prompt/config/adapter timestamp after first formal call.

---

### Task 15: Build independent G2 packages and analyze first-round agreement

**Files:**

- Create: `09-experiments/tests/test_llm_phase1_g2.py`
- Modify: `09-experiments/scripts/score_llm_phase1.py`
- Generate: `09-experiments/llm_compiler_v0.3/generated/g2-audit/<audit_id>/`

**Interfaces:**

- `select_g2_panel(test_manifest, seed=2026071503) -> list[dict]`
- `build_g2_bundles(panel, outputs, output_dir) -> dict[str, Any]`
- `analyze_g2(annotator_a_csv, annotator_b_csv, public_items) -> dict[str, Any]`

- [ ] **Step 1: Write panel and blinding tests.**

```python
def test_g2_has_two_positive_and_two_null_per_case(self):
    panel = scorer.select_g2_panel(TEST_MANIFEST, seed=2026071503)
    self.assertEqual(24, len(panel))
    for case_id in CASES:
        rows = [row for row in panel if row["case_id"] == case_id]
        self.assertEqual(2, sum(row["packet_role"] == "positive" for row in rows))
        self.assertEqual(2, sum(row["packet_role"] == "null" for row in rows))

def test_annotator_orders_are_independent_and_condition_blind(self):
    bundles = scorer.build_g2_bundles(panel_fixture(), output_fixture(), temp_dir())
    self.assertNotEqual(bundles["a_order_sha256"], bundles["b_order_sha256"])
    for text in bundle_texts(bundles):
        self.assertNotIn("Qwen", text)
        self.assertNotIn("Rule", text)
        self.assertNotIn("adapter", text.casefold())
```

- [ ] **Step 2: Build four conditions × 24 packets × independent A/B order.**

Conditions: Rule、General compiler + structured conclusion、Adapted compiler、General direct。Each annotator receives 96 rows with source excerpt and blinded output。Labels: `supported/partial/unsupported/unassessable`、pointer valid、conclusion over ceiling。No model name、G1 ID、score or other annotator label。

- [ ] **Step 3: Keep null construction audit separate.**

G2 manifest references the earlier null-audit hash only as provenance。Earlier null reviewers do not see model outputs in the construction protocol; G2 files do not overwrite either null audit CSV。

- [ ] **Step 4: Collect two independent first-round CSVs.**

This is the only remaining double-person scientific audit。It may be skipped, but skipping forces interface/author-gold-only paper form。A third person can adjudicate after first-round agreement is frozen; adjudication never replaces kappa。

- [ ] **Step 5: Analyze agreement before adjudication.**

Report weighted kappa for ordered support labels、nominal kappa for pointer/ceiling、raw agreement、unassessable rate and condition counts。Do not delete difficult rows。If kappa `<0.70` or unassessable `>0.20`, stop GPS/UCR computation.

- [ ] **Step 6: Run G2 tests and commit code/tests only.**

```powershell
& $ProjectPython -m unittest 09-experiments.tests.test_llm_phase1_g2 -v
git add 09-experiments/scripts/score_llm_phase1.py 09-experiments/tests/test_llm_phase1_g2.py
git diff --cached --name-only
git commit -m "experiment: add blind g2 audit"
```

---

### Task 16: Score Gates, write the Markdown result record and verify the repository

**Files:**

- Modify: `09-experiments/scripts/score_llm_phase1.py`
- Modify: `09-experiments/tests/test_llm_phase1_scoring.py`
- Generate: `04-progress/llm-apt-phase1-qwen25-results-20260716.md`

**Interfaces:**

- `score_gps_ucr(outputs, adjudicated_labels, panel) -> dict[str, Any]`
- `evaluate_adapter_gate(general, adapted) -> dict[str, Any]`
- `publication_decision(g2, rule_gate, structured_gate, adapter_gate) -> dict[str, Any]`

- [ ] **Step 1: Write failure-form and adapter-guard tests.**

```python
def test_g2_failure_never_emits_gps_or_ucr(self):
    result = scorer.publication_decision(
        g2={"kappa": 0.62, "unassessable_rate": 0.10},
        rule_gate={}, structured_gate={}, adapter_gate={}
    )
    self.assertEqual("negative_evaluation_or_interface_pilot", result["paper_form"])
    self.assertFalse(result["allow_grounding_claim"])
    self.assertNotIn("gps", result)
    self.assertNotIn("ucr", result)

def test_adapter_gain_requires_effect_case_guard_and_coverage(self):
    decision = scorer.evaluate_adapter_gate(general_fixture(), adapted_fixture())
    self.assertGreaterEqual(decision["macro_gps_delta"], 0.05)
    self.assertGreaterEqual(decision["non_worse_case_count"], 4)
    self.assertGreaterEqual(decision["coverage_delta"], -0.05)
    self.assertTrue(decision["passed"])
```

- [ ] **Step 2: Compute valid-G2 metrics at the case level.**

Packet score first, then per-case mean, then six-case macro。Report bootstrap/paired diagnostics only as exploratory; do not treat 64 packets as n=64 independent cases。For any invalid G2, rename outputs to machine/author proxies and omit GPS/UCR fields entirely。

- [ ] **Step 3: Enforce all claim Gates.**

Rule Gate、structured/direct Gate and adapter-vs-General Gate use the frozen 0.05、4-of-6 and coverage/error guards。A positive adapter result does not by itself unlock title language; title/core positive grounding still requires G2 + Rule + structured/direct Gates。

- [ ] **Step 4: Write the result Markdown before any paper prose.**

The record contains exact model/adapter/data/runtime hashes、n=6、packet/repeat counts、4-bit limitation、contamination `unknown` unless proven otherwise、refusal strata、G2 first-round/adjudication、every Gate pass/fail、negative results and Paper A/Phase 2/3 status。It does not generate a positive abstract automatically。

- [ ] **Step 5: Run final targeted and full tests.**

```powershell
& $ProjectPython -m unittest 09-experiments.tests.test_llm_packet_separation 09-experiments.tests.test_llm_phase1_contract 09-experiments.tests.test_llm_phase1_validation 09-experiments.tests.test_llm_phase1_scoring 09-experiments.tests.test_llm_compiler_pilot 09-experiments.tests.test_llm_v03_inheritance 09-experiments.tests.test_llm_finetuning_data 09-experiments.tests.test_llm_finetuning_leakage 09-experiments.tests.test_qwen_runtime_lock 09-experiments.tests.test_qwen_qlora 09-experiments.tests.test_llm_phase1_adapter 09-experiments.tests.test_llm_phase1_g2 -q
& $ProjectPython -m unittest discover -s 09-experiments\tests -p 'test_*.py'
git diff --check
git diff --name-only -- 09-experiments/scripts/run_mvp.py 09-experiments/real_cases 08-writing/paper-package-v1.0-parameter-governance 08-writing/patent-package*
```

Expected: all tests `OK`; forbidden-file diff empty; no DOCX/PPT/PDF generated; result wording matches actual Gates.

- [ ] **Step 6: Present complete diff and result record before commit/push.**

Only after user review may tracked code/config/tests/reports be committed and pushed。Never stage model weights、adapter binaries、raw source corpora、private G1/G2 CSV or local environment/cache。

---

## Hard-Stop Summary

| Gate | Earliest allowed work | Blocked until explicit user action |
|---|---|---|
| Plan review（current） | Read-only inspection and this Markdown | Any v0.3 code/data/runtime mutation |
| V3-B source review | Schemas、validators、metadata-only source review | Corpus download、tokenizer-only fixed assets and normalization |
| V3-C data Gate | Reviewed source normalization、author labels、packet freeze | Runtime install and model download |
| V3-D QLoRA smoke | Runtime install、fixed snapshot、20-packet smoke | Formal adapter training |
| V3-E atomic pilot | Primary training、adapter freeze、28 calls | Formal 64-packet inference |
| G2 decision | Machine/G1 proxy report | GPS/UCR and positive grounding claim |

---

## Design Traceability

| v0.3 requirement | Implementation task |
|---|---|
| One Qwen2.5 base + adapter | Tasks 1、8–12 |
| Preserve v0.2 frozen test and Rule | Tasks 1–2、14 |
| No C07–C12/test-family training | Tasks 3–7、9、12 |
| 4+2 source-family split | Tasks 3、5、7 |
| 400/100、40%–60%、distractor >=50% | Task 7 |
| Token p50/p95/max、p95 <=1024、no truncation | Task 7；Task 10 revalidation |
| Author-only training labels; G2 separate | Tasks 6、15 |
| QLoRA exact config and `<1%` | Tasks 8–12 |
| 10.5 GiB / 24 GPU h / 30 GB | Tasks 8、10–14 |
| 448 calls and structured stage reuse | Tasks 2、13–14 |
| Same-model structured/direct | Tasks 1–2、9、14 |
| Contamination unknown and refusal strata | Task 14 |
| G2/GPS/UCR and failure form | Tasks 15–16 |
| Paper A、Phase 2/3 isolation | Global constraints、Task 16 |

---

## Self-Review Checklist

- [ ] Tasks 1–9 can be implemented and tested without model weights; Tasks 3–5 do not download corpus payload before source approval.
- [ ] v0.2 generated inputs are inherited by hash and never rewritten.
- [ ] Existing 60-test baseline remains green after every refactor.
- [ ] Source family, not packet, is the train/validation split unit.
- [ ] Qwen2.5 tokenizer counts full prompt+target; token p50/p95/max are frozen, final max is <=1024, and no truncation is enabled.
- [ ] DARPA E3/E5、OpTC、OTRF、WitFoo are blocked from QLoRA training.
- [ ] Trainer has no path or API to v0.2 development/test/G2/Paper A.
- [ ] General and Adapted conditions load one base; adapter state is the only intended model difference.
- [ ] Structured conclusion consumes the already-recorded General compiler result and does not incur a duplicate stage-1 call.
- [ ] The 448/256 arithmetic counts actual `generate()` invocations, not logical rows.
- [ ] Training labels never become G2 or human-consensus gold.
- [ ] Test output cannot affect prompt、Rule、data、adapter、matching or checkpoint selection.
- [ ] G2 failure removes GPS/UCR fields and forces the negative/interface-pilot form.
- [ ] No plan step stages binary weights、raw corpora、private gold/audits or unrelated dirty files.
- [ ] No Paper A、patent、DOCX/PPT/PDF or Phase 2/3 mutation appears.

## Execution Handoff

Plan review is the current deliverable. After user approval, the safe default is inline execution of Tasks 1–4, followed by **HARD STOP V3-B** for the source catalog. If the user explicitly requests subagent execution, use `superpowers:subagent-driven-development`; otherwise use `superpowers:executing-plans` in this task and report at every hard stop. Plan approval alone does not authorize source downloads、runtime installation、model download、QLoRA training or inference.
