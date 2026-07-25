# Paper B Phase 1 受证据约束 LLM 编译实施计划 v0.1

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不修改 Paper A、`run_mvp.py` 或冻结实验结果的前提下，实现 Paper B Phase 1 的泄漏隔离、context-packet 构建、G0 admission、规则基线、stub 运行、structured/direct 对照、G1/G2 评分与声明 Gate。

**Architecture:** 新分支完全位于 `09-experiments/llm_compiler_v0.2/`、四个新脚本、四组新 schema/contract 与四个新测试模块中。推理进程只读取 `public/`；admission 只使用 G0 机械事实；private G1 gold 只由推理结束后的 scorer 读取。正式模型执行由两个硬 Gate 分开：先完成 dependency-free 泄漏修复、规则快照与 stub 测试，再单独申请依赖和权重授权；G2 未过时只发布负结果/接口 pilot，不解锁 Phase 2/3。

**Tech Stack:** Python 3.11 标准库、JSON/JSONL/GZIP、JSON Schema 2020-12 合同、`unittest`；单独授权后才允许使用 PyTorch、Transformers、Accelerate、bitsandbytes、safetensors 与 Hugging Face Hub。主运行限定 RTX 2080 Ti 11 GB、7B、4-bit。

## Global Constraints

- 权威设计为 `08-writing/llm-apt-provenance-research-design-v0.2-20260715.md`，本计划只授权 RQ1、RQ5；RQ2 仅作污染/拒答/4-bit 次级分层。
- Phase 1 不实现 RQ3 端到端传导、RQ4 selector、DQN/RL、semantic-link planner mode、多模态、原始 PCAP 全文或微调。
- 不修改 `09-experiments/scripts/run_mvp.py`、任何 `real_cases/*`、`acquisition_actions.json`、Paper A 文稿或既有结果目录。
- C04–C06 仅作开发集：26 positive + 26 matched null；C07–C12 仅作冻结测试集：32 positive + 32 matched null、6 个独立案例。
- `request_id`、`candidate_claim_id`、`gold_claim_id` 必须三分；public 字节中不得出现 canonical `claim_id` 或 `gold_claim_id`。
- Admission 只能读取 G0：schema、request/candidate ID、packet pointer、record hash、literal entity 与格式；G1/private gold 永不进入 validator、runner 或 structured 第二阶段输入。
- G1 匹配在测试输出前冻结为字段级规范化 exact：`source_type`、subject/entity type/value、`predicate`、object/entity type/value、pointer artifact/record；candidate 匹配任一可接受 observation gold 即通过。
- Rule 只能在开发集校准；必须在任何 LLM 输出产生前写入不可变 snapshot，后续实现/config/hash 漂移一律拒跑。
- Null 构造审计与 G2 输出评分是两轮独立流程：前者在模型前确认包内无可接受 observation，后者在模型后盲评四个输出包。
- 两项主指标只有 GPS、UCR。无合格 G2 时，名称必须降级为 `project_gold_packet_agreement`、`ceiling_violation_rate` 和 `invalid_pointer_rate`。
- G2 固定为 24 packets（每个 C07–C12 各 2 positive + 2 null）、4 输出包、96 项/标注者、两名独立盲审者；kappa `>=0.70` 且 unassessable `<=20%`。
- 一致性面板四条件固定为 `general_compiler`、`security_compiler`、`general_structured`、`general_direct`。Structured 的重复 identity 必须绑定完整两阶段 hash chain。
- 主运行 `temperature=0`、`do_sample=false`、first-pass 不可被 repair 覆盖；64-packet first-pass 为 256 次模型调用，一致性诊断最多另加 192 次，总计 448。
- 若 pilot 估计 448 次超过 24 GPU 小时，只能取消 192 次一致性诊断；不得删测试 packets、换案例或只跑表现较好的模型。
- 模型/缓存磁盘上限 30 GB。OOM、超时、许可或后端失败时停止对应条件，不得静默换模型。
- 所有结果先写 Markdown/JSON 审阅稿；本计划不生成 DOCX、PPT 或 PDF。

---

## File Map

### Source files to create

- `09-experiments/llm_compiler_v0.2/README.md`：状态、命令、Gate、禁用声明和产物目录。
- `09-experiments/llm_compiler_v0.2/experiment_config.json`：split、seed、条件、模型角色、解码、调用预算、runtime lock 状态。
- `09-experiments/llm_compiler_v0.2/prompts/compiler-system-v0.2.txt`：candidate observation 编译约束。
- `09-experiments/llm_compiler_v0.2/prompts/compiler-user-v0.2.txt`：public packet 序列化协议。
- `09-experiments/llm_compiler_v0.2/prompts/structured-system-v0.2.txt`：只消费 admitted claims 的第二阶段结论协议。
- `09-experiments/llm_compiler_v0.2/prompts/direct-system-v0.2.txt`：同 packet、同模型、独立 schema 的 direct 对照。
- `09-experiments/data_schema/llm_context_packet.schema.json`：public packet 合同。
- `09-experiments/data_schema/llm_compiler_result.schema.json`：compiler first-pass 合同。
- `09-experiments/data_schema/llm_conclusion_result.schema.json`：structured/direct 结论合同。
- `09-experiments/data_schema/llm_run_manifest.schema.json`：模型/config/prompt/input/output/hash-chain 合同。
- `09-experiments/governance/contracts/llm-compiler-contract-v0.2.json`：G0/G1 边界、规范化字段、条件、主指标和声明 Gate。
- `09-experiments/scripts/build_llm_evaluation_packets.py`：source adapter、packet/null 构造、ID 分离、null 审计与 bundle freeze。
- `09-experiments/scripts/run_llm_phase1.py`：Rule/stub/local-HF 条件、两阶段输入、完整 hash chain 和调用预算。
- `09-experiments/scripts/validate_llm_phase1_output.py`：G0-only admission、manifest/schema/identity 检查。
- `09-experiments/scripts/score_llm_phase1.py`：G1 exact、多 gold、case macro、G2 bundle/agreement、GPS/UCR 与声明 Gate。
- `09-experiments/tests/test_llm_packet_separation.py`：泄漏、确定性、public/private、null 审计。
- `09-experiments/tests/test_llm_phase1_contract.py`：schema/contract/config/条件/预算。
- `09-experiments/tests/test_llm_phase1_validation.py`：G0 admission 与 structured 第二阶段可见性。
- `09-experiments/tests/test_llm_phase1_scoring.py`：多 gold exact、代理命名、G2 agreement 与 Gate。

### Generated artifacts

```text
09-experiments/llm_compiler_v0.2/generated/
  development/{public,private}/
  test/{public,private}/
  atomic-pilot/public/
  null-construction-audit/
  frozen/
    rule-baseline-development.json
    rule-baseline-development.sha256
    prompt-config-lock.json
    model-runtime-lock.json
  runs/<run_id>/
  g2-audit/<audit_id>/
```

`generated/*/private/`、本地模型、A/B 回收表和未脱敏原始输出不得进入模型运行目录；是否提交由对应 manifest 的 `distribution` 字段决定。

---

