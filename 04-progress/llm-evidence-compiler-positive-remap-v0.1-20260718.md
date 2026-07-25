# LLM evidence compiler positive-remap implementation v0.1

Status: `completed_with_formal_data_gate_closed`  
Date: 2026-07-18  
Authority: `authority-lock-v0.6.json`

## Outcome

The authorized dependency-free positive-remap phase is complete. Versioned,
record-local parsers now convert explicit CAM-LDS Linux Audit execution records
and Loghub OOM killed-process lines into pointer-bound candidate edges. A
read-only audit reproduced the preregistered counts without rewriting source
records or constructing candidate pairs.

The formal data gate remains closed. The remap raises training diversity from
two to three G0-positive source families and validation diversity from one to
two, but training still requires one independent family. BETH remains a
metadata candidate and is not download-authorized.

## Implemented interfaces

- `parse_linux_audit_execve_candidate(record)` parses the audit timestamp,
  `argc`, and the complete ordered `a0...aN` sequence. Missing, duplicate,
  malformed, undecodable or ambiguous arguments fail closed.
- `parse_linux_audit_proctitle_candidate(record)` hex-decodes the bound
  `PROCTITLE` bytes, requires a nonempty NUL-separated UTF-8 argv sequence, and
  preserves the exact source pointer and audit timestamp.
- `parse_loghub_oom_candidate(record)` accepts only the literal form
  `host kernel: Out of Memory: Killed process PID (name).` and emits a
  record-scoped `system --terminated--> process` candidate.
- `propose_record_candidates(record, field_maps)` dispatches only parsers named
  in immutable v0.2 field maps.
- `validate_g0_candidate(...)` recomputes parser-backed candidates from the
  bound source record and requires canonical byte equivalence. Altered values,
  pointers or extra fields are not admitted.
- `audit_positive_remap(...)` verifies every historical GZip byte count and
  SHA-256 against the frozen v0.1 readiness manifest before counting new
  candidates.
- CLI subcommand `positive-remap-audit` writes atomically and refuses an
  existing output path.

## Frozen read-only result

| Split | Family | Baseline G0 | New parser G0 | Projected G0 |
|---|---|---:|---:|---:|
| train | CAM-LDS | 0 | 166 | 166 |
| train | SOCBED | 683 | 0 | 683 |
| train | Atomic Red Team | 798 | 0 | 798 |
| train | Splunk manifests | 0 | 0 | 0 |
| training-validation | Loghub Linux | 0 | 193 | 193 |
| training-validation | Zeek non-PCAP | 483 | 0 | 483 |

CAM-LDS breakdown:

- `cam_linux_audit_execve_v1`: 59
- `cam_linux_audit_proctitle_hex_v1`: 107

Loghub breakdown:

- `loghub_oom_killed_process_v1`: 193

Projected totals:

- train: 1,647 G0 positives, three source families, maximum 3,294 balanced
  candidate pairs;
- training-validation: 676 G0 positives, two source families, maximum 1,352
  balanced candidate pairs;
- failure reason: `train_g0_positive_families_below_4`;
- `formal_data_gate_passed=false`;
- legacy packet-null negative credit remains exactly zero.

The Loghub candidates are newly derived from literal record content. The old
`null_eligible_candidate` field is ignored and is not relabelled or used as
negative truth.

## TDD and verification evidence

Red states were observed before implementation:

1. missing `field_maps/v0.2/field-map-lock.json`;
2. missing parser and proposal interfaces;
3. missing `audit_positive_remap` and frozen readiness output.

Fresh green verification:

| Scope | Result |
|---|---|
| positive-remap focused suite | 10 passed |
| complete LLM evidence-compiler suite | 131 passed |
| complete `09-experiments/tests` suite | 631 passed, 6 skipped |
| repeated frozen-output command | refused with `FileExistsError` as designed |

## Frozen artifact hashes

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `build_candidate_edge_training.py` | 44,070 | `8E4915C13516946B885B0CEDC1D82A4191E0B3BDB4AF9F2F408B83C4D1E9826F` |
| `test_llm_evidence_compiler_positive_remap.py` | 9,824 | `9F43EF58449418A80E8604D88D78E138A34CB99249D4FCF1CC2920263AC974AE` |
| `field_maps/v0.2/source-field-maps.json` | 4,922 | `507FA301410681E2ADCD5A941368CC10D323CC30F1A33D3A67C105EC7B16BCD8` |
| `field_maps/v0.2/field-map-lock.json` | 282 | `FFDB89F3A5822C2642F2211916492BAC4B9F70EED4339A9776347DDB9294A64A` |
| `qwen-positive-remap-readiness-v0.1.json` | 6,169 | `171736E29958DAAE42B8CF978D7C7F159D2B4A8A6B5025A5046D7CCA5FE645F4` |
| unchanged baseline readiness | 4,985 | `048E578D4C7FCD0EFEC513A62E93152AC5C2037462F3CB36D23A1DEADF5DDFDE` |

## Preserved boundaries

No corpus was downloaded or copied. No normalized source record or historical
readiness file was overwritten. No candidate pair was constructed. No
tokenizer, Qwen weight, model runtime, dependency installation, training,
formal inference or M3 runtime integration occurred. `run_mvp.py`, frozen
cases, frozen results, papers and patents were not modified by this phase.

## Remaining blocker and next gate

The sole non-token family-diversity gap is one independent train family. The
current primary candidate is BETH. The metadata-only decision is now recorded
in `llm-evidence-compiler-beth-metadata-source-decision-v0.1-20260718.md`
(6,426 bytes, SHA-256
`697CD3C056C10C02DAFD4B5A58D44017EA9FA4480D4B8BA2D5FEA501B94ABC71`).
It pins Kaggle version 3, the 928,188,305-byte dataset-level declaration, the
15-file inventory, the API license field and the official CC0 legalcode hash.

That decision still sets `download_authorized=false`. The next gate is a new
authority lock plus explicit user authorization for at most one version-pinned
per-host process CSV under a 512 MiB cap. Until that authorization and the
post-acquisition license/exclusion/parser checks pass, pair construction and
all model work remain closed.
