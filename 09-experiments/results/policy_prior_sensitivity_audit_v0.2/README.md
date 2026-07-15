# Policy channel-prior sensitivity audit

All comparisons are paired within six independent cases. The 270 mask/intensity/seed conditions are repeated measurements, not 270 independent attacks. No inferential p-values are reported.

## Findings

- AFA myopic at ×0.75: 2 success losses and 14 outcome differences versus ×1.00.
- AFA rollout-h3 at ×0.75: success unchanged, but 75 action sequences changed.
- Depth-2 at ×0.75: 1 loss and 1 gain offset in the aggregate success count; 52 action sequences changed.
- At ×1.25, no tested policy changed actions or outcomes under the present discrete decision boundary.
- M2 and oracle controls did not change across prior arms, supporting fixed execution-environment isolation.

## Endpoint boundary

AFA uses the frozen runtime allowlist. Depth-2 now uses the frozen dedicated runtime allowlist; declared expected effects remain visible while realized outcomes are forbidden.

`all_experiments_complete=false`; paper/patent writing remains closed.
