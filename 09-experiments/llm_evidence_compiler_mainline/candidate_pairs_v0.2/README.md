# Token-aware label-blind candidate pairs v0.2

This directory supersedes the local v0.1 pair payload without deleting or
rewriting the historical v0.1 evidence. `local-data/` contains the regenerated
1,500-example payload and is Git-ignored. Only contracts, counts, hashes and
audit summaries may be committed.

Selection uses the fixed Qwen2.5 tokenizer solely to require both members of a
supported/unsupported pair to fit within 1,024 tokens. It may continue only
within the same source family and negative-generator quota. Accepted payloads
are never truncated, summarized or rewritten.

Passing construction alone does not authorize model weights, training,
inference, C07–C12 model execution or M3 integration.

Current status (2026-07-19): pair construction, non-token audits and the
byte-identical second construction passed. The independent token Gate also
passed; the formal data Gate is true, while model and training gates remain
closed.
