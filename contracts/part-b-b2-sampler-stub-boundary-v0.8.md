# Part B B2 local sampler stub boundary v0.8

Status: **LOCAL FIXTURE STUB ONLY — NO PRODUCTION AUTHORITY**

```text
Authorized slice: B2_SAMPLER_STUB_LOCAL_FIXTURE_ONLY
Claim ceiling: CONTRACT_CONSISTENCY_ONLY
Source scope: FROZEN_B2_FIXTURE_CATALOG_ONLY
catalog_ceiling_eligible=false
Production sampling: DENY
Real source / connector / download: DENY
holdout release: DENY
Planner execution: DENY
Certificate / system state / CERTIFIED_STOP: DENY
```

## 1. Narrow authorized result

This slice implements one deterministic replay stub over the two finite
contract examples already present in
`configs/part-b-stochastic-observation-catalog-v0.8.yaml`. It adds no action,
world, outcome probability, external source, connector, dataset, holdout,
training input, Planner or experiment.

The stub is local and fixture-only. It is not the Part A deterministic
Executor and is not exported by `src.executor`. Its traces cannot enter the
Part A Executor, formal catalog ceiling, world elimination, evidence
admission, certification or `CERTIFIED_STOP` path.

## 2. Reproducibility subset

The local subset of `PB-B2-SI-002` is closed only for this frozen stub:

- generator: `SHA256_COUNTER_V1`, version `1.0.0`;
- seed identity: `SHA256_CANONICAL_JSON` commitment before replay;
- trial budget: finite, per trace, non-adaptive;
- request and trace identity: canonical SHA-256 bindings;
- resource trace: requested/completed trials and deterministic draw count;
- failures: timeout, resource exhaustion and invalid model are `UNKNOWN`;
  infeasibility remains separate.

The remainder of `PB-B2-SI-002` stays OPEN. There is no production RNG
validation, cross-runtime conformance claim, concurrency policy, persistence,
real-source execution, empirical calibration or external validity.

## 3. Frozen inputs and identities

The stub reads mappings supplied by the caller and performs no filesystem,
network or connector I/O. It accepts only cases explicitly listed in the new
fixture, which binds the unchanged B2 catalog:

```text
Stochastic catalog:
sha256:200f0ccd89525bcbda89ea77101cdcab7fda675888938ee106e389a1a8beeab5

Exact finite decision:
sha256:1a9668ef8c968c968e14587778d261b023dff60a0234e4e67251051ec07e5919

Sampler policy:
sha256:4a35eeab3849cafbf1b6c902f839fd0196a78eafbdea83c13513ec81ed1a8c14

Fixture:
sha256:6ecad3604608148b2fc2831f8a691ca00ae676d8433081ebcee29fdc0198119c

Stub manifest:
sha256:aeb77d8938833520d0942d9e9231a1d29f748d402035cb1274561f4733b1232f
```

No B0–B9 frozen artifact or approved hash is modified.

## 4. Fail-closed boundary

Unknown actions, worlds outside the fixture, malformed or mismatched hashes,
unapproved generator specifications, non-normalized rows and trial budgets
outside the finite policy range fail before a trace is emitted.

`PB-B2-SI-003` remains
`OPEN_BLOCKS_EMPIRICAL_MODEL_ADMISSION`. `PB-SI-006` and `PB-B5-SI-001`
remain `OPEN_DEFAULT_DENY`. A simulated trace has
`admitted_case_evidence=false` and `catalog_ceiling_eligible=false`.

The stub grants no true-data access, holdout release, Planner execution,
performance claim, certificate, system status or STOP authority.

## 5. Delivery gate

Passing the local contract tests establishes reproducibility and boundary
conformance for this fixture stub only. It does not authorize commit, push,
PR, production sampling, data access or any subsequent execution-queue item.
