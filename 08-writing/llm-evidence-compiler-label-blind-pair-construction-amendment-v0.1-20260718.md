# LLM evidence compiler label-blind pair-construction amendment v0.1

Status: `authorized_candidate_pair_construction_only`
Date: 2026-07-18
Parent authority: `authority-lock-v0.9.json`

## User decision

The user approved construction and audit of a label-blind candidate training
dataset after the BETH source Gate passed. This authorization ends at the
non-token data Gate. It does not authorize tokenizer/model downloads, runtime
changes, QLoRA training, inference or M3 integration.

## Frozen design

The dataset contains exactly 1,500 pointer-bounded examples:

| Split | Positive families | Supported | Pointer-unsupported | Total |
|---|---|---:|---:|---:|
| train | Atomic, SOCBED, CAM-LDS, BETH | 600 (150/family) | 600 | 1,200 |
| training-validation | Loghub Linux, Zeek non-PCAP | 150 (75/family) | 150 | 300 |

Every supported example is derived from explicit fields in one bound source
record. Every negative means only that the candidate is unsupported by its
current bound pointer. It does not assert that the event is false in the world,
benign, normal or absent from the wider packet.

## Label-blind boundary

The constructor must not use or emit `sus`, `evil`, attack/benign labels,
original split membership, filename, host role, attack narrative, actor,
tactic, technique ID or path/scenario-derived supervision. Changing only BETH
`sus`/`evil` values must leave record IDs, selection, examples and dataset
digest unchanged.

BETH rows are converted directly into pair-embedded source snapshots. The
three fields absent from the real v3 host file are not imputed. No standalone
normalized BETH corpus may be written.

## Frozen deterministic quotas

Train negative-generator quotas are:

- CAM-LDS: 150 × N4 explicit timestamp mismatch;
- Atomic: 50 × N1 object swap, 50 × N2 pointer swap, 50 × N3 predicate incompatibility;
- SOCBED: 50 × N1, 50 × N2, 50 × N3;
- BETH: 50 × N1, 50 × N2, 50 × N3.

Training-validation quotas are 25 × N1, 25 × N2 and 25 × N3 for each of
Loghub and Zeek. Generator N1/N2/N4 donors must be from the same source family
and packet. N3 uses a frozen field-map incompatibility on the same record.

Selection is deterministic, without randomness or model scoring. A source
family that cannot meet its exact positive or generator quota fails closed; no
cross-family substitution or quota reduction is allowed.

An exact byte-equivalent normalized record repeated with the same pointer may
be removed once by full-record SHA-256 before selection, with the removed count
reported per family. Content-equivalent records with different pointers are
not duplicates and may not be collapsed.

## Required audits

1. All six required family/split assignments and frozen source hashes match.
2. Train and validation families are disjoint.
3. Supported fraction is exactly 0.5 in each split.
4. At least three negative generator families are present; no generator is
   more than 0.5 of negatives.
5. All negatives pass the mechanical proof validator.
6. All examples retain exact source pointers and matching modalities.
7. Protected exact/near matches are zero.
8. Forbidden supervision keys and TTP identifiers are absent.
9. Pair files are deterministic gzip JSONL in a Git-ignored local directory;
   only counts, hashes and audit metadata may be committed.
10. Exact-record duplicate removals are reported; no fuzzy/content-only
    deduplication is allowed.

The tokenizer-length Gate remains `pending_not_authorized`. Passing this
amendment means only `non_token_data_gate_passed=true`; the formal data Gate
remains false until the separately authorized tokenizer audit passes.

## Still prohibited

No new corpus retrieval, dependency installation, Qwen/tokenizer download,
QLoRA training, formal inference, C07-C12 model execution, M3 runtime
integration, `run_mvp.py` change, Paper A result change or frozen-result
rewrite is authorized.
