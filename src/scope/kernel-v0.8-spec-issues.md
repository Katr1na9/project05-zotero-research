# Kernel v0.8 specification issues

Status: lifecycle issue register for the P0--P11 Part A implementation. Each
issue carries an explicit state; closing an issue here does not silently modify
the normative v0.8 document.

Implementation snapshot (`2026-07-22`): P0--P11 are implemented on
`feat/kernel-v0.8` (code tip lineage through remediation `a85b99a`), with
131/131 Kernel tests passing pending final closeout replay. Human A16
re-review on `2026-07-22` is `PASSED` / `GO` for Kernel v0.8 Part A only.
Push/PR are authorized only after closeout commit, clean replay, and a
Kernel-only PR diff. Part B remains CLOSED. `CERTIFIED_STOP` is established
only for the frozen finite-domain Kernel Γ with approved policy/catalog
hashes and declared completeness / solver assumptions. The controlling
status entry is `08-writing/KERNEL-V0.8-AUTHORITY-STATUS-20260722.md`.

## SI-001 — CLOSED: normative v0.8 file is tracked

**State:** `CLOSED` at commit `3b34f3e01b18afa9b010adc2f517d59f36e83a43`.

The normative v0.8 source is tracked at
`08-writing/active-attribution-experiment-revision-plan-v0.8-20260721.md`.
Its raw SHA-256 is
`99fa98b9489cfe49d4da6fe02e06b457201a59d9024ca62233c5dd82f7b7baa9`,
which is byte-identical to the source previously read from the sibling
`beth-single-source-gate` worktree. This closes the artifact-absence issue;
it does not resolve the separate semantic issues below.

## SI-002 — CLOSED — APPROVED: Γ/catalog canonical hash contract

**State:** `CLOSED — APPROVED` by explicit user ruling on `2026-07-22`.

Both documents contain their own `hash`, while v0.8 does not define field
exclusion or canonical byte serialization. The approved v0.8 rule is:

1. parse YAML to a data object;
2. remove only the top-level `hash` field;
3. serialize as JSON with UTF-8, Unicode preserved, keys sorted, and separators
   `,` and `:` without added whitespace;
4. write lowercase SHA-256 as `sha256:<64 hex>`.

The controlling contract is `contracts/gamma-hash-v0.8.md`. It binds the exact
P0 replay procedure and current test vectors. Any semantic change requires
explicit approval, a new contract/config version and regenerated references;
already frozen hashes must not be silently reinterpreted.

## SI-003 — CLOSED BY AUTHORITY CONTRACT: Appendix Γ skeleton is not schema-complete

**Disposition:** `FIXED FOR IMPLEMENTATION — CLOSED` on `2026-07-22`.

Appendix A omits fields required by the A6.6 machine-schema body, including
retention/missingness assumptions and finiteness basis. The P0 Γ follows A6.6
and records the appendix mismatch rather than weakening the Schema.

`contracts/gamma-schema-authority-v0.8.md` freezes the authority relationship:
the complete A6.6 requirements control runtime validation and
`schemas/gamma-kernel.schema.json` is their executable fail-closed contract;
the shorter Appendix skeleton is informative and cannot make an A6.6 field
optional. A future normative contradiction must open a new issue/version. The
Appendix prose itself has not been silently edited.

## SI-004 — CLOSED: promotion event field ruling

**State:** `CLOSED — APPROVED` by explicit user ruling on `2026-07-22`.

Every Kernel Claim IR object must contain `promotion_event_id`. Its value may
be null only while the claim is not promoted; when
`promotion_status=promoted`, `promotion_event_id` must be a non-null,
non-empty identifier. The existing P0 Claim IR Schema implements this ruling.
Promotion still must not change `modality`.

## SI-005 — CLOSED: Checker result and system STOP names are distinct

**State:** `CLOSED — APPROVED` by explicit user ruling on `2026-07-22`.

The Checker truth-table result for a supported candidate with no alternative
is `CANDIDATE_CERTIFIED`. This candidate-level result is not a system STOP.
The system state `CERTIFIED_STOP` may be emitted only when complete
level-level certification holds. Candidate-level certification, M3*, LLM,
probability thresholds and human judgment have no STOP authority.

