# LLM evidence compiler candidate-edge verification implementation plan v0.1

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` and `superpowers:test-driven-development` task-by-task. Subagents are not used unless the user explicitly requests them. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and audit the dependency-free candidate-edge verification contract that replaces invalid packet-level null supervision with pointer-bounded `supported | unsupported_by_bound_pointer | abstain` supervision.

**Architecture:** Source-specific field maps first prove positive candidate edges directly from normalized public record fields. Four deterministic negative generators then produce pointer-bounded counterexamples with independently verifiable proof objects; a separate read-only auditor measures whether the historical proposal pool can satisfy the non-token data gate without creating formal pairs. Authority and readiness artifacts remain fail-closed and do not authorize tokenizer, model, environment, training, or formal inference work.

**Tech Stack:** Python 3.11 standard library, JSON/JSONL/GZip/SHA-256, JSON Schema draft 2020-12, `unittest`, existing `jsonschema` dependency.

## Global constraints

- Work in the main repository because the user explicitly made this compiler a Project05 mainline component; do not alter the historical `codex/llm-apt-phase1` branch.
- Read the historical normalized corpus only from `.worktrees/llm-apt-phase1/09-experiments/llm_finetuning_v0.3/generated/exclusion-passed-records/`; do not copy its raw corpus into the mainline tree.
- Do not reinterpret any legacy `packet_role=null` or `null_eligible_candidate=true` row as a candidate-edge negative.
- A negative label means only “the bound source record does not support this candidate”; it never means the event is false in the world, the host is benign, or the packet is empty.
- Do not download a corpus, tokenizer, Qwen weight, or dependency; do not install or modify an environment; do not train or run formal inference.
- Do not modify `run_mvp.py`, frozen cases, frozen results, Paper A result claims, patent text, or M3 runtime behavior.
- Do not generate DOCX, PPTX, or PDF. Plans and progress remain Markdown/JSON.
- Do not stage, commit, or push until the user explicitly authorizes the current changes; never use `git add .` or `git add -A`.
- Every production behavior is implemented through a red-green TDD cycle. A passing legacy test does not count as the required red observation.
- The non-token audit must fail when train has fewer than four G0-positive source families or training-validation has fewer than two G0-positive source families, even if total candidate count is sufficient.

---

### Task 1: Freeze implementation authority without granting model execution

**Files:**

- Create: `08-writing/llm-evidence-compiler-candidate-verification-amendment-v0.1-20260718.md`
- Create: `09-experiments/llm_evidence_compiler_mainline/contracts/candidate-edge-verification-contract-v0.1.json`
- Create: `09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.5.json`
- Create: `09-experiments/tests/test_llm_evidence_compiler_candidate_training.py`

**Interfaces:**

- Consumes: the frozen draft amendment, draft contract, `authority-lock-v0.4.json`, and the user's instruction to continue dependency-free implementation.
- Produces: an authority chain in which `candidate_edge_dependency_free_implementation=true`, while `formal_candidate_pair_construction`, tokenizer/model acquisition, runtime changes, training, inference, M3 runtime integration, and frozen-file mutation remain false or forbidden.

- [ ] **Step 1: Write a failing authority test.**

```python
def test_v05_authorizes_only_dependency_free_candidate_edge_work(self):
    authority = load_json(CONTRACT_ROOT / "authority-lock-v0.5.json")
    self.assertTrue(authority["candidate_verification_amendment"]["authority_granted"])
    self.assertTrue(authority["candidate_verification_amendment"]["dependency_free_implementation_allowed"])
    self.assertFalse(authority["candidate_verification_amendment"]["formal_candidate_pair_construction_allowed"])
    self.assertTrue({"tokenizer_download", "model_download", "formal_training", "formal_inference"} <= set(authority["not_authorized"]))
