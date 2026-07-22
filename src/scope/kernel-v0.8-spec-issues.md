# Kernel v0.8 specification issues

Status: issue register for P0 artifact implementation. Each issue carries an
explicit state; closing an issue here does not silently modify the normative
v0.8 document.

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

## SI-003 — Appendix Γ skeleton is not schema-complete

Appendix A omits fields required by the A6.6 machine-schema body, including
retention/missingness assumptions and finiteness basis. The P0 Γ follows A6.6
and records the appendix mismatch rather than weakening the Schema.

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

## SI-006 — Compiler/Kernel ownership is prose-only

The v0.8 text forbids the LLM from changing authority, promotion and STOP, but
does not provide a machine interface. P0 therefore publishes the
`candidateCompilerRequest`/`candidateCompilerResponse` profiles and a stable
interface manifest. Whether these profiles become normative requires review.

## SI-007 — Existing runtime contracts conflict with the Kernel boundary

The existing M3* runtime uses stochastic transitions, a 0.90 reliability gate
and planner-owned stopping behavior. The legacy action schema requires scalar
cost and ground-truth outcome/recoverable fields. The legacy Claim schema does
not fully separate modality, truth status, epistemic role and certification
authority. P0 does not modify or reuse these implementations.

## SI-008 — Existing frozen artifact hash is line-ending sensitive

The linked worktree changes LF/CRLF representation of an old M3* CSV artifact:
the runtime contract expects `90b286...`, while the worktree bytes produce
`5a8b25...`. This is a pre-existing baseline issue and the frozen experiment
artifact is intentionally untouched.

## SI-009 — v0.7 is reference-only

The user-supplied v0.7 file has raw SHA-256
`b1ff751758377afa2e3287ce68a2e579ac0a4bcb8c687bf4731e1927290de0da`.
It is used for inherited truth-table and fixture component checks only. Where
v0.7 and v0.8 differ, this P0 implementation follows v0.8 and records ambiguity
instead of silently selecting v0.7 behavior.

## SI-010 — OPEN: fixture policy hash is forbidden for formal certification

**State:** `OPEN — FIXTURE PLACEHOLDER MUST NOT CERTIFY`.

`TWIN-COUNTEREXAMPLE-001` uses repeated numeric SHA-256-shaped values to test
Claim IR validation. They are explicitly fixture placeholders, not hashes of
an accepted policy artifact. They must never be consumed as policy proof,
support a formal certificate, or appear in a formal certification claim. Any
certificate depending on such a placeholder is invalid and must be rejected.
Before formal freeze, the placeholders must be replaced by the actual hash of
the approved admission-policy artifact and all bound references regenerated.
