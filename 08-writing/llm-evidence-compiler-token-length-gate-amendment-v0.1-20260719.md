# LLM evidence compiler tokenizer-length Gate amendment v0.1

Status: `authorized_tokenizer_audit_only`

Date: 2026-07-19

Parent authority: `authority-lock-v0.12.json`

## User decision

After being told that the next step was the pending tokenizer-length Gate, the
user instructed the project to continue. This authorizes only the bounded
tokenizer audit defined here. It does not authorize Qwen model weights,
Transformers/PyTorch/PEFT/bitsandbytes, QLoRA training, inference or M3 runtime
integration.

## Frozen tokenizer identity

The audit uses the same base identity as the frozen General-versus-Adapted
fairness contract:

- model/tokenizer repository: `Qwen/Qwen2.5-7B-Instruct`;
- revision: `a09a35458c702b33eeacc393d103063234e8bc28`;
- remotely retrievable files: `tokenizer.json`, `tokenizer_config.json`,
  `merges.txt` and `vocab.json` only;
- aggregate tokenizer download limit: 20,000,000 bytes;
- tokenizer engine: isolated `tokenizers==0.21.4` wheel, without Transformers
  or any model runtime.

All files are stored in Git-ignored local directories. The repository may keep
only their names, sizes, SHA-256 values, the resolved revision and audit output.

## Frozen prompt and target serialization

Each of the 1,500 candidate examples becomes one three-message training record:

1. a fixed system instruction defining pointer-bounded support;
2. a canonical user JSON object containing only `source_family_id`,
   `source_modality`, `source_record` and `candidate`;
3. a canonical assistant JSON object containing only `support_decision`,
   `normalized_edge` and `pointer`.

`negative_proof`, generator identity, `example_id`, split role, packet key and
reason code are not exposed to the model. JSON uses UTF-8, sorted keys,
`ensure_ascii=false` and compact separators. The Qwen `<|im_start|>` /
`<|im_end|>` chat serialization is rendered explicitly and hashed. Tokenization
uses `add_special_tokens=false` because those chat tokens are already present in
the rendered text.

## Gate

The audit encodes complete system + user + assistant content with no truncation,
padding, dropping or payload rewrite. It reports count, min, nearest-rank p50,
nearest-rank p95, max and over-1024 count for train, training-validation, every
source family and the complete dataset.

The tokenizer Gate passes only if:

- all 1,500 frozen examples are counted exactly once;
- train remains 1,200 and training-validation remains 300;
- every split and the overall dataset have `p95 <= 1024`;
- every example has `tokens <= 1024`;
- zero examples are truncated, excluded or rewritten;
- a second run produces the same distribution and serialization digest.

If any maximum exceeds 1024, the run fails closed and requires a new design
amendment. It must not silently remove examples from the already frozen family
quotas.

## Still prohibited

No model configuration or weight files, model runtime, training dependency,
adapter, optimizer, checkpoint, inference, C07–C12 model execution, M3
integration, `run_mvp.py` modification, Paper A result change or frozen-result
rewrite is authorized.