```

- [ ] **Step 2: Run the named test and confirm `authority-lock-v0.5.json` is missing.**

Run: `python -m unittest 09-experiments.tests.test_llm_evidence_compiler_candidate_training.CandidateTrainingAuthorityTests.test_v05_authorizes_only_dependency_free_candidate_edge_work -v`

Expected: `ERROR` caused by the missing v0.5 authority file, not an import typo.

- [ ] **Step 3: Add the approved amendment, approved contract, and hash-linked v0.5 authority.**

The approved contract must retain exactly these labels and negative semantics:

```json
{
  "labels": ["supported", "unsupported_by_bound_pointer", "abstain"],
  "negative_semantics": {
    "world_false_claim": false,
    "benign_or_normal_claim": false,
    "whole_packet_empty_claim": false
  },
  "formal_candidate_pair_construction_allowed": false
}
```

- [ ] **Step 4: Run the authority test and the existing draft-authority tests.**

Run: `python -m unittest 09-experiments.tests.test_llm_evidence_compiler_candidate_training.CandidateTrainingAuthorityTests 09-experiments.tests.test_llm_evidence_compiler_candidate_verification_draft -v`

Expected: all named tests pass; v0.4 and its hashed draft files remain byte-identical.

---

### Task 2: Add schemas, source field maps, and G0-positive validation

**Files:**

- Create: `09-experiments/data_schema/candidate_edge_training.schema.json`
- Create: `09-experiments/data_schema/pointer_bounded_negative_proof.schema.json`
- Create: `09-experiments/llm_evidence_compiler_mainline/field_maps/v0.1/source-field-maps.json`
- Create: `09-experiments/llm_evidence_compiler_mainline/field_maps/v0.1/field-map-lock.json`
- Create: `09-experiments/scripts/build_candidate_edge_training.py`
- Modify: `09-experiments/tests/test_llm_evidence_compiler_candidate_training.py`

**Interfaces:**

- `load_field_maps(path: Path, lock_path: Path) -> dict[str, Any]`
- `record_sha256(record: dict[str, Any]) -> str`
- `validate_g0_candidate(record: dict[str, Any], candidate: dict[str, Any], field_maps: dict[str, Any]) -> dict[str, Any]`
- `build_supported_example(record: dict[str, Any], candidate: dict[str, Any], field_maps: dict[str, Any]) -> dict[str, Any]`

`validate_g0_candidate` returns a report with `eligible`, `template_id`, and sorted `reason_codes`. It accepts only exact field reads or named frozen transforms such as `join_host_port`; it rejects constants that invent a host instance, TTP/path/scenario supervision, absent provenance, pointer mismatch, and source families without an approved template.

- [ ] **Step 1: Write failing schema and G0 tests.**

```python
def test_atomic_executed_candidate_is_g0_supported(self):
    report = module.validate_g0_candidate(atomic_record(), atomic_candidate(), field_maps())
    self.assertTrue(report["eligible"])
    self.assertEqual("atomic_process_executed_command_v1", report["template_id"])

def test_cam_placeholder_host_is_not_a_g0_positive(self):
    report = module.validate_g0_candidate(cam_record(), cam_candidate(), field_maps())
    self.assertFalse(report["eligible"])
    self.assertIn("explicit_subject_field_missing", report["reason_codes"])

def test_legacy_null_cannot_be_reinterpreted(self):
    with self.assertRaisesRegex(ValueError, "legacy packet null"):
        module.build_supported_example(loghub_null_record(), {}, field_maps())
```

- [ ] **Step 2: Run the three named tests and confirm import/file failures.**

Expected: failure because the schemas/module/field-map lock do not exist.

- [ ] **Step 3: Implement the two schemas and minimal G0 field-map evaluator.**

The field map must explicitly cover all six historical families. Atomic, SOCBED, and Zeek may define eligible templates. CAM-LDS must be declared `g0_ineligible` because its proposal uses an unbound `host` placeholder; Splunk and Loghub must be declared `g0_ineligible` because they have no legacy observation candidate. The lock hashes the canonical source-field-map bytes.

- [ ] **Step 4: Run schema/G0 tests and confirm pass.**

Run: `python -m unittest 09-experiments.tests.test_llm_evidence_compiler_candidate_training.CandidateTrainingSchemaAndG0Tests -v`

Expected: all G0 tests pass, including negative cases for altered payload fields, pointer mismatch, missing provenance, and legacy null rows.

---

### Task 3: Implement N1–N4 and fail-closed proof validation

**Files:**

- Modify: `09-experiments/scripts/build_candidate_edge_training.py`
- Modify: `09-experiments/tests/test_llm_evidence_compiler_candidate_training.py`

**Interfaces:**

- `generate_n1_object_swap(positive: dict, donor: dict, field_maps: dict) -> dict`
- `generate_n2_pointer_swap(positive: dict, bound_record: dict, field_maps: dict) -> dict`
- `generate_n3_predicate_incompatibility(positive: dict, replacement_predicate: str, field_maps: dict) -> dict`
- `generate_n4_time_mismatch(positive: dict, donor: dict, field_maps: dict) -> dict`
- `validate_negative_example(example: dict, record_index: dict[str, dict], field_maps: dict) -> dict[str, Any]`

All generators require the same source family. N1, N2, and N4 additionally require the same packet key (`source_family_id + document_id`), and they record both source hashes. The validator recomputes support from the bound record and rejects proofs that claim world falsity, use path/scenario supervision, omit a check, cross source families, or still support the altered candidate.

- [ ] **Step 1: Write one positive and at least one adversarial failing test for each generator.**

```python
def test_n2_pointer_swap_is_pointer_bounded_and_revalidated(self):
    example = module.generate_n2_pointer_swap(supported_a(), record_b(), field_maps())
    report = module.validate_negative_example(example, record_index(), field_maps())
    self.assertTrue(report["valid"])
    self.assertEqual("unsupported_by_bound_pointer", example["support_decision"])
    self.assertFalse(example["negative_proof"]["mechanical_checks"]["world_false_claim_made"])

