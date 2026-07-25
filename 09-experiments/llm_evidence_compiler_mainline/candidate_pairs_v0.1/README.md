# Label-blind candidate pairs v0.1

This directory stores only the committed contract, README and counts/hash audit
for the authorized 1,500-example candidate dataset. Pair payloads are written
under Git-ignored `local-data/` and must not be committed or pushed.

Passing this non-token Gate does not authorize a tokenizer, Qwen weights,
training, inference or M3 integration.

Current status (2026-07-19): the user approved the v0.2 Zeek quota amendment,
and the constructor passed the complete non-token data Gate. The Git-ignored
payload contains exactly 1,200 train and 300 training-validation examples. The
committable counts/hash audit is `generated/data-gate-audit-v0.1.json`; a second
independent construction was byte-identical and is recorded in
`generated/determinism-audit-v0.1.json`.

The historical v0.1 fail-closed capacity evidence remains in
`generated/preflight-failure-audit-v0.1.json`. The formal data Gate is still
false because the tokenizer-length Gate remains pending and unauthorized.
