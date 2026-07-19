# LLM evidence compiler tokenizer-length Gate v0.1 — 2026-07-19

Status: `failed_closed_tokenizer_length_gate`

## Authorized execution

The user authorized continuation into the previously pending tokenizer-length
Gate. The run retrieved only four files from
`Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28`:
`merges.txt`, `tokenizer.json`, `tokenizer_config.json` and `vocab.json`.
Their total size is 11,487,622 bytes. An isolated
`tokenizers==0.21.4` wheel was used without dependencies.

The isolated runtime contained no Transformers, Torch, PEFT or bitsandbytes.
No model configuration, model weight, adapter, optimizer or checkpoint was
downloaded or created.

## Frozen v0.1 result

All 1,500 complete system + user + assistant serializations were encoded with
`add_special_tokens=false` and no truncation or padding.

| Scope | Count | p50 | p95 | Max | Over 1024 |
|---|---:|---:|---:|---:|---:|
| Overall | 1,500 | 808 | 1,131 | 2,094 | 173 |
| Train | 1,200 | 835 | 1,144 | 2,094 | 173 |
| Training-validation | 300 | 715 | 800 | 873 | 0 |

Family over-limit counts were CAM-LDS 17, SOCBED 131, Atomic 25, and zero for
BETH, Loghub and Zeek. The Gate failed as required. No example was excluded,
truncated or rewritten; `formal_data_gate_passed=false`.

A second independent audit was byte-identical at SHA-256
`C00267542C0CAC3A7D4CD9ED1EBF5FBC1EFF8969DCFDF54D19989534606AFDC6`.

## Diagnostic and proposed resolution

The v0.1 chat record redundantly exposed full source-record metadata and
provenance hashes in addition to payload, candidate, normalized edge and output
pointer. A compact model-visible record that keeps full payload, candidate,
bound pointer, normalized edge and output pointer reduces the current selected
set to p95 909, but 27 complete long-command examples still exceed 1,024.

A deterministic in-memory preflight then moved past over-length pair candidates
within the same frozen source family and negative-generator quota. It completed
all 1,500 examples without truncating any accepted payload:

| Scope | Count | p50 | p95 | Max | Over 1024 |
|---|---:|---:|---:|---:|---:|
| Overall | 1,500 | 589 | 881 | 1,021 | 0 |
| Train | 1,200 | 611 | 897 | 1,021 | 0 |
| Training-validation | 300 | 492 | 580 | 659 | 0 |

The proposed v0.2 amendment preserves all source-family, split, support balance,
Zeek and N1–N4 quotas. It is not active without explicit user approval.

## Verification and boundary

The tokenizer Gate test suite passes 7 tests and 5 subtests. The tokenizer lock
and failed result are SHA-256 anchored by `authority-lock-v0.14.json`.

Model files, training runtime, QLoRA, inference, C07–C12 model execution, M3
integration, Paper A, `run_mvp.py` and frozen case/results remain untouched.
