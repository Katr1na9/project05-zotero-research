# LLM evidence compiler BETH single-file source Gate v0.1

Status: `passed_candidate_fourth_family_source_gate`
Date: 2026-07-18
Current authority: `authority-lock-v0.9.json`

## Outcome

The exact authorized BETH v3 per-host process-event file passed the bounded
source Gate and may count as the fourth *candidate* G0-positive training
family. It has not been converted into normalized records or training pairs.
The formal data Gate, tokenizer/model work and M3 integration remain closed.

| Check | Result |
|---|---|
| exact dataset/version | `katehighnam/beth-dataset`, v3 |
| exact CSV | `labelled_2021may-ip-10-100-1-105.csv` |
| CSV | 99,560,489 bytes; SHA-256 `528AD1F4813A9FBB839F3C4B37F7B1A861F0E33D998FB46E6D59CAEF119FB597` |
| official ZIP transport | 3,997,971 bytes; SHA-256 `82AEEBC2CE0D0027EDC9DB794F11FC50F536557AA2EBA5031DAA671B41CE1E0A` |
| ZIP identity/integrity | one exact root CSV member; deflated; CRC passed |
| license | Kaggle v3 `CC0: Public Domain` + official 15-file inventory + official CC0 legalcode passed |
| schema | exact observed 13-column header passed |
| protected exact / near | 0 / 0; maximum Jaccard 0.20 at threshold 0.85 |
| records | 409,931 |
| eligible record-local G0 candidates | 409,931 |
| abstained | 0 |
| minimum | 150 |
| candidate digest | `4A371C789A220DF45DC2DD57EA4792E9899948F216B3A40A6DBBD37A8CDC26AB` |

## Transport correction

Kaggle's authenticated single-file API returned an official ZIP wrapper named
`labelled_2021may-ip-10-100-1-105.csv.zip`, not the 928 MB dataset archive. The
v0.7 downloader initially rejected this response before reading its body. v0.8
then allowed only this exact wrapper with exactly one exact CSV member. Any
second member, directory, traversal path, encryption, symbolic link,
unsupported compression, CRC error, size excess or compression ratio over
100:1 fails closed and deletes all partial outputs.

The successful ZIP contained one member, compressed size 3,997,761 bytes,
uncompressed size 99,560,489 bytes, deflate method 8 and CRC `C4A3290B`.
Signed URL query material and Kaggle credentials were not persisted.

## Observed schema correction

The paper describes 14 raw features plus two labels, but the exact Kaggle v3
per-host file contains these 13 columns:

```text
timestamp,processId,parentProcessId,userId,processName,hostName,eventId,eventName,argsNum,returnValue,args,sus,evil
```

`threadId`, `mountNamespace` and `stackAddresses` are absent. v0.9 freezes the
real header rather than imputing those fields. The record-local G0 basis still
has timestamp, process/parent IDs, process name, host and event name. `sus` and
`evil` are present but stripped before candidate logic; no label, split,
filename, host-role or scenario context receives supervision credit.

## Composite license evidence

The official Kaggle dataset-view response binds dataset identity, current
version 3 and `CC0: Public Domain`, but its embedded file list is empty. The
official authenticated dataset-files endpoint separately returned exactly the
15 frozen filenames and included the allowlisted CSV. This was cross-checked
against the tracked Kaggle page extract and the official CC0 legalcode hash.

The earlier metadata note's page-extract byte/hash claim did not match the
tracked file. v0.9 records the actual tracked SHA-256
`1ABF7C4AFF6DF502AAFF79FE3919E36D1752331A10800357AB0FDEE32704D231`
without editing the earlier hash-locked document.

## Read-only scientific result

The audit streamed all 409,931 records. It emitted only counts and the digest
above. Exact/near protected scans were clean, the G0 minimum was exceeded by
more than three orders of magnitude, and no record required abstention under
the frozen row-local parent-process rule.

This establishes source sufficiency only. It does not demonstrate model
quality, does not make BETH same-distribution with C07-C12, and does not support
an “APT-domain model” claim.

## Verification and artifact hashes

| Artifact | SHA-256 |
|---|---|
| Kaggle metadata bundle | `478E4AB567F4F2D00DD7717BA01C1A3050177800E8BFCEC0AAAE0552FE301129` |
| acquisition manifest | `B0B44A408403FA0656D549599B1BC9E2A673A7B41B9F4E88D48EDA9D15C449C1` |
| source-Gate audit | `EF54A56C23BDA4988F49C4C2694F2C08EBD69A4664252CE1962C822DA13BDB5E` |
| source-Gate script | `EDDF6338241789317B20F0A69E444BD6D0FFA1BAB18100D57863477BB01A0A14` |
| BETH focused tests | 18 passed, 18 subtests passed; test-file SHA-256 `4751AD32DD5AAC730B4B452D0C344EE2AA63F2198D2339685DEC74080B104025` |
| v0.9 authority | `342D49A9CA9E47CA8A0A3168D062651B1F4E3E5282376204D960AF4F82C9940D` |
| v0.2 source contract | `703822FCB5EA3A54A939E3D3B795DD1604E7F05A40F498022C6666CE06ADF174` |
| main-worktree experiment suite | 625 passed, 6 skipped, 370 subtests passed |
| credential-material scan | 0 repository hits outside ignored quarantine |
| Python compilation / `git diff --check` | passed / passed |

Raw CSV, ZIP and legalcode bytes remain under the Git-ignored `quarantine/`
directory and must not be committed or pushed.

The linked worktree's selected adjacent suite produced 36 passes plus two
known environment-only failures: one test resolves an ignored historical
records directory through the main worktree, and one compares a legacy
CRLF-byte hash against an LF Git blob. The unchanged main worktree's full suite
passes as reported above. No frozen data or expected hash was changed to mask
these worktree-only conditions.

## Boundary and next Gate

The current family flag is `candidate_fourth_train_family=true` while
`formal_data_gate_passed=false`. The next possible task is a separately
authorized, label-blind candidate-pair construction amendment covering all
four training families and the existing held-out families. Until that Gate is
explicitly approved, no training records/pairs, tokenizer, Qwen download,
QLoRA run, formal inference or M3 runtime integration may occur.