## SI-006 — CLOSED BY VERSIONED INTERFACE: Compiler/Kernel ownership

**Disposition:** `FIXED FOR IMPLEMENTATION — CLOSED` on `2026-07-22`.

The v0.8 text forbids the LLM from changing authority, promotion and STOP, but
does not provide a machine interface. P0 therefore publishes the
`candidateCompilerRequest`/`candidateCompilerResponse` profiles and a stable
interface manifest. Whether these profiles become normative requires review.

The ownership boundary is now frozen in
`contracts/compiler-kernel-boundary-v0.8.md`, the versioned interface manifest,
the Claim IR schema profiles, and `src/ir/migration-v0.8.md`. The compiler is
candidate-only; the Kernel owns protected Claim fields, admission/promotion,
actions, Checker, certificate, and state. P11's per-action
`certification_basis_rule_id` is explicitly Kernel-owned and cannot be set by
the compiler. Any silent cross-track adaptation is a breaking contract change.

## SI-007 — DISPOSITIONED: legacy M3* runtime is excluded

**Disposition:** `DEFERRED — NON-BLOCKING FOR PART A A16; CLAIM-SCOPE
EXCLUSION` on `2026-07-22`.

The existing M3* runtime uses stochastic transitions, a 0.90 reliability gate
and planner-owned stopping behavior. The legacy action schema requires scalar
cost and ground-truth outcome/recoverable fields. The legacy Claim schema does
not fully separate modality, truth status, epistemic role and certification
authority. P0 does not modify or reuse these implementations.

Part A A16 claims are therefore limited to the deterministic Kernel v0.8
contracts and frozen fixtures. No current result may be described as legacy
M3* integration, M3* validation, Planner validation, or evidence that a
stochastic/probabilistic runtime satisfies this Kernel. Integrating such a
runtime requires a separately authorized, versioned adapter and new tests.

## SI-008 — DISPOSITIONED: historical CRLF-sensitive artifact is excluded

**Disposition:** `DEFERRED — NON-BLOCKING FOR PART A A16; REPRODUCIBILITY-SCOPE
EXCLUSION` on `2026-07-22`.

The linked worktree changes LF/CRLF representation of an old M3* CSV artifact:
the runtime contract expects `90b286...`, while the worktree bytes produce
`5a8b25...`. This is a pre-existing baseline issue and the frozen experiment
artifact is intentionally untouched.

The A16 reproducibility statement covers only Kernel v0.8 artifacts whose
hashes are replayed by the current contracts/tests. It explicitly excludes the
legacy M3* CSV and makes no claim about its byte reproduction. No line-ending
normalization or legacy expected hash is changed in this track. Re-admitting
that artifact requires a separate migration decision with raw-byte provenance.

## SI-009 — v0.7 is reference-only

The user-supplied v0.7 file has raw SHA-256
`b1ff751758377afa2e3287ce68a2e579ac0a4bcb8c687bf4731e1927290de0da`.
It is used for inherited truth-table and fixture component checks only. Where
v0.7 and v0.8 differ, this P0 implementation follows v0.8 and records ambiguity
instead of silently selecting v0.7 behavior.

## SI-010 — CLOSED: exact-hash admission policy approved and rebound

**State:** `CLOSED — APPROVED BY PROJECT05 REPOSITORY OWNER` on `2026-07-22`.

The user explicitly approved `admission-policy-kernel-v0.8` at policy hash
`sha256:8f34a5e99c2cba3d79304667acd5bb010492af74b8b99425352375a796825671`.
The repository approval manifest now records `APPROVED` and replays as
`sha256:2eda84dd347d1a0acdf8802edb01e7ba1cd00c6b8e767d02d78170e3d0fd1f8b`.

Both Gamma documents, fixture references, counterexample metadata, and frozen
formal-ceiling reports were regenerated from that binding. Runtime authority
still requires exact policy/manifest/Gamma agreement; wrong, missing,
PENDING, or tampered inputs fail closed. Fixture-only SHA-shaped values remain
non-authoritative unless they equal a verified bound artifact.

Closing SI-010 establishes admission-policy authority only. P7 allow/P8 admit
is not a level certificate, this ruling does not emit `CERTIFIED_STOP`, and it
does not change A16 NO-GO or authorize push/PR.

