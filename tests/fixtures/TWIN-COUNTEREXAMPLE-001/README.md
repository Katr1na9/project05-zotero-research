# TWIN-COUNTEREXAMPLE-001

This P0 fixture freezes a two-world ambiguity under Γ v0.8. The admitted case
evidence shows use of `ACCOUNT-A` on `H3` and an ordinary process record on
`H1`, but it does not reveal whether the initial foothold was `H1` followed by
lateral authentication or a direct external credential login to `H3`.

Expected Checker rows are `base=SAT`, `support=SAT`, `alternative=SAT`, hence
`COUNTEREXAMPLE_FOUND`. Because at least one deterministic, executable action
distinguishes the worlds, the expected main system state is `CONTINUE`.

The fixture is a contract artifact only. The counterexample is an expected
solver-side world pair, not external ground truth. Action observations and
resource traces are evaluator-side post-execution examples and are not inputs
to candidate, certificate or counterexample generation.

The CTI background row is `admitted` only for candidate/ranking consumption:
`admitted` does not mean `certifying`, and its
`certification_authority.allowed=false` prevents it from excluding worlds or
supporting a certificate. Repeated numeric `policy_hash` values in this fixture
are schema-exercise placeholders, not policy proof; a formal freeze must bind
the real policy artifact hash.

The fixture deliberately includes:

- a distinguishing positive observation;
- a zero-hit whose elimination use is legal only with bounded completeness;
- a high-resource, low-discrimination action;
- a formally distinguishing but currently unauthorized action;
- formally observation-equivalent/control queries;
- a heuristic-only action with no formal observation model; and
- a genuine empty-result control query.
