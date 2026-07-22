# Kernel finite formal ceiling contract v0.8

Status: **IMPLEMENTED — A16 RE-REVIEW REQUIRED**

- Contract ID: `formal-ceiling-v0.8`
- Contract version: `0.8.0`
- Recorded: `2026-07-22`

## Exact definition

For a fixed canonical Gamma hash, compiled finite problem, target level, and
canonical action-catalog hash, the Kernel formal ceiling is the tuple:

1. the exact finite target candidate set;
2. every finite auxiliary-variable domain;
3. the complete Cartesian assignment bound;
4. the exhaustively enumerated legal-world subset under the compiled
   constraints; and
5. the catalog actions whose observation model is deterministic, has exactly
   one declared world dependency, and has at least one world-elimination rule.

The verifier reports `VERIFIED` only when the enumerated legal worlds exactly
match the compiler's Gamma-bound legal-world declaration and every target
candidate appears in at least one legal world.  The report binds Gamma,
catalog, compiler profile, target, domains, legal-world digest, formal actions,
deterministic observables, exclusions, guarantees, and limitations under one
canonical report hash.

This is a **model-relative formal ceiling**, not a claim that the Gamma contains
every hypothesis that could occur in reality.  It does not establish external
validity, connector correctness, action-effect correctness, or superiority to
future algorithms.

## Formal guarantees versus test evidence

The following are enforced by runtime validation and exhaustive enumeration:

- finite target and auxiliary domains;
- exact Gamma/compiled-problem hash binding;
- exhaustive traversal up to the declared Cartesian bound;
- exact equality between enumerated and declared legal worlds;
- representation of every declared result candidate;
- deterministic observation models for ceiling-eligible actions;
- explicit exclusion of heuristic/no-model/no-elimination-rule actions; and
- certificate/STOP binding to the exact ceiling report hash.

Recertification filters the compiler's complete legal-world table, never only
the support/alternative witnesses serialized in one counterexample. Level
certificate coverage must exactly match the ceiling's ordered result
candidates, legal-world count/hash, and Cartesian assignment bound; the
Checker's alternative-UNSAT query must have examined that full bound. Caller
supplied coverage booleans alone cannot satisfy the issuer.

Automated tests demonstrate these implementation properties on two frozen,
structurally different domains.  Tests are not themselves a proof that either
Gamma is an exhaustive model of the external world.

## Fail-closed boundary

| Condition | Result | Never interpreted as |
|---|---|---|
| requested target absent/different | `OUTSIDE_FROZEN_DOMAIN` | UNSAT or certification |
| requested action outside the formal action subset | `OUTSIDE_FROZEN_DOMAIN` | infeasible high-cost action |
| assignment budget below Cartesian bound | `UNKNOWN_RESOURCE_EXHAUSTED` | UNSAT |
| bad/stale/tampered Gamma, catalog, compiler binding, or world table | `INVALID_ARTIFACT` | verified ceiling |
| valid report but no approved admission policy or level-complete proof | no certificate/STOP | `CERTIFIED_STOP` |

Wall-clock timeout remains a resource condition.  A timed-out or interrupted
enumeration must be mapped to `UNKNOWN_RESOURCE_EXHAUSTED`; it cannot use the
absence of a discovered world as UNSAT.

## Frozen replay evidence

| Domain | Target candidates | Cartesian bound | Legal worlds | Formal actions | Report hash |
|---|---:|---:|---:|---:|---|
| endpoint lateral/direct Twin | 2 | 4 | 2 | 4 | `sha256:b774c330b1df0d3e7bfabd9ada03dca0b465d2ae26bc5dfb606dba4fea83a0b4` |
| supply-chain package origin | 3 | 27 | 3 | 3 | `sha256:83283e0c9a34af8f4903480f60d55f6cf9ad99995a53241caec0fd729af16804` |

The machine reports are frozen at:

- `tests/fixtures/TWIN-COUNTEREXAMPLE-001/expected/formal_ceiling.json`; and
- `tests/fixtures/TWIN-SUPPLY-CHAIN-002/expected/formal_ceiling.json`.

The admission-policy manifest is now exact-hash APPROVED, but neither ceiling
report alone authorizes production `CERTIFIED_STOP`. A separately issued and
fully bound level-complete certificate plus a new A16 Go ruling remain
independent requirements.
