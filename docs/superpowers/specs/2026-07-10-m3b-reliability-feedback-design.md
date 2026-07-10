# M3b-3 Reliability Feedback Design

## Goal

Extend the Project05 M3b sequential evidence-acquisition policy with a
lightweight reliability posterior. The policy must learn only from the
observable outcome of actions it has already executed, so it can reduce repeat
waste after a source or acquisition interface returns no useful evidence.

This is intentionally not a claim that the policy can identify an unseen,
publicly indistinguishable decoy before its first execution.

## Scope

In scope:

- A Beta posterior for the reliability of a public action group.
- A sequential policy score that multiplies M3b's predicted critical-gap
  resolution probability by that posterior mean.
- Trace fields that expose the posterior before and after each action.
- Matched normal and decoy stress evaluations against M2, M3a, static M3b, and
  the oracle.

Out of scope:

- Learning from hidden `recoverable_claim_ids` before an action is executed.
- Fine-tuning an LLM, a neural sequence model, or external threat-intelligence
  retrieval.
- Claiming statistical independence among multiple masks derived from one
  attack case.

## Public Reliability Group

Each action belongs to a public group:

```text
action_type + sorted(expected_evidence_types)
```

For example, an `extend_log_window` action expected to return `local_log`
evidence belongs to a different group than `recover_network_summary` expected
to return `network_summary`. The grouping deliberately excludes action ID,
hidden recovery targets, and actual evidence content.

The initial posterior for every unseen group is `Beta(alpha=1, beta=1)`, whose
mean reliability is `0.5`. A positive yield increments `alpha`; a zero yield
increments `beta`. For an action group with no history in the current episode,
the posterior remains neutral.

## Policy and Data Flow

For every available candidate action `a` in state `s`:

```text
p_gap(a, s)  = M3b logistic model prediction from public features
r(a, s)      = alpha_group / (alpha_group + beta_group)
utility(a,s) = p_gap(a, s) * r(a, s) - lambda * cost(a)
```

The policy selects the action with maximal utility, executes it through the
existing simulator, observes only `recovered_count`, and updates the posterior
for that action's group. Its action selector receives state, public actions,
and its own local posterior only. The simulator continues to keep hidden claim
IDs out of non-oracle planner selection.

Each action trace records:

- `reliability_group`
- `reliability_mean_before`
- `reliability_mean_after`
- `predicted_gap_probability`
- `reliability_adjusted_utility`

## Evaluation Design

The model is trained only on C01-C03 and replayed only on C04-C06. Each
`case_id + mask_strategy + mask_intensity + seed` condition is paired across
planners; summaries must report the independent case count separately from the
repeated condition count.

Two evaluations are required:

1. Normal candidate-action space: adaptive M3b must not read hidden outcomes
   and its cost/success should be reported beside static M3b, M2, M3a,
   coverage-greedy, and oracle.
2. Matched zero-yield decoy stress: adaptive M3b should change subsequent
   rankings after a failure. This measures online adaptation, not clairvoyant
   detection. A repeated-decoy variant is required only if the single-twin
   stress condition cannot expose a second decision in the same group.

## Failure Handling

- Missing `expected_evidence_types` maps to the stable sentinel `unknown`.
- A no-yield action is a valid observation, not an exception.
- No actions within budget stops the episode exactly as in the existing runner.
- A posterior never reaches zero or one with the specified Beta prior, avoiding
  irreversible decisions from a single observation.

## Tests

1. A positive and a zero-yield observation update the intended group's Beta
   parameters and do not affect another group.
2. The reliability-adjusted selector changes after a zero-yield observation
   while an otherwise identical static selector does not.
3. Changing `recoverable_claim_ids` before execution does not change the
   adaptive selector's first action.
4. An episode trace records posterior values and uses feedback only after the
   corresponding action event.
5. The experiment writer creates separate adaptive-policy and stress-test
   outputs.

## Decision

This design uses a Beta posterior rather than a sequence model because the
current project has three training cases and a small action space. It introduces
a falsifiable sequential capability with interpretable uncertainty, while
leaving a later hierarchical or learned reliability estimator as a clearly
separable extension.
