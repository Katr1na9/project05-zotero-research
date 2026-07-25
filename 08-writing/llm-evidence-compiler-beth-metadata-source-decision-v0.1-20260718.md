# BETH metadata-only source decision v0.1

Status: `conditional_metadata_pass_download_not_authorized`  
Date: 2026-07-18  
Authorized action performed: public metadata retrieval only  
Corpus bytes retrieved: `0`

## Decision row

| Field | Frozen decision |
|---|---|
| candidate family | `beth_process_events` |
| intended split role | train |
| scientific role | fourth independent G0-positive training family for candidate-edge verification |
| current decision | conditional metadata pass; eligible for a separate bounded-acquisition authorization request |
| download authorized | **false** |
| normalization authorized | **false** |
| pair construction authorized | **false** |
| tokenizer/model/training authorized | **false** |
| allowed external claim | task/schema-adapted evidence compiler only; not “APT-domain model” |

## Frozen public metadata

On 2026-07-18T07:18:30.8749369Z, the unauthenticated public Kaggle
dataset-view API returned HTTP 200 for:

`https://www.kaggle.com/api/v1/datasets/view/katehighnam/beth-dataset`

| Field | Value |
|---|---|
| dataset ref | `katehighnam/beth-dataset` |
| title | `BETH Dataset` |
| current version | `3` |
| version 3 creation / last update | `2021-07-29T15:45:31.827Z` |
| version 3 status | `Ready` |
| declared total bytes | `928188305` |
| API license field | `CC0: Public Domain` |
| API response UTF-8 bytes | `13743` |
| API response SHA-256 | `5B099B428CB6CFD1B13BF52D924F501C101B733ED73D246DFD837FE5B25A6CFB` |

The API also listed ready versions 1, 2 and 3. Any future request must name
version 3 explicitly and must not silently follow a later mutable “current”
version.

The public Kaggle page extract reports 15 files for version 3:

1. `labelled_2021may-ip-10-100-1-105-dns.csv`
2. `labelled_2021may-ip-10-100-1-105.csv`
3. `labelled_2021may-ip-10-100-1-186-dns.csv`
4. `labelled_2021may-ip-10-100-1-186.csv`
5. `labelled_2021may-ip-10-100-1-26-dns.csv`
6. `labelled_2021may-ip-10-100-1-26.csv`
7. `labelled_2021may-ip-10-100-1-4-dns.csv`
8. `labelled_2021may-ip-10-100-1-4.csv`
9. `labelled_2021may-ip-10-100-1-95-dns.csv`
10. `labelled_2021may-ip-10-100-1-95.csv`
11. `labelled_2021may-ubuntu-dns.csv`
12. `labelled_2021may-ubuntu.csv`
13. `labelled_testing_data.csv`
14. `labelled_training_data.csv`
15. `labelled_validation_data.csv`

The frozen page extract is
`llm-evidence-compiler-positive-source-gap-audit-v0.1-20260718/extract-02-beth-kaggle.json`,
6,137 bytes, SHA-256
`EB43FC548185876C18BAA48E15F33989213DDE3F7053B610999554AFC12FC87B`.

## License discrepancy and resolution rule

The BETH paper states Attribution 4.0, while the exact current Kaggle version 3
metadata states CC0. This decision does not claim that the discrepancy never
existed. It binds any future acquisition request to Kaggle dataset version 3
and records the paper statement as an upstream-version discrepancy.

The Kaggle page's CC0 link resolves to the Creative Commons CC0 1.0 legalcode.
On 2026-07-18T07:18:53.9249835Z, the official UTF-8 legalcode response was
7,048 bytes with SHA-256
`A2010F343487D3F7618AFFE54F789F5487602331C0A8D03F49E9A7C547CF0499`:

`https://creativecommons.org/publicdomain/zero/1.0/legalcode.txt`

This metadata is sufficient only to request a bounded version-3 acquisition.
After acquisition, any embedded README, LICENSE, per-file notice or API
metadata that conflicts with CC0 must fail closed before normalization. The
paper's license is not substituted for missing or conflicting dataset notices.

## Proposed future bounded acquisition scope

No acquisition is performed by this decision. If separately authorized, the
first acquisition should request only the version-3 process file:

`labelled_2021may-ip-10-100-1-105.csv`

Rationale: it is a per-host process-event artifact rather than a benchmark
train/test split file or DNS-only file, and the published schema should provide
far more than the minimum 150 record-local candidates while limiting data
movement. The request must hard-stop if an individual-file, version-pinned
download cannot be made; downloading the whole 928,188,305-byte dataset is not
implicitly authorized.

Proposed acquisition limits:

- exact dataset: `katehighnam/beth-dataset`, version `3`;
- exact allowlisted file: `labelled_2021may-ip-10-100-1-105.csv`;
- maximum one source file;
- maximum downloaded bytes: 512 MiB;
- no credential persistence in the repository;
- write only to a quarantined source-gate directory;
- compute file SHA-256 before any parsing;
- run nested-notice, schema, payload-exclusion and protected-family scans;
- if the file is larger than the cap or the endpoint cannot isolate it, stop
  and return to metadata review.

## Truth and supervision prohibitions

The following fields or context may not select records, candidates, predicates,
targets, splits, checkpoints or reported success:

- `sus` and `evil`;
- attack/benign labels or anomaly labels;
- original train/validation/test membership;
- filename, host role or attack narrative;
- path-derived or scenario-derived supervision.

Only values explicit in the same bound record may support an edge: timestamp,
host name, process ID, parent-process ID, process name, event name, argument
count/arguments and other fields confirmed after schema inspection. Parent
process names may not be inferred from a different record in the G0 admission
path. Missing, ambiguous or truncated fields must abstain.

## Post-acquisition hard stops

Even after a future bounded acquisition, the file cannot count as the fourth
family until all of the following pass:

1. exact version/file identity and SHA-256 are frozen;
2. embedded license and nested notices are compatible with the metadata lock;
3. prohibited label/path/scenario fields are stripped before candidate logic;
4. protected payload exact/near-duplicate scans report zero matches;
5. a versioned parser and G0 recomputation tests pass;
6. at least 150 exact, pointer-bound candidates remain after all filters;
7. authoring code reports only counts before formal pair authorization;
8. the non-token 4+2 family Gate and later tokenizer-length Gate both pass.

## Current boundary

This document does not authorize any corpus download, dependency change,
tokenizer or Qwen access, pair construction, QLoRA training, inference or M3
runtime integration. A new authority lock and explicit user decision are
required before the proposed single-file acquisition.
