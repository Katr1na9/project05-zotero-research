# LLM evidence compiler label-blind candidate pairs — 2026-07-19

Status: `passed_non_token_data_gate_token_gate_pending`

## Outcome

The authorized v0.2 constructor completed one label-blind, pointer-bounded
candidate dataset with exactly 1,500 examples. Pair payloads remain local under
the Git-ignored `candidate_pairs_v0.1/local-data/` directory. Only contracts,
source code, tests, counts and hashes are eligible for commit and push.

| Split | Supported | Pointer-unsupported | Total |
|---|---:|---:|---:|
| Train | 600 | 600 | 1,200 |
| Training-validation | 150 | 150 | 300 |
| Total | 750 | 750 | 1,500 |

Train contains 150 supported and 150 pointer-unsupported examples from each of
CAM-LDS, BETH, SOCBED and Atomic. Training-validation contains 75 + 75 from each
of Loghub Linux and Zeek non-PCAP. There is no family overlap between splits.

## Zeek amendment resolution

The v0.1 run correctly failed before output because Zeek's frozen N2 quota was
25 while the exact one-to-one capacity was four. After explicit user approval,
v0.2 changed only Zeek's negative allocation to N1/N2/N3 = 36/4/35. Counts,
families, split assignments and proof requirements remained unchanged.

The resulting validation generator totals are N1/N2/N3 = 61/29/60. The largest
share is 0.4067, below the 0.5 cap. Train remains N1/N2/N3/N4 = 150 each.

## Audit results

- unique example IDs: 1,500/1,500;
- mechanical negative proofs: 750/750 passed;
- pointer audit: 1.0;
- source-modality audit: 1.0;
- same-packet negative fraction: 1.0 in both splits;
- protected exact/near matches: 0/0 (`maximum_jaccard=0.6585 < 0.85`);
- forbidden supervision keys: none;
- TTP identifier values: none;
- BETH `sus`/`evil` values read: false; used: false;
- BETH rows retained: 2,000; standalone normalized records written: false;
- exact duplicate removals: Zeek 1, all other historical families 0.

The canonical example digest is
`B2B1620B40BF7CEC94FD08EB4692CE7212FEB40E6A0E92228AB739B4A8DFB882`.
The data-gate audit SHA-256 is
`E495DC901DD5247C04401646389B1300315CE8541FB30428B2DDDECC2308DAB5`.

## Determinism

A second independent construction with the same frozen inputs and code produced
byte-identical gzip files:

- `train.jsonl.gz`: `CEB1B12B42BC702E8DC403195682E6FFC37DA2E9E5204550C1E6C9CAADAC5FC9`;
- `training-validation.jsonl.gz`: `7607F79387CD2139640B2DB323C45C87815D2E8780B84D979092432ADAFBF552`.

The pair-manifest digest matched at
`C13CFF9E667C460B933D29B9B5519A73A58FF252062AF1573E2799E26BB10B6C`.
The reproduction payload was deleted after comparison; the counts/hash audit is
retained with SHA-256
`5FDDC84DC270F7946F7EC0651662E2C69442D0A98472F46BD87A442EE13059A2`.

## Boundary

`non_token_data_gate_passed=true`, but `formal_data_gate_passed=false` and
`token_gate_status=pending_not_authorized`. No tokenizer or model was downloaded
or used; no runtime was installed or changed; no training, inference, C07–C12
model execution or M3 integration occurred. Paper A, `run_mvp.py` and frozen
case/result artifacts were not modified.

## Verification

The dedicated constructor suite passed 8 tests and 4 subtests. The inherited
candidate-edge builder suite passed 18 tests and 4 subtests. A broader
LLM-evidence-compiler selection passed 154 tests and 180 subtests with one skip.

That broader run also reproduced three unrelated baseline failures: a frozen
citation-report hash mismatch, a worktree-relative historical-record path that
incorrectly nests `.worktrees`, and a frozen WP2 snapshot hash mismatch. None of
the three failing artifacts is modified by this work. They were retained and
reported instead of rewriting frozen evidence to make the suite green.