## Part A closeout note

The A16 supplement records explicit dispositions rather than silently closing
issues: SI-003 and SI-006 are fixed by versioned authority/interface
contracts; SI-007 and SI-008 are deferred as non-blocking scope exclusions;
SI-013 and SI-014 have engineering remediations; SI-015 has a written review
record awaiting human acceptance. SI-010 is now closed by the user's exact-hash
approval and regenerated bindings. The legacy stochastic Planner/runtime
remains outside this Kernel boundary.

The default P10 Twin path ends in `COUNTEREXAMPLE_FOUND` plus `CONTINUE`; an
explicit single-hit feedback path may reach `CANDIDATE_CERTIFIED` but still
ends in `CONTINUE`. Neither path supplies level-complete authority.

**Original human A16 ruling (`2026-07-22`):** `NOT PASSED` / `NO-GO`. Push NO.
PR NO. Part B CLOSED. That ruling required closing SI-010, real-form ceiling
evidence, resolving the single-Twin / narrow-compiler overclaim, an itemized
81-file review record, and formal dispositions for SI-003/006/007/008.

**Superseding human A16 re-review (`2026-07-22`):** `PASSED` / `GO` —
Kernel v0.8 Part A only. Push/PR authorized after closeout commit, clean
replay, and Kernel-only PR scope. Part B remains CLOSED. LLM integration and
legacy M3* are not authorized or validated by this ruling.
`CERTIFIED_STOP` is established only for the frozen finite-domain Kernel Γ,
approved policy/catalog hashes, declared completeness assumptions, and the
recorded solver/proof policy. Do not infer Part B, LLM, or real-world
exhaustiveness from this scoped GO.

The opt-in P11 path adapts only observations actually emitted by P5, evaluates
them through P7 and may admit Firewall-allowed claims through P8. It preserves
`modality=observed`, leaves the existing feedback/recertification/state path
unchanged, and cannot issue a level certificate or `CERTIFIED_STOP`.

## SI-011 — IMPLEMENTED — APPROVED SCOPE: Firewall reason-code collision

**State:** `IMPLEMENTED — PENDING HUMAN DIFF REVIEW` under explicit user
authorization on `2026-07-22`.

The old P7 implementation assigned `FW-016` both to a missing observation
context and to an unsupported observation kind. The repair preserves
`FW-016_OBSERVATION_CONTEXT_REQUIRED` and assigns
`FW-017_OBSERVATION_KIND_UNSUPPORTED` to the second condition. Unit tests bind
the two conditions independently so downstream audit consumers can distinguish
them.

## SI-012 — IMPLEMENTED — APPROVED SCOPE: compiled Twin worlds and projections

**State:** `IMPLEMENTED — PENDING HUMAN DIFF REVIEW` under explicit user
authorization on `2026-07-22`.

P1/P2/P3/P9/P10 previously reconstructed the Twin worlds in test-owned lambdas;
P9/P10 directly embedded H1/H3, while predicate projections were caller strings
with no catalog provenance check. The repair adds:

- a narrow `EvidenceGammaFiniteProblemCompiler` that reads the explicit finite
  result domain and required mechanism-rule IDs from Γ, then binds the source
  and destination only from admitted, observed, supported case evidence;
- a caller-supplied variable-to-action binding document whose predicates are
  resolved only from the matched action's single catalog
  `world_dependencies` entry; and
- rejection of raw MinDiff projection mappings, unknown variables/actions and
  ambiguous catalog dependencies.

The normative Γ, Γ hash, action catalog and fixture expected outputs remain
unchanged. The projection contract is documented at
`contracts/predicate-projection-v0.8.md`. This repair does not make the narrow
mechanism compiler a generic rule engine and does not grant certificate or STOP
authority.

## SI-013 — CLOSED BY SECOND NON-ISOMORPHIC Γ/FIXTURE

**Disposition:** `FIXED FOR ENGINEERING RE-REVIEW — CLOSED` on `2026-07-22`.

One complete Twin counterexample chain and a mechanism-specific
`EvidenceGammaFiniteProblemCompiler` do not establish generality or a real
wide-domain ceiling. Re-review requires either:

