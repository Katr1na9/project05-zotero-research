# Part B B9 freeze and claims contract v0.8

Status: **B9_CONTRACT_ONLY — LOCAL CONTRACT REVIEW**

## Freeze inventory

The authoritative example contains a literal ordered `frozen_artifacts` array
with 39 entries:

- the 38 distinct identities in the B0–B8 manifest union; and
- the B8 no-data holdout analysis envelope.

Each entry carries `slice_id`, `artifact_id`, repository-relative `path` and
canonical `sha256:` identity. Paths and hashes replay against the
`be33ef8` baseline. B9 is not present in its own upstream freeze inventory.
The record cannot rewrite an upstream document or change its authority.

## Directed hash chain

The B9 identity graph is deliberately acyclic:

```text
B0–B8 frozen identities
  -> freeze record
  -> freeze/claims policy
  -> claim boundary
  -> B9 manifest
  -> final freeze audit
```

The frozen B9 hashes for local review are:

```text
Freeze record:
sha256:92182dbe5b58163b35f113831847a6349dba1c1f19cfd3a42a352b52a6a968ab

Freeze and claims policy:
sha256:bd04bac10be6e9b049a700eccf8d7f1e771cec89dbf9f6fce412145f40609999

Claim boundary:
sha256:0ee41ab84b171d7b4789a3b76d7971e15ed3e8f5d6501889b4d486b7e70722a8

B9 manifest:
sha256:6cff911409da42f66b3fef1e25cf555f72f6620f5fd713bdf3bc16bcf50c563e

Freeze audit:
sha256:102c6d1871d89fcbf8a3902f3b26a5e1ac081b578dc220481f6f8b4792e8b8d0
```

Hash-chain validity establishes `CONTRACT_CONSISTENCY_ONLY`. It does not
establish execution, external validity, source validity, empirical
performance, implementation admission, holdout release or delivery authority.

## Non-authority

`PB-SI-006`, `PB-B5-SI-001` and `PB-B8-SI-004` remain **OPEN**. The holdout
release decision stays `DENY`. No sampler, connector, Planner, baseline,
evaluation, statistical procedure, LLM or `09-experiments` workflow is opened.
No certificate, system status or `CERTIFIED_STOP` is emitted.

```text
commit / push / PR: NOT AUTHORIZED
```

