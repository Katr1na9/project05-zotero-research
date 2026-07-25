# Positive-source gap audit search protocol v0.1

Date frozen: 2026-07-18  
Scope: metadata, license, schema, independence, and published-use evidence only  
Download authority: none

## Question

Can Project05 obtain at least two additional train and one additional training-validation source families whose records support pointer-bounded candidate SPO/time labels through exact fields or frozen mechanical parsing?

## Candidate routes

1. Previously rejected packet-null candidates reconsidered only as positive-edge sources: BETH, LID-DS, ProvSec.
2. Independent public host/network telemetry: LANL unified host/network datasets and comparable institutional sources.
3. No-download rescue of already approved records: fresh explicit-edge parsing from CAM-LDS audit messages or Loghub messages. Legacy null labels receive zero credit and are never renamed.

## Hard gates

- official or repository-pinned license permits the intended local research use;
- family is independent of Project05 C07–C12 test families and current train/validation families;
- records expose process/file/network/time values or a source string that a frozen parser can recover;
- no ATT&CK/TTP, actor, scenario, path name, attack/benign label, or missing annotation is used as target truth;
- source can be assigned to exactly one split without publisher/family overlap;
- payload exclusion scan is required before any future normalization;
- this review cannot authorize downloads, normalization, pair construction, tokenizer/model access, runtime changes, training, or inference.

## Frozen searches

1. Academic evidence for BETH, LID-DS, ProvSec schemas and published dataset use.
2. Official license and repository metadata for BETH, LID-DS, ProvSec.
3. Academic and official evidence for LANL host/network security datasets.
4. Published/official schema evidence for mechanically parsing Linux audit/EXECVE and Loghub Linux messages into explicit event relations.

## Decision labels

- `candidate_for_source_gate`
- `conditional_candidate_needs_license_or_schema_check`
- `method_only_no_new_family_credit`
- `reject_license`
- `reject_truth_contract`
- `reject_independence_or_test_overlap`
- `reject_insufficient_fields`

Absence language is bounded to the frozen searches and is not a claim that no suitable source exists globally.
