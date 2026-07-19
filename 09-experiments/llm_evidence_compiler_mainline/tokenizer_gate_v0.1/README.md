# Tokenizer-length Gate v0.1

This directory contains only committable contracts, scripts and count/hash
audits for the bounded Qwen2.5 tokenizer-length Gate. The tokenizer snapshot,
isolated tokenizer engine, downloaded wheel and any reproduction-only outputs
are Git-ignored.

This Gate may count the complete frozen prompt+target serialization for the
1,500 label-blind examples. It does not authorize Qwen model files, a training
runtime, QLoRA, inference or M3 integration.

Current v0.1 result: `failed_closed_tokenizer_length_gate`. Overall p95 is
1,131, maximum is 2,094 and 173 examples exceed 1,024; zero were truncated or
excluded. A v0.2 serialization and deterministic same-family length-aware
selection amendment is proposed under `08-writing` and is not active without
explicit user approval.
