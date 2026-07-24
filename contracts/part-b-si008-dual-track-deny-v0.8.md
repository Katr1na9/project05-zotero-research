# PB-SI-008 dual-track DENY contract v0.8

## Frozen status

The three normative states are simultaneous:

```text
part_b_status=OUTSIDE_AUTHORIZED_TRACK_DENY
experiment_track_status=MAY_PROCEED_UNDER_SEPARATE_AUTHORITY
PB-SI-008=NOT_OPENED
```

The contract is a **dual-track separation** gate, **not a global LLM ban**.
It leaves independent experiment activity to separate authority and never
uses the experiment track as Part B evidence.

## Deterministic decision table

| Request | Part B decision | Experiment-track decision |
|---|---|---|
| `EXPERIMENT_TRACK_ONLY` + `NONE` | `NO_PART_B_ADMISSION_REQUEST` | `NO_INTERFERENCE_SEPARATE_AUTHORITY_REQUIRED` |
| `PROMOTE_TO_PART_B` + `EVIDENCE` | `DENY` | `NO_INTERFERENCE_SEPARATE_AUTHORITY_REQUIRED` |
| `PROMOTE_TO_PART_B` + `CLAIM` | `DENY` | `NO_INTERFERENCE_SEPARATE_AUTHORITY_REQUIRED` |
| `PROMOTE_TO_PART_B` + `AUTHORITY` | `DENY` | `NO_INTERFERENCE_SEPARATE_AUTHORITY_REQUIRED` |
| `PROMOTE_TO_PART_B` + `PASS_CONDITION` | `DENY` | `NO_INTERFERENCE_SEPARATE_AUTHORITY_REQUIRED` |
| Missing, unknown or contradictory fields | `DENY` | `NO_INTERFERENCE_SEPARATE_AUTHORITY_REQUIRED` |

References are classified in memory and never dereferenced. There is **no
real LLM call** and **no experiment artifact read**. No experiment output,
payload, path contents, label, result or test outcome is part of the policy,
record, manifest or validation evidence.

## Authority ceiling

```text
part_b_evidence_authority=false
part_b_claim_authority=false
part_b_authority_grant=false
part_b_pass_condition_authority=false
llm_execution_authority=false
experiment_artifact_access_authority=false
holdout_release=DENY
pb_si_006_download=DENY
pb_b5_execution=NOT_ESTABLISHED
pb_b8_si_004=OPEN
stop_authority=NONE
```

`PB-SI-008` is not opened by this gate. The result cannot become a Part A or
Part B certificate, `CERTIFIED_STOP`, empirical claim, performance claim or
proof that an independent experiment succeeded or failed.
