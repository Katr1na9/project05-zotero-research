# LLM evidence compiler tokenizer-length Gate amendment v0.2

Status: `authorized_serialization_and_same-family_length-aware_reselection`

Date: 2026-07-19

Parent authority: `authority-lock-v0.14.json`

## User decision

The user explicitly approved “tokenizer Gate v0.2 serialization compaction and
same-family length-aware reselection” on 2026-07-19. The approval authorizes
only pair regeneration and the complete audit chain described below. It does
not authorize model weights, training or inference.

## Frozen reason for amendment

The exact v0.1 audit failed closed: 173 of 1,500 complete prompt-and-target
records exceeded 1,024 tokens. Overall p95 was 1,131 and maximum was 2,094.
No record was truncated, removed or rewritten after admission.

## Authorized v0.2 serialization

The model-visible user record contains only:

```json
{
  "source_modality": "...",
  "bound_pointer": {"artifact_id": "...", "record_id": "...", "record_sha256": "..."},
  "payload": {},
  "candidate": {}
}
```

The assistant record continues to contain `support_decision`,
`normalized_edge` and `pointer`. Complete payload values remain visible.
Provenance, license hashes, repeated record identifiers and construction-only
metadata are retained in the local source/audit layer but are not model input.

## Authorized deterministic selection

For each frozen source family and negative-generator quota, construct one
supported/unsupported pair and render both members with the locked Qwen2.5
tokenizer. Admit the pair only when both members are at most 1,024 tokens. If a
member is longer, continue in the existing deterministic order within the same
source family and the same negative generator.

The following remain prohibited:

- truncating, summarizing or rewriting an accepted payload;
- moving a quota across source families or negative generators;
- changing the six-family, split, 750/750 balance, Zeek or N1–N4 quotas;
- using a label, scenario path, TTP or protected C07–C12 payload;
- downloading model files or installing a training runtime.

## Required completion evidence

The regenerated 1,500 examples must pass the non-token count, proof, pointer,
modality, forbidden-supervision and protected-payload audits; an independent
full tokenizer audit must report p95 and maximum at most 1,024 with zero
over-limit examples; a second construction and token audit must be
byte-identical. Pair payload, tokenizer files, runtime and corpus remain
Git-ignored.
