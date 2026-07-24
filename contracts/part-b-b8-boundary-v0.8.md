# Part B B8 boundary contract v0.8

Status: **LOCAL REVIEW — CONTRACT ONLY**

```text
Authorized slice: B8_HOLDOUT_ANALYSIS
holdout_preregistration_contract_authority=true
statistical_analysis_contract_authority=true
analysis_envelope_contract_authority=true
holdout_data_access_authority=false
holdout_label_access_authority=false
holdout_result_access_authority=false
statistical_analysis_execution_authority=false
source_selection_authority=false
source_authorization_authority=false
connector_execution_authority=false
planner_execution_authority=false
sampling_authority=false
scalarization_authority=false
performance_claim_authority=false
stop_authority=NONE
B9=CLOSED
```

## 1. Authorized result

B8 may freeze closed JSON Schemas, a deny-only policy, an outcome-blind
preregistration, a statistical-analysis plan, a no-data analysis envelope,
canonical hashes, a manifest, contracts, issue records and deterministic
contract tests.

These artifacts establish `CONTRACT_CONSISTENCY_ONLY`. There is NO HOLDOUT
LABEL access, NO HOLDOUT RESULT access and NO STATISTICAL EXECUTION. A valid
contract is not evidence that a real split exists, is uncontaminated or has
been analyzed.

## 2. Isolation and source boundary

The B4 order `TRAIN`, `TUNE`, `EVALUATION`, `HOLDOUT` remains unchanged.
The abstract split fingerprint commits only the inert fixture phrase recorded
by the preregistration; it is not a dataset fingerprint or completeness
attestation. The contract does not unseal HOLDOUT.

`PB-SI-006` remains OPEN. B7 provenance validity and descriptor conformance do
not select or authorize a real source. Every real source still requires
PER-SOURCE SEPARATE AUTHORIZATION, followed by a separate execution decision.

`PB-B5-SI-001` remains OPEN. No Planner implementation is admitted, and legacy
M3* execution authority remains NONE.

## 3. Hash direction

The policy, preregistration and statistical plan bind only frozen upstream
identities. The B8 manifest binds those three B8 hashes. The no-data analysis
envelope then binds the manifest and the three earlier B8 artifacts.

This directed order avoids a circular hash dependency. The manifest does not
claim to contain an analysis output, and the envelope cannot rewrite any
bound identity.

## 4. Non-authority

B8 reads no data, labels, outcomes, rankings or historical experimental
material. It runs no baseline, Planner, sampler, connector, evaluator,
statistical procedure or resampling loop. It creates no performance claim,
certificate, system status or `CERTIFIED_STOP`. B9 remains closed.
