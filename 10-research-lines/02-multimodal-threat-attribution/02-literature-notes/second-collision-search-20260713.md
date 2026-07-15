# Second Collision Search and Adversarial Gap Audit

Freeze date: 2026-07-13
Execution and metadata verification: 2026-07-13 to 2026-07-15
Scope: source-preserving traffic/log event graphs, cross-source relation confidence, missing/conflicting evidence, chain-grounded intent, and evidence-constrained LLM investigation.

## 1. Purpose

The first search showed that “PCAP + logs + graph + LLM” is already too broad to be a defensible contribution. The second search therefore tested five narrower residual claims (R1-R5) using functional wording, historical prior-art queries, current paper searches and patent redlines.

This is a collision search, not a citation-count review. A work is included when it owns a distinct input-representation-output cell, even if it is old, withdrawn or access-limited. Access-limited works can invalidate broad novelty wording but cannot support detailed performance claims.

## 2. Sources and protocol

- Discovery: Exa search via agent-reach; arXiv; OpenReview; Crossref; Semantic Scholar; publisher pages at IEEE, ACM, Springer, MDPI and official repositories.
- Verification: DOI/Crossref metadata, official publisher abstract/HTML, legal open PDF, official code/data artifact.
- Citation sweep: Semantic Scholar/OpenAlex forward checks for MuSAR and Traffic2Chain; backward families cross-checked against historical packet/log evidence graphs, probabilistic evidence merging and provenance reconstruction literature.
- Patent boundary: public patent records were used only for novelty wording; this is not a legal freedom-to-operate opinion.
- Cutoff rule: publications after 2026-07-13 are excluded. Metadata checked on 2026-07-14/15 does not alter the cutoff.

Search-result totals are intentionally not reported: Exa ranking, publisher indexes and deduplication do not expose a stable denominator. Reporting a pseudo-PRISMA count would create false precision. Every included functional collision is instead assigned an ID, access status and 15-section note.

## 3. Exact residual queries

1. `raw PCAP system logs cross-source event evidence graph attack chain`
2. `packet log provenance graph cross-source link confidence calibration cyber attack`
3. `network traffic host logs evidence graph missing modality conflict attack reconstruction`
4. `attack intent inference reconstructed attack chain packet logs cybersecurity`
5. `source-aware provenance graph evidence lineage packet index log record cybersecurity`
6. `LLM evidence-grounded attack chain claim citation raw security telemetry`

Additional redline variants:

- `network-enhanced threat provenance graph packet host process`
- `probabilistic integrated evidence graph missing cyber evidence`
- `CTI query graph provenance attack reconstruction`
- `potential relation completion provenance graph APT`
- `agentic backward tracking missing security logs`

## 4. Newly included collisions

| IDs | Functional family | Strongest conclusion |
|---|---|---|
| C42, C45, C55 | audit/multi-log graph and chain | graph construction and log correlation are mature contributions, not residual novelty |
| C44, C47, C49 | packet/network + host/log evidence | broad dual-source graph/fusion is occupied from 2016 through 2026 |
| C46, C50-C54 | uncertainty, confidence, missing evidence and relation completion | generic probability/confidence/graph completion wording is occupied |
| C48, C58, C59, C61 | LLM/multi-agent investigation | agentic backtracking, objectives, missing-event recovery and report generation are occupied |
| C57, C60 | CTI-to-provenance matching | CTI query graph/Sigma-guided reconstruction is occupied |
| C56 | multimodal detection/attention trace | feature fusion plus traceability is occupied, although this submission is withdrawn |
| F06 | systematic event-log correlation review | corroborates heterogeneity, causality and evaluation gaps across 120 selected studies |

## 5. Access-control gate

| Work | Access decision | Permitted use |
|---|---|---|
| ProHunter, SherAgent, ProvAgent | legal official PDF, `full-read` | method, experimental and limitation claims after note audit |
| T-Trace | `extended-indexed-read` | broad functional collision and official abstract claims only |
| M-IDAS | `extended-openreview-read`, withdrawn | multimodal/attention-path novelty redline only; not effectiveness evidence |
| Citar | `extended-publisher-read` | CTI-guided provenance reconstruction boundary; headline result kept qualified |
| ANTEATER | `metadata-abstract-only` | architecture-level agent redline only |

