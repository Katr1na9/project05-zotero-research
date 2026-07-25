# LLM evidence compiler BETH single-file acquisition amendment v0.1

Status: `authorized_bounded_source_gate_only`
Date: 2026-07-18
Parent authority: `authority-lock-v0.6.json`

## User decision

The user explicitly approved continuing the next Gate after the metadata-only
decision. This amendment grants only a bounded acquisition and read-only source
audit for one BETH version-3 process-event file.

## Exact authorized object

- dataset: `katehighnam/beth-dataset`;
- dataset version: `3`;
- file: `labelled_2021may-ip-10-100-1-105.csv`;
- maximum source files: `1`;
- maximum downloaded bytes: `536870912` (512 MiB);
- destination: a Git-ignored quarantine directory;
- credentials: no credential or session material may be written to the
  repository.

The request must send `owner_slug`, `dataset_slug`,
`dataset_version_number=3`, and the exact `file_name` as independent fields.
The final response identity and filename must be checked before parsing. A
response that is an archive, HTML page, JSON error, a different file, or the
whole 928,188,305-byte dataset fails closed.

## Authorized checks

1. Freeze the downloaded byte count and SHA-256 before parsing.
2. Recheck exact Kaggle version-3 metadata and official CC0 legalcode evidence.
3. Scan the single CSV and any returned headers for conflicting embedded or
   nested license notices.
4. Validate the published 14-feature plus `sus`/`evil` process-event schema.
5. Run exact and 5-gram near-duplicate scans against the existing hash-only
   protected-family lock.
6. Strip `sus`, `evil`, original split, filename, host-role and scenario context
   before any candidate logic.
7. Run a read-only, record-local G0 count audit and emit counts/hashes only.

## G0 truth boundary

Candidate support may use only values explicit in the same CSV row. Eligible
fields are timestamp, process ID, parent-process ID, process name, host name,
event ID/name, argument count/arguments and other fields confirmed by the
schema audit. A parent process name may not be joined from another row. Missing,
ambiguous, malformed or truncated values require abstention.

`sus`, `evil`, attack/benign labels, original benchmark split, filename, host
role and attack narrative may not select records, candidates, predicates,
targets, splits, checkpoints or reported success. Changing `sus` or `evil`
alone must not change the G0 audit result.

## Pass and hard-stop conditions

The family may be reported as a fourth *candidate* G0-positive training family
only if all of the following are true:

- exact file/version identity and SHA-256 are frozen;
- license/nested-notice checks pass without conflict;
- schema and prohibited-supervision checks pass;
- protected exact and near-duplicate matches are zero;
- at least 150 unique, pointer-bound record-local candidates remain;
- no normalized records or candidate pairs are written.

Failure of any condition leaves the formal data Gate closed. Counts from this
source Gate do not authorize pair construction or model work.

## Still not authorized

This amendment does not authorize a second BETH file, the whole BETH archive,
normalization output, candidate-pair construction, dependency changes,
tokenizer or Qwen downloads, QLoRA training, smoke/formal inference, C07-C12
model execution, M3 runtime integration, `run_mvp.py` changes, or frozen
case/result rewrites.
