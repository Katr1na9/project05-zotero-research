# M3* final-blind data intake v0.1

This directory is an input-governance artifact, not a paper or patent draft.
It records only public source metadata and candidate counts. No C13+ labels,
cost values, model outputs, or ground truth were opened or stored here.

## Counting rule

One independent case means one complete campaign execution with a unique
attack-chain definition and a unique telemetry capture. A host slice, time
slice, masking condition, sensor view, or parameter-only rerun is not a new
case. The 45 experimental conditions remain paired repeated measurements
inside a case.

The source matrix uses three deliberately different counts:

- `reported_attack_sessions`: the publisher's session/run count.
- `conservative_unique_chain_upper_bound`: the largest count defensible before
  raw-artifact hashing and cross-source overlap review.
- `hash_bound_intake_cases`: cases that have actually passed the C13+ identity,
  isolation, and hash checks. This remains zero.

## Current result

The verified public-source metadata now provides a conservative upper bound of
70 candidate chain definitions before raw-artifact and overlap auditing. This
is not 70 recruited blind cases. The increase comes from CAPD (23), AVIATOR
(7), and the APT Sandworm Dataset (1). CAPD's paper/repository disagreement
(23 versus 24 campaigns) is resolved conservatively at 23, AVIATOR's 16 ZIP
files collapse to seven unique chain definitions after representation and
implementation variants are removed, and Sandworm is one continuous campaign.

A 2026 preprint describes 50 additional unique scenarios but exposes no
verifiable public data artifact from its article page, so those scenarios
remain excluded from the current public-artifact count. If all 50 later became
available and all 120 metadata candidates survived download, identity,
isolation, and overlap checks, the upper bound would exceed the target by 24.
That hypothetical surplus does not replace the frozen 96-case intake gate.

The next valid step is download/hash intake and cross-source overlap auditing
for the 70 public candidates while continuing source acquisition for the
remaining metadata gap of 26. No C13+ outcome may be opened, and
pseudoreplication cannot be used to fill the gap.
