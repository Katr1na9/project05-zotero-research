# LO2v2 index bounded audit attempt 1 launcher failure

## Disposition

The single execution authority committed at `f70b2ec3b96a44c1faf0079ab7188077c71411ef` is exhausted and must not be reused.

This is a sanitized launcher failure record, not a data-audit result. The Python process and audit script never started.

## Failure

- Target: `lo2v2_index_json`
- Stage: external supervisor child-process creation
- Reason code: `windows_start_process_environment_key_collision_path_case`
- Cause: Windows `Start-Process` rejected the inherited environment because it exposed duplicate case-insensitive `Path/PATH` keys.
- Python process started: no
- Watchdog started: no
- Automatic retry or resume: no
- Alternate launcher used: no
- Temporary stdout/stderr: both zero bytes

## Prelaunch checks

Before the failed launcher call, the committed activation authority, frozen authority, reader amendment, audit contract, audit script, and acquisition-result hashes matched. All six reader component size and SHA-256 checks passed. Both reserved audit-result paths were absent.

The target JSON was not statted, opened, read, parsed, or hashed during the prelaunch checks or the failed launcher call.

## Scientific boundary

No privacy, notice, schema, manifest, lineage, label, v1/v2 overlap, or pointer finding exists. No source role or family, lineage, sample, or quota credit is awarded. The effective catalog, training data, baseline, fine-tuning, Kernel, Gamma, M3, and L2 Gate remain unchanged.

The reserved bounded data-audit result paths remain absent because no data-audit process ran.

## Next gate

A corrected direct-invocation launcher amendment and a new separately hash-pinned one-execute authority are required. Neither `plan` nor `execute` may run without a further explicit authorization.