### Task 1: Freeze schemas, contract, config, and declared conditions

**Files:**

- Create: `09-experiments/data_schema/llm_context_packet.schema.json`
- Create: `09-experiments/data_schema/llm_compiler_result.schema.json`
- Create: `09-experiments/data_schema/llm_conclusion_result.schema.json`
- Create: `09-experiments/data_schema/llm_run_manifest.schema.json`
- Create: `09-experiments/governance/contracts/llm-compiler-contract-v0.2.json`
- Create: `09-experiments/llm_compiler_v0.2/experiment_config.json`
- Create: `09-experiments/tests/test_llm_phase1_contract.py`

**Interfaces:**

- Consumes: v0.2 §§5–11 and reviewer R1–R3/R6.
- Produces: `CONTRACT_VERSION="project05-llm-compiler-contract-v0.2"`; condition IDs; schema paths; `match_fields`; call-budget constants.

- [ ] **Step 1: Write failing contract tests.**

```python
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "data_schema"
CONTRACT = ROOT / "governance" / "contracts" / "llm-compiler-contract-v0.2.json"
CONFIG = ROOT / "llm_compiler_v0.2" / "experiment_config.json"


class LlmPhase1ContractTests(unittest.TestCase):
    def load(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_public_packet_schema_has_no_gold_or_canonical_claim_id(self):
        schema = self.load(SCHEMA_DIR / "llm_context_packet.schema.json")
        serialized = json.dumps(schema, sort_keys=True)
        self.assertNotIn("gold_claim_id", serialized)
        self.assertNotIn('"claim_id"', serialized)
        self.assertIn("request_id", schema["required"])
        self.assertIn("records", schema["required"])

    def test_admission_is_g0_only_and_g1_is_scorer_only(self):
        contract = self.load(CONTRACT)
        self.assertEqual("G0", contract["admission"]["maximum_gold_level"])
        self.assertEqual(["score_llm_phase1.py"], contract["g1"]["authorized_readers"])
        self.assertFalse(contract["structured_stage_2"]["raw_packet_visible"])
        self.assertFalse(contract["structured_stage_2"]["private_gold_visible"])

    def test_multigold_match_fields_and_normalizer_are_frozen(self):
        contract = self.load(CONTRACT)
        self.assertEqual("any_acceptable_gold", contract["g1"]["match_policy"])
        self.assertEqual(
            ["unicode_nfkc", "strip", "collapse_whitespace", "casefold"],
            contract["g1"]["normalization"],
        )
        self.assertEqual(8, len(contract["g1"]["match_fields"]))

    def test_four_repeat_conditions_and_call_budget_are_exact(self):
        config = self.load(CONFIG)
        self.assertEqual(
            ["general_compiler", "security_compiler", "general_structured", "general_direct"],
            config["repeat_panel"]["conditions"],
        )
        self.assertEqual(256, config["call_budget"]["first_pass"])
        self.assertEqual(192, config["call_budget"]["repeat_diagnostic"])
        self.assertEqual(448, config["call_budget"]["maximum_formal"])
```

- [ ] **Step 2: Run tests and verify missing-file failure.**

Run:

```powershell
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest 09-experiments.tests.test_llm_phase1_contract -v
```

Expected: `ERROR` with `FileNotFoundError` for the new schema/contract/config.

- [ ] **Step 3: Create the four strict schemas.**

All four use `"$schema": "https://json-schema.org/draft/2020-12/schema"` and `"additionalProperties": false`. Freeze these required roots:

```json
{
  "llm_context_packet": ["request_id", "case_id", "split", "packet_role", "support_ceiling", "records"],
  "llm_compiler_result": ["request_id", "condition_id", "attempt_index", "status", "candidate_claims", "telemetry"],
  "llm_conclusion_result": ["request_id", "condition_id", "attempt_index", "status", "observation_claims", "highest_supported_granularity", "path_summary", "actor", "campaign", "missing_evidence", "abstain", "citations"],
  "llm_run_manifest": ["run_id", "condition_id", "split", "input_manifest_sha256", "config_sha256", "contract_sha256", "prompt_sha256", "model_lock", "stage_hash_chain", "result_sha256", "status"]
}
```

`records[]` requires `packet_record_id` (`REC-[A-F0-9]{24}`), `source_type`, `source_pointer.artifact_id`, `source_pointer.record_id`, `record_sha256`, and `source_payload`. `candidate_claims[]` requires `candidate_claim_id` (`CC-[A-F0-9]{24}`), the eight G1 match fields, and no `claim_id`/`gold_claim_id`. Conclusion granularity enum is `G0_unknown/G1_technique/G2_tactic_intent/G3_campaign`; `actor` and `campaign` are string-or-null, never implicit free text.

- [ ] **Step 4: Create the authoritative contract and pre-model config.**

Write the following exact policy values; model revisions remain absent rather than represented by placeholder text:

```json
{
  "contract_version": "project05-llm-compiler-contract-v0.2",
  "admission": {
    "maximum_gold_level": "G0",
    "checks": ["schema", "candidate_id", "pointer_membership", "record_sha256", "literal_entity"],
    "forbidden_inputs": ["private_gold", "gold_claim_id", "canonical_claim_id", "g1_match_result"]
  },
  "g1": {
    "authorized_readers": ["score_llm_phase1.py"],
    "match_policy": "any_acceptable_gold",
    "normalization": ["unicode_nfkc", "strip", "collapse_whitespace", "casefold"],
    "match_fields": [
      "source_type", "subject.entity_type", "subject.value", "predicate",
      "object.entity_type", "object.value",
      "source_pointer.artifact_id", "source_pointer.record_id"
    ]
  },
  "structured_stage_2": {
    "raw_packet_visible": false,
    "rejected_claims_visible": false,
    "private_gold_visible": false,
    "allowed_inputs": ["admitted_claims", "explicit_gaps", "support_ceiling"]
  },
  "primary_metrics": ["GPS", "UCR"],
  "without_g2_names": ["project_gold_packet_agreement", "ceiling_violation_rate", "invalid_pointer_rate"]
}
```

Config status is `pre_model_infrastructure`; split counts are 26/26 and 32/32; seeds are `2026071501` for packets, `2026071502` for nulls, `2026071503` for G2 and `2026071504` for repeats. Declare the two model IDs but omit `revision`, `weights_sha256` and `local_path` until the model-lock task resolves them.

- [ ] **Step 5: Pass tests and commit the frozen contract.**

```powershell
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest 09-experiments.tests.test_llm_phase1_contract -v
git add 09-experiments/data_schema/llm_* 09-experiments/governance/contracts/llm-compiler-contract-v0.2.json 09-experiments/llm_compiler_v0.2/experiment_config.json 09-experiments/tests/test_llm_phase1_contract.py
git commit -m "experiment: freeze llm phase1 contracts"
```

Expected: 4 tests pass; commit contains no runtime/model downloads.

### Task 2: Implement deterministic IDs and physical public/private separation

**Files:**

- Create: `09-experiments/scripts/build_llm_evaluation_packets.py`
- Create: `09-experiments/tests/test_llm_packet_separation.py`

**Interfaces:**

