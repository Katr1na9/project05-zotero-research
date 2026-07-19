# Qwen2.5 QLoRA smoke v0.1

This directory contains only the portable contract, configuration and sanitized
audit outputs for the user-authorized QLoRA smoke. The environment, model
snapshot, adapter, optimizer state and raw/generated model text remain local and
Git-ignored.

The intended execution host is one NVIDIA RTX 4090 server. Scientific settings
remain frozen at 4-bit NF4 with double quantization, FP16 compute, LoRA r=16,
alpha=32, dropout=0.05 and a 1,024-token maximum. The smoke selects 20 train
examples (10 supported and 10 pointer-unsupported), executes one optimizer step
over 16 gradient-accumulated microbatches, saves/reloads only the adapter and
runs one bounded training-validation generation.

Passing this smoke does not authorize primary adapter training, C07-C12
inference, M3 integration or a positive paper claim.

## RTX 4090 execution boundary

The only authorized server home is `/home/myy`. The repository is placed at
`/home/myy/Project05-Zotero`; runtime, caches and local adapter outputs are
placed at `/home/myy/project05-qwen25-smoke-v0.1`. The launcher refuses another
user, repository location or run root and contains no delete operation.

After the frozen branch and the two Git-ignored pair payloads have been copied
into those locations, run from `/home/myy`:

```bash
bash /home/myy/Project05-Zotero/09-experiments/llm_evidence_compiler_mainline/qlora_smoke_v0.1/run-server-smoke-v0.1.sh
```

The launcher creates a Python 3.11 virtual environment, installs exact package
versions, downloads only the 14 allowlisted files from the fixed Qwen revision,
checks file sizes plus Git/LFS hashes, runs the bounded smoke and stops. Raw
pair payloads, model files, adapter files and generated text remain local and
Git-ignored; only a separately reviewed sanitized audit may later be committed.
