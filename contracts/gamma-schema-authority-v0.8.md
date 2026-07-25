# Gamma schema authority contract v0.8

Status: **FROZEN IMPLEMENTATION INTERPRETATION FOR A16 RE-REVIEW**

- Contract ID: `gamma-schema-authority-v0.8`
- Contract version: `0.8.0`
- Recorded: `2026-07-22`

## Authority order

For Kernel v0.8 runtime validation, the complete A6.6 Gamma requirements in
`active-attribution-experiment-revision-plan-v0.8-20260721.md` control the
machine contract. `schemas/gamma-kernel.schema.json` is the executable,
fail-closed expression of those requirements. The shorter Appendix Gamma
skeleton is an informative serialization sketch; omission of a field from the
skeleton does not make an A6.6-required field optional.

The Appendix skeleton therefore cannot relax retention or missingness
assumptions, finite-domain basis, exhaustive coverage, solver semantics,
candidate protocol, policy bindings, or action-catalog bindings. A Gamma that
matches the skeleton but fails the complete Schema is invalid.

## Conflict handling

This contract does not silently rewrite the normative v0.8 document. If a
future normative revision contradicts A6.6 or the executable Schema, the
runtime must fail closed and open a new spec issue. Changing this authority
order requires an explicit versioned ruling and regenerated Gamma hashes.

This closes the implementation ambiguity recorded as SI-003 without claiming
that the Appendix text itself was edited.
