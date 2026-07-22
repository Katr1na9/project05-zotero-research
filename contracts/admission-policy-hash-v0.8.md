# Admission-policy authority and hash contract v0.8

Status: **APPROVED — EXACT HASH BOUND**

- Contract ID: `admission-policy-hash-v0.8`
- Contract version: `0.8.0`
- Recorded: `2026-07-22`
- Policy artifact: `configs/admission-policy-kernel-v0.8.yaml`
- Approval manifest: `configs/admission-policy-approval-kernel-v0.8.yaml`

## Separation of policy content and approval

The policy artifact states deterministic admission semantics.  The approval
manifest records whether a human authority approved those exact bytes.  Code,
tests, a Compiler, an LLM, M3*, or a SHA-256-shaped string cannot create that
approval.  Runtime authority exists only when all of the following hold:

1. both documents validate against their JSON Schemas;
2. both canonical document hashes replay exactly;
3. the manifest binds the policy ID, version, and exact policy hash;
4. `decision=APPROVED` and the human authority fields are complete; and
5. the active Gamma reference binds the same policy, manifest, and active rule
   subset.

Any missing, malformed, wrong, stale, or tampered value fails closed.  A
policy artifact with a valid content hash but a `PENDING` manifest has no
admission, certificate, or `CERTIFIED_STOP` authority.

## Canonicalization

Both documents use the approved sort-key JSON procedure:

1. parse UTF-8 YAML into a JSON-compatible mapping;
2. remove exactly the top-level `hash` field;
3. serialize with Unicode preserved, recursively sorted mapping keys, compact
   separators `,` and `:`, and no NaN/Infinity values;
4. SHA-256 hash the UTF-8 bytes; and
5. encode as lowercase `sha256:<64 hex>`.

Duplicate mapping keys and non-JSON YAML values are outside the accepted
domain and must be rejected before authority construction.

## Current exact artifacts

| Artifact | Decision | Canonical hash |
|---|---|---|
| `admission-policy-kernel-v0.8.yaml` | content candidate | `sha256:8f34a5e99c2cba3d79304667acd5bb010492af74b8b99425352375a796825671` |
| `admission-policy-approval-kernel-v0.8.yaml` | `APPROVED` | `sha256:2eda84dd347d1a0acdf8802edb01e7ba1cd00c6b8e767d02d78170e3d0fd1f8b` |

The normative source bytes referenced by the policy are
`08-writing/active-attribution-experiment-revision-plan-v0.8-20260721.md`
with raw SHA-256
`99fa98b9489cfe49d4da6fe02e06b457201a59d9024ca62233c5dd82f7b7baa9`.

## Runtime bindings

- Gamma binds policy ID/version/hash, approval-manifest ID/hash, and active
  rules.
- Firewall decisions expose both verified hashes and reject claims whose
  basis rule, source family, levels, or policy hash do not match.
- ADMIT audit events include both hashes inside the append-only hash payload.
- Level certificates include both hashes.
- The system-state STOP gate requires the certificate hashes to match the
  active Gamma policy reference as well as Gamma/evidence hashes.

These bindings do not establish a level-complete proof.  They only prevent an
unapproved or substituted admission policy from participating in one.

## Approval record and remaining gates

The Project05 repository owner explicitly approved policy hash
`sha256:8f34a5e99c2cba3d79304667acd5bb010492af74b8b99425352375a796825671`
in the Codex task on `2026-07-22`. The repository manifest records that ruling
and its canonical hash is
`sha256:2eda84dd347d1a0acdf8802edb01e7ba1cd00c6b8e767d02d78170e3d0fd1f8b`.
Both Gamma documents and all fixture/ceiling references were regenerated.

This closes SI-010 policy authority only. It does not imply A16 Go, create a
level-complete certificate, authorize `CERTIFIED_STOP`, or authorize push/PR.
Those gates remain independent.