- `canonical_json(value: Any) -> bytes`
- `derive_request_id(public_body: dict[str, Any]) -> str`
- `derive_candidate_claim_id(request_id: str, condition_id: str, attempt_index: int, output_index: int) -> str`
- `derive_gold_claim_id(case_id: str, canonical_claim_id: str) -> str`
- `write_jsonl_gz(path: Path, rows: Iterable[dict[str, Any]]) -> None`
- `write_bundle(output_dir: Path, public_rows, private_rows, public_catalog, metadata) -> dict[str, Any]`

- [ ] **Step 1: Write failing separation tests.**

```python
class PacketIdentityTests(unittest.TestCase):
    def test_public_bytes_never_contain_canonical_or_gold_id(self):
        public, private = builder.make_fixture_packet("C07-EC-001")
        payload = builder.canonical_json(public)
        self.assertNotIn(b"C07-EC-001", payload)
        self.assertNotIn(b"GOLD-", payload)
        self.assertIn("gold_claim_id", private)

    def test_private_gold_mutation_does_not_change_public_bytes_or_request_id(self):
        public, private = builder.make_fixture_packet("C07-EC-001")
        before = builder.canonical_json(public)
        request_before = builder.derive_request_id(public)
        private["acceptable_observations"][0]["predicate"] = "changed_only_in_private"
        self.assertEqual(before, builder.canonical_json(public))
        self.assertEqual(request_before, builder.derive_request_id(public))

    def test_candidate_id_binds_condition_attempt_and_output_index(self):
        ids = {
            builder.derive_candidate_claim_id("REQ-" + "A" * 24, "general_compiler", attempt, index)
            for attempt in (0, 1) for index in (0, 1)
        }
        self.assertEqual(4, len(ids))

    def test_write_bundle_places_no_private_file_under_public(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = builder.write_fixture_bundle(Path(temp))
            public_files = {path.name for path in (Path(temp) / "public").iterdir()}
            self.assertEqual({"context_packets.jsonl.gz", "public_cti_catalog.json", "input_manifest.json"}, public_files)
            self.assertFalse(any("private" in str(path) for path in (Path(temp) / "public").rglob("*")))
            self.assertEqual("separated", manifest["separation_status"])
```

- [ ] **Step 2: Run tests and verify missing builder failure.**

Expected: import fails for `build_llm_evaluation_packets.py`.

- [ ] **Step 3: Implement canonical hashing and ID derivation.**

```python
def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_id(prefix: str, payload: bytes) -> str:
    return f"{prefix}-{hashlib.sha256(payload).hexdigest()[:24].upper()}"


def derive_request_id(public_body: dict[str, Any]) -> str:
    body = {key: value for key, value in public_body.items() if key != "request_id"}
    return digest_id("REQ", canonical_json(body))


def derive_candidate_claim_id(request_id, condition_id, attempt_index, output_index):
    payload = f"{request_id}|{condition_id}|{attempt_index}|{output_index}".encode("utf-8")
    return digest_id("CC", payload)


def derive_gold_claim_id(case_id: str, canonical_claim_id: str) -> str:
    return digest_id("GOLD", f"{case_id}|{canonical_claim_id}".encode("utf-8"))
```

`gold_claim_id` and the canonical `claim_id` are written only to `private/observation_gold.jsonl.gz`. GZIP uses `mtime=0`; JSON uses sorted keys and `\n`, so repeated builds are byte-identical.

- [ ] **Step 4: Implement manifest separation checks.**

Before writing, recursively scan the canonical public payload and reject keys matching `claim_id`, `gold_claim_id`, `acceptable_observations`, `recoverable_claim_ids`, or `required_claim_ids`. After writing, reopen all public files, scan their decoded bytes for every private ID, and write their SHA-256 to `input_manifest.json`. A bundle with any collision must be deleted before raising `ValueError`.

- [ ] **Step 5: Run tests and commit.**

```powershell
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest 09-experiments.tests.test_llm_packet_separation -v
git add 09-experiments/scripts/build_llm_evaluation_packets.py 09-experiments/tests/test_llm_packet_separation.py
git commit -m "experiment: separate llm public and private identities"
```

### Task 3: Build positive and matched-null context packets from frozen sources

**Files:**

- Modify: `09-experiments/scripts/build_llm_evaluation_packets.py`
- Modify: `09-experiments/tests/test_llm_packet_separation.py`

**Interfaces:**

- `load_case_records(root: Path, case_dir: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]`
- `build_positive_packets(case_id: str, records, claims, seed: int) -> tuple[list[dict], list[dict]]`
- `build_null_candidates(case_id: str, records, claimed_record_ids: set[str], positive_packets, seed: int) -> list[dict]`
- `build_split(root: Path, split: Literal["development", "test"], output_dir: Path) -> dict[str, Any]`

- [ ] **Step 1: Add failing count, multi-gold, distractor and determinism tests.**

```python
def test_development_and_test_counts_are_frozen(self):
    with tempfile.TemporaryDirectory() as temp:
        dev = builder.build_split(ROOT, "development", Path(temp) / "dev")
        test = builder.build_split(ROOT, "test", Path(temp) / "test")
        self.assertEqual({"positive": 26, "null": 26}, dev["packet_counts"])
        self.assertEqual({"positive": 32, "null": 32}, test["packet_counts"])
        self.assertEqual(6, test["case_count"])

def test_positive_packet_has_no_target_marker_and_private_allows_multiple_gold(self):
    public, private = builder.build_case_fixture_with_two_distractors()
    self.assertNotIn("target", json.dumps(public).casefold())
    self.assertGreaterEqual(len(public["records"]), 3)
    self.assertGreaterEqual(len(private["acceptable_observations"]), 1)

def test_repeated_build_is_byte_identical(self):
    with tempfile.TemporaryDirectory() as temp:
        first = Path(temp) / "first"
        second = Path(temp) / "second"
        builder.build_split(ROOT, "test", first)
        builder.build_split(ROOT, "test", second)
        self.assertEqual((first / "public/input_manifest.json").read_bytes(), (second / "public/input_manifest.json").read_bytes())
        self.assertEqual((first / "public/context_packets.jsonl.gz").read_bytes(), (second / "public/context_packets.jsonl.gz").read_bytes())
```

- [ ] **Step 2: Run the three tests and confirm they fail on missing adapters.**

Expected: failures mention `build_split`/`load_case_records`.

- [ ] **Step 3: Implement six source-family adapters without importing gold into public records.**

Reuse read-only parsing helpers from `compile_real_motifs.py` for C04–C06, `build_claim_source_excerpts.py` for PGDMP/eCAR/OTRF C07–C11, and `compile_witfoo_c12_case.py` only for C12 integrity/path conventions. Each adapter returns:

```python
{
    "packet_record_id": digest_id("REC", canonical_json({"artifact_id": artifact_id, "record_id": record_id})),
    "source_type": source_type,
    "source_pointer": {"artifact_id": artifact_id, "record_id": record_id},
    "record_sha256": hashlib.sha256(canonical_json(source_payload)).hexdigest().upper(),
    "source_payload": source_payload,
}
```

