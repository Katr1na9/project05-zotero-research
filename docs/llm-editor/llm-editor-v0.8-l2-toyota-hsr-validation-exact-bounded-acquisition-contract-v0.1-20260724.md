# Toyota HSR validation archive exact bounded acquisition contract

## Frozen target

Only the following immutable object is in scope:

| Field | Frozen value |
|---|---|
| Target ID | `toyota_hsr_place_action_validation_archive` |
| Zenodo record | `4578539`, revision 3 |
| Source key | `place_action_validation.tar.gz` |
| URL | `https://zenodo.org/api/records/4578539/files/place_action_validation.tar.gz/content` |
| Exact bytes | `365983836` |
| MD5 | `76cb0cab741c3a55eaf662df979f4637` |
| Container | gzip-compressed tar |
| Curator-declared trials | 6 successful trials |

This contract does not authorize downloading the object.

## Why this object

It is the smallest immutable archive in the record and still contains more than four curator-declared placement trials. That makes it the narrowest possible future acquisition for bounded audit feasibility.

The selection does not inherit either part of the curator description:

- `validation` does not make the object Project05 validation or development data;
- `successful` does not make the object label-free, safe, representative, positive, observed, or suitable for training.

## Excluded objects

The following are outside the contract:

- `place_action_train.tar.gz`;
- `place_action_test.tar.gz`;
- every other revision or concept-record object;
- mirrors, caches, byte ranges, partial objects, member-only downloads, slices, extracted subtrees, transformed tables, and renamed objects.

There is no automatic fallback to train or test after failure.

## Future acquisition controls

A future attempt requires, in order:

1. a committed execution-authority document naming exactly `toyota_hsr_place_action_validation_archive` and pinning this contract hash;
2. a frozen launcher or exact invocation;
3. non-network preflight verifying all hashes, executable identity, target absence, and capacity;
4. a separate activation;
5. an explicit authorization for one initial attempt.

The future maximum is one initial attempt. Automatic retry and resume are forbidden. A terminal failure must stop without source substitution or fallback.

## Integrity and hard stop

If a future acquisition is authorized:

1. write only to the frozen local path;
2. require exact size `365983836`;
3. compute MD5 only after exact size passes;
4. require MD5 `76cb0cab741c3a55eaf662df979f4637`;
5. report verified only when both checks pass;
6. hard stop.

Successful identity verification does not authorize reading the gzip header, parsing tar headers, listing member names, decompressing, extracting, or reading any member.

## Required later audit boundary

Any later archive work needs a new contract and authority that freeze:

- gzip and tar reader identities and hashes;
- header, member-count, path-token, per-member, total-byte, decompressed-byte, and wall-time caps;
- nested notice and third-party rights handling;
- image, depth, rendered-model, calibration, split, outcome, and frame-annotation exclusion;
- outcome-blind trial manifest and duplicate/retry/partial/interruption/collision/reset policy;
- visual and non-visual privacy rules;
- sanitized aggregate-only output;
- unbound pointer suggestions and deterministic source round trip.

No raw member path, trial ID, timestamp, image, telemetry value, annotation, or outcome may be persisted by default.

## Scientific stop Gate

Even a size-and-MD5 verified archive:

- is not Project05 validation, development, or train data;
- does not establish six verified lineages or samples;
- does not award family, lineage, sample, or quota credit;
- does not bind a pointer;
- does not fill Direction 04;
- does not write the effective catalog;
- does not pass L2;
- does not start a model, baseline, fine-tuning job, or St.Gallen v0.2.

## Current scope

No HTTP request, download, launcher, authority, activation, retry, resume, gzip/tar open, member listing, decompression, extraction, payload read, catalog change, role, credit, training, baseline, fine-tuning, Kernel, Gamma, M3, L2, commit, or push is authorized or performed by this contract-drafting step.
