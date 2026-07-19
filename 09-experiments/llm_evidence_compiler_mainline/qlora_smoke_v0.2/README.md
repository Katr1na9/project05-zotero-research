# Local RTX 2080 Ti QLoRA smoke v0.2

This route supersedes, but does not rewrite, the abandoned RTX 4090 server
proposal. No further server connection, installation, model download or
training is authorized by the current authority chain.

The local smoke uses the fixed Qwen2.5-7B-Instruct revision, 4-bit NF4 with
double quantization, FP16 compute and LoRA r=16. It selects 20 balanced train
examples, executes sixteen microbatches and one optimizer step, saves/reloads
only the adapter and performs one bounded training-validation generation.

All environment, package cache, model snapshot and adapter bytes are confined
to the Git-ignored repository directory `.local-qwen25-smoke/`. The launcher
requires at least 40 GB free disk space and stops above 10.5 GiB peak reserved
VRAM. Passing the smoke does not authorize primary training, formal inference,
C07-C12 execution, M3 integration or a paper claim.

Run from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File 09-experiments\llm_evidence_compiler_mainline\qlora_smoke_v0.2\run-local-smoke-v0.2.ps1
```
