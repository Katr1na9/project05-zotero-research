# LO2v2 index bounded audit attempt 2 launcher failure

## Disposition

Attempt 2 is exhausted. Its authority at `617d3ea0be53f030e6c331d5d15bcac6c377c88a` must not be reused.

This is a sanitized launcher failure record, not a data-audit result.

## Failure

- Target: `lo2v2_index_json`
- Stage: outer PowerShell script load
- Reason code: `windows_powershell_execution_policy_script_disabled`
- Exit code: `1`
- Cause: Windows PowerShell refused to load the committed corrected launcher because script execution is disabled by the active system execution policy.
- Corrected launcher body executed: no
- Python process started: no
- Audit script started: no
- 300-second timeout reached: no
- Automatic retry, resume, execution-policy bypass, or alternate launcher: none

## Prelaunch checks

Before invocation, the attempt-2 authority, corrected launcher, launcher amendment, attempt-1 failure result, reader amendment, audit contract, and audit script identities matched. All six reader component size and SHA-256 checks passed. The reserved audit-result paths were absent.

The target JSON was not statted, opened, read, parsed, or hashed.

## Scientific boundary

No privacy, notice, schema, manifest, lineage, label, v1/v2 overlap, or pointer finding exists. No source role or family, lineage, sample, or quota credit is awarded. The effective catalog, training data, baseline, fine-tuning, Kernel, Gamma, M3, and L2 Gate remain unchanged.

The reserved bounded data-audit result paths remain absent because no data-audit process ran.

## Stop condition

Do not rerun attempt 2, add `-ExecutionPolicy Bypass`, use an alternate launcher, or infer a data-audit verdict. No third attempt is authorized.
