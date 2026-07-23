# Part B B0 planning and contracts plan v0.8

Status: **B0 ARTIFACTS IMPLEMENTED — PENDING HUMAN REVIEW**

```text
Authorized slice: B0_PLANNING_AND_CONTRACTS
Execution authority: NO
B1–B9: CLOSED
LLM: NOT AUTHORIZED
Planner / M3* / stochastic execution / connectors: NOT AUTHORIZED
Part A certificate and STOP semantics: UNCHANGED
```

## 1. Why B0 exists

Part A A16 has passed for the frozen deterministic Kernel. The v0.8 Part B
section permits later work on heterogeneous federation, stochastic
observations, full cost, M3* and full baselines, but compresses those topics
into five lines and inherits most detail from v0.7. Runtime work would therefore
begin with unresolved authority, probability, cost and interface semantics.

B0 freezes reviewable contracts before any Part B algorithm or data path is
implemented. It is analogous to an artifact gate, not an experiment condition.
In particular, it is unrelated to the legacy `B0 no-acquisition` baseline in
`experiment-plan-v0.1-20260707.md`.

## 2. Source hierarchy

1. Explicit user authorization on `2026-07-23` controls the current scope.
2. The tracked v0.8 specification controls Part A invariants and Part B entry.
3. The v0.7 implementation-ready source is reference-only for inherited Part B
   detail; its raw SHA-256 is
   `b1ff751758377afa2e3287ce68a2e579ac0a4bcb8c687bf4731e1927290de0da`.
4. This B0 plan and its contracts are drafts until separately approved.

No B0 artifact may weaken the exact-hash admission policy, finite-domain
certificate gate, modality separation, no-evidence-laundering rule, pointer
requirements, UNKNOWN semantics, or Checker-only STOP authority.

## 3. B0 deliverables

| Artifact | Purpose |
|---|---|
| `schemas/part-b-observation-contract.schema.json` | Finite exact probability and preregistered TV-threshold representation. |
| `schemas/part-b-cost-contract.schema.json` | Ordered eight-dimensional cost/provenance contract with separate feasibility. |
| `schemas/part-b-b0-manifest.schema.json` | Machine-enforced B0 authority, bindings, closed slices and error codes. |
| `configs/part-b-observation-contract-v0.8.yaml` | Non-executable representation example. |
| `configs/part-b-cost-contract-v0.8.yaml` | Dimension/unit/source draft; contains no measurements. |
| `configs/part-b-b0-manifest-v0.8.yaml` | Canonical B0 contract-only authority record. |
| `contracts/part-b-b0-boundary-v0.8.md` | Human-readable boundary and interface contract. |
| `src/scope/part-b-b0-spec-issues.md` | Ambiguities and decisions that must not be resolved silently. |
| `tests/unit/test_part_b_b0_contracts.py` | Schema, hash, probability, cost and authority invariants. |

## 4. Proposed later decomposition — not authorized

The following map is planning vocabulary only. It does not open any slice.

| Slice | Proposed subject | Current state |
|---|---|---|
| B1 | Semantic-family federation schemas and adapter conformance | CLOSED |
| B2 | Stochastic observation catalog, TV policy and simulation contract | CLOSED |
| B3 | Eight-dimensional executor/resource instrumentation | CLOSED |
| B4 | Full baseline preregistration and isolation | CLOSED |
| B5 | M3* public-state/action interface and bounded planner evaluation | CLOSED |
| B6 | Integrated Part B closed-loop evaluation | CLOSED |
| B7 | Broad-input connectors and provenance validation | CLOSED |
| B8 | External/holdout preregistration and statistical analysis | CLOSED |
| B9 | Final freeze, audit and claim-boundary package | CLOSED |

The v0.7 document names B1–B6 differently and does not define B7–B9. The map
above is intentionally non-normative until human review resolves PB-SI-002.

## 5. B0 invariants

1. All design domains shown in examples are finite.
2. Probabilities use exact rational values; no binary float is normative.
3. Every stochastic action must eventually preregister \(\delta_a\) and bind it
   into its approved catalog hash before execution.
4. Timeout/resource exhaustion remain UNKNOWN; neither is an observation,
   zero probability event or UNSAT proof.
5. Feasibility is separate from cost.
6. Full cost has exactly eight ordered dimensions and trace provenance.
7. B0 has no runtime, empirical or STOP authority.
8. LLM components and artifacts are absent, not merely disabled at runtime.
9. Frozen Part A artifacts and behavior remain byte-for-value unchanged.

## 6. RED → GREEN verification

The B0 contract test is written before artifacts. RED is the expected missing
Schema failure. GREEN requires:

```text
python -m unittest tests.unit.test_part_b_b0_contracts -v
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tests
git diff --check
```

Static path review must show no changes under `src/checker`, `src/firewall`,
`src/executor`, `src/actions`, `src/cli`, `src/counterexample`, Planner/M3*,
LLM/training/datasets or `09-experiments`.

## 7. Human decisions required after B0

- approve or revise exact-rational probability encoding;
- define which world pairs a stochastic action must distinguish;
- approve the semantic meaning and selection procedure for \(\delta_a\);
- approve cost units, aggregation and missing-data rules;
- decide the normative Part B phase numbering;
- authorize one specific B1+ slice, or keep Part B stopped.

Until those decisions are explicit, B0 completion means only that the planning
package is internally consistent and ready for review.

## 8. B0 implementation verification — 2026-07-23

The authorized contract-only artifacts are complete in the isolated B0
worktree. Verification at the review tip produced:

```text
B0 contract tests: 7/7 PASS
Full repository regression: 138/138 PASS
python -m compileall -q src tests: PASS
git diff --check: PASS
Changed paths outside the B0 allowlist: NONE
```

These results establish internal contract consistency only. They do not
approve the draft stochastic/cost semantics and do not open B1–B9, runtime
execution, LLM integration, Planner/M3*, connectors, experiments or STOP
authority.
