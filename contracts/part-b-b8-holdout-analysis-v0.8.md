# Part B B8 holdout-analysis contract v0.8

Status: **LOCAL REVIEW — NO-DATA PREREGISTRATION**

## 1. Frozen domain

The only registered analysis identifier is
`HOLDOUT-ANALYSIS-V0.8-001`. The registry is finite and does not permit
dynamic additions.

The preregistration replays the complete B4 baseline roster, including the
evaluator-only oracle identity, without changing any B4 role. Roster presence
does not admit an implementation or make an evaluator-only method eligible
for a deployable comparison.

The split commitment has semantics
`ABSTRACT_CONTRACT_FIXTURE_NOT_DATA`. Its SHA-256 value is a commitment to an
inert contract phrase. It contains no record identifiers, labels, outcomes or
real-source information and proves no split validity.

## 2. Release gate

The policy default is `DENY`. All of the following would be required before a
future request could even be considered:

1. the B4 roster is frozen;
2. the B4 isolation policy is bound;
3. a real split commitment is frozen;
4. the real source has separate authorization under `PB-SI-006`;
5. the statistical plan is frozen; and
6. statistical execution receives separate explicit authorization.

Failure of any condition is `FAIL_CLOSED_NO_ACCESS`. The current contract
sets `contract_only_no_release=true`, so satisfying the Schema is never an
access grant.

## 3. Feedback prohibition

HOLDOUT information may not flow to TRAIN, TUNE, EVALUATION, a Planner or any
model. Post-holdout model updates are forbidden in this slice. The contract
does not read holdout labels and does not read holdout results.

Timeout, resource exhaustion and missing outcome are `UNKNOWN_NO_RANK`.
Infeasibility remains a separate channel. Partial information is
`UNKNOWN_INCOMPLETE_NO_RANK`; none of these states becomes a loss, a zero, an
UNSAT result or a ranking.

## 4. Evidence limit

Passing these contracts proves only that the frozen documents are mutually
consistent. It gives NO EXTERNAL VALIDITY, NO PERFORMANCE CLAIM, NO HOLDOUT
LABEL, NO HOLDOUT RESULT and NO STATISTICAL EXECUTION.

`PB-SI-006` and `PB-B5-SI-001` remain OPEN. B9, certificates, system status and
`CERTIFIED_STOP` remain outside B8 authority.
