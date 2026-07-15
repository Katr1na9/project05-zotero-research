# Patent Collision Redline

Search cutoff: 2026-07-13
Verification note: this is an academic novelty screen using public patent records. It is **not** a legal validity, infringement or freedom-to-operate opinion. Final legal conclusions require CNIPA records and qualified patent counsel.

## 1. Purpose

Patents are used here to prevent broad engineering claims such as “first multi-source attack trace graph” or “first packet/log attack path reconstruction.” They do not prove scientific validity, but they can destroy novelty wording.

## 2. Direct redlines

| Publication | Functional scope visible in public record | Collision strength | What cannot be claimed |
|---|---|---|---|
| CN121356897B | standardizes at least three heterogeneous logs, preserves offsets/record IDs, builds semantic event streams and reconstructs multi-scale attack traces | high for multi-log lineage | first source-aware multi-log trace graph |
| CN121940189A | active-window graph across network/host data, causal snapshots/path hash and historical-current stitching; critiques weak timestamp/5-tuple joins | very high | first network-host graph, first to improve timestamp/5-tuple joins, first path-hash trace |
| CN113783896B | network-traffic threat events + host process communication + AttackGraph knowledge graph + campaign path tracing | very high | first traffic+process+KG attack-path system |
| CN116112211A/B | ETW/auditd/EDR/log+CTI graph, local chain scoring/merge, ATT&CK mapping and high-level intent | high | first graph-based chain restoration plus ATT&CK/intent |
| CN120474836A | six-modal feature fusion, DTW/cross-self-gated attention, Dirichlet uncertainty, graph explanation | medium-high for architecture | first multimodal uncertainty-aware fusion or explanatory GNN |
| CN112765603B | logs + provenance anomaly detection and traceability | high for log-side pipeline | first provenance-log anomaly tracing |
| CN117692198A | multi-source network/alert/knowledge graph integration and PageRank-style tracing | medium | first multi-source KG trace ranking |
| CN122226502A | power-domain knowledge graph, dynamic deception and attack-intent analysis | medium/low for this implementation | first knowledge-graph attack-intent analysis |

Stable public-record pattern: `https://patents.google.com/patent/<publication-number>/zh`.

## 3. Scientific residual after patent screen

The patents reinforce the paper-level collision result: system-level fusion, multi-source graph construction, path stitching, ATT&CK mapping, uncertainty and intent are already broad prior-art language.

The surviving academic contribution must be stated as a **specific learning and evaluation problem**:

1. packet/log observation nodes retain immutable source identifiers and hashes;
2. cross-source candidate relations are multi-valued rather than a single deterministic join;
3. relation probabilities are empirically calibrated on campaign-disjoint data;
4. observed, candidate, verified, rejected, conflict and knowledge-hypothesis edges are distinct;
5. downstream chain/LLM gains are attributed to relation quality through controlled ablation;
6. every generated claim can be replayed to both packet and log records.

## 4. Forbidden novelty phrases

- “首次融合网络流量和系统日志进行攻击溯源”
- “首次构建多源攻击证据图”
- “首次利用知识图谱恢复攻击链”
- “首次利用大模型/多智能体进行自动攻击调查”
- “首次对缺失证据进行攻击链补全”
- “首次将 ATT&CK 与高层攻击意图结合”
- “首次提出带置信度的溯源图”

## 5. Safer contribution wording

- “We formulate packet-to-log observation linking as a campaign-disjoint, calibrated multi-candidate relation task rather than a deterministic join.”
- “We preserve source-specific subgraphs and immutable raw-record anchors while separating observed evidence from model hypotheses.”
- “We quantify how cross-source relation calibration affects chain reconstruction, selective abstention and claim-to-record replay.”
- “The LLM is constrained to cite graph and raw-record identifiers; unsupported high-level interpretations are rejected.”

## 6. Legal/academic follow-up gate

- [ ] Verify each publication's claims, legal status and family in CNIPA before manuscript submission.
- [ ] Search English-language patent families using the final method nouns and assignee names.
- [ ] Ask a patent professional if commercialization or filing is planned.
- [ ] Keep this screen separate from peer-reviewed related work; patents belong in novelty/prior-art discussion where venue rules permit.
