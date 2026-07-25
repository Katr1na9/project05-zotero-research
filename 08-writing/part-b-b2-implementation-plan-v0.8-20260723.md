# Part B B2 stochastic-observation contract plan v0.8

Status: **APPROVED — CONTRACT ONLY**

```text
Authorized slice: B2_STOCHASTIC_OBSERVATION
Authority kind: CONTRACT ONLY
execution_authority=false
sampling_authority=false
PB-SI-003: OPEN — BLOCKS STOCHASTIC EXECUTION
B3–B9: CLOSED
LLM / training / Planner / M3*: NOT AUTHORIZED
CERTIFIED_STOP: UNCHANGED / NO B2 AUTHORITY
Local commit: AUTHORIZED FOR THE EXACT 13 FILES
Push / PR: NOT AUTHORIZED
```

## 1. Objective

B2 freezes the machine representation and review boundary for finite
stochastic observations without running them. It separates three questions:

1. Can a finite conditional distribution be represented exactly?
2. Can a named design-pair TV value be recomputed exactly?
3. Has a production stochastic decision and sampling policy been approved?

B2 answers yes only to the first two. The third remains no because
`PB-SI-003` is OPEN.

## 2. Source and authority hierarchy

1. The user's explicit `B2_STOCHASTIC_OBSERVATION` contract-only authorization
   on `2026-07-23`.
2. The normative v0.8 Part B map approved under PB-SI-002.
3. Approved B0 and B1 manifests and their frozen hashes.
4. B0 stochastic-observation draft as reference representation.
5. v0.7 as reference lineage only.

No B2 artifact may modify Part A, B0, B1, Claim IR or the approved B1 YAML
hashes.

## 3. Exact 13-file allowlist

| Path | Purpose |
|---|---|
| `schemas/part-b-stochastic-observation-catalog.schema.json` | Finite exact, non-executable catalog representation. |
| `schemas/part-b-stochastic-tv-policy.schema.json` | TV replay and unresolved-policy contract. |
| `schemas/part-b-b2-manifest.schema.json` | Machine-enforced B2 authority boundary. |
| `configs/part-b-stochastic-observation-catalog-v0.8.yaml` | Two structurally distinct design examples. |
| `configs/part-b-stochastic-tv-policy-v0.8.yaml` | Non-decision TV replay examples. |
| `configs/part-b-b2-manifest-v0.8.yaml` | Hash bindings and closed runtime authority. |
| `contracts/part-b-b2-boundary-v0.8.md` | Human-readable slice boundary. |
| `contracts/part-b-b2-stochastic-observation-v0.8.md` | Mathematical and future simulation-envelope contract. |
| `src/scope/part-b-b2-spec-issues.md` | Open issues and fail-closed gates. |
| `tests/unit/test_part_b_b2_contracts.py` | Schema, hash and authority tests. |
| `tests/unit/test_part_b_b2_stochastic_observation.py` | Exact distribution and TV invariants. |
| `08-writing/part-b-b2-implementation-plan-v0.8-20260723.md` | Plan and verification record. |
| `08-writing/KERNEL-V0.8-AUTHORITY-STATUS-20260722.md` | Shared authority-state update. |

No other file is authorized.

### 3.1 Whitelist naming ratification — 2026-07-23

The user retrospectively ratified the following three naming-only
substitutions:

| Superseded planned path | Ratified path |
|---|---|
| `schemas/part-b-tv-acceptance-policy.schema.json` | `schemas/part-b-stochastic-tv-policy.schema.json` |
| `configs/part-b-tv-acceptance-policy-v0.8.yaml` | `configs/part-b-stochastic-tv-policy-v0.8.yaml` |
| `tests/unit/test_part_b_b2_tv_policy.py` | `tests/unit/test_part_b_b2_stochastic_observation.py` |

The ratified paths are the normative entries in the 13-file allowlist above.
This decision changes names only. It changes no Schema semantics, config
content, test boundary, authority flag or artifact hash.

## 4. Contract invariants

1. All design world and outcome domains are finite and unique.
2. Probabilities are exact rationals and every row sums exactly to one.
3. Failure channels are outside the observation outcome distribution.
4. A design TV replay is not a threshold, ranking or eligibility decision.
5. Production pair/threshold/aggregation/estimation semantics remain
   `UNRESOLVED_PB_SI_003`.
6. Missing approved policy means `FAIL_CLOSED_NO_SAMPLING`.
7. Catalog examples are not executable and are not formal-ceiling eligible.
8. `execution_authority=false` and `sampling_authority=false` are const
   machine fields.
9. B2 emits no observation, claim, certificate, system state or
   `CERTIFIED_STOP`.
10. LLM and B3–B9 are outside scope.

## 5. RED to GREEN protocol

RED is recorded before artifact creation: both B2 test modules failed only
because the first B2 Schema did not exist.

GREEN requires:

```text
python -m unittest tests.unit.test_part_b_b2_contracts -v
python -m unittest tests.unit.test_part_b_b2_stochastic_observation -v
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tests
git diff --check
```

The final audit must show exactly the 13 allowlisted paths, no staged files and
no Part A/B0/B1/Claim IR/LLM/training/experiment changes.

## 6. Review and stop gate

Passing tests establishes internal representation consistency only. It does
not approve the new artifact hashes, close `PB-SI-003`, authorize simulation
or sampling, or establish empirical validity.

The user approved the B2 contract slice, the ratified 13-file naming map and
the three exact artifact hashes on `2026-07-23`. Only a local commit of the
exact 13 files is authorized. Do not push, open a PR, start B3 or perform
sampling/execution without later explicit authorization.

## 7. Local verification record

The final local 13-file review state produced:

```text
B2 targeted tests: 15/15 PASS
Full repository tests: 171/171 PASS
python -m compileall -q src tests: PASS
git diff --check: PASS
Placeholder-hash scan: PASS / NONE
Canonical hash replay: 3/3 MATCH
Exact 13-file allowlist audit: PASS
Tracked changes outside allowlist: NONE
Staged changes: NONE
```

Approved contract artifact identities:

```text
Stochastic catalog:
sha256:200f0ccd89525bcbda89ea77101cdcab7fda675888938ee106e389a1a8beeab5

TV policy:
sha256:b25ed05fdbd9780c1d0de1889e7651220e8a2fc9ce6a86fcdf4720926a31d3e8

B2 manifest:
sha256:6d6f67d9722eff1b2e1aa75277b0c390dc485751067728a347ae89c77f83faed
```

These hashes identify approved contract artifacts only. Their approval confers
no execution, sampling, empirical or STOP authority and does not close
`PB-SI-003`.