The adapter may use canonical claims only to locate representative source records and write private acceptable observations; it must construct public `source_payload` exclusively from frozen source files. C04–C06 map to 26 development claims; C07–C12 map to all 32 test claims.

- [ ] **Step 4: Build positive packets with real distractors and all acceptable gold.**

For each canonical claim, include its representative record plus the next two same-case records under a seeded stable cyclic order. Remove any `target`, claim ID, motif ID, technique/tactic, actor/campaign, confidence and author notes from public records. Private gold lists every canonical observation whose representative pointer occurs in the packet, so GPS accepts any real packet observation rather than one post-selected target.

- [ ] **Step 5: Build matched null candidates.**

For every positive packet, sample three same-case/same-source-family raw records not used by any canonical claim and not duplicated in another null packet until the candidate pool is exhausted; then allow deterministic reuse while recording `reuse_count`. Null rows remain `status="pending_human_construction_audit"` and cannot be frozen by this task.

- [ ] **Step 6: Run builders, verify counts, and commit source adapters.**

```powershell
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 09-experiments\scripts\build_llm_evaluation_packets.py --root . --split development --output 09-experiments\llm_compiler_v0.2\generated\development --draft
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 09-experiments\scripts\build_llm_evaluation_packets.py --root . --split test --output 09-experiments\llm_compiler_v0.2\generated\test --draft
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest 09-experiments.tests.test_llm_packet_separation -v
git add 09-experiments/scripts/build_llm_evaluation_packets.py 09-experiments/tests/test_llm_packet_separation.py
git commit -m "experiment: build llm context packet drafts"
```

Expected: 52 development and 64 test draft packets; both manifests say `formal_ready=false` solely because null audits are pending.

### Task 4: Separate model-pre null construction audit from model-post G2 audit

**Files:**

- Modify: `09-experiments/scripts/build_llm_evaluation_packets.py`
- Modify: `09-experiments/tests/test_llm_packet_separation.py`

**Interfaces:**

- `write_null_construction_audit(packet_rows, output_dir: Path) -> dict[str, Any]`
- `validate_null_construction_audit(audit_csv: Path, expected_request_ids: set[str]) -> dict[str, Any]`
- `freeze_packet_bundle(bundle_dir: Path, audit_csv: Path) -> dict[str, Any]`

- [ ] **Step 1: Write failing audit-separation tests.**

```python
def test_pending_or_single_person_null_audit_cannot_freeze(self):
    with tempfile.TemporaryDirectory() as temp:
        bundle = builder.write_fixture_bundle(Path(temp) / "bundle")
        audit = builder.write_fixture_null_audit(Path(temp), author="yes", reviewer="")
        with self.assertRaisesRegex(ValueError, "two independent confirmations"):
            builder.freeze_packet_bundle(Path(temp) / "bundle", audit)

def test_null_audit_has_no_model_output_or_g2_labels(self):
    fields = set(builder.NULL_AUDIT_FIELDS)
    self.assertEqual(
        {"request_id", "author_no_acceptable_observation", "author_id", "reviewer_no_acceptable_observation", "reviewer_id", "notes"},
        fields,
    )
    self.assertNotIn("supported", fields)
    self.assertNotIn("condition_id", fields)
```

- [ ] **Step 2: Implement the two-person construction Gate.**

`freeze_packet_bundle` requires both decisions equal `yes`, non-empty distinct `author_id`/`reviewer_id`, exact request-ID coverage, no duplicate rows, and no private source access failure. It records only the audit file SHA-256 and decision counts in `private/gold_manifest.json`; it never copies reviewer identities or decisions into public files.

- [ ] **Step 3: Generate audit templates and stop for human completion.**

```powershell
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 09-experiments\scripts\build_llm_evaluation_packets.py --root . --split development --prepare-null-audit 09-experiments\llm_compiler_v0.2\generated\null-construction-audit\development.csv
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 09-experiments\scripts\build_llm_evaluation_packets.py --root . --split test --prepare-null-audit 09-experiments\llm_compiler_v0.2\generated\null-construction-audit\test.csv
```

Expected: 26 and 32 blank audit rows. Do not fabricate decisions. Formal test inference remains blocked until both completed files validate.

- [ ] **Step 4: Pass tests and commit audit machinery, not human labels.**

```powershell
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest 09-experiments.tests.test_llm_packet_separation -v
git add 09-experiments/scripts/build_llm_evaluation_packets.py 09-experiments/tests/test_llm_packet_separation.py
git commit -m "experiment: gate llm null packet construction"
```

### Task 5: Implement G0-only validation and structured stage-2 visibility

**Files:**

- Create: `09-experiments/scripts/validate_llm_phase1_output.py`
- Create: `09-experiments/tests/test_llm_phase1_validation.py`

**Interfaces:**

- `validate_candidate(candidate: dict[str, Any], packet: dict[str, Any], condition_id: str, attempt_index: int, output_index: int) -> list[str]`
- `admit_candidates(result: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]`
- `build_structured_stage2_input(admission: dict[str, Any], support_ceiling: str) -> dict[str, Any]`
- `validate_run_manifest(manifest, config, input_manifest, prompt_lock, model_lock) -> list[str]`

- [ ] **Step 1: Write failing R1 boundary tests.**

```python
def test_admission_signature_and_result_do_not_depend_on_private_gold(self):
    self.assertEqual(
        ["candidate", "packet", "condition_id", "attempt_index", "output_index"],
        list(inspect.signature(validator.validate_candidate).parameters),
    )
    candidate, packet = fixture_valid_candidate_and_packet()
    before = validator.validate_candidate(candidate, packet, "general_compiler", 0, 0)
    private_gold = {"acceptable_observations": [{"predicate": "contradicts-candidate"}]}
    private_gold["acceptable_observations"][0]["predicate"] = "another-change"
    after = validator.validate_candidate(candidate, packet, "general_compiler", 0, 0)
    self.assertEqual(before, after)

def test_structured_stage2_input_excludes_raw_rejected_and_private(self):
    payload = validator.build_structured_stage2_input(
        {"admitted_claims": [{"candidate_claim_id": "CC-" + "A" * 24}], "rejected": [{"raw": "secret"}], "explicit_gaps": ["missing_source"]},
        "G2_tactic_intent",
    )
    serialized = json.dumps(payload, sort_keys=True)
    self.assertNotIn("source_payload", serialized)
    self.assertNotIn("rejected", serialized)
    self.assertNotIn("private", serialized)
    self.assertEqual({"admitted_claims", "explicit_gaps", "support_ceiling"}, set(payload))
```

- [ ] **Step 2: Run tests and verify missing validator failure.**

- [ ] **Step 3: Implement G0 checks only.**

