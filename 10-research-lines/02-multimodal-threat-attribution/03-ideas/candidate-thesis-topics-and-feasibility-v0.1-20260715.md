# Candidate Thesis Topics and Feasibility Matrix v0.1

Status: **pending user selection**
Prepared: 2026-07-15
Literature freeze: 2026-07-13
Upstream evidence: collision corpus v0.3, functional matrix v0.2, second-search audit, dataset audit and patent redline.

## Material Passport

| Field | Value |
|---|---|
| Research line | Project05 / multimodal threat attribution branch |
| User-owned main line | LLM + threat tracing/attack-intent sensing |
| Reusable Project03 asset | PCAP -> ThreatObservation, graph query and trace localization |
| Added evidence line | host/system/application logs -> LogObservation/provenance subgraph |
| Environment variables | IPv4, IPv6, MPLS, Geo and SCION are protocol/environment conditions, not five modalities |
| Excluded scope | CENI controller/network-element deployment compromises; actor/nation attribution without labels; autonomous agent novelty |
| Decision owner | user |

## 1. Non-negotiable novelty boundary

The following are already occupied and cannot be primary contributions:

- network/host multi-source graph construction in the broad sense;
- deterministic 5-tuple/PID/time joins;
- probabilistic attack/evidence graphs in the broad sense;
- graph-internal relation completion;
- CTI/ATT&CK query graph matching against provenance;
- LLM or multi-agent attack-chain investigation;
- missing-hop recovery and fluent incident-report generation.

The strongest residual is **R2: calibrated multi-candidate packet-log observation linking**, strengthened by source-preserving graph construction (R1), conflict/abstention propagation (R3) and evidence replay (R5). High-level goal intent (R4) remains a downstream extension.

## 2. Candidate A: complete main-line thesis

### Proposed title

**中文：面向威胁溯源的源保持流量-日志双线事件证据图与证据约束大模型攻击链推理方法**

**English: Source-Preserving Traffic-Log Event Evidence Graphs for Evidence-Constrained LLM Attack-Chain Reasoning**

### Core research question

Can calibrated cross-source relations between independently constructed traffic and log observation graphs improve attack-chain reconstruction and evidence-grounded high-level interpretation over traffic-only, log-only, fixed-window fusion and deterministic joins?

### Contribution package

1. A source-preserving schema that keeps immutable packet/log anchors and separates observation, candidate relation and semantic hypothesis layers.
2. A campaign-disjoint calibrated multi-candidate traffic-log relation model with explicit conflict and abstention states.
3. An uncertainty-aware joint event graph and controlled chain reconstruction evaluation.
4. An evidence-constrained LLM that maps chains to ATT&CK and goal-intent candidates only when every claim cites graph/raw-record IDs.

### Minimum publishable version

Items 1-3 are mandatory. Item 4 may be limited to ATT&CK/chain explanation if high-level intent labels are unreliable. Agents remain an appendix.

### Main risk

Scope creep: graph schema, relation learning, chain reconstruction and LLM evaluation can become four separate theses. The implementation must use Candidate B as the frozen core and treat the LLM as one downstream experiment.

## 3. Candidate B: safest measurable core

### Proposed title

**中文：面向攻击溯源事件图构建的可校准流量-日志跨源关系学习与不确定性传播**

**English: Calibrated Traffic-to-Log Relation Learning and Uncertainty Propagation for Attack Provenance Graph Construction**

### Core research question

How accurately and reliably can packet/log observation pairs be linked under campaign shift, clock drift, ambiguous identifiers and missing sources, and how does relation quality affect downstream graph and chain fidelity?

### Contribution package

1. A record-level relation task, annotation protocol and campaign-disjoint benchmark split.
2. Deterministic, feature-based and representation-learning baselines with probability calibration.
3. Explicit `candidate/verified/rejected/conflict` edges and uncertainty propagation.
4. Causal attribution of relation quality to graph/chain quality through traffic-only, log-only and join-rule ablations.

### Minimum publishable version

One primary dataset (ProvICS), one external dataset (AIT v2), at least four join/model baselines, edge discrimination + calibration + chain-level downstream evaluation.

### Main risk

It is less visibly “LLM-centric.” To preserve the Project05 main line, add a small evidence-grounded LLM interpretation experiment after the core results, but do not make LLM performance a condition of thesis success.

