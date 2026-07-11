# LLM evidence-claim compiler pilot

This optional branch is separate from the Project05 planner-model mainline. No LLM output is used by the current M2/M3a/M3b results. XGBoost and later DQN, not Qwen, are the planned core decision models.

## Optional LLM comparison

- Base model: `Qwen/Qwen1.5-7B-Chat`, 4-bit.
- CTI-domain model: `Multilingual-Multimodal-NLP/SEVENLLM-Qwen1.5-7B`, 4-bit.
- Non-LLM baseline: deterministic compiler.
- Upper bound: manually reviewed gold claims.

## Pilot data

Build the answer-key-separated pilot set:

```powershell
python 09-experiments/scripts/build_llm_compiler_pilot.py `
  --experiment-root 09-experiments `
  --output 09-experiments/results/llm_compiler_pilot/c07_c09_pilot.jsonl.gz
```

The file contains 14 samples:

- 10 `primary_atomic` event-to-claim samples;
- 4 `context_required_control` samples whose benign status cannot be inferred safely from one event alone.

Only `model_input` may be passed to a model. `gold_claim` is scorer-only data. Motif rules and claim templates are excluded from `model_input`.

## Gate

Model weights have not been downloaded and no model inference has been run. This branch is postponed until the XGBoost planner baseline and the DQN feasibility gate are complete.