def test_cross_family_donor_fails_closed(self):
    with self.assertRaisesRegex(ValueError, "source family"):
        module.generate_n1_object_swap(supported_a(), cross_family_donor(), field_maps())
```

- [ ] **Step 2: Run generator tests and verify they fail because N1–N4 are absent.**

- [ ] **Step 3: Implement minimal generators and independent proof revalidation.**

Do not add automatic corpus-wide pair construction. Generator functions operate only on explicit records supplied by a caller or test.

- [ ] **Step 4: Run generator/proof tests and the existing mechanical admission tests.**

Run: `python -m unittest 09-experiments.tests.test_llm_evidence_compiler_candidate_training.CandidateNegativeGeneratorTests 09-experiments.tests.test_llm_evidence_compiler_admission -v`

Expected: all tests pass; the formal admission path remains unchanged.

---

### Task 4: Run a read-only historical quantity audit and freeze a failed readiness result

**Files:**

- Modify: `09-experiments/scripts/build_candidate_edge_training.py`
- Modify: `09-experiments/tests/test_llm_evidence_compiler_candidate_training.py`
- Create: `09-experiments/llm_evidence_compiler_mainline/qwen-candidate-edge-readiness-v0.1.json`
- Create: `04-progress/llm-evidence-compiler-candidate-verification-implementation-v0.1-20260718.md`

**Interfaces:**

- `audit_historical_proposals(records_root: Path, field_maps: dict[str, Any]) -> dict[str, Any]`
- CLI: `python 09-experiments/scripts/build_candidate_edge_training.py audit --records-root <historical-root> --field-maps <maps> --field-map-lock <lock> --output <readiness.json>`

The auditor reads exclusion-passed `.jsonl.gz` records, validates existing observation proposals only, and emits counts/reasons without outputting candidate pairs. Gate status must be `failed_non_token_data_gate` unless train has at least four G0-positive families, validation has at least two family-disjoint G0-positive families, and at least 600/150 G0 positives respectively.

- [ ] **Step 1: Write a failing audit test with sufficient counts but insufficient families.**

```python
def test_quantity_does_not_override_source_family_gate(self):
    report = module.evaluate_non_token_gate(train_counts={"a": 700}, validation_counts={"b": 200})
    self.assertEqual("failed_non_token_data_gate", report["status"])
    self.assertIn("train_g0_positive_families_below_4", report["failure_reasons"])
    self.assertIn("validation_g0_positive_families_below_2", report["failure_reasons"])
```

- [ ] **Step 2: Run the named test and confirm missing evaluator failure.**

- [ ] **Step 3: Implement read-only GZip audit and atomic no-overwrite JSON output.**

The report must record source-root hash metadata, per-family total/legacy-null/proposal/G0 counts, ineligibility reasons, and explicit false flags for corpus copy, pair construction, tokenizer, model, runtime, and training use.

- [ ] **Step 4: Run the historical audit against the old worktree.**

Run:

```powershell
python 09-experiments/scripts/build_candidate_edge_training.py audit `
  --records-root .worktrees/llm-apt-phase1/09-experiments/llm_finetuning_v0.3/generated/exclusion-passed-records `
  --field-maps 09-experiments/llm_evidence_compiler_mainline/field_maps/v0.1/source-field-maps.json `
  --field-map-lock 09-experiments/llm_evidence_compiler_mainline/field_maps/v0.1/field-map-lock.json `
  --output 09-experiments/llm_evidence_compiler_mainline/qwen-candidate-edge-readiness-v0.1.json
```

Expected: command exits zero because the audit completed, while report status is `failed_non_token_data_gate`; no training packet or pair file is created.

- [ ] **Step 5: Run fresh verification.**

Run targeted: `python -m unittest 09-experiments.tests.test_llm_evidence_compiler_candidate_training -v`

Run mainline: `python -m unittest discover -s 09-experiments/tests -p 'test_llm_evidence_compiler*.py' -v`

Run full experiments: `python -m unittest discover -s 09-experiments/tests -v`

Expected: new targeted tests and the 103-test mainline baseline pass. Any pre-existing full-suite failures must be reported separately and must not be “fixed” by changing frozen data.

- [ ] **Step 6: Update the Markdown progress record with exact counts and verification output.**

The record must state that model/runtime work remains unauthorized and identify the next scientifically valid branch: add independent same-modality positive source families through a new source gate, or accept smoke-only adapter status.

## Self-review

- Spec coverage: authority, schemas, source field maps, N1–N4, proof validation, source-family/modality gates, legacy-null separation, and execution hard stops all map to Tasks 1–4.
- Placeholder scan: no `TBD`, `TODO`, “similar to”, or unspecified implementation step remains.
- Type consistency: all Task 3 generators consume Task 2 supported examples; Task 4 consumes Task 2 field maps but never invokes Task 3 to build formal pairs.
- Scope boundary: no tokenizer/model/environment/training/M3/frozen-result operation appears in any authorized task.
