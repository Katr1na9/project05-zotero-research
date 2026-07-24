# Part B B3 synthetic capture fixture boundary v0.8

Status: **B3_CAPTURE_FIXTURE_LOCAL_ONLY**

This slice adds a deterministic, synthetic fixture path around the frozen B3
eight-dimensional cost trace instrumenter. It consumes evaluator-supplied
integer events and emits a wrapper containing the existing B3 trace plus
explicit provenance:

```text
source_kind=FIXTURE_SYNTHETIC
measurement_class=NOT_PRODUCTION_MEASUREMENT
production_adapter_authority=false
```

The fixture never reads an operating-system clock, CPU or memory counter,
billing API, connector, holdout, or Part A Executor. It is not a production
capture measurement and cannot be described as one.

## Frozen behavior

- The existing B3 policy and `part-b-cost-trace.schema.json` are read-only
  upstream inputs.
- The eight dimensions, units, exact rational arithmetic and event-order
  invariance are inherited from B3.
- Missing dimensions require an explicit reason and remain
  `UNKNOWN_NOT_ZERO`; implicit numeric zero is forbidden.
- Mixed currencies fail closed. This fixture has no FX source or normalization
  authority.
- The result contains no scalar cost, scalarization, performance claim,
  execution result, holdout result, certificate or `CERTIFIED_STOP`.

`FIXTURE_SYNTHETIC` provenance is an evidence boundary, not an admission or
certification boundary. It does not close SI-006, grant B5 execution authority,
release a holdout, or add any Part A authority.

## Explicitly outside this slice

Real OS/CPU/memory/billing capture, production adapters, sampling, Planner/M3*,
scalarization, superiority claims, LLM and data acquisition remain outside the
approved scope. Holdout release: `DENY`. `CERTIFIED_STOP` remains outside the
approved scope.
