# Part B B3 eight-dimensional cost instrumentation v0.8

Status: **LOCAL REVIEW — DETERMINISTIC TRACE AGGREGATION**

```text
B3_COST_INSTRUMENTATION
capture: evaluator-supplied integer events
UNKNOWN_NOT_ZERO
SEPARATE_NOT_HIGH_COST
sampling_authority=false
scalarization_authority=false
performance_claim_authority=false
CERTIFIED_STOP: NONE
```

## 1. Source events

The instrumenter consumes already captured, versioned events. It deliberately
does not call a clock or operating-system counter:

| Event | Required integer fields | Dimension |
|---|---|---|
| `HUMAN_ACTIVITY` | `duration_ns` | `T_human` |
| `EXECUTOR_WALL_INTERVAL` | `start_ns`, `end_ns` | `T_wall` |
| `CPU_ACCOUNTING` | `cpu_delta_ns` | `T_CPU` |
| `MEMORY_INTEGRAL` | `byte_nanoseconds` | `M_byte_sec` |
| `SOURCE_SCAN` | `bytes_scanned`, `records_scanned` | `D_scan`, `N_record` |
| `BILLED_USAGE` | `currency_code`, `currency_microunits` | `C_money` |
| `AUTHORIZATION_ACTIVITY` | `duration_ns` | `T_auth` |

Fields must be exact non-negative integers; booleans and binary floats are
rejected. Every event has a unique `event_id`. Event ordering cannot change
the result.

## 2. Aggregation

- `T_human`, `T_CPU`, `M_byte_sec`, `D_scan`, `N_record`, `C_money` and
  `T_auth` are sums after unit conversion.
- `T_wall` is the outer attempt envelope:
  `max(end_ns) - min(start_ns)`. Overlapping intervals are not double-counted.
- Nanoseconds and byte-nanoseconds are divided by exactly `1_000_000_000`;
  outputs are reduced rational numerator/denominator objects.
- A dimension is `MEASURED` only when at least one matching source event
  exists. A measured zero therefore still has provenance.

If no event exists, the caller must explicitly declare an approved missing
reason. Otherwise the entire request fails closed. An UNKNOWN value is JSON
`null`, never numeric zero.

## 3. Money and feasibility

`C_money` is summed only within one declared ISO-4217 currency. Mixed
currencies fail as `NO_IMPLICIT_FX`; B3 neither downloads exchange rates nor
selects a normalization date.

Feasibility remains separate under `SEPARATE_NOT_HIGH_COST`. For an
infeasible or failed action, B3 preserves any measured overhead and explicit
UNKNOWN dimensions. It never substitutes an arbitrarily large cost and never
creates a scalar cost.

## 4. Trace identity and authority

The output binds the B3 policy hash and a canonical source-trace hash. The
trace itself has a canonical document hash. These hashes prove identity, not
measurement truth or performance.

The output contains the eight-dimensional vector, completeness and
feasibility metadata. It has no action outcome, evidence, planner score,
certificate or system state. `sampling_authority=false`,
`scalarization_authority=false`, `performance_claim_authority=false`, and
`CERTIFIED_STOP` remains outside B3.
