# Project05 mainline evidence compiler

Status: `qwen25_paired_route_packet_null_source_search_closed_candidate_verification_draft_pending` (2026-07-18)

This namespace contains the dependency-free contract and information-boundary layer, the WP2 public/private data package and development-only `RULE-STRONG` snapshot, plus the WP3 clean-room component-output adapter. It does not contain a model runtime, model weights, training code, formal inference output, or frozen-case replacements. Private scorer/executor manifests are physically separated under `generated/wp2/private/` and are never an input to the Rule runner, component adapter, or mechanical admission.

## Current interfaces

- `CompilerPublicRequest`: currently visible artifacts plus a public target-node contract;
- `CandidateClaimEnvelope`: request-scoped candidate observation without a canonical claim ID;
- `EntityBinding`: host/process/time-scoped entity normalization sidecar;
- `ClaimNodeLink`: mechanically eligible support link from an admitted claim to a public target node;
- `CompilerAdmissionDecision`: admitted/rejected/abstained output with reason codes;
- `CompilerRunManifest`: request, candidate and admission hash chain.

Passing mechanical admission means contract-eligible, not human-verified semantic truth. Private reference claims are scorer-only and are not an admission input.

## WP2 frozen package

- `generated/wp2/public/`: 58 request-scoped artifacts, 37 target nodes and 405 public visibility scenarios for C04–C12;
- `generated/wp2/private/`: frozen-reference and action-revelation manifests for scorer/executor use only;
- `generated/wp2/data-readiness.json`: 9 cases and 58/58 source pointers resolved, with zero canonical-ID collisions in public files;
- `generated/wp2/rule-strong-development/`: C04–C06-only Rule requests, results and immutable snapshot.

The public target qualification vocabulary is derived from fixed observable operations and public stage semantics. It does not use private `required_claim_ids` or frozen-reference predicates. The Rule snapshot reports 26 mechanically admitted development observations and 15 conservative links; these counts are interface-readiness evidence, not a semantic-quality or superiority result.

## Authorized commands

```powershell
python -m unittest discover -s 09-experiments/tests -p 'test_llm_evidence_compiler_*.py' -v
python -m py_compile 09-experiments/scripts/build_compiler_public_request.py 09-experiments/scripts/validate_compiler_admission.py 09-experiments/scripts/run_compiler_mainline_stub.py 09-experiments/scripts/build_compiler_wp2_data.py 09-experiments/scripts/run_compiler_rule_strong.py 09-experiments/scripts/adapt_reuse_component_graph.py 09-experiments/scripts/run_compiler_reuse_hybrid.py
```

## WP3 clean-room component boundary

- `wp3/component-catalog-v0.1.json` freezes component revision, license, I/O profile and current runtime authority;
- `wp3/contracts/` contains two WP3-only contracts and does not change the six M1 contracts;
- `scripts/adapt_reuse_component_graph.py` accepts a CTINexus-compatible aligned-triplet bundle, recovers the shortest same-record source sentence containing both endpoints, and emits a controller-ineligible source-grounded sidecar;
- unknown revision, unapproved runtime, unknown/non-CTI pointer, actor/campaign elevation, missing same-sentence support and duplicate edges fail closed;
- `generated/wp3/reuse-hybrid-development/` reuses the frozen Rule output for C04-C06 and explicitly abstains on the CTI route because WP2 contains no `cti_text` artifact.

WP3 proves an interface and rejection boundary only. It does not establish CTINexus, OntoLogX, LLM, component, or end-to-end performance. A real component Gate requires a separately reviewed source-licensed CTI-text amendment and separate runtime/model authority. Environment installation, model or embedding download, training, C07-C12 execution and formal inference remain prohibited.

## Qwen2.5 paired route (design authority only)

`contracts/authority-lock-v0.3.json` restores one fixed
`Qwen/Qwen2.5-7B-Instruct` checkpoint as the only LLM base and requires a paired
comparison between `QWEN-GENERAL` (adapter off) and `QWEN-ADAPTED`
(`project05_obs_compiler` on). The fairness contract requires the base,
tokenizer, quantization, prompt, schema, packet, decoding, hardware, admission
and scorer hashes to match; adapter state is the only allowed model difference.

This approval does not authorize execution. The external-evidence Gate in
`contracts/train-null-source-literature-gate-v0.1.json` concludes that CISA KEV
is CC0-permitted for processing but scientifically ineligible as a formal
case-level train-null: KEV is CVE-level positive exploitation evidence, not
endpoint/provenance evidence that an event did not occur. It may only be used
as a separately reported `non_entailing_contract_negative` diagnostic and
receives zero training-Gate credit.

The superseding readiness report
`qwen-data-reuse-readiness-v0.2.json` therefore records 2 eligible train-null
records versus a minimum of 480, leaving a deficit of 478. The obsolete 50-row
single-author KEV review is no longer requested; its blank queue is retained as
a historical artifact. Interference has not been measured and the Qwen
tokenizer length Gate has not been run. No historical corpus was copied into
this namespace.

## Packet-null alternative-source review

`contracts/train-null-source-literature-gate-v0.2.json` records the frozen
follow-up review of benign/provenance windows, security IE/NLI negatives and
controlled counterfactuals. No external source receives formal packet-null
credit. ProvSec, BETH and LID-DS benign/normal data still contain the concrete
process, file, network and syscall relations the compiler is meant to emit;
security IE `no-trigger` or `no-relation` labels are target-ontology or
candidate-relative, not evidence that an unconditioned packet has an empty
observation graph.

The review therefore closes continued benign-log search as the default way to
fill the 478-row deficit. `qwen-data-reuse-readiness-v0.3.json` preserves the
current Gate as failed and does not reinterpret any old row.

`contracts/candidate-edge-verification-contract-draft-v0.1.json` is a
non-authorizing alternative. It proposes training on an exact source record and
pointer plus a candidate SPO/time, with labels `supported`,
`unsupported_by_bound_pointer` or `abstain`. Controlled negatives would make
only a local pointer-support claim and would be paired within the same approved
source modality. `authority-lock-v0.4.json` freezes the review but leaves this
amendment pending user review: candidate-pair construction, tokenizer/model
download, environment changes, training and inference remain prohibited.
