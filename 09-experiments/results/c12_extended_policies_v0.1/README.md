# C12 frozen policy-family transfer v0.1

All policies are evaluated on one G1 operational incident with 45 repeated conditions. XGBoost training remains C01-C06, and all three model hashes match the C07-C10 frozen evaluation.

Depth-2 matches Oracle cost (`0.8889`); Rollout-H3, XGBoost and Logistic cost `0.9778`; M2 costs `1.4222`; AFA Myopic costs `1.5111`. Every deterministic policy reaches the internal G1 target, so this is a cost-ordering and boundary result, not a success-rate or actor-attribution result.
