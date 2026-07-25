# LO2v2 index bounded audit corrected-launcher amendment

## Status

The corrected launcher is frozen but has not been executed. This amendment grants no attempt by itself.

## Correction

Attempt 1 failed before Python started because Windows `Start-Process` rejected duplicate case-insensitive `Path/PATH` environment keys. The corrected launcher:

- uses the PowerShell direct call operator `&`;
- does not use `Start-Process`;
- does not reserialize the environment dictionary;
- fixes the target to `lo2v2_index_json`;
- fixes the inner command to `audit_lo2v2_index_v0_1.py --mode execute`;
- accepts only the separately named attempt-2 authority;
- checks the launcher, reader, audit script, contract, attempt-1 failure record, and reserved-result gates before invoking Python.

The launcher parsed with zero PowerShell AST errors. It was not run, and the target JSON was not accessed.

## Supervision

The frozen outer invocation declares `-ExternalSupervisorSeconds 300`, but that parameter is only a fail-closed guard. The caller must independently enforce the 300-second wall timeout.

## Attempt boundary

Attempt 1 remains exhausted and its authority may not be reused. This amendment does not itself authorize attempt 2. A separately committed authority must:

- name `lo2v2_index_json`;
- authorize exactly one attempt numbered 2;
- pin the corrected launcher SHA-256;
- retain every reader/audit cap;
- keep retry and resume disabled;
- treat success, guard failure, Python failure, timeout, or audit failure as consuming attempt 2.

No third attempt is authorized.

## Scientific boundary

The corrected launcher does not approve a source role, write the effective catalog, award family/lineage/sample/quota credit, generate training data, run baseline or fine-tuning, modify Kernel/Gamma/M3, or pass the L2 Gate.
