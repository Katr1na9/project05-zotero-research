# Kernel v0.8 specification issues

Status: open issues recorded during P0 artifact implementation. None is
silently resolved by changing the normative v0.8 document.

## SI-001 — Normative v0.8 file is not tracked on the implementation baseline

The normative source was read from the sibling worktree
`beth-single-source-gate/08-writing/active-attribution-experiment-revision-plan-v0.8-20260721.md`
with raw SHA-256
`99fa98b9489cfe49d4da6fe02e06b457201a59d9024ca62233c5dd82f7b7baa9`.
It is not present at baseline commit `d156b682`. Review must decide where the
normative specification is tracked before merge. The reviewed P0 restage now
proposes a byte-identical copy at
`08-writing/active-attribution-experiment-revision-plan-v0.8-20260721.md` as
the authoritative repository path; SI-001 remains open until that path is
accepted and committed.

## SI-002 — Self-referential Γ/catalog hash is underspecified

Both documents contain their own `hash`, while v0.8 does not define field
exclusion or canonical byte serialization. P0 uses this provisional rule:

1. parse YAML to a data object;
2. remove only the top-level `hash` field;
3. serialize as JSON with UTF-8, Unicode preserved, keys sorted, and separators
   `,` and `:` without added whitespace;
4. write lowercase SHA-256 as `sha256:<64 hex>`.

This convention is tested but remains a spec issue until ratified.

## SI-003 — Appendix Γ skeleton is not schema-complete

Appendix A omits fields required by the A6.6 machine-schema body, including
retention/missingness assumptions and finiteness basis. The P0 Γ follows A6.6
and records the appendix mismatch rather than weakening the Schema.

## SI-004 — Promotion event field mismatch

Invariant I4 requires `promotion_event_id`, but the A5.5 minimum-field listing
does not include it. The P0 Claim IR requires the field and requires a non-null
value for promoted claims.

## SI-005 — Checker result naming mismatch

A8 lists `CERTIFIED`; the A7 truth table names the decisive candidate outcome
`CANDIDATE_CERTIFIED`. P0 freezes the A7 seven-row truth-table name and does
not implement Checker translation logic.

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

## SI-010 — Fixture policy hash is not a formal policy freeze

`TWIN-COUNTEREXAMPLE-001` uses repeated numeric SHA-256-shaped values to test
Claim IR validation. They are explicitly fixture placeholders and must be
replaced by the hash of the accepted admission-policy artifact before any
formal freeze or certification claim.