```python
def validate_candidate(candidate, packet, condition_id, attempt_index, output_index):
    errors = []
    expected_id = derive_candidate_claim_id(packet["request_id"], condition_id, attempt_index, output_index)
    if candidate.get("candidate_claim_id") != expected_id:
        errors.append("candidate_id_mismatch")
    pointer = candidate.get("source_pointer") or {}
    records = {(row["source_pointer"]["artifact_id"], row["source_pointer"]["record_id"]): row for row in packet["records"]}
    record = records.get((pointer.get("artifact_id"), pointer.get("record_id")))
    if record is None:
        errors.append("pointer_not_in_packet")
        return errors
    if hashlib.sha256(canonical_json(record["source_payload"])).hexdigest().upper() != record["record_sha256"]:
        errors.append("record_sha256_mismatch")
    visible = [normalize_literal(value) for value in iter_scalar_values(record["source_payload"])]
    for entity in (candidate.get("subject") or {}, candidate.get("object") or {}):
        value = normalize_literal(entity.get("value") or "")
        if not value or not any(value in field for field in visible):
            errors.append("literal_entity_not_in_source")
    return sorted(set(errors))
```

`iter_scalar_values` recursively yields only scalar values from dict/list fields; `normalize_literal` applies Unicode NFKC, trim, whitespace collapse and casefold without JSON escaping. This allows a path inside a command-line field to count as literal presence while still rejecting values absent from every structured field.

Do not add a `gold`, `acceptable_observations`, scorer or semantic-match argument. G0 admission may reject malformed literal claims; it may not accept/reject based on whether candidate matches G1.

- [ ] **Step 4: Implement stage-2 projection and manifest hash validation.**

Stage 2 receives only admitted claim objects, machine-generated gap codes (`no_admitted_claim`, `invalid_pointer`, `literal_entity_absent`, `schema_invalid`) and the case `support_ceiling`. Bind `stage1_raw_sha256`, `admission_sha256`, `stage2_input_sha256`, `stage2_raw_sha256` and `final_result_sha256` in order.

- [ ] **Step 5: Run tests and commit.**

```powershell
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest 09-experiments.tests.test_llm_phase1_validation -v
git add 09-experiments/scripts/validate_llm_phase1_output.py 09-experiments/tests/test_llm_phase1_validation.py
git commit -m "experiment: enforce g0-only llm admission"
```

### Task 6: Implement frozen Rule baseline and development snapshot

**Files:**

- Create: `09-experiments/scripts/run_llm_phase1.py`
- Modify: `09-experiments/tests/test_llm_phase1_contract.py`
- Modify: `09-experiments/tests/test_llm_phase1_validation.py`

**Interfaces:**

- `rule_compile(packet: dict[str, Any]) -> dict[str, Any]`
- `run_condition(config, packet, condition_id, backend, attempt_index=0) -> tuple[dict, dict]`
- `freeze_rule_snapshot(config_path, contract_path, development_manifest, rule_results, output_path) -> dict`
- `require_rule_snapshot_unchanged(snapshot_path, config_path, contract_path) -> None`

- [ ] **Step 1: Write failing Rule snapshot tests.**

```python
def test_rule_snapshot_is_required_before_any_llm_backend(self):
    with tempfile.TemporaryDirectory() as temp:
        with self.assertRaisesRegex(ValueError, "rule baseline snapshot"):
            runner.preflight_llm_backend(Path(temp) / "missing.json", CONFIG, CONTRACT)

def test_rule_or_config_drift_after_snapshot_is_rejected(self):
    with tempfile.TemporaryDirectory() as temp:
        snapshot = runner.write_fixture_rule_snapshot(Path(temp), CONFIG, CONTRACT)
        changed = json.loads(CONFIG.read_text(encoding="utf-8"))
        changed["rule_baseline"]["operation_map"]["EVENT_READ"] = "changed_after_freeze"
        changed_path = Path(temp) / "changed.json"
        changed_path.write_text(json.dumps(changed), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "snapshot hash mismatch"):
            runner.require_rule_snapshot_unchanged(snapshot, changed_path, CONTRACT)
```

- [ ] **Step 2: Implement one conservative, format-aware Rule compiler.**

The Rule may use only public `source_payload`. It extracts explicit source/destination entities and operation/event names for CDM, PGDMP, eCAR, Windows event and WitFoo structured lead formats. It never maps ATT&CK, actor, campaign, maliciousness or author notes. If either entity is absent, it abstains rather than inventing values. Each candidate ID uses `derive_candidate_claim_id(..., "rule_compiler", 0, output_index)` and passes through G0 admission.

- [ ] **Step 3: Run Rule on development only and report the pre-LLM proxy distribution.**

Snapshot fields are exact:

```json
{
  "status": "frozen_before_any_llm_output",
  "split": "development",
  "packet_count": 52,
  "positive_count": 26,
  "null_count": 26,
  "schema_valid_rate": 0.0,
  "claim_count_distribution": {},
  "abstain_rate": 0.0,
  "project_gold_packet_agreement": 0.0,
  "config_sha256": "computed",
  "contract_sha256": "computed",
  "runner_sha256": "computed",
  "development_input_manifest_sha256": "computed",
  "rule_results_sha256": "computed"
}
```

Numeric values and hashes are generated, never hand-filled. If Rule emits zero claims for all positives or claims for all nulls, record `baseline_strength_gate="failed"` and stop; do not look at LLM output and then strengthen it.

- [ ] **Step 4: Freeze and commit the development snapshot before any model work.**

```powershell
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 09-experiments\scripts\run_llm_phase1.py --config 09-experiments\llm_compiler_v0.2\experiment_config.json --split development --condition rule_compiler --backend rule --output 09-experiments\llm_compiler_v0.2\generated\runs\rule-development
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 09-experiments\scripts\run_llm_phase1.py --freeze-rule-snapshot 09-experiments\llm_compiler_v0.2\generated\frozen\rule-baseline-development.json --rule-run 09-experiments\llm_compiler_v0.2\generated\runs\rule-development
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest 09-experiments.tests.test_llm_phase1_contract 09-experiments.tests.test_llm_phase1_validation -v
git add 09-experiments/scripts/run_llm_phase1.py 09-experiments/tests/test_llm_phase1_contract.py 09-experiments/tests/test_llm_phase1_validation.py 09-experiments/llm_compiler_v0.2/generated/frozen/rule-baseline-development*
git commit -m "experiment: freeze llm rule baseline before model output"
```

### Task 7: Implement frozen multi-gold G1 scoring and proxy naming

**Files:**

- Create: `09-experiments/scripts/score_llm_phase1.py`
- Create: `09-experiments/tests/test_llm_phase1_scoring.py`

**Interfaces:**

- `normalize_exact(value: Any) -> str`
- `observation_key(claim: dict[str, Any]) -> tuple[str, ...]`
- `matches_any_acceptable_gold(candidate, acceptable_gold) -> bool`
- `score_project_gold_packet(packet, admitted_claims, private_gold) -> dict[str, Any]`
- `case_macro(rows: list[dict], metric: str) -> float`
- `evaluate_claim_gates(summary: dict[str, Any], g2_status: dict[str, Any]) -> dict[str, Any]`

- [ ] **Step 1: Write failing R2 multi-gold tests.**