No access-limited paper is silently labeled full-read.

## 6. Forward/backward citation sweep

### MuSAR

- Semantic Scholar listed one forward citation at the time of checking: ZERO-APT (automated penetration testing).
- It does not construct a source-preserving packet/log event graph or calibrate packet-log relations, so it was screened out of R1-R5.
- MuSAR's backward functional neighborhood is represented by multi-log correlation, provenance reconstruction, ATT&CK stage mapping and multi-host chain works in C20/C30/C37/C40/C47/C54/F06.

### Traffic2Chain

- Semantic Scholar listed FSG-NID and LFRNet as forward citations at the time of checking.
- Both focus on network intrusion detection/feature modeling rather than independent traffic/log evidence graphs, so they do not occupy R1-R5.
- Its backward functional neighborhood is represented by traffic behavior correlation, traffic KG/LLM, ATT&CK labeling and attack-chain reconstruction in C05-C09/C41.

Citation indexes are dynamic and incomplete. This sweep proves only that the indexed forward citations checked by the cutoff did not close the residual; it is not a claim of exhaustive global citation coverage.

## 7. Adversarial gap audit

### Challenge 1: “BotFence has already built the same graph.”

Mostly true for the broad claim. BotFence joins SmartNIC DPI results to eBPF host provenance through deterministic 5-tuples and creates a network-enhanced TTP graph. The surviving distinction is not “network-enhanced provenance”; it is multi-candidate record-level relation learning, calibration, conflict states, independent subgraph fidelity and raw evidence anchors.

### Challenge 2: “He et al. already unified packets and logs in 2016.”

True for broad packet+log evidence graphs and raw-packet backtracking. The residual must require immutable packet/log observation identities, explicit candidate/verified/rejected/conflict states, learned/calibrated cross-source relations and campaign-disjoint link truth.

### Challenge 3: “APMP/MPCA already learn confidence and complete edges.”

They occupy graph-internal relation completion and event confidence. Their scores are not demonstrated to be calibrated packet-log pairing probabilities. The proposed task must define a cross-source candidate set, hard negatives, edge truth, Brier/ECE/reliability and selective prediction.

### Challenge 4: “HunterAgent/SherAgent already solve missing evidence.”

They occupy missing-hop recovery, query relaxation and evidence insufficiency. The residual is narrower: source disagreement and missingness must propagate from upstream relation states into chain and intent risk, with measured abstention.

### Challenge 5: “Clouseau/ProvAgent already infer objectives or intent.”

They produce objectives, stages or narrative conclusions, but do not isolate high-level goal-intent correctness from event retrieval or stage coverage. Intent can remain only as a secondary, explicitly annotated endpoint.

### Challenge 6: “The LLM itself is the novelty.”

Rejected. By 2026, LLM and multi-agent investigation over logs/provenance are crowded. The LLM is an evidence-constrained consumer of the graph, not the core novelty unit.

## 8. Residual verdict

| Residual | Verdict after second search | Strength |
|---|---|---|
| R1 source-preserving dual graph | survives only in strict form; broad dual-source graph is occupied | medium |
| R2 calibrated packet-log relation | no direct functional equivalent found | strongest |
| R3 conflict/missing-source propagation | generic missing evidence occupied; disagreement-aware propagation remains | medium-high |
| R4 chain-grounded goal intent | appears open but annotation and construct-validity risk are high | medium/secondary |
| R5 joint evidence replay/entailment | components exist separately; joint packet+log claim replay remains | high as trust contribution |

## 9. Search conclusion

The defensible core is **not** a new multimodal/agent framework. It is a measurement-centered problem:

> Given independently constructed, source-preserving traffic and log observation graphs, can a calibrated multi-candidate relation model connect the correct records, preserve conflict and abstention, and measurably improve attack-chain reconstruction and evidence-grounded high-level interpretation over traffic-only, log-only, fixed-window and deterministic-join baselines?

This conclusion authorizes candidate-topic synthesis, but final topic selection remains a user decision.
