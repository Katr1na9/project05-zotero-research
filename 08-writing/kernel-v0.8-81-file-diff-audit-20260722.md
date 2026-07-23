# Kernel v0.8 15-commit / 81-file diff audit

Status: **ENGINEERING REVIEW COMPLETE — HUMAN A16 ACCEPTANCE PENDING**

- Baseline: `d156b68`
- Historical review tip: `5e9c0ba`
- Range: `d156b68..5e9c0ba`
- Inventory: 15 commits, 81 files, 12,069 inserted lines
- Review date: `2026-07-22`

This is the written review record requested by the A16 NO-GO ruling. It is a
Codex-assisted engineering diff review, not a substitute for the user's final
human A16 decision. The exact 81-path inventory is the output of:

```text
git diff --name-status d156b68..5e9c0ba
```

and is reproduced by section and count in the A16 review package. All 81 paths
were inspected by commit, owning slice, and invariant category. No path under
`src/compiler/llm/`, `training/`, `datasets/llm/`,
`tests/compiler_contract/`, `09-experiments/`, or Part B occurs in the range.

## Commit-by-commit conclusion

| Commit | Slice | Scope conclusion | Technical conclusion |
|---|---|---|---|
| `3b34f3e` | P0 | within authorized schemas/configs/IR/fixture/tests/spec paths | finite/deterministic contracts present; placeholders are fixture-only |
| `43ba22a` | P0 rulings | within hash/spec-issue contract | approved Gamma hash rule and SI-004/SI-005 rulings only |
| `0e72757` | P1 | Checker + tests only | seven-row result table; timeout remains UNKNOWN |
| `54174e3` | P2 | MinDiff + tests only | timeout cannot rewrite `COUNTEREXAMPLE_FOUND` |
| `1ebbf91` | P3 | artifact assembler + tests only | no action execution, authority, or STOP emission |
| `ede7b30` | P4 | action selection + tests only | oracle/hidden actions rejected; no execution |
| `1bae135` | P5 | deterministic executor + tests only | deterministic models only; failures stay explicit |
| `4da8d2a` | P6 | elimination/recert + tests only | historical two-witness exhaustiveness defect found; remediated in the current A16 supplement with complete compiled legal worlds and a three-world regression |
| `ee06f37` | P7 | Firewall + tests only | admission decision is not promotion/certificate/STOP |
| `5d678bf` | P8 | lifecycle/audit + tests only | modality preserved; pointer required; append-only in-run hash chain |
| `441c7c4` | P9 | certificate/state + tests only | candidate-only cannot STOP; historical caller-declared coverage weakness remediated in the current A16 supplement by ceiling/world/hash/bound binding |
| `93af889` | P10 | thin E2E driver + tests only | existing components wired; no Planner/M3*/probability policy |
| `592f13f` | closeout | status documents only | no runtime semantics changed |
| `d546b93` | approved debt repair | FW code, compiler, projection, tests/docs | no LLM/training/Part B changes; predicates catalog-bound |
| `5e9c0ba` | P11 | adapter + opt-in driver hook + tests | default P10 behavior preserved; adapter/FW/admit cannot sign or STOP |

## Required invariant conclusions

### Authorization and forbidden-track isolation

PASS. Every path belongs to the progressively authorized P0–P11 Part A
slices or their tests/status documents. The forbidden-path scan returned zero
matches for LLM compiler implementation, training, LLM datasets/compiler
contract tests, `09-experiments`, or Part B. No Planner or M3* algorithm was
introduced.

### P11 versus default P10 and STOP gate

PASS. `observation_admission=None` preserves the original P10 path. P11 is an
explicit opt-in hook after P5 and before existing feedback/state derivation.
Neither the adapter, Firewall evaluation, nor P8 admission can create a level
certificate. `CERTIFIED_STOP` remains isolated to P9 and requires an already
issued, artifact-bound level-complete certificate.

### OBS evidence boundary

PASS. On the frozen Twin rows, OBS-001/002 are deterministic formal action
observations and may pass Firewall/admission. OBS-003 is an empty-control row
and OBS-004 is heuristic CTI; both are denied and cannot be promoted or used
for certification. The default action selection executes OBS-001/002 only;
OBS-003/004 denial is exercised as an explicit frozen-row contract test and is
not misreported as default execution.

### Pointer, modality, and oracle/hidden fail-closed behavior

PASS. P11 binds `pointer.record_id` to the emitted `observation_id`, preserves
`modality=observed`, and rejects missing/unresolvable rows, unknown actions,
oracle/hidden fields, and unsupported/control/heuristic observations. P8
rejects promotion that changes modality or loses a resolvable pointer. Oracle
field occurrences in source are deny lists or rejection logic; none is a
runtime input to Checker, action selection, certificate, or artifact output.

### Findings requiring remediation

Two material findings were found rather than silently waived:

1. P6 treated one counterexample's two witnesses as the complete world table.
   The current A16 supplement now requires `CompiledFiniteProblem`, filters all
   compiler-declared legal worlds, and proves on a three-world supply-chain
   fixture that eliminating MIRROR-B leaves BUILDER-C as a valid alternative.
2. P9 accepted internally consistent caller coverage counts without binding
   them to the ceiling legal-world table. The current supplement now binds the
   ordered candidates, legal-world count/hash, Cartesian bound, and actual
   alternative-UNSAT enumeration count.

Both remediations are outside the historical `d156b68..5e9c0ba` range and must
be reviewed as part of the new A16 supplement before any Go decision.

## Review disposition

The historical 81-file inventory has a written engineering conclusion for all
five A16 checklist questions. There is no forbidden-track mix-in. The two
technical findings have current-tree remediations and regression tests. The
admission policy is now exact-hash approved; human acceptance of this record,
final full regression, and a new A16 ruling remain separate gates. This
document does not authorize
push, PR, Part B, level certification, or `CERTIFIED_STOP`.
