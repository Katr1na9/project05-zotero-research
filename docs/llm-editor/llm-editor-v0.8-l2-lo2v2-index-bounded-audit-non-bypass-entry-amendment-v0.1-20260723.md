# LO2v2 index bounded audit non-Bypass entry amendment

## Status

The non-Bypass entry is frozen but has not been executed. This amendment grants no attempt by itself.

## Entry surface

The new entry uses the already installed and hash-pinned CPython reader executable. It:

- does not load a PowerShell script;
- does not change or bypass host execution policy;
- contains no `ExecutionPolicy` option;
- does not use a shell or subprocess;
- validates its own authority and all pinned artifacts;
- hands control to the pinned audit script in the same process using `runpy`;
- fixes the audit mode to `execute`;
- exposes no `plan` mode.

The entry passed Python AST parsing. It was not executed, and the target JSON was not accessed.

## Supervision

The invocation carries `--external-supervisor-seconds 300` as a fail-closed guard. The caller must independently enforce the 300-second wall timeout.

## Attempt boundary

Attempts 1 and 2 remain permanently exhausted. This amendment does not itself authorize attempt 3. A separately committed authority must:

- name `lo2v2_index_json`;
- authorize exactly one attempt numbered 3;
- pin the non-Bypass entry SHA-256;
- pin the trusted CPython and reader identities;
- retain all reader and audit caps;
- prohibit retry, resume, execution-policy override, alternate entry, and attempt 4;
- treat entry-process start, guard failure, timeout, success, or audit failure as consuming attempt 3.

## Scientific boundary

The entry does not approve a source role, write the effective catalog, award family/lineage/sample/quota credit, generate training data, run baseline or fine-tuning, modify Kernel/Gamma/M3, or pass the L2 Gate.
