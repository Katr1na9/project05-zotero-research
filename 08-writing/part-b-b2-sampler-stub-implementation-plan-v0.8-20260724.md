# Part B B2 sampler stub implementation plan v0.8

Date: `2026-07-24`
Baseline: `984a2f89f43f4cc9b427e29c1a3ecfd92f418b87`
Branch: `codex/part-b-b2-sampler-stub`

## 1. Authorized slice

```text
Slice: Part B execution queue item ① — B2 sampler stub
Depth: local stub / fixture only
Source scope: FROZEN_B2_FIXTURE_CATALOG_ONLY
Claim ceiling: CONTRACT_CONSISTENCY_ONLY
catalog_ceiling_eligible=false
Production sampling: DENY
Real source / downloads / holdout release: DENY
Planner / LLM / CERTIFIED_STOP: DENY
Commit / push / PR: NOT AUTHORIZED
```

This plan does not open execution-queue items ②–⑦.

## 2. Exact 13-file allowlist

```text
schemas/part-b-b2-sampler-stub-policy.schema.json
schemas/part-b-b2-sampler-stub-fixture.schema.json
schemas/part-b-b2-sampler-stub-trace.schema.json
schemas/part-b-b2-sampler-stub-manifest.schema.json
configs/part-b-b2-sampler-stub-policy-v0.8.yaml
configs/part-b-b2-sampler-stub-fixture-v0.8.yaml
configs/part-b-b2-sampler-stub-manifest-v0.8.yaml
contracts/part-b-b2-sampler-stub-boundary-v0.8.md
src/executor/part_b_b2_sampler_stub.py
src/scope/part-b-b2-sampler-stub-spec-issues.md
08-writing/part-b-b2-sampler-stub-implementation-plan-v0.8-20260724.md
tests/unit/test_part_b_b2_sampler_stub_contracts.py
tests/unit/test_part_b_b2_sampler_stub_runtime.py
```

No B0–B9 frozen artifact appears in the allowlist.

## 3. RED-to-GREEN contract

RED contained 14 tests. All failed because the approved sampler artifacts and
module did not exist; there were no import-collection errors or malformed
assertions.

GREEN must preserve the assertions and establish:

1. closed Draft 2020-12 Schemas;
2. schema-valid, canonically hashed policy, fixture and manifest;
3. an explicit generator and seed commitment;
4. finite, non-adaptive per-trace trial budgets;
5. identical seed/input replay to the identical trace;
6. fail-closed unknown action/world and budget handling;
7. explicit resource/failure semantics;
8. simulated/non-evidence output with no Planner, holdout or STOP authority.

## 4. Algorithm and trace identity

`SHA256_COUNTER_V1` hashes canonical JSON containing the request identity,
frozen generator specification and zero-based trial index. The 256-bit digest
is interpreted as an exact value in `[0,1)` using
`UINT256_OVER_2_POW_256`; cumulative exact-rational probabilities select the
outcome. No process-global PRNG state is used.

The seed is not emitted. Its canonical commitment, together with catalog,
policy, fixture, generator, action, world and finite trial budget, defines the
request identity. The trace identity additionally binds the emitted outcome
sequence and resource trace.

## 5. Authority and issue disposition

`PB-B2-SI-002` advances only to
`CLOSED_LOCAL_STUB_REPRODUCIBILITY_ONLY_REMAINDER_OPEN`. Production simulation
and all non-fixture reproducibility questions remain open.

```text
PB-B2-SI-003 = OPEN_BLOCKS_EMPIRICAL_MODEL_ADMISSION
PB-SI-006 = OPEN_DEFAULT_DENY
PB-B5-SI-001 = OPEN_DEFAULT_DENY
holdout release = DENY
stop_authority = NONE
```

The stub is not imported by `src.executor.__init__` and does not enter the
Part A Executor, catalog ceiling, evidence path, certificate or
`CERTIFIED_STOP`. No B0–B9 frozen artifact or approved hash is modified.

## 6. Artifact identities

```text
Sampler policy:
sha256:4a35eeab3849cafbf1b6c902f839fd0196a78eafbdea83c13513ec81ed1a8c14

Fixture:
sha256:6ecad3604608148b2fc2831f8a691ca00ae676d8433081ebcee29fdc0198119c

Stub manifest:
sha256:aeb77d8938833520d0942d9e9231a1d29f748d402035cb1274561f4733b1232f
```

## 7. Verification gate

```text
python -m unittest \
  tests.unit.test_part_b_b2_sampler_stub_contracts \
  tests.unit.test_part_b_b2_sampler_stub_runtime -v

python -m compileall -q src tests
git diff --check
```

Acceptance requires `14/14 PASS`, exact canonical hash replay, no placeholder
hash, porcelain restricted to the 13-file allowlist and zero B0–B9 diff.
Completion stops at local review; no delivery action is authorized.
