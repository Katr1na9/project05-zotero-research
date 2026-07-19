# LLM evidence compiler tokenizer-length Gate amendment v0.2 (proposed)

Status: `pending_user_design_amendment_approval`

Date: 2026-07-19

Parent authority: `authority-lock-v0.14.json`

## Why v0.1 failed

The exact Qwen2.5 tokenizer audit counted all 1,500 complete prompt+target
serializations without truncation. The Gate correctly failed:

| Scope | p50 | p95 | Max | Over 1024 |
|---|---:|---:|---:|---:|
| Overall | 808 | 1,131 | 2,094 | 173 |
| Train | 835 | 1,144 | 2,094 | 173 |
| Training-validation | 715 | 800 | 873 | 0 |

The over-limit examples were CAM-LDS 17, SOCBED 131 and Atomic 25. BETH,
Loghub and Zeek had none. No example was dropped, truncated or rewritten, and
the formal data Gate remains false.

The failure is mainly serialization redundancy rather than an unavoidable
dataset-wide context requirement. v0.1 placed the complete source record,
license/source hashes, repeated record identifiers, full candidate, normalized
edge and output pointer in one chat record. SOCBED additionally repeated the
same event in both a raw `message` and parsed fields.

## Proposed v0.2 serialization

Preserve the complete semantic payload and exact pointer but remove operational
metadata that the model does not need. The user message becomes:

```json
{
  "source_modality": "...",
  "bound_pointer": {"artifact_id": "...", "record_id": "...", "record_sha256": "..."},
  "payload": {...},
  "candidate": {...}
}
```

The assistant still returns `support_decision`, `normalized_edge` and `pointer`.
Thus the LLM remains a pointer-bounded semantic compiler/admission layer; it is
not reduced to a decision-only classifier. Full payload values, including long
commands, are not shortened or summarized. Provenance/license metadata remains
in the source dataset and audit but is not model-visible.

The system message is shortened without changing semantics:

> Decide whether candidate is supported by the bound evidence. Use only the
> payload and pointer. Return only JSON. Unsupported means unsupported by this
> record, not false or benign.

Applied to the current selected examples, this reduces overall p95 from 1,131
to 909, but 27 examples remain over 1,024 because their complete commands are
genuinely long.

## Proposed length-aware deterministic selection

Re-run pair selection from the same already approved source pools. For each
frozen family and negative-generator quota, construct the positive/negative
pair, render both complete v0.2 chat records and accept it only when both are at
most 1,024 tokens. If either is over length, move deterministically to the next
eligible candidate in the same family and generator. Do not truncate, summarize,
cross-substitute families or change any quota.

An in-memory preflight using this rule completed all existing quotas:

| Scope | Examples | p50 | p95 | Max | Over 1024 |
|---|---:|---:|---:|---:|---:|
| Overall | 1,500 | 589 | 881 | 1,021 | 0 |
| Train | 1,200 | 611 | 897 | 1,021 | 0 |
| Training-validation | 300 | 492 | 580 | 659 | 0 |

All six source families, the 750/750 support balance, v0.2 Zeek allocation and
all N1–N4 quotas remain unchanged. Every accepted example preserves its full
payload. The previous pair files and audits would remain as historical evidence
and be superseded, not overwritten in Git history.

## Authorization requested

Approval would authorize only:

1. a v0.2 serialization contract and length-aware pair-selection amendment;
2. regeneration of the local Git-ignored 1,500-example pair files from the same
   approved sources;
3. rerunning non-token, protected, proof, tokenizer and determinism audits;
4. committing and pushing only code, contracts, Markdown, counts and hashes.

It would still not authorize model configuration or weights, Transformers,
Torch, PEFT, bitsandbytes, QLoRA training, inference, C07–C12 model execution or
M3 integration.
