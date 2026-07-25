# Tokenizer-length Gate v0.2

This directory records the independent full-token audit of the regenerated
candidate pairs. It reuses the fixed four-file Qwen2.5 tokenizer snapshot and
isolated `tokenizers==0.21.4` engine from v0.1. No new tokenizer or model files
are downloaded.

The audit renders every complete v0.2 system, user and assistant record without
truncation or padding. Passing requires p95 and maximum at most 1,024 and zero
over-limit examples. A second audit must be byte-identical.

Current status (2026-07-19): passed with overall p50/p95/max of
589/881/1,021 and zero examples over 1,024. The second complete audit was
byte-identical. This result does not open the model or training gates.