## 4. Candidate C: high-risk trust/intent extension

### Proposed title

**中文：基于双源事件证据图的可信大模型攻击链解释与高层攻击意图感知**

**English: Trustworthy LLM Attack-Chain Explanation and High-Level Intent Sensing over Dual-Source Event Evidence Graphs**

### Core research question

Can evidence-linked generation, conflict-aware abstention and claim replay make LLM-derived attack-chain explanations and high-level goal-intent candidates more trustworthy than unconstrained RAG or provenance summaries?

### Contribution package

1. Claim-to-node/edge/raw-record citation and deterministic citation validation.
2. Evidence/hypothesis separation with conflict-aware abstention.
3. A goal-intent annotation protocol distinct from ATT&CK tactic, event maliciousness and actor identity.
4. Claim support, replay success, intent calibration and analyst verification-time evaluation.

### Minimum publishable version

Requires an already functioning dual-source graph and a double-annotated intent/claim set. Without acceptable inter-annotator agreement, reduce the endpoint to ATT&CK/chain explanation.

### Main risk

Construct validity and labeling cost are high. “Intent” may collapse into ATT&CK tactic or analyst speculation, while LLM evaluation can become subjective. This is best treated as a second paper or thesis extension, not the first implementation milestone.

## 5. Weighted feasibility matrix

Scale: 1 weak/high risk, 5 strong/low risk. Weighted score is a planning aid, not a scientific result.

| Criterion | Weight | A complete main line | B measurable core | C trust/intent extension |
|---|---:|---:|---:|---:|
| Novelty after collision search | 0.25 | 4.4 | 4.8 | 4.1 |
| MSc implementation feasibility | 0.25 | 3.7 | 4.7 | 2.8 |
| Dataset/annotation feasibility | 0.15 | 3.8 | 4.3 | 2.5 |
| Project03 reuse | 0.15 | 5.0 | 4.8 | 3.8 |
| Evaluation clarity | 0.10 | 4.3 | 5.0 | 2.8 |
| Alignment with LLM+tracing main line | 0.10 | 5.0 | 3.8 | 5.0 |
| **Weighted total** | **1.00** | **4.26** | **4.60** | **3.37** |

## 6. Recommendation

**Recommend Candidate A as the thesis title and scientific narrative, implemented with Candidate B as the non-negotiable core.**

This resolves the apparent trade-off:

- A preserves the user's main line: LLM is genuinely integrated with threat tracing, not merely appended to IDS.
- B supplies the strongest unoccupied novelty unit, clear labels, calibration metrics and a fallback that can stand without subjective intent claims.
- C becomes an optional second contribution after the graph and relation experiments pass their gates.

The resulting contribution hierarchy is:

```text
Primary: calibrated traffic-log cross-source relation
  -> enables source-preserving joint event evidence graph
  -> improves attack-chain reconstruction
  -> constrains LLM ATT&CK/goal-intent interpretation and abstention
```

## 7. Proposed method framework for Candidate A

### M1. Independent source adapters

- Traffic side: reuse Project03 PCAP parsing and ThreatObservation generation; preserve pcap hash, packet/frame index, timestamp, five-tuple, protocol and payload-derived evidence pointer.
- Log side: parse audit/system/application logs into LogObservation with record ID/offset, host, process/PID, file/socket/action and parser version.
- Environment fields: IPv4/IPv6/MPLS/Geo/SCION are recorded as protocol/environment strata. They are not counted as modalities.

### M2. Source-preserving evidence schema

Node classes:

- `TrafficObservation`
- `LogObservation`
- `Entity` (host, process, file, socket, account, endpoint)
- `AttackEvent`
- `TechniqueHypothesis`
- `IntentHypothesis`

Edge layers:

- observed intra-source edges;
- candidate cross-source relations;
- verified/rejected/conflict relations;
- knowledge/ATT&CK hypotheses.

No model-generated edge may overwrite an observed edge or lose its raw anchor.

### M3. Candidate generation and calibrated relation learning

1. Generate a high-recall candidate set with broad temporal, endpoint, PID/socket and protocol rules.
2. Compare deterministic 5-tuple/time/PID rules, logistic/gradient-boosting features, dual encoders and a lightweight cross-encoder/GNN relation scorer.
3. Calibrate on a campaign-disjoint calibration set using temperature, isotonic or Platt scaling as appropriate.
4. Select relations by risk/coverage, not one fixed probability threshold.
5. Preserve top-k competing edges and explicit conflicts.