```python
def test_candidate_matches_any_acceptable_gold_after_frozen_normalization(self):
    candidate = observation(" PowerShell.EXE ", "CREATED", " C:\\Temp\\A.zip ", "event-1")
    gold = [
        observation("other.exe", "connected", "10.0.0.1", "event-2"),
        observation("powershell.exe", "created", "C:\\Temp\\A.zip", "EVENT-1"),
    ]
    self.assertTrue(scorer.matches_any_acceptable_gold(candidate, gold))

def test_partial_field_match_is_not_semantic_match(self):
    candidate = observation("powershell.exe", "created", "C:\\Temp\\wrong.zip", "event-1")
    gold = [observation("powershell.exe", "created", "C:\\Temp\\A.zip", "event-1")]
    self.assertFalse(scorer.matches_any_acceptable_gold(candidate, gold))

def test_g2_absence_forbids_gps_and_ucr_names(self):
    report = scorer.name_metrics({"agreement": 0.5, "ceiling": 0.1, "invalid_pointer": 0.0}, g2_valid=False)
    self.assertNotIn("GPS", report)
    self.assertNotIn("UCR", report)
    self.assertIn("project_gold_packet_agreement", report)
```

- [ ] **Step 2: Implement the frozen normalizer exactly.**

```python
def normalize_exact(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value))
    return " ".join(text.strip().split()).casefold()


MATCH_PATHS = (
    ("source_type",), ("subject", "entity_type"), ("subject", "value"),
    ("predicate",), ("object", "entity_type"), ("object", "value"),
    ("source_pointer", "artifact_id"), ("source_pointer", "record_id"),
)


def observation_key(claim):
    values = []
    for path in MATCH_PATHS:
        current = claim
        for part in path:
            current = current[part]
        values.append(normalize_exact(current))
    return tuple(values)


def matches_any_acceptable_gold(candidate, acceptable_gold):
    key = observation_key(candidate)
    return any(key == observation_key(gold) for gold in acceptable_gold)
```

This algorithm is frozen before any test LLM output. Changing paths or normalization creates a new contract version, not an in-place edit.

- [ ] **Step 3: Implement packet and case-macro proxies.**

Positive proxy success requires at least one admitted candidate match to any acceptable gold and zero candidates outside the acceptable set. Null proxy success requires abstain and zero admitted candidates. Report per-case first, then unweighted six-case macro; technical repeats are never extra cases.

- [ ] **Step 4: Encode claim Gates without positive defaults.**

`evaluate_claim_gates` returns booleans and explicit failure reasons. Rule comparison requires `delta_GPS>=0.05`, at least 4/6 non-inferior cases, unsupported and invalid-pointer rates no worse, and no refusal-only win. Structured/direct requires `delta_UCR<=-0.05`, at least 4/6 favorable cases, and coverage drop no more than 0.05. Title Gate is true only when G2, Rule and structured/direct Gates all pass.

- [ ] **Step 5: Run tests and commit scoring logic.**

```powershell
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest 09-experiments.tests.test_llm_phase1_scoring -v
git add 09-experiments/scripts/score_llm_phase1.py 09-experiments/tests/test_llm_phase1_scoring.py
git commit -m "experiment: freeze llm multigold scoring"
```

### Task 8: Add prompts, stub backend, structured/direct parity, and full hash chains

**Files:**

- Create: `09-experiments/llm_compiler_v0.2/prompts/compiler-system-v0.2.txt`
- Create: `09-experiments/llm_compiler_v0.2/prompts/compiler-user-v0.2.txt`
- Create: `09-experiments/llm_compiler_v0.2/prompts/structured-system-v0.2.txt`
- Create: `09-experiments/llm_compiler_v0.2/prompts/direct-system-v0.2.txt`
- Modify: `09-experiments/scripts/run_llm_phase1.py`
- Modify: `09-experiments/tests/test_llm_phase1_contract.py`
- Modify: `09-experiments/tests/test_llm_phase1_validation.py`

**Interfaces:**

- `InferenceBackend.generate(messages, generation_config) -> tuple[str, dict[str, Any]]`
- `StubBackend(InferenceBackend)`
- `run_compiler(packet, condition_id, backend, attempt_index) -> tuple[dict, dict]`
- `run_structured(packet, backend, attempt_index) -> tuple[dict, dict]`
- `run_direct(packet, backend, attempt_index) -> tuple[dict, dict]`
- `hash_chain_complete(manifest: dict[str, Any]) -> bool`

- [ ] **Step 1: Write failing visibility, fairness, and repeat-identity tests.**

```python
def test_direct_and_structured_share_model_and_generation_config(self):
    config = load_json(CONFIG)
    self.assertEqual(config["conditions"]["general_direct"]["model_role"], config["conditions"]["general_structured"]["model_role"])
    self.assertEqual(config["conditions"]["general_direct"]["generation"], config["conditions"]["general_structured"]["generation"])

def test_structured_repeat_hash_binds_both_stages(self):
    result, manifest = runner.run_fixture_structured_with_stub(attempt_index=3)
    self.assertEqual(
        ["stage1_prompt_sha256", "stage1_raw_sha256", "admission_sha256", "stage2_input_sha256", "stage2_prompt_sha256", "stage2_raw_sha256", "final_result_sha256"],
        list(manifest["stage_hash_chain"]),
    )
    self.assertTrue(runner.hash_chain_complete(manifest))

def test_stub_backend_does_not_import_model_packages(self):
    before = set(sys.modules)
    runner.run_fixture_compiler_with_stub()
    loaded = set(sys.modules) - before
    self.assertFalse({"torch", "transformers", "bitsandbytes"} & loaded)
```

- [ ] **Step 2: Write exact compiler and conclusion prompts.**

Compiler system rules: use only visible records; output zero or more atomic observation claims; copy no request ID into claim semantics; cite one packet pointer per claim; emit no tactic/technique/maliciousness/actor/campaign/confidence; abstain when an atomic SPO cannot be supported. Structured prompt states that its input is the complete admitted evidence and forbids guessing from omitted raw data. Direct prompt receives the same public packet and must output the same conclusion schema, including observation claims, per-claim citations, highest granularity, actor/campaign nullable fields, missing evidence and abstain.

- [ ] **Step 3: Implement a deterministic dependency-free stub.**

```python
class StubBackend:
    backend_id = "deterministic_stub_v0.2"

    def generate(self, messages, generation_config):
        request = json.loads(messages[-1]["content"])
        payload = request.get("stub_response", {"status": "abstain", "candidate_claims": []})
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return text, {"latency_ms": 0.0, "peak_vram_mb": 0, "input_tokens": None, "output_tokens": None}
```

Stub tests exercise JSON parse failures, abstain, admitted/rejected candidates, direct output and both structured stages without importing or installing any model package.

- [ ] **Step 4: Freeze prompt/config lock and verify 448-call arithmetic.**

The lock hashes every prompt, config, contract and four schemas. Repeat panel selects 12 test request IDs by seed/case/role stratification and adds attempts 1–4 to first-pass attempt 0. Assert `64*2 + 64 + 64 = 256` first-pass and `12*4*4 = 192` diagnostic invocations. For each packet/attempt, `general_structured` reuses the already generated `general_compiler` attempt as stage 1 and adds one stage-2 call; it does not trigger a second duplicate compiler call.

- [ ] **Step 5: Run all pre-model modules and commit.**

