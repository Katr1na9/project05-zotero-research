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

The verified public-source metadata now provides an upper bound of 112
candidate chain definitions before raw-artifact hashing and overlap auditing.
This is not 112 recruited blind cases. The matrix now separates that total into
three evidence-risk tiers: Tier A contains 11 candidates with an authoritative
artifact and a clear public whole-chain boundary; Tier B contains 91 candidates
whose artifact exists but whose boundary, representation, full-coverage, or
cross-source overlap risk can materially reduce the count; Tier C contains ten
ATLASv2 metadata candidates for which no publisher-controlled original payload
artifact has yet been verified.

Accordingly, the authoritative-artifact-verified upper bound is only 102, six
above the frozen target of 96. This is a thin pre-curation margin, not evidence
that the cohort is recruitable. The high-confidence Tier-A pool is only 11 and
is 85 short of the operational target. The risk split is intentionally more
informative than the headline 112 because it exposes where curator attrition is
likely to occur.

In addition to the earlier sources, the current increase from 108 comes from
the AttackMate Robotdog dataset (at most one chain) and the AInception dataset
(at most three storylines). Robotdog describes one combined physical-cyber
attack, but only robot-unit audit logs are public, so all-device coverage must
be proven by the curator. AInception publishes 15 complete simulations split
across SL100, SL300, and SL700. Those archives are variants or executions of
three storyline definitions, so they contribute three rather than 15.

Windows-APT reports 36 scenario definitions and ten repeat executions per
scenario. The 360 executions, 16 period CSV files, combined file, three agents,
and row-level mappings are not independent cases. Its v4 documentation also
identifies five scenario definitions whose technique sets are subset-masked by
larger scenarios, so those five are withheld pending an isolated chain-
definition separability audit. The current conservative contribution is
therefore 31, not 36.

The reserve pool includes AttackMate (at most three scenario definitions) and two
annual Locked Shields Partners Run captures (at most one each for LSPR23 and
LSPR24). AttackMate/Caldera implementations and their SCP, SSH, and timeout
variants do not expand the three definitions. Zenodo records 18834219 and
19810174 share concept record 17639279; the newer record adds Atomic Red Team
implementations and replaces, rather than duplicates, the older release.
Locked Shields flows, packets, hosts, labels, and attack-narrative entries
remain within annual exercise captures. LSPR25 currently has no public files
and contributes zero.

Linux-APT-Dataset-2024 was also audited but contributes zero. Its 17 CSV files
are explicitly date or 10,000-record-limit partitions spanning 2023-10-01 to
2024-01-07, and its five listed APT or payload categories are not five proven
complete executions. Positive credit would require curator-only proof of a
unique complete chain boundary and sufficient telemetry coverage.

A 2026 preprint describes 50 additional unique scenarios but exposes no
verifiable public data artifact from its article page, so those scenarios
remain excluded from the current metadata count. If all 50 later became
available and all 162 metadata candidates survived download, identity,
isolation, and overlap checks, the upper bound would exceed the target by 66.
That hypothetical surplus does not replace the frozen 96-case intake gate.

The metadata gap is closed with a headline surplus of 16, but the verified-
artifact surplus is only six and the hash-bound intake count remains zero. The
next valid step is isolated, non-consuming download/hash intake, independent
case-identity construction, and cross-source chain-definition and capture-
overlap auditing. Additional source discovery and acquisition are now paused
until the fixed-pool qualification result is available. No C13+ outcome may be
opened, and pseudoreplication cannot be used to fill the cohort.

## Qualification-first decision

Source discovery is now paused. The 102 Tier-A plus Tier-B candidates are frozen
as an independent-curator qualification pool in
`candidate-qualification-pool-v0.1.json`; the ten Tier-C ATLASv2 metadata-only
candidates are not included. The qualification result, not the current upper
bound, decides whether searching resumes:

- at least 96 qualified: retain all qualified cases and do not search;
- 79 through 95 qualified: retain all, do not search solely to reach 96, and
  amend the count gate before any outcome or cost value is opened;
- fewer than 79 qualified: resume source discovery only for the shortfall to
  the frozen power-design minimum.

The current qualification readiness result is
`awaiting_independent_curator_report`. No independent curator report exists yet,
so the observed qualified-case count is unknown rather than zero. The model-
development role cannot convert the 102 upper-bound slots into qualification
claims by opening candidate payloads itself.

`source-artifact-access-boundary-v0.1.json` freezes which source artifacts may
be inspected as public non-label metadata, which telemetry may only be
downloaded and hashed by an isolated curator, and which labels, narratives,
validation summaries, or row mappings remain sealed with the ground-truth
custodian. Downloading or hashing a source package never increments the case
count by itself. `isolated-curator-handoff-protocol-v0.1.md` defines the exact
label-free artifact and identity package that a disjoint curator must return
before the repository can enter non-consuming preflight.
