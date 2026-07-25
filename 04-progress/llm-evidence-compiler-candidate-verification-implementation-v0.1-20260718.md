# LLM evidence compiler candidate-edge verification implementation v0.1

Date: 2026-07-18  
Status: `dependency_free_implementation_complete_non_token_data_gate_failed`  
Authority: `09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.5.json`

## Outcome

The invalid packet-level train-null route has been replaced at the contract and dependency-free implementation level by pointer-bounded candidate-edge verification:

```text
source record + exact pointer + candidate SPO/time
→ supported | unsupported_by_bound_pointer | abstain
```

No formal candidate pairs were constructed. No corpus was copied into the mainline tree. No tokenizer, model, modified runtime, training, or formal inference was used.

## Implemented artifacts

- Approved amendment and contract that retain the Qwen2.5 General-versus-QLoRA comparison but authorize only dependency-free work.
- Candidate-edge training and pointer-bounded proof JSON schemas.
- Hash-locked source field maps for all six historical families.
- G0 validator that admits only exact fields or named frozen mechanical transforms.
- Explicit N1–N4 generator functions and independent proof revalidation.
- Read-only GZip auditor and frozen readiness result.
- 18 focused tests covering authority, schema, G0, generator, adversarial proof, and source-family gates.

## Read-only historical audit

Source root:

` .worktrees/llm-apt-phase1/09-experiments/llm_finetuning_v0.3/generated/exclusion-passed-records `

Source manifest SHA-256: `A1CA1180A0D47BB358C43CE83BDF598416A16F5BF0458DDCA863D2E8D4530CEA`

| split | source family | proposals | G0 positive | main exclusion |
|---|---|---:|---:|---|
| train | CAM-LDS filtered | 800 | 0 | 800 candidates use an unbound placeholder subject |
| train | SOCBED winlogbeat | 795 | 683 | 112 lack the explicit subject field required by the frozen template |
| train | Atomic Red Team | 799 | 798 | 1 object differs from the bound source field |
| train | Splunk manifests | 0 | 0 | 2 legacy packet-null rows receive zero candidate-edge credit |
| training-validation | Loghub Linux | 0 | 0 | 500 legacy packet-null rows receive zero candidate-edge credit |
| training-validation | Zeek non-PCAP | 483 | 483 | none under the current exact map |

### Gate result

- Train G0 positives: `1481`; maximum one-positive/one-negative balance: `2962` candidate pairs.
- Training-validation G0 positives: `483`; maximum balanced count: `966` candidate pairs.
- Train G0-positive families: `2`, required `4`.
- Training-validation G0-positive families: `1`, required `2` and train-disjoint.
- Result: `failed_non_token_data_gate`.
- Token gate: `not_measured_not_authorized`.
- Formal data gate: `false`.

Quantity is sufficient, but family diversity is not. The implementation therefore prevents total row count from hiding a source-modality shortcut.

## Negative semantics and fail-closed checks

- N1 swaps a same-type object only within the same source family and packet.
- N2 swaps the pointer only within the same source family and packet.
- N3 accepts only predicates frozen as incompatible for the positive template.
- N4 requires explicit, different timestamps in the same source family and packet.
- The proof validator reloads the positive and bound records, revalidates the positive, and confirms the altered candidate is unsupported by the bound record.
- Cross-family donors, cross-packet donors, missing records, candidate/proof mismatch, still-supported candidates, path/scenario supervision, and world-false claims fail closed.
- Legacy `packet_role=null` and `null_eligible_candidate=true` rows cannot enter this negative contract.

## Verification

Fresh commands on 2026-07-18:

1. Python compile: exit `0`.
2. Candidate-edge focused suite: `Ran 18 tests` — `OK`.
3. LLM evidence-compiler mainline suite: `Ran 121 tests` — `OK`.
4. Full `09-experiments/tests`: `Ran 615 tests` — `OK (skipped=6)`.

## Preserved boundaries

- `run_mvp.py` was not modified by this milestone.
- Frozen cases and historical result files were not overwritten.
- The historical QLoRA corpus remains in the old feature worktree and was read only.
- No Paper A result, patent claim, DOCX, PPTX, or PDF was generated or rewritten.
- Current code is not controller-eligible and does not enter M3 runtime.

## Next scientifically valid step

The adapter route cannot proceed to formal pair construction under the current source family Gate. The next read-only task is a new positive-source gap audit, seeking at least:

1. two independent train families with explicit endpoint/provenance SPO fields; and
2. one independent training-validation family with the same candidate-edge truth contract.

Every candidate must pass license, family independence, test-family exclusion, exact field mapping, source-modality, and payload leakage gates. If such families are not found, the QLoRA branch remains `smoke_only`; Qwen-General and Reuse-Hybrid remain the mainline compiler fallbacks.
