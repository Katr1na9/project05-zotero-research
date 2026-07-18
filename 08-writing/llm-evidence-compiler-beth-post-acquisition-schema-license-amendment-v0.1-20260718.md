# LLM evidence compiler BETH post-acquisition schema and license amendment v0.1

Status: `authorized_exact_observed_schema_and_composite_license_evidence`
Date: 2026-07-18
Parent authority: `authority-lock-v0.8.json`

## Post-acquisition facts

The authorized Kaggle version-3 single-file response produced exactly one CSV:

- CSV bytes: `99,560,489`;
- CSV SHA-256:
  `528AD1F4813A9FBB839F3C4B37F7B1A861F0E33D998FB46E6D59CAEF119FB597`;
- transport ZIP bytes: `3,997,971`;
- transport ZIP SHA-256:
  `82AEEBC2CE0D0027EDC9DB794F11FC50F536557AA2EBA5031DAA671B41CE1E0A`;
- ZIP members: one exact allowlisted CSV;
- CRC check: passed.

The exact CSV header is:

```text
timestamp,processId,parentProcessId,userId,processName,hostName,eventId,eventName,argsNum,returnValue,args,sus,evil
```

This is an observed Kaggle v3 per-host schema variant. Relative to the paper's
14-feature description, it omits `threadId`, `mountNamespace`, and
`stackAddresses`. The amendment does not impute these fields and does not
relax any G0 truth rule. The fields required by the record-local parent-process
candidate (`timestamp`, process ID, parent-process ID, process name, host name
and event name) remain explicit in the same row.

## Schema decision

The source Gate may validate this one exact observed header instead of falsely
requiring absent columns. Any additional, missing, duplicated, reordered or
renamed column fails closed. `sus` and `evil` remain prohibited supervision:
they may be checked for presence and stripped, but may not select records,
candidates, targets, splits or reported success.

This is a source-format correction, not permission to normalize records or
construct training pairs.

## Composite license evidence

Kaggle's current dataset-view response identifies the dataset, current version
3 and `CC0: Public Domain`, but its embedded `files` list is empty. Kaggle's
official authenticated dataset-files endpoint independently returns 15 files,
including the exact authorized CSV. The frozen Kaggle page extract also lists
the same 15 filenames. Therefore the post-acquisition license/identity check
must use all of the following without inventing fields in any source response:

1. official dataset-view JSON for dataset identity, version and CC0;
2. official dataset-files JSON for the 15-file inventory;
3. the tracked Kaggle page extract, SHA-256
   `1ABF7C4AFF6DF502AAFF79FE3919E36D1752331A10800357AB0FDEE32704D231`;
4. the explicit version-3 single-file request and exact response/member names;
5. official CC0 1.0 legalcode, SHA-256
   `A2010F343487D3F7618AFFE54F789F5487602331C0A8D03F49E9A7C547CF0499`.

The earlier metadata note reported a different byte count/hash for the page
extract. This amendment corrects that statement using the current tracked file
bytes; it does not alter the prior locked document.

Any mismatch in dataset identity, version, CC0 name, the exact 15-file set,
page-extract hash, legalcode hash, retrieved CSV hash or header fails closed.

## Unchanged boundary

Only license, schema, protected-payload and read-only counts/hashes audits are
authorized. No normalized record, candidate pair, tokenizer, Qwen weight,
training run, inference, M3 integration, Paper A change or frozen-result change
is authorized.