1. a structurally different, non-trivial Γ/fixture that traverses Checker,
   MinDiff, artifact, observation, P7, P8 and P9; or
2. an explicit claim-scope reduction to the frozen Twin, with all statements
   suggesting a general Kernel, real ceiling or wide-domain certification
   removed.

Adding only near-duplicate cases does not close this issue.

`TWIN-SUPPLY-CHAIN-002` supplies a structurally different package-origin
domain with three result candidates, two auxiliary variables, a 27-assignment
Cartesian space, three explicit legal worlds, different evidence families,
three deterministic actions, and A003/A004 admission bindings. It traverses
Checker, MinDiff, artifact, action selection/execution, Firewall, audit,
recertification, and P9 `CONTINUE`. This closes the single-Twin objection but
does not claim external validity or universal Gamma coverage.

## SI-014 — CLOSED BY MODEL-RELATIVE FORMAL CEILING CONTRACT

**Disposition:** `FIXED FOR ENGINEERING RE-REVIEW — CLOSED` on `2026-07-22`.

The current implementation proves behavior only inside the frozen finite Twin
and catalog eligibility contract. Re-review requires a reviewable definition
of the ceiling, its exact domain/actions/observations, a separation of formal
guarantees from test coverage, explicit timeout/resource-exhaustion/UNKNOWN
versus UNSAT semantics, and fail-closed behavior outside the frozen domain.

`contracts/formal-ceiling-v0.8.md`, the machine schema/verifier, and two frozen
reports now define and replay the exact model-relative ceiling. Outside target
or action scope fails closed; resource exhaustion is UNKNOWN, never UNSAT;
tampered/stale artifacts are invalid. P6 filters the complete compiled
legal-world table, and the certificate issuer binds exact candidate/world/hash
and Cartesian-bound coverage. This is not a real-world exhaustiveness or
external-validity claim and does not itself authorize STOP.

## SI-015 — ENGINEERING AUDIT COMPLETE, HUMAN ACCEPTANCE PENDING

**State:** `REVIEW RECORD COMPLETE — A16 HUMAN ACCEPTANCE REQUIRED`.

The 15 commits and 81 files now have an inventory, automated test evidence, and
itemized written findings for authorization scope, absence of
LLM/training/Part B/experiment mix-in, P11 default-P10/STOP invariants,
OBS-001/002 versus OBS-003/004 evidence boundaries, and
pointer/modality/oracle-hidden fail-closed behavior. This completes the
engineering review record; human acceptance of that record is still required.

The written record is
`08-writing/kernel-v0.8-81-file-diff-audit-20260722.md`. It covers all 15
commits/81 paths, forbidden-track isolation, P11/default-P10 and STOP
invariants, OBS boundaries, and pointer/modality/oracle-hidden behavior. It
also records two material findings (P6 two-witness exhaustiveness and P9
caller-declared coverage) and their current-tree remediations. The record is
ready for human acceptance; it does not self-approve A16.

## SI-016 — CLOSED: P6 witness pair was not an exhaustive world table

**Disposition:** `FIXED — REGRESSION BOUND` on `2026-07-22`.

The historical P6 implementation rebuilt recertification from only the
counterexample support/alternative witnesses. It could therefore certify the
candidate after eliminating one alternative even when a third legal world
remained. P6 now requires the Gamma/evidence compiler's complete
`CompiledFiniteProblem`, validates the artifact witnesses against that table,
filters every legal world, and constrains the original full finite problem.
The three-world supply-chain regression eliminates MIRROR-B while retaining
BUILDER-C and correctly remains `COUNTEREXAMPLE_FOUND + CONTINUE`.

## SI-017 — CLOSED: level coverage was caller-declared rather than ceiling-bound

**Disposition:** `FIXED — FAIL-CLOSED TESTED` on `2026-07-22`.

The historical P9 issuer checked internally consistent coverage booleans and
counts but did not bind them to the verified ceiling's exact legal-world
table. Certificate coverage now carries and exactly matches the ordered result
candidates, legal-world count/hash, and Cartesian assignment bound. The
alternative-UNSAT Checker query must report that full enumeration count.
Wrong candidate lists, counts, hashes, bounds, or incomplete enumeration all
fail with `P9-CERT-008_FORMAL_CEILING_UNVERIFIED`.
