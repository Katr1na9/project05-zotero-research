# Production Claim-ID mint single-execute activation audit

Status: activated single mint execute authorized, not executed.

This Markdown file is a non-authority audit companion. The adjacent JSON is
the exact authority object intended for the mint executor gate; no audit-only
field is added to that JSON.

## Frozen authority chain

- Base commit:
  `373a00dbaa9ccd1fe7c69f6b2cc5b0e44e1fc62a`
- Surface:
  `project05_depth2_public`
- Production mint authority design SHA-256:
  `47c5924ce6584e2e43186d42788e88061ce771d4518fb87004a8b12bf7439211`
- Minting design SHA-256:
  `8f7ee8bd6808ea443f04f8f2cbef253c6f948a8708fa93b58ef643b7955bcabe`
- Source-field mapping design SHA-256:
  `c9ed6df54c0f23389a33679abac8d80929eee2dc290885975878f14d92b77799`
- Claim IR schema SHA-256:
  `5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e`

## Exact structural input

- Package path:
  `.tmp/m1-planner-inputs-single-execute-v0.1/package.json`
- Package SHA-256:
  `a97dcdd63974cb86afd1cd76de23df41f178fbcedf4657c3345d5253f0e9a650`
- Consumed source M1 activation SHA-256:
  `070c86604af03cff9c21174c6fc316a608365c55e3104a8ff59df3df78d0e79a`
- Source M1 execute ledger:
  `authorized=1, maximum=1, started=1, consumed=1, remaining=0`

The input package is structural only: all Claim IDs are null,
`claim_id_state=not_minted`, `admission_state=not_admitted`, and
`kernel_state=pending_kernel_schema`.

## Namespace key boundary

The authority JSON contains only the external namespace identifier
`project05-depth2-public-mint-ns-v01` and the required non-persistence
attestations. It contains no key bytes, secret, HMAC material, environment
value, credential, or derivation material.

Any future authorized mint execution must obtain key material only from an
external ephemeral provider. Such material must never be written, logged, or
committed. Creating this activation does not inject a key, call
`mint_claim_ids`, mint a Claim-ID, admit a package, write Kernel/E_case state,
generate a certificate, or change catalog, role, credit, quota, or L2 state.
