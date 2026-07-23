# Part B B0 specification issues

Status: **B0 DRAFT ISSUE REGISTER — NO RUNTIME AUTHORITY**

## PB-SI-001 — B0 name collision

**State:** `RESOLVED FOR NAMING ONLY`.

The legacy experiment plan uses `B0 no-acquisition` for a baseline condition.
The current slice is `B0_PLANNING_AND_CONTRACTS` under Part B and is never an
experimental arm. Documents and manifests must use the full identifier.

## PB-SI-002 — Part B inheritance and phase numbering

**State:** `OPEN — BLOCKS NORMATIVE B1–B9 MAP`.

v0.8 says Part B inherits v0.7, but v0.7 defines only B1–B6 while v0.8 earlier
mentions B0–B9. B0 records a proposed map but cannot make it normative. The
reference v0.7 raw SHA-256 is
`b1ff751758377afa2e3287ce68a2e579ac0a4bcb8c687bf4731e1927290de0da`.

## PB-SI-003 — TV threshold semantics are underspecified

**State:** `OPEN — BLOCKS STOCHASTIC EXECUTION`.

v0.8 requires preregistered \(\delta_a\) in the catalog hash but does not state
which world pairs are compared, whether the threshold is per pair or worst
case, or how an estimated observation model is accepted. B0 freezes an exact
finite representation and a non-executable two-world example only.

## PB-SI-004 — Full-cost measurement governance is not approved

**State:** `OPEN — BLOCKS COST CLAIMS`.

v0.7 lists eight dimensions but does not fully freeze units, aggregation,
missingness, currency normalization or scalarization. The B0 cost contract is a
review proposal; it contains no measurements and supports no superiority claim.

## PB-SI-005 — Legacy M3* is not a Part B interface

**State:** `OPEN — BLOCKS PLANNER INTEGRATION`.

Part A SI-007 excludes the legacy stochastic M3* runtime. B0 does not reuse or
validate it and does not define a planner API. A later slice must specify a
public-state, action-ID-only interface and preserve Checker-only STOP authority.

## PB-SI-006 — Broad connector and dataset scope is unselected

**State:** `OPEN — BLOCKS CONNECTOR/DATA WORK`.

No semantic family, connector, dataset, external holdout or download is
authorized by B0. Adding a source requires explicit pointer, modality, role,
authority, open/closed-world and adapter-conformance contracts.

## PB-SI-007 — Part A and stochastic certification domains must not mix

**State:** `CLOSED FOR B0 BOUNDARY; RUNTIME DESIGN STILL REQUIRED`.

B0 explicitly forbids a stochastic observation contract from entering the
Part A deterministic Executor, formal ceiling or level certificate. Future
Part B certification semantics require separate authorization and cannot
silently extend `CERTIFIED_STOP` beyond the frozen deterministic Kernel Gamma.

## PB-SI-008 — LLM remains outside the authorized track

**State:** `CLOSED FOR B0 SCOPE`.

The user explicitly authorized B0 without LLM. B0 contains no LLM code, prompt,
model, dataset, training, inference, selector or judge contract. Any later LLM
work is a separate authority decision and cannot be inferred from Part B.
