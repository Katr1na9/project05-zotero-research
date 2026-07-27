# PB-SI-008 named Path A CLAIM candidacy boundary v0.8

Status:
`OPENED_FOR_NAMED_TARGET_ONLY_EVIDENCE_AND_CLAIM`.

CLAIM named target:
`PATH_A_CLAIM_IR_STRUCTURAL_CANDIDACY_V0_1`.

Hard ban: Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or unrestricted Part B elevation.

This contract documents an additive classification gate. It does not grant
Claim-ID mint, admission, Part B CLAIM authority, Part B PASS, Path B write,
production registration, Kernel/E_case write, certificate, or STOP.

## Routing and compatibility

The successor accepts three closed routes:

1. An exact legacy four-field request is passed to the existing EVIDENCE gate,
   which passes it to the protected dual-track deny runtime. The returned
   `NOT_OPENED` or experiment-separation record is returned unmodified.
2. An exact existing EVIDENCE eighteen-field request is passed to
   `evaluate_si008_named_open_request` and its record is returned unmodified.
3. An exact CLAIM eighteen-field request for the CLAIM named target is checked
   against the two pairs below.

The existing EVIDENCE runtime and manifest are not modified. The existing
caller and Path A composition remain EVIDENCE-only; this slice does not widen
either one to CLAIM.

## Exact CLAIM request

The CLAIM request has exactly these 18 fields and no others:

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

Required constants:

- `request_kind=PROMOTE_TO_PART_B_NAMED_TARGET`
- `promotion_target=CLAIM`
- `named_target_id=PATH_A_CLAIM_IR_STRUCTURAL_CANDIDACY_V0_1`
- `record_class=public_evidence_declaration`
- `claim_id=null`
- `claim_id_state=not_minted`
- `admission_state=not_admitted`
- `structural_validation_status=PASS_STRUCTURAL_ONLY_NO_INGESTION_AUTHORITY`
- `requested_authority_scope=CLAIM_STRUCTURAL_CANDIDACY_ONLY`
- `reference_access_mode=CLASSIFY_DECLARED_REFERENCE_ONLY_NO_DEREFERENCE`

Schema, consumer, package, and validation-receipt digests must be lowercase
64-character SHA-256 declarations.

## Qualifying CLAIM pairs

There is no wildcard, prefix match, fallback, implicit default, or cross-pair
dispatch.

| Reference kind | Schema identity and SHA-256 | Consumer identity and SHA-256 |
|---|---|---|
| `PATH_A_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE` | `claim-ir-external-evidence-v0.1`, `9abc23e2258298038e137dbbe38168867d07108fa27719aa68c1c2b752ae2a7c` | `shared-claim-ir-consumer-contract-evidence-candidate-effective-v0.2`, `fe5222b9b4e0ddaf990761b34bdfc5004f45f55d3e2155b09388fb9596a1e504` |
| `PATH_A_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE` | `claim-ir-external-evidence-v0.2`, `e246c44b7513a5bc2f3410a2739a53bd1f40dad3e767036bb1af3158c9e02ac6` | `shared-claim-ir-consumer-contract-evidence-candidate-effective-v0.3`, `7662762d045381921b8f94a39753d0c491322b3a41d473226cc5fe3f4688457c` |

The legacy planner identity `claim-ir-external-v0.1`, the legacy consumer
v0.1, existing EVIDENCE reference kinds, future versions, and cross-version
schema/consumer combinations do not qualify for this CLAIM target.

## Qualified output ceiling

Only an exact qualifying CLAIM request may return:

- `pb_si_008_status=OPENED_FOR_NAMED_TARGET_ONLY_EVIDENCE_AND_CLAIM`
- `part_b_status=NAMED_TARGET_CLAIM_CANDIDACY_ONLY_NO_MINT_NO_ADMISSION`
- `decision=ALLOW_NAMED_CLAIM_CANDIDACY_ONLY`

This result is a structural candidacy classification only. The gate declares
`part_b_claim_authority=false`, `mint_authority=false`,
`admission_authority=false`, `path_b_write_authority=false`, and
`allow_is_part_b_pass=false`.

## Fail-closed and no dereference

`AUTHORITY` and `PASS_CONDITION` are denied. Wrong target, wrong pair,
missing/extra fields, malformed digest, wildcard, non-null `claim_id`,
`minted`, `admitted`, legacy planner Claim-IR, or an EVIDENCE reference kind
relabelled as CLAIM is denied without partial output.

The successor never reads the referenced package or validation receipt.
Paths and URIs are not request fields. It performs no network, filesystem,
LLM, registry, mint, admission, or write operation.

The experiment track remains separately authorized and is not stopped by a
CLAIM classification. Adjacent gates remain:
`holdout_release=DENY`, `pb_si_006_download=DENY`,
`pb_b5_execution=NOT_ESTABLISHED`, and `stop_authority=NONE`.