```powershell
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest 09-experiments.tests.test_llm_packet_separation 09-experiments.tests.test_llm_phase1_contract 09-experiments.tests.test_llm_phase1_validation 09-experiments.tests.test_llm_phase1_scoring 09-experiments.tests.test_llm_compiler_pilot -v
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m py_compile 09-experiments\scripts\build_llm_evaluation_packets.py 09-experiments\scripts\run_llm_phase1.py 09-experiments\scripts\validate_llm_phase1_output.py 09-experiments\scripts\score_llm_phase1.py
git add 09-experiments/llm_compiler_v0.2/prompts 09-experiments/llm_compiler_v0.2/generated/frozen/prompt-config-lock.json 09-experiments/scripts/run_llm_phase1.py 09-experiments/tests/test_llm_phase1_contract.py 09-experiments/tests/test_llm_phase1_validation.py
git commit -m "experiment: add llm phase1 stub and hash chain"
```

### Task 9: Produce and review the pre-model readiness Gate

**Files:**

- Create: `09-experiments/llm_compiler_v0.2/README.md`
- Generate: `09-experiments/llm_compiler_v0.2/generated/pre-model-readiness.json`

**Interfaces:**

- `run_llm_phase1.py --pre-model-readiness ...` produces a non-editable evidence report.

- [ ] **Step 1: Document current and forbidden states.**

README must say: Phase 1 only; old `llm_compiler/` and 14-row pilot are historical; no model output exists yet; Rule snapshot predates LLM; null construction audit status; Paper A isolation; G2 failure publication form; no title/abstract claim before Gates 9.1–9.3.

- [ ] **Step 2: Generate the readiness report.**

The report requires: all five targeted test modules pass; old pilot tests remain pass; public/private scan is clean; Rule snapshot and prompt lock validate; test manifest contains exactly 64 packets/6 cases; `torch`, `transformers`, `accelerate`, `bitsandbytes` and model cache paths are absent from the implementation process; Git diff does not touch forbidden files.

- [ ] **Step 3: Run repository-scope checks.**

```powershell
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 09-experiments\scripts\run_llm_phase1.py --pre-model-readiness 09-experiments\llm_compiler_v0.2\generated\pre-model-readiness.json
git diff --check
git diff --name-only -- 09-experiments/scripts/run_mvp.py 09-experiments/real_cases 08-writing/paper-main* 08-writing/patent*
```

Expected: readiness `status="ready_to_request_model_authorization"`; whitespace check succeeds; forbidden-file diff is empty.

- [ ] **Step 4: Commit readiness evidence and STOP.**

```powershell
git add 09-experiments/llm_compiler_v0.2/README.md 09-experiments/llm_compiler_v0.2/generated/pre-model-readiness.json
git commit -m "docs: record llm phase1 pre-model readiness"
```

**HARD STOP A:** Do not install `jsonschema`, torch, Transformers or any inference dependency; do not query/download model weights. Show the readiness JSON and complete diff to the user and request separate authorization.

### Task 10: After explicit authorization, lock runtime/model provenance and run the 28-call atomic pilot

**Files:**

- Modify: `09-experiments/llm_compiler_v0.2/experiment_config.json`
- Modify: `09-experiments/scripts/run_llm_phase1.py`
- Generate: `09-experiments/llm_compiler_v0.2/generated/frozen/model-runtime-lock.json`
- Generate: `09-experiments/llm_compiler_v0.2/generated/runs/atomic-pilot/`

**Interfaces:**

- `HuggingFaceLocalBackend(InferenceBackend)` is imported lazily only for `--backend hf-local`.
- `lock_model_runtime(config, resolved_models, package_versions, gpu_probe) -> dict[str, Any]`
- `estimate_formal_runtime(pilot_manifests) -> dict[str, Any]`

- [ ] **Step 1: Verify authorization and collect read-only hardware facts.**

Run `nvidia-smi`; record GPU name, driver, reported CUDA, total VRAM and timestamp. If the GPU is not the declared 2080 Ti 11 GB environment, stop for plan amendment rather than silently changing the hardware claim.

- [ ] **Step 2: Install only the reviewed runtime lock.**

The reviewed lock is Python 3.11 plus `torch==2.3.1+cu121`, `transformers==4.41.2`, `accelerate==0.31.0`, `bitsandbytes==0.43.1`, `safetensors==0.4.3`, `huggingface-hub==0.23.4`, `sentencepiece==0.2.0`, and `jsonschema==4.22.0`. Install into a dedicated untracked `.venv-llm-phase1`; if any package is unavailable or bitsandbytes cannot execute a 4-bit smoke load on Windows/2080 Ti, stop and report the failed condition. Do not substitute versions without a reviewed amendment.

- [ ] **Step 3: Resolve model revisions before weight download.**

Resolve each model ID to an immutable Hugging Face commit, capture license/model-card URLs, and write them to a draft model lock. User reviews the two resolved commits before `snapshot_download`. Download only those revisions; compute SHA-256 for every weight/config/tokenizer file and total disk size. Reject total model/cache size above 30 GB.

- [ ] **Step 4: Build new-ID atomic pilot packets and run exactly 28 compiler calls.**

Use the historical 14 source records only as smoke inputs, rewrite them into public-only packets with `REQ-*` IDs, and run `14 × 2 models × 1 first-pass`. Record p50/p95 latency, peak VRAM, parse/schema failures, refusal/abstain rates and package versions. Do not score pointer copying as scientific source localization.

- [ ] **Step 5: Apply the runtime Gate.**

If either model cannot complete 14 calls, stop that condition. If projected 448-call runtime exceeds 24 GPU hours, set `repeat_panel.enabled=false` and retain the 256 first-pass calls. Prompt text, Rule, test packets and thresholds remain frozen regardless of pilot outputs.

### Task 11: Run frozen Phase 1 first-pass, optional repeat panel, and contamination diagnostics

**Files:**

- Generate: `09-experiments/llm_compiler_v0.2/generated/runs/phase1-<lock_hash>/`
- Modify: `09-experiments/llm_compiler_v0.2/README.md`

- [ ] **Step 1: Revalidate every preflight Gate.**

Require frozen test bundle and two-person null construction audit; Rule snapshot unchanged; prompt/config/contract/schema hashes unchanged; model/runtime lock frozen; output directory absent/empty. A non-empty output directory is rejected to prevent mixing old and new attempts.

- [ ] **Step 2: Run 256 first-pass calls.**

Run 128 compiler calls (64 × general/security), 64 general structured stage-2 calls after G0 admission, and 64 general direct calls. First-pass raw output is immutable. Repair attempts, if later authorized for diagnostics, are separate records and never replace attempt 0.

- [ ] **Step 3: Run at most 192 repeat calls only when the runtime Gate permits.**

Use the frozen 12-packet panel and attempts 1–4 for the four exact conditions. For general structured, bind the same packet/attempt's fresh `general_compiler` output as stage 1, then run admission and one conclusion call. Thus the panel remains 192 new model invocations while structured identity is the complete seven-element hash chain, not conclusion-only output.

- [ ] **Step 4: Run and label contamination/refusal diagnostics.**

