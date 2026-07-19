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
103 candidate chain definitions before raw-artifact and overlap auditing. This
is not 103 recruited blind cases. In addition to the earlier CAPD (23), AVIATOR
(7), and APT Sandworm Dataset (1) audit, the current increase comes from the
GOOSE power-substation APT dataset (1), Cyber Czech 2019 (1), and Windows-APT
2025 (31). GOOSE and Cyber Czech each describe one campaign despite multiple
stages, days, actions, replicas, and sensor views.

Windows-APT reports 36 scenario definitions and ten repeat executions per
scenario. The 360 executions, 16 period CSV files, combined file, three agents,
and row-level mappings are not independent cases. Its v4 documentation also
identifies five scenario definitions whose technique sets are subset-masked by
larger scenarios, so those five are withheld pending an isolated chain-
definition separability audit. The current conservative contribution is
therefore 31, not 36.

A 2026 preprint describes 50 additional unique scenarios but exposes no
verifiable public data artifact from its article page, so those scenarios
remain excluded from the current public-artifact count. If all 50 later became
available and all 153 metadata candidates survived download, identity,
isolation, and overlap checks, the upper bound would exceed the target by 57.
That hypothetical surplus does not replace the frozen 96-case intake gate.

The metadata gap is now closed with a provisional surplus of seven, but the
hash-bound intake count remains zero. The next valid step is non-consuming
download/hash intake, independent case-identity construction, and cross-source
chain-definition and capture-overlap auditing. Source acquisition continues
only as a reserve against expected attrition. No C13+ outcome may be opened,
and pseudoreplication cannot be used to fill the cohort.
