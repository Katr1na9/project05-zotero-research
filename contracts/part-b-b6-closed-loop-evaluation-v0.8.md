# Part B B6 closed-loop evaluation contract v0.8

Status: **NON-EXECUTING PROTOCOL CONTRACT**

## 1. Finite protocol

Every episode declares a positive finite `finite_step_count`, a canonical
zero-based step order and the exact sequence:

```text
PUBLIC_STATE_REFERENCE
ACTION_ID_DECISION_REFERENCE
FEEDBACK_ENVELOPE_REFERENCE
```

The contract validator is deterministic. It checks identities, finite lists,
membership, ordering and hash bindings. It does not create public state,
invoke a Planner, execute an action or create feedback.

## 2. Public-state and decision boundary

The public-state reference binds the frozen B5 public-state hash and exposes
only its feasible action-ID domain. The decision reference binds that same
state hash and contains only an action ID or explicit null. A selected action
outside `feasible_action_ids` fails closed as
`FAIL_CLOSED_ACTION_NOT_FEASIBLE`; a stale state hash fails closed as
`FAIL_CLOSED_STATE_BINDING_MISMATCH`.

Action payloads, oracle labels, hidden ground truth, holdout labels, realized
outcomes, evaluator worlds, certificates and system states are not fields of
the episode contract.

## 3. Feedback boundary

The feedback envelope cross-binds case, episode, step, public-state hash,
decision hash and selected action ID. Its pointer identifies an
evaluator-supplied contract reference. The frozen example explicitly has
`availability=NOT_EXECUTED_CONTRACT_EXAMPLE`.

The envelope has no raw payload and no ownership of Claim IR. It cannot set or
change `modality`, `truth_status`, `epistemic_role` or
`certification_authority`; Firewall/admission remains outside B6.

## 4. B2 and B3 bindings

B2 is referenced only through the exact catalog, TV-policy and world-pair
decision hashes. B6 has no sampler or distribution-estimation authority and
the B2 design catalog examples remain non-executable.

B3 remains `B3_EIGHT_DIMENSION_VECTOR_ONLY`. Missing measurement is
`UNKNOWN_NOT_ZERO`; infeasibility is `SEPARATE_NO_ACTION`, never high cost.
No scalarization or implicit weighting is defined.

Timeout and resource exhaustion are `UNKNOWN_NO_RANK`; general unknown is
`FAIL_CLOSED_NO_RANK`. None of these channels is a method ranking.

## 5. Claim boundary

Contract validation can count interface conformance, feedback-boundary
conformance and failure channels, and can validate the shape of an
unscalarized resource vector. It supplies no execution evidence, performance
validity, superiority statement, certificate or `CERTIFIED_STOP`.