Review model cards for disclosed DARPA/OTRF/CTI sources. Use fixed no-payload case/report-name probes for both models, then exact/near-exact checks for UUIDs, timestamps, commands and local event strings. These diagnostic calls are logged separately from the formal 448 and do not influence model/prompt selection. If absence of contamination cannot be proven, write `contamination_status="unknown"`. Stratify empty, explicit refusal, erroneous abstain, conservative response and invalid format by model and packet role.

- [ ] **Step 5: Validate outputs before opening private gold.**

Run manifest/schema/G0 checks using public paths only. Only after validation completes may `score_llm_phase1.py` open private G1 for `project_gold_packet_agreement`. Save public validation and private scoring as separately hashed stages.

### Task 12: Build the independent G2 audit, compute GPS/UCR, and enforce the publication fallback

**Files:**

- Modify: `09-experiments/scripts/score_llm_phase1.py`
- Modify: `09-experiments/tests/test_llm_phase1_scoring.py`
- Generate: `09-experiments/llm_compiler_v0.2/generated/g2-audit/<audit_id>/`
- Generate: `04-progress/llm-apt-phase1-experiment-20260715.md`

**Interfaces:**

- `select_g2_panel(test_manifest, seed=2026071503) -> list[str]`
- `build_g2_bundles(panel, outputs, output_dir) -> dict[str, Any]`
- `analyze_g2(annotator_a_csv, annotator_b_csv, public_items) -> dict[str, Any]`
- `score_gps_ucr(outputs, adjudicated_labels, panel) -> dict[str, Any]`

- [ ] **Step 1: Write failing G2 independence and failure-form tests.**

```python
def test_g2_panel_has_two_positive_and_two_null_per_case(self):
    panel = scorer.select_g2_panel(fixture_test_manifest(), seed=2026071503)
    self.assertEqual(24, len(panel))
    for case_id in ("C07", "C08", "C09", "C10", "C11", "C12"):
        roles = [row["packet_role"] for row in panel if row["case_id"].startswith(case_id)]
        self.assertEqual(2, roles.count("positive"))
        self.assertEqual(2, roles.count("null"))

def test_g2_failure_forces_negative_pilot_form_and_blocks_phase2(self):
    decision = scorer.publication_decision({"kappa": 0.62, "unassessable_rate": 0.1})
    self.assertEqual("negative_evaluation_or_interface_pilot", decision["paper_form"])
    self.assertFalse(decision["allow_grounding_claim"])
    self.assertFalse(decision["allow_phase2"])
```

- [ ] **Step 2: Build four blind output packages with independent A/B order.**

Conditions are: Rule compiler; General compiler claims + structured conclusion; Security compiler; General direct. Each annotator receives 24 × 4 = 96 items under independent deterministic shuffle and blind IDs. CSV labels are `supported/partial/unsupported/unassessable`, pointer valid separately, and conclusion-over-ceiling separately. Bundles contain no model name, condition order, private G1 IDs, Rule/LLM scores or other annotator CSV.

- [ ] **Step 3: Keep construction and output audits separate.**

G2 bundle manifest includes the null-construction audit SHA-256 only as provenance. Null construction reviewers do not score model outputs in the same session/protocol; G2 annotators receive source excerpts and blinded outputs, not the earlier yes/no construction sheet.

- [ ] **Step 4: Analyze first-round agreement before adjudication.**

Compute weighted kappa for ordered support labels after separately reporting unassessable, nominal kappa for pointer/ceiling labels, raw agreement and per-condition counts. Third-person adjudication is a second file and never replaces first-round kappa. Do not delete difficult rows.

- [ ] **Step 5: Score and enforce Gates.**

If kappa `<0.70` or unassessable `>0.20`, do not emit GPS/UCR and write the negative/interface-pilot form. If G2 passes, compute per-packet GPS/UCR, per-case means and six-case macro; evaluate Rule and structured/direct 0.05/4-of-6/coverage guards. Only all three Gates may enable positive title/core-contribution wording.

- [ ] **Step 6: Write the Markdown evidence record and final verification.**

The record states independent case count `n=6`, packet and technical-repeat counts, 4-bit limit, contamination status, refusal strata, Rule snapshot hash, G2 first-round and adjudicated results, exact Gate outcomes, negative results, and the ban on generalization/SOTA/actor accuracy. It explicitly states whether Phase 2 remains unauthorized.

```powershell
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest 09-experiments.tests.test_llm_packet_separation 09-experiments.tests.test_llm_phase1_contract 09-experiments.tests.test_llm_phase1_validation 09-experiments.tests.test_llm_phase1_scoring 09-experiments.tests.test_llm_compiler_pilot -v
& 'C:\Users\35393\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s 09-experiments\tests -p 'test_*.py'
git diff --check
git diff --name-only -- 09-experiments/scripts/run_mvp.py 09-experiments/real_cases 08-writing/paper-main* 08-writing/patent*
```

Expected: all tests report `OK`; forbidden-file diff is empty; Markdown wording matches Gate status.

---

## Reviewer Requirement Traceability

| Reviewer item | Locked implementation |
|---|---|
| R1 Admission ≠ G1 | Task 1 contract + Task 5 function signature and mutation-invariance test |
| R2 GPS multi-gold | Task 7 eight-field NFKC/strip/collapse/casefold exact match against any acceptable gold |
| R3 Rule calibration/freeze | Task 6 development-only proxy report and pre-LLM hash snapshot |
| R4 Null vs G2 separation | Task 4 two-person construction audit; Task 12 independent post-model blind audit |
| R5 G2 failure paper form | Task 7 naming downgrade and Task 12 `negative_evaluation_or_interface_pilot` |
| R6 Four repeat conditions | Task 1 exact config list; Task 8/11 full structured two-stage hash chain |
| Hardware/pollution/refusal | Tasks 10–11 model/runtime lock, 24h/30GB Gate, contamination `unknown`, refusal strata |
| Paper A/B isolation | Global constraints, Task 9 forbidden diff, Task 12 Markdown-only record |

## Self-Review Checklist

- [ ] Every v0.2 Phase 1 deliverable maps to a task; RQ3/RQ4 remain absent.
- [ ] No plan step allows G1/private gold in admission or structured stage 2.
- [ ] No test-output feedback path can modify Rule, prompts, packets, matching fields or thresholds.
- [ ] Null construction and G2 are distinct people/protocol/files and distinct time points.
- [ ] GPS/UCR names are impossible without a valid G2 Gate.
- [ ] Four repeat conditions and 448-call arithmetic are exact; structured repeats bind both stages.
- [ ] Pre-model tasks require no new package and end at HARD STOP A.
- [ ] No command modifies `run_mvp.py`, real cases, Paper A, patent text or frozen results.
- [ ] No DOCX/PPT/PDF generation appears in the plan.

## Execution Handoff

Plan review is the current deliverable. After user approval, execute Tasks 1–9 under `superpowers:executing-plans` (or task-by-task review under `superpowers:subagent-driven-development`) and stop at HARD STOP A. Tasks 10–12 require a second, explicit authorization after the pre-model readiness report is reviewed.
