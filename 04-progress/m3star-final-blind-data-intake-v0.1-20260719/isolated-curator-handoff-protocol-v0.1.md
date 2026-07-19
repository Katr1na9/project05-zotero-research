# Isolated curator handoff protocol v0.1 with staged amendment v0.2

This is an experiment-input governance artifact. It does not authorize model
evaluation and contains no C13+ labels, costs, ground truth, or model outcomes.

## Mandatory role separation

The curator, model-development team, and ground-truth custodian must be three
disjoint identities. The curator must not receive M3* or baseline outputs. The
model-development team must not open candidate telemetry, case-boundary
material, labels, validation summaries, attack narratives, or cost values. The
ground-truth custodian alone retains outcome-bearing material until the
authorized one-shot execution.

The access classification for each prioritized source is frozen in
`source-artifact-access-boundary-v0.1.json`.

The original 102-candidate A+B pool and its full-pool audit are preserved as
the superseded record in `candidate-qualification-pool-v0.1.json`. They must
not be used as the active acquisition instruction after the v0.2 amendment.

The pre-access resource amendment
`staged-acquisition-protocol-amendment-v0.2.json` supersedes the full-pool
acquisition order without changing case eligibility rules. AVIATOR is excluded
before payload access because its indivisible official archive is 109.261 GB.
The remaining 95 slots must be acquired only in the amendment's frozen phases.
Phase 1 must be exhausted; later slots are sequential reserves and acquisition
stops as soon as at least 79 independently qualified complete cases exist.
This stopping rule may not use any model output, cost, ground truth, success
result, or action sequence.

## Curator procedure

1. Download candidate artifacts only from the official locators in the source
   evidence files. Record the release identifier, file name, byte size,
   publisher checksum, local SHA-256, retrieval UTC time, and final resolved
   URL. Acquire Phase 1 only at first. Do not download a Phase-2 or Phase-3
   artifact until the v0.2 auditor returns that exact candidate as
   `next_frozen_candidate`. A downloaded source package is not yet a case.
2. Verify every local artifact against the publisher checksum when one exists.
   A mismatch excludes the artifact; silent substitution or retry against an
   unofficial mirror is forbidden.
3. Identify complete campaign-execution boundaries without consulting model
   outputs. Each retained case must contain the full execution interval and all
   in-scope host/sensor telemetry. Host slices, arbitrary time windows, rows,
   flow subsets, masks, and parameter-only reruns are forbidden.
4. Bind each retained case to exactly one unique scenario-family definition,
   campaign-execution identifier, telemetry-capture identifier, and event
   namespace. Hash the canonical chain definition, execution record, capture,
   and every case file with SHA-256.
5. Deduplicate within and across sources. At most one case may remain for a
   scenario family. Alternate frameworks, repeated runs, representations,
   sensors, and annual-series views do not create extra cases. Check all
   campaign-execution identifiers against the frozen preblind-used-campaign
   registry.
6. Assign canonical C13+ identifiers only after all identity and independence
   checks pass. Keep source-cluster identifiers so the final analysis can test
   dependence on CAPD, AIT, Locked Shields, or another shared generator.
7. Produce the frozen case manifest conforming to
   `09-experiments/data_schema/m3star_final_blind_intake_manifest.schema.json`.
   Run `09-experiments/scripts/validate_m3star_final_blind_intake.py` without
   opening ground truth or cost values.

After exhausting Phase 1, and after each later candidate if a reserve is
needed, return a checkpoint report conforming to
`09-experiments/data_schema/m3star_blind_staged_candidate_qualification.schema.json`.
Start from `curator-staged-candidate-qualification-report.template.json`.
Phase 1 must exhaust all 81 slots. Later results must be the exact prefix of
the frozen Phase-2/Phase-3 order. Every audited slot is either `qualified` or
`not_qualified`; every untouched later slot remains an unaudited reserve and
is not a failure. Attrition reason counts must exactly exhaust only the
not-qualified audited slots. Each qualified case is represented only by opaque
identifiers, source/release identity, SHA-256 values, seal identifiers, and
eligibility booleans. No telemetry, label, narrative, cost value, or model
output may be returned.

