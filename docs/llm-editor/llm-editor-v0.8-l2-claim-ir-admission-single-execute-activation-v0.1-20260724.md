# Claim IR Admission single-execute activation audit note

Status: activated but not executed.

This note supplements, but is not part of, the strict executor authority payload
in the adjacent JSON file. The executor requires an exact field set, so local
path and implementation audit pins are recorded here rather than inserted as
non-canonical authority fields.

## Authority and approval

- Base HEAD: `aaa47602f6298a84bdd5cb4c071b59374c70a55b`
- Admission contract SHA-256:
  `623cc44ce3d07f64e6c3f45b7fa96e11044d727703a0e27ec20578a980053ef3`
- Admission authority design SHA-256:
  `44fc0900852cae0f325d2929cd6fc938949438e8b55cbdf56836532a16bc3d7b`
- Admission executor SHA-256:
  `7ed0af8a9af72d0dd31c33558a45ad3aef9634952b84c856ee2b9a4a4058e199`
- PI approval artifact:
  `docs/llm-editor/llm-editor-v0.8-l2-claim-ir-admission-pi-approval-v0.1-20260724.json`
- PI approval canonical SHA-256:
  `93a50f9f69edb505b6e763c4d21abf8364ed4c7fc10d9472b741e71e06c075a9`
- PI approval file SHA-256:
  `dcd54e4cc98161e7efe9aae790533d49ddd6be0ead34f452f56ef8df0a66926a`

## Exactly selected candidate

- `candidate_id`: `minted_planner_inputs_package`
- `candidate_kind`: `minted_package`
- Local audit path:
  `.tmp/production-claim-id-mint-single-execute-v0.1/package.json`
- SHA-256:
  `29a260fe46c3ccf45822e4e2b8d2085cfb6fef0b6a9a0edddfe9a30462cbb1a9`
- `claim_id_state`: `minted_opaque`
- `admission_state`: `not_admitted`
- `kernel_state`: `pending_kernel_schema`
- Selection cardinality: exactly one; the structural candidate is not selected
  or implied.

## Ledger and boundaries

- Ledger: authorized/maximum/started/consumed/remaining = `1/1/0/0/1`.
- Retry, resume, and fallback are false.
- This activation authorizes exactly one future in-memory admission operation
  under the frozen executor gates.
- It does not execute admission and does not authorize a persisted admitted
  package.
- Mint, Claim-ID transition, Kernel/E_case write, certificate generation,
  catalog/source-role/lineage-credit/quota-credit/L2 changes, M2 fit, and
  four-family fine-tuning remain blocked.
- No key, secret, or HMAC material is present.

