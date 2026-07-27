# PB-SI-008 named Path A evidence candidacy boundary v0.8

Status: `OPENED_FOR_NAMED_TARGET_ONLY`

Named target:
`PATH_A_EVIDENCE_CLAIM_IR_STRUCTURAL_CANDIDACY_V0_1`.

Hard ban: Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or unrestricted Part B elevation.

This contract documents the Owner-authorized additive successor gate. It is
not a new admission, write, production-registration, claim, authority,
pass-condition, certificate, or STOP grant.

## Allowed classification

Only an exact closed-world named request with `promotion_target=EVIDENCE`
may return:

- `pb_si_008_status=OPENED_FOR_NAMED_TARGET_ONLY`
- `part_b_status=NAMED_TARGET_EVIDENCE_CANDIDACY_ONLY_NO_ADMISSION`
- `decision=ALLOW_NAMED_EVIDENCE_CANDIDACY_ONLY`

The result means structural candidacy classification only.
`allow_is_admission=false`, `allow_is_part_b_pass=false`, and
`part_b_evidence_authority=false`.

## Exact named request

The request has exactly these 18 fields and no others:

1. `request_id`
2. `request_kind`
3. `promotion_target`
4. `reference_kind`
5. `named_target_id`
6. `source_schema_version`
7. `source_schema_sha256`
8. `consumer_contract_id`
9. `consumer_contract_sha256`
10. `package_sha256`
11. `structural_validation_receipt_sha256`
12. `record_class`
13. `claim_id`
14. `claim_id_state`
15. `admission_state`
16. `structural_validation_status`
17. `requested_authority_scope`
18. `reference_access_mode`

Required constants are:

- `request_kind=PROMOTE_TO_PART_B_NAMED_TARGET`
- `promotion_target=EVIDENCE`
- `named_target_id=PATH_A_EVIDENCE_CLAIM_IR_STRUCTURAL_CANDIDACY_V0_1`
- `record_class=public_evidence_declaration`
- `claim_id=null`
- `claim_id_state=not_minted`
- `admission_state=not_admitted`
- `structural_validation_status=PASS_STRUCTURAL_ONLY_NO_INGESTION_AUTHORITY`
- `requested_authority_scope=EVIDENCE_STRUCTURAL_CANDIDACY_ONLY`
- `reference_access_mode=CLASSIFY_DECLARED_REFERENCE_ONLY_NO_DEREFERENCE`

Schema, consumer, package, and validation-receipt digests must be lowercase
64-character SHA-256 declarations.

## Qualifying reference pairs

There is no wildcard or fallback.

| Reference kind | Schema identity and SHA-256 | Consumer identity and SHA-256 |
|---|---|---|
| `PATH_A_EVIDENCE_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE` | `claim-ir-external-evidence-v0.1`, `9abc23e2258298038e137dbbe38168867d07108fa27719aa68c1c2b752ae2a7c` | `shared-claim-ir-consumer-contract-evidence-candidate-effective-v0.2`, `fe5222b9b4e0ddaf990761b34bdfc5004f45f55d3e2155b09388fb9596a1e504` |
| `PATH_A_EVIDENCE_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE` | `claim-ir-external-evidence-v0.2`, `e246c44b7513a5bc2f3410a2739a53bd1f40dad3e767036bb1af3158c9e02ac6` | `shared-claim-ir-consumer-contract-evidence-candidate-effective-v0.3`, `7662762d045381921b8f94a39753d0c491322b3a41d473226cc5fe3f4688457c` |

The gate classifies these declarations without reading the referenced package
or receipt. Paths and URIs are not request fields.

## Fail-closed decisions

- `CLAIM`, `AUTHORITY`, and `PASS_CONDITION` return `DENY` with
  `SI008-NAMED-002_PROMOTION_TARGET_NOT_AUTHORIZED`.
- Missing, unknown, malformed, mismatched, wildcard, or ambiguous named
  requests return `DENY` with
  `SI008-NAMED-003_REQUEST_NOT_QUALIFIED`.
- No request can silently fall back into the named opening.

## Legacy compatibility and experiment separation

An exact legacy four-field request is delegated to
`src/scope/part_b_si008_dual_track_deny.py`. Its existing `NOT_OPENED`
record semantics are preserved. In particular, a legacy Part B promotion
remains denied, while an experiment-only notice remains
`NO_PART_B_ADMISSION_REQUEST` and is not stopped or evaluated by this gate.

## Adjacent gates

Path B write, production registration, mint, admission, Kernel/E_case write,
certificate, CERTIFIED_STOP, holdout release, SI-006 download, and B5
execution remain denied, not authorized, or not established exactly as
pinned. `stop_authority=NONE`.