### M4. Joint graph and chain reconstruction

- Build the joint graph by referencing source nodes; do not flatten them into one event table.
- Produce top-k temporally valid chains using relation posterior and source-edge confidence.
- Compare against traffic-only, log-only, fixed-window concatenation, He-style event normalization, BotFence-style deterministic joins, MuSAR-style heuristic association and APMP-style graph-internal completion.

### M5. Evidence-constrained LLM layer

- Input only a bounded candidate subgraph plus an ID-indexed evidence table.
- Output structured claims: stage/technique, chain explanation, optional goal-intent candidates, supporting IDs and confidence/abstention.
- A deterministic verifier rejects nonexistent IDs, unsupported edge directions and claims without minimum evidence.
- `ATT&CK tactic != goal intent`; actor attribution is excluded unless a separate actor-label dataset is introduced.

## 8. Experiment blueprint

### Hypotheses

- H1: calibrated relation learning improves cross-source edge AUPRC and Brier/ECE over deterministic joins under campaign-disjoint testing.
- H2: improved cross-source relation quality yields measurable chain-edge F1/campaign recall gains beyond traffic-only and log-only graphs.
- H3: conflict-aware selective prediction lowers wrong-chain risk at useful coverage.
- H4: evidence-constrained LLM generation lowers unsupported-claim rate and improves replay success without unacceptable chain/intent recall loss.

### Datasets

- Primary: ProvICS pilot, then full selected campaigns.
- External validity: AIT Log Dataset 2.0.
- Additional provenance-heavy set: CICAPT-IIoT or ProvCon only after license verification.
- OpTC: log/flow ablation only, not packet-level proof.

### Baselines

1. traffic-only graph;
2. log-only provenance graph;
3. early feature concatenation/fixed time window;
4. deterministic time + five-tuple join;
5. deterministic PID/socket join where available;
6. BotFence-style deterministic network-to-host attachment;
7. MuSAR-style IP/time/stage/keyword association;
8. uncalibrated learned relation;
9. calibrated learned relation;
10. unconstrained LLM/RAG versus evidence-constrained LLM.

### Metrics

- Subgraph: node/edge precision/recall and raw-anchor survival.
- Relation: AUPRC, macro-F1, Hits@k/MRR, Brier, ECE and reliability diagrams.
- Selective prediction: risk-coverage and conflict recall.
- Chain: edge F1, stage order, campaign recall and graph edit distance.
- LLM: supported-claim precision, unsupported-claim rate, claim-to-record entailment, replay success and abstention quality.
- Operational: latency, memory, graph size, alerts/campaign and analyst verification time.

### Mandatory splits and ablations

- campaign-disjoint train/calibration/test;
- source missingness, clock drift, NAT/shared IP and benign interleaving;
- without traffic line, without log line, without relation calibration, without conflict state, without raw anchor and without LLM verifier;
- protocol/environment stratification where IPv4/IPv6/MPLS/Geo/SCION data are genuinely available.

## 9. Kill criteria and fallback

| Gate | Kill criterion | Fallback |
|---|---|---|
| relation labels | pilot double annotation has unacceptable agreement or no defensible relation semantics | reduce relation types to `same-action/supports/unrelated` and document ambiguity |
| calibration | learned model does not beat deterministic joins on discrimination or calibration | publish dataset/schema/negative result only if annotation quality and analysis are strong; otherwise stop |
| chain gain | relation improvement does not change chain metrics | thesis narrows to calibrated graph construction and failure analysis |
| LLM gain | verifier reduces recall without improving support/replay | remove LLM as contribution; keep it as diagnostic appendix |
| intent validity | low agreement or sparse classes | replace goal intent with ATT&CK technique/tactic and abstention evaluation |
| dataset transfer | external dataset lacks required raw anchors/license | keep external test at flow/log level and state the generalization boundary |

## 10. User decision gate

- [ ] Select A, B or C.
- [ ] Approve or revise the recommended “A narrative + B core + C optional” hierarchy.
- [ ] After approval only: freeze the final RQ, acquire the pilot dataset and write the implementation/experiment plan.
