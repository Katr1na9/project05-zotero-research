# LLM evidence compiler label-blind pair-construction amendment v0.2

Status: `authorized_candidate_pair_construction_only`

Date: 2026-07-19

Parent authority: `authority-lock-v0.10.json`

## User decision

The user explicitly approved the v0.2 Zeek quota amendment on 2026-07-19.
This approval authorizes a revised non-token candidate-pair construction run
only. It does not authorize a tokenizer/model download, training, inference or
M3 runtime integration.

## Why an amendment is required

The authorized v0.1 constructor stopped before writing pair payloads because the
Zeek training-validation family cannot satisfy its frozen quota of 25 unique N2
pointer-swap negatives. This is a data-capacity failure, not a model result and
not permission to relax the proof rules.

After the single allowed exact-record duplicate was removed, Zeek contained 482
eligible records in 24 packets. Only one packet contained more than one distinct
observation semantic. Its 437 records split into semantic groups of 435 and 2;
all other packets contained one semantic only. Under the frozen requirements of
same-packet donors, unique supported examples, unique negative example IDs and
one negative per selected positive, the exact N2 capacity is therefore four.
The fifth requested N2 pair correctly failed closed.

The machine-readable evidence is in
`candidate_pairs_v0.1/generated/preflight-failure-audit-v0.1.json`.

## Authorized minimal revision

Change only the Zeek training-validation negative-generator quotas:

| Generator | v0.1 | Authorized v0.2 |
|---|---:|---:|
| N1 object swap | 25 | 36 |
| N2 pointer swap | 25 | 4 |
| N3 predicate incompatibility | 25 | 35 |
| Total | 75 | 75 |

All family, split, positive and total-example quotas remain unchanged. Loghub
remains 25/25/25. The resulting validation split has N1/N2/N3 totals of
61/29/60, so all three generator families remain represented and the largest
generator share is 61/150 = 0.4067, below the frozen 0.5 cap.

An in-memory preflight using the authorized Zeek allocation produced 75 unique
supported plus 75 unique pointer-unsupported examples. All 75 negatives passed
the existing mechanical proof validator. No raw payload, tokenizer, model,
training, inference or M3 runtime was used.

## Boundaries preserved

- no cross-family donor or substitution;
- no reduction of Zeek's 75 positive / 75 negative count;
- no use of labels, path/scenario truth, attack narrative or TTP identifiers;
- no relaxation of same-packet, pointer, modality or proof checks;
- no content-only/fuzzy deduplication;
- no change to train-family quotas, Loghub quotas, Paper A, `run_mvp.py`, M3 or
  frozen results;
- tokenizer/model download, training and inference remain prohibited.
