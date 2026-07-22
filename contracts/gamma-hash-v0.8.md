# Γ and action-catalog hash contract v0.8

Status: **APPROVED**

- Contract ID: `gamma-hash-v0.8`
- Contract version: `0.8.0`
- Recorded: `2026-07-22`
- Approved: `2026-07-22` by explicit user ruling

## Purpose and scope

This approved contract makes the P0 hash replay rule unambiguous for:

- `configs/gamma-kernel-v0.8.yaml`; and
- `configs/action-catalog-kernel-v0.8.yaml`.

It is the controlling v0.8 canonicalization contract for these two document
hashes. Its approval governs hash replay only; it neither grants certification
authority nor implements a Checker, MinDiff, Firewall, Promote runtime,
Executor, Planner, Part B, or any training behavior.

## Canonicalization procedure

Given a UTF-8 YAML document:

1. Parse the document into a JSON-compatible data object using the repository
   safe YAML loader. A parse failure or non-mapping document is invalid.
2. Make a shallow copy of the top-level mapping.
3. Remove exactly the top-level key `hash`. A nested key named `hash` is not
   removed.
4. Serialize the remaining object as JSON with:
   - Unicode preserved (`ensure_ascii=False`);
   - mapping keys sorted recursively (`sort_keys=True`);
   - separators `,` and `:` with no added whitespace; and
   - UTF-8 output bytes.
5. Compute SHA-256 over those UTF-8 bytes.
6. Encode the document value as `sha256:` followed by 64 lowercase hexadecimal
   characters.
7. Compare that value to the original document's top-level `hash` field.

In Python notation, the approved replay function is:

```python
def document_hash(value):
    canonical_value = dict(value)
    canonical_value.pop("hash", None)
    payload = json.dumps(
        canonical_value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()
```

## Consequences

- YAML comments, indentation, line endings, quoting style and mapping order do
  not affect the canonical hash when they parse to the same data object.
- Scalar type changes do affect the hash; for example, `1`, `1.0` and `"1"`
  are not interchangeable contract values.
- The raw-file SHA-256 and this canonical document hash serve different
  purposes and must not be substituted for each other.
- Duplicate mapping keys, custom YAML tags and non-JSON scalar values do not
  occur in the P0 replay vectors and are outside the approved input domain.
  Conforming validators must reject them before canonicalization; the current
  replay vectors do not by themselves prove duplicate-key rejection by every
  YAML parser.
- A change to this procedure requires explicit approval, a new contract/config
  version and regeneration of every bound hash/reference. It must not be
  applied retroactively to preserve a preferred result.

## P0 replay vectors

The P0 integration test currently binds these canonical values:

| Document | Canonical hash |
|---|---|
| `gamma-kernel-v0.8.yaml` | `sha256:0eb3cbb8be3cf51dc9952a447e4d1f90fc89b5dc2c5e2f0edafca32c6805399a` |
| `action-catalog-kernel-v0.8.yaml` | `sha256:0cd3ee1331aef81ca955e973ae9bc30c364acd2a2f6c34247438f4dd94add8eb` |

Replay coverage is located in
`tests/integration/test_twin_counterexample_fixture.py`. Passing that test
demonstrates conformance to the approved replay procedure; it does not grant
any certification or STOP authority.

## Approval record and change control

Decision: **APPROVED**. SI-002 is closed.

Any revision requires explicit approval, a new contract/config version and
regeneration of all affected hashes and references. Existing frozen hashes
must not be silently reinterpreted under a different canonicalization rule.