The model-development side audits the returned report with:

```text
python 09-experiments/scripts/audit_m3star_blind_staged_candidate_qualification.py \
  --amendment 04-progress/m3star-final-blind-data-intake-v0.1-20260719/staged-acquisition-protocol-amendment-v0.2.json \
  --report <curator-checkpoint-report.json> \
  --output 09-experiments/results/m3star_blind_staged_candidate_qualification_readiness_v0.2/readiness_audit.json
```

This audit does not consume the final blind evaluation.

Before case construction, the curator may run
`09-experiments/scripts/verify_m3star_blind_source_artifacts.py` against a
curator-prepared catalog conforming to
`09-experiments/data_schema/m3star_blind_source_artifact_catalog.schema.json`.
The verifier streams opaque bytes only, checks byte size and publisher
MD5/SHA-256, computes local SHA-256, rejects path escape and role overlap, and
always returns `case_credit_claimed: false`. It refuses ground-truth-custodian-
only artifacts.

## Source-specific hard gates

- Windows-APT receives no case credit from its 16 period files alone. For each
  retained scenario, the curator must prove one complete run boundary and
  unique all-host capture. The five subset-masked definitions receive no credit
  unless their execution and capture are independently separable. The combined
  CSV is a duplicate representation.
- AttackMate receives at most three cases. AttackMate versus Caldera, SSH
  versus SCP, and timeout variants do not create additional scenario families.
  Definition and capture overlap with AIT Log Data Set and CAM-LDS must be
  resolved before credit.
- AttackMate Robotdog receives at most one case. The attack and clean logs are
  conditions of one scenario. Positive credit requires sufficient campaign-
  wide device coverage rather than robot-only activity fragments.
- AInception receives at most three cases: one each for SL100, SL300, and
  SL700. Its 15 archives are storyline variants or executions and cannot be
  counted as 15 unique chains. At most one complete execution is preselected
  per storyline without using labels, cost values, or model outputs.
- Locked Shields receives at most one case per annual Partners Run capture.
  Flows, packets, hosts, sectors, labels, and attack-narrative entries cannot be
  counted separately. LSPR23 and LSPR24 remain in one source cluster.
- CICAPT-IIoT is the final reserve only. Its official catalog is not publicly
  enumerable without registration. The curator must not submit any user's
  identity or registration data unless the user gives separate authorization
  after all earlier frozen reserves have been exhausted below 79.

## Label-free return package

The curator may return only the frozen intake manifest, a source-artifact hash
ledger, a duplicate/attrition summary containing counts and reason codes, and
sealed opaque identifiers for ground truth and cost measurement. No event
content, scenario labels, attack narratives, validation results, cost values,
success results, action sequences, or model-comparative information may be
returned to model development.

## Gate to non-consuming preflight

Each checkpoint has exactly one allowed transition:

- At least 79 qualified cases after all of Phase 1 or after one sequential
  reserve: stop acquisition immediately and retain every qualified case.
- Fewer than 79 with unaudited reserves: acquire only the single
  `next_frozen_candidate` returned by the auditor and issue another checkpoint.
- Fewer than 79 after all 95 amended slots are audited: resume metadata-only
  source discovery only for the shortfall to 79.

The staged acquisition amendment does not silently rewrite the legacy
execution runner's 96-case preflight gate. Because the amended candidate upper
bound is 95, a separately hashed, pre-outcome count-gate amendment must be
frozen before preflight whenever staged qualification succeeds. This is a
known governance step, not permission to reopen acquisition or inspect model
outcomes. In every branch, the dataset manifest must hash every retained case
file and an independently measured cost profile must cover exactly the same
case identifiers. Preflight does not consume the one-shot evaluation;
execution does.
