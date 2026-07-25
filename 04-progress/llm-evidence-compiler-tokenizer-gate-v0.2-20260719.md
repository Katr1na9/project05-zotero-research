# LLM evidence compiler tokenizer-length Gate v0.2 — 2026-07-19

Status: `formal_data_gate_passed_model_and_training_gates_closed`

## Outcome

The user-approved v0.2 serialization and same-family length-aware reselection
completed successfully. The regenerated local dataset contains exactly 1,500
examples: 1,200 train and 300 training-validation, with 750 supported and 750
pointer-unsupported examples. Six source families, split assignments, the
approved Zeek allocation and every N1–N4 quota remain unchanged.

Pair payload remains under the Git-ignored `candidate_pairs_v0.2/local-data/`.
No corpus, pair payload, tokenizer file, wheel, runtime or credential is
eligible for commit.

## Length-aware selection

The model-visible v0.2 record keeps complete payload, candidate and bound
pointer, plus the complete support decision, normalized edge and output
pointer. It removes only provenance/license hashes and repeated operational
metadata that the model does not need.

Before admission, both members of a supported/unsupported pair had to fit the
1,024-token limit. The deterministic selector rejected 1,541 candidate
serialization attempts: 1,136 SOCBED and 405 Atomic. These were pre-admission
attempts, not deletions from a frozen dataset. CAM-LDS, BETH, Loghub and Zeek
required no length rejection. Selection never crossed a family or generator
quota and never truncated, summarized or rewrote an accepted payload.

## Data and leakage audits

- examples: 1,500; unique IDs: 1,500;
- supported / pointer-unsupported: 750 / 750;
- mechanical negative proofs: 750/750 passed;
- pointer and source-modality pass fractions: 1.0 / 1.0;
- protected exact / near matches: 0 / 0;
- maximum protected Jaccard: 0.587 below the frozen 0.85 threshold;
- forbidden supervision and TTP identifier values: none;
- BETH label values read or used: false / false;
- pair construction reproduced byte-identically.

The train gzip SHA-256 is
`61B9F3C724CB65A3A2ED8839ED36881A717DC906F32267D7CDED510C2F01B82B`;
training-validation remains
`7607F79387CD2139640B2DB323C45C87815D2E8780B84D979092432ADAFBF552`.

## Independent tokenizer Gate

All admitted examples were independently rendered and counted again. No
selection was permitted during this audit.

| Scope | Count | p50 | p95 | Max | Over 1024 |
|---|---:|---:|---:|---:|---:|
| Overall | 1,500 | 589 | 881 | 1,021 | 0 |
| Train | 1,200 | 611 | 897 | 1,021 | 0 |
| Training-validation | 300 | 492 | 580 | 659 | 0 |

The full token audit reproduced byte-identically at SHA-256
`9F8B9A4DA5CC2A79EB5845ADE61C8A41D4D78B5DFDA423DA0187171F977E72DC`.
Thus the formal data Gate is now passed.

## Boundary and next Gate

Passing the data Gate does not authorize model weights or training. No model
configuration or weights were downloaded; Transformers, Torch, PEFT and
bitsandbytes were not installed; no adapter, optimizer, training, inference,
C07–C12 model execution or M3 integration occurred. Paper A, `run_mvp.py` and
frozen case/results were not modified.

The next action requires separate user authorization and should begin with a
bounded runtime/weight/smoke-training plan, not formal training.

## Verification

The four directly affected suites passed 53 tests. The focused authority,
constructor and tokenizer suites passed 21 tests.

A broader compiler discovery ran 152 tests with one skip and reproduced the
same three pre-existing worktree/baseline failures reported before this change:
one citation-report hash mismatch, one worktree-relative historical-record root
error and one frozen WP2 snapshot sidecar mismatch. None of those artifacts is
modified by v0.2, and they were not rewritten to make the broader suite green.
