# Part B claims and CERTIFIED_STOP DENY contract v0.8

## Frozen ceiling

The simultaneous state is:

```text
slice_status=CLAIMS_STOP_DENY_GATE_ONLY
claim_ceiling_remainder=CONTRACT_CONSISTENCY_ONLY
scalarization_authority=false
scalarization_decision=DENY
performance_superiority_authority=false
performance_superiority_decision=DENY
stop_authority=NONE
CERTIFIED_STOP=NOT_AUTHORIZED
```

## Decision table

| Request | Decision |
|---|---|
| Contract consistency check with no elevation target | `NO_CLAIM_OR_STOP_AUTHORIZATION_REQUEST` |
| `SCALARIZED_RANKING` | `DENY` |
| `PERFORMANCE_SUPERIORITY` | `DENY` |
| `CERTIFICATE_ISSUED` | `DENY` |
| `CERTIFIED_STOP` | `DENY` / `NOT_AUTHORIZED` |
| Missing, unknown or contradictory fields | fail-closed `DENY` |

The local record is deterministic. It carries no weights, results,
certificate payload or system status. A sampler stub, capture fixture or
admission record is never accepted as stop proof.

## Authority boundary

Holdout release and PB-SI-006 download remain `DENY`; PB-SI-008 remains
`NOT_OPENED`; B5 execution remains `NOT_ESTABLISHED`. There is no Planner,
sampling, connector, LLM, holdout, certificate or stop execution here.

This is a **DENY GATE ONLY**. **PART A KERNEL GAMMA UNCHANGED** is a hard
boundary. Enabling scalarization, superiority claims, certificate issuance
or Part B `CERTIFIED_STOP` requires **SEPARATE HIGHEST-STRINGENCY
AUTHORIZATION**.
