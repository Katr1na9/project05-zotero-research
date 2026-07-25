# LLM evidence compiler positive-remap implementation plan v0.1

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` and `superpowers:test-driven-development` task-by-task. Subagents are not used unless the user explicitly requests them.

**Goal:** Activate CAM-LDS and Loghub as mechanically grounded positive-edge families through new versioned parsers, then freeze a read-only remap audit without creating training pairs or downloading BETH.

**Architecture:** A v0.2 source-map version adds named parser transforms for Linux Audit EXECVE/PROCTITLE and Loghub OOM killed-process lines. The candidate-edge validator recomputes each parsed candidate from the bound record, and a separate read-only audit measures exact counts while preserving zero credit for legacy null labels.

**Tech Stack:** Python 3.11 standard library (`re`, `shlex`, `bytes.fromhex`, `gzip`, JSON/SHA-256), JSON Schema, `unittest`.

## Global constraints

- Preserve v0.1 field maps and readiness bytes; create v0.2 files instead of editing immutable locks.
- No corpus download, dependency/environment change, candidate-pair output, tokenizer/model access, training, inference or M3 runtime integration.
- CAM candidates may use only the bound message’s audit timestamp and explicit EXECVE arguments or decoded PROCTITLE bytes.
- Loghub candidates may use only exact `host kernel: Out of Memory: Killed process PID (name).` message fields.
- Old placeholder CAM candidates remain rejected. Old `null_eligible_candidate` values receive zero negative credit and are never renamed.
- BETH remains metadata-only and not download-authorized.
- Do not stage, commit or push without explicit user authorization.

### Task 1: Freeze positive-remap authority

**Files:**

- Create: `08-writing/llm-evidence-compiler-positive-remap-amendment-v0.1-20260718.md`
- Create: `09-experiments/llm_evidence_compiler_mainline/contracts/positive-remap-contract-v0.1.json`
- Create: `09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.6.json`
- Create: `09-experiments/tests/test_llm_evidence_compiler_positive_remap.py`

**Interface:** v0.6 sets `positive_remap_dependency_free_implementation_allowed=true` and keeps `beth_download_allowed=false`, `formal_candidate_pair_construction_allowed=false`, and all model/runtime flags false.

- [ ] Write authority/hash-chain tests.
- [ ] Run tests and observe missing v0.6 authority failure.
- [ ] Add amendment, contract and v0.6 hash chain.
- [ ] Run v0.6 plus v0.5 authority tests and confirm pass.

### Task 2: Add v0.2 maps and exact record parsers

**Files:**

- Create: `09-experiments/llm_evidence_compiler_mainline/field_maps/v0.2/source-field-maps.json`
- Create: `09-experiments/llm_evidence_compiler_mainline/field_maps/v0.2/field-map-lock.json`
- Modify: `09-experiments/scripts/build_candidate_edge_training.py`
- Modify: `09-experiments/tests/test_llm_evidence_compiler_positive_remap.py`

**Interfaces:**

- `parse_linux_audit_execve_candidate(record: dict) -> dict | None`
- `parse_linux_audit_proctitle_candidate(record: dict) -> dict | None`
- `parse_loghub_oom_candidate(record: dict) -> dict | None`
- `propose_record_candidates(record: dict, field_maps: dict) -> list[dict]`
- `validate_g0_candidate(...)` accepts a `candidate_parser` template only when the recomputed candidate is byte-equivalent.

- [ ] Write failing tests for quoted EXECVE, hex PROCTITLE, malformed hex, exact Loghub parsing, pointer retention, and altered candidate rejection.
- [ ] Run and observe missing parser failures.
- [ ] Implement minimal parsers and v0.2 maps.
- [ ] Run parser/G0 tests and confirm pass.

### Task 3: Freeze the read-only remap audit

**Files:**

- Modify: `09-experiments/scripts/build_candidate_edge_training.py`
- Modify: `09-experiments/tests/test_llm_evidence_compiler_positive_remap.py`
- Create: `09-experiments/llm_evidence_compiler_mainline/qwen-positive-remap-readiness-v0.1.json`
- Create: `04-progress/llm-evidence-compiler-positive-remap-v0.1-20260718.md`

**Interface:** `audit_positive_remap(records_root, field_maps, baseline_readiness) -> dict` reads old GZip records and outputs counts only.

- [ ] Write a failing readiness test requiring CAM `166`, Loghub `193`, projected train families `3`, projected validation families `2`, and formal gate `false`.
- [ ] Run and observe missing audit/report failure.
- [ ] Implement read-only remap audit and no-overwrite CLI subcommand.
- [ ] Generate the frozen report; do not generate record or pair files.
- [ ] Run focused, 121-test mainline, and full experiment suites.
- [ ] Record exact verification and the remaining BETH source-gate blocker in Markdown.

## Self-review

- The plan adds no new dataset and does not use old null labels as negatives.
- Every parser is record-local, deterministic and pointer-preserving.
- Family diversity remains fail-closed: remap alone cannot satisfy train 4-family Gate.
- BETH acquisition remains a separate future user decision.
