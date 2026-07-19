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

The verified public-source metadata provides a conservative upper bound of 39
candidate chain definitions before raw-artifact and overlap auditing. This is
not 39 recruited blind cases. A 2026 preprint describes 50 additional unique
scenarios but exposes no verifiable public data artifact from its article
page, so those scenarios are excluded from the current public-artifact count.
Even if all 50 later became available and passed intake, the combined upper
bound would be 89, still below the frozen target of 96.

The next valid step is therefore continued source acquisition or a
prospectively revised clustered collection design before any C13+ outcome is
opened. Pseudoreplication cannot be used to fill the gap.
