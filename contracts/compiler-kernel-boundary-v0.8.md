# Compiler / Kernel ownership contract v0.8

Status: **FROZEN SHARED INTERFACE FOR A16 RE-REVIEW**

- Contract ID: `compiler-kernel-boundary-v0.8`
- Contract version: `0.8.0`
- Claim schema: `schemas/claim-ir-kernel.schema.json`
- Interface manifest: `src/ir/candidate-claim-ir-interface-v0.8.json`
- Migration note: `src/ir/migration-v0.8.md`

## Compiler-owned output

The LLM/compiler may emit only a schema-valid
`candidateCompilerResponse`: candidate subject/predicate/object/time/location,
polarity, binding proposals, or an explicit abstention. It has no admission,
promotion, certificate, Checker, action, or STOP authority.

## Kernel-owned fields and decisions

The trusted Kernel exclusively owns Claim IDs and pointers, modality,
truth-status, epistemic role, certification authority, binding/admission/
promotion/lifecycle state, confidence, rule trace, and support/contradiction
links. It also owns Gamma compilation, action selection/execution eligibility,
Checker results, certificates, and system state.

Compiler responses containing protected or oracle/hidden fields fail closed
under the stable `CKI-*` errors. A compiler cannot copy a request pointer into
its response or manufacture a replacement pointer.

## Observation adapter boundary

The deterministic P11 observation adapter is a Kernel component, not an LLM
compiler. Its `ObservationClaimActionBinding` is supplied per action and must
name a Kernel-owned `certification_basis_rule_id`. The adapter resolves the
action against the frozen catalog and binds `pointer.record_id` to the actual
P5 `observation_id`; it may not infer oracle/hidden data or change modality.
Moving the rule ID back to one batch-wide default is a breaking interface
change because it could launder one source-family rule across another action.

Any future interface change requires a new manifest/schema version and an
explicit migration note. Silent adaptation by either track is forbidden.
