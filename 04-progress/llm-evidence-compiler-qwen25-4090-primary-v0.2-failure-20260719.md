# Project05 Qwen2.5 QLoRA: RTX 4090 primary v0.2 failure record

Date: 2026-07-19

Status: `failed_or_interrupted_4090_primary_training`

## Decision

The single authorized RTX 4090 primary v0.2 run did not complete the preregistered 3 epochs / 225 optimizer steps. It stopped after optimizer step 173 with a CUDA illegal memory access raised inside `bitsandbytes` during `optimizer.step()`.

This is not the same failure as the earlier v0.1 free-memory Gate stop. The v0.32 cache-normalized memory Gate passed during v0.2, and the failure occurred before the next scheduler step, gradient reset, and memory sample could be recorded.

No automatic restart, resume, configuration change, checkpoint selection, generation, evaluation, M3 connection, or Paper A update is authorized by this failure record.

## Executed Scope

| Item | Result |
|---|---:|
| Authorized run | `primary-v0.2` |
| Completed microbatches | 2784 |
| Completed optimizer steps | 173 / 225 |
| Completed epochs | 2 / 3 |
| Saved epoch checkpoints | 2 |
| Final epoch-003 checkpoint | not created |
| Elapsed wall time | 2845.076 seconds |

Server-side checkpoint directories were observed for:

- `checkpoint-epoch-001`
- `checkpoint-epoch-002`

Each observed epoch checkpoint contains adapter-only files plus optimizer, scheduler, RNG, and trainer state. These files remain on the server. They were not downloaded or pushed.

## Failure

The terminal traceback ended with:

```text
RuntimeError: CUDA error: an illegal memory access was encountered
```

The stack trace points to:

- `execute_qwen_qlora_4090.py`, inside `run_primary`
- `optimizer.step()`
- `bitsandbytes/optim/optimizer.py`
- `torch.cuda.synchronize()`

The last completed optimizer step was 173:

| Field | Value |
|---|---:|
| epoch | 3 |
| loss mean | 0.0011367739279535272 |
| gradient norm | 0.10501138865947723 |
| learning rate | 2.678823375955314e-05 |
| allocated bytes | 8,003,503,616 |
| reserved bytes diagnostic | 21,372,076,032 |
| free bytes | 3,338,797,056 |

## Memory Gate

The v0.32 memory Gate passed:

| Field | Value |
|---|---:|
| `passed` | true |
| maximum peak allocated bytes | 23,622,320,128 |
| peak allocated bytes | 8,003,503,616 |
| minimum synchronized free bytes | 1,073,741,824 |
| minimum observed free bytes | 1,073,872,896 |
| sample count | 174 |

The triggering observation had about 3.34 GB driver free, so the stop should be treated as a CUDA/bitsandbytes execution failure, not as a preregistered memory-capacity failure.

## GPU Release

After process exit, the bound GPU was released:

| Field | Value |
|---|---|
| GPU index | 2 |
| GPU UUID | `GPU-b0302acd-64e2-8218-7b5c-07a152007357` |
| memory used | 18 MiB |
| memory free | 24094 MiB |

## Local GitHub Sync Boundary

The local repository records only a redacted failure summary:

- `09-experiments/llm_evidence_compiler_mainline/results/qwen25-4090-primary-v0.2-failure-summary-v0.1.json`

The full adapter/checkpoint artifacts, optimizer states, scheduler states, RNG states, model files, and raw training text remain outside GitHub.

## Current Hard Stop

The v0.32 one-shot authorization has been consumed and ended in failure. Continuing requires a new written amendment and explicit approval.

Acceptable next amendments must choose one primary path before any new run:

- diagnostic-only reproduction with `CUDA_LAUNCH_BLOCKING=1` on a bounded short run;
- optimizer/runtime stabilization while preserving model/data/sequence/LoRA settings;
- a deliberate optimizer change, with a new smoke Gate and a statement that the training implementation changed;
- abandoning the adapted checkpoint path and evaluating only the original Qwen compiler.

Until then, checkpoint selection, training-validation generation, General-vs-Adapted evaluation, C07-C12 formal inference, and M3 integration remain closed.
