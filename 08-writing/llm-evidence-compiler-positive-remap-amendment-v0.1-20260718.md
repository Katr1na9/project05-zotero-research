# Project05 LLM evidence compiler positive-remap amendment v0.1

Status: `approved_dependency_free_parser_and_read_only_audit_only`  
Date: 2026-07-18  
Evidence: `llm-evidence-compiler-positive-source-gap-audit-v0.1-20260718/positive-source-gap-audit-v0.1.md`

## Decision

Authorize new versioned, record-local positive proposal parsers for:

1. CAM-LDS Linux Audit `EXECVE` argument fields;
2. CAM-LDS hex `PROCTITLE` command-line fields;
3. Loghub Linux `kernel: Out of Memory: Killed process PID (name).` messages.

Authorize a read-only audit against the already exclusion-passed historical records. The audit may report projected G0-positive counts and family diversity but may not write normalized records or candidate pairs.

## Truth boundary

- CAM subject, command, timestamp and pointer must all come from the same bound audit record.
- Loghub host/kernel, PID, process name and pointer must all come from the same bound log line.
- Quoting and hex decoding must be deterministic, reversible and tested.
- A malformed, partial or ambiguous record yields no candidate.
- Existing CAM placeholder proposals remain rejected.
- Existing Loghub `null_eligible_candidate` fields are ignored for positive extraction and receive zero negative credit.
- No attack/benign label, path, scenario, TTP or model output may select or label a record.

## Remaining hard stop

Even if the projected counts reproduce 166 CAM and 193 Loghub candidates, train will have only three G0-positive families. BETH remains metadata-only and requires a separate user authorization before acquisition. Therefore formal pair construction, tokenizer/model download, environment modification, training, inference and M3 runtime integration remain prohibited.

