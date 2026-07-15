# Collision Corpus v0.3

Freeze date: 2026-07-13
Scope: traffic/log observations, event/evidence graph construction, LLM investigation, trace/stage/intent, and evidence trust.

This version closes the second residual-cell search and citation sweep. It extends C01-C41 with direct historical evidence-graph, recent dual-source, relation-completion, CTI-provenance and agentic-investigation redlines. The corpus is frozen at **2026-07-13**; metadata and access-state checks performed on 2026-07-14/15 do not expand the publication cutoff.

## 1. Status vocabulary

| Status | Meaning |
|---|---|
| `full-read` | complete paper text read and a 15-section note exists |
| `reused-full-read` | complete note already existed in the shared workspace and was re-audited for this line |
| `extended-publisher-read` | publisher HTML/preview exposed method and results beyond the abstract; PDF unavailable |
| `metadata+artifact-read` | verified metadata plus official code/data artifacts were inspected; PDF unavailable |
| `metadata-only` | title/authors/venue/DOI/abstract verified; no claim beyond accessible metadata |
| `extended-indexed-read` | official metadata plus search-index-visible method text; no complete legal full text, so detailed claims are prohibited |
| `extended-openreview-read` | OpenReview metadata/revisions and indexed content checked; PDF unavailable or submission withdrawn |
| `metadata-abstract-only` | official publication metadata and abstract only; no method/result detail beyond the abstract |
| `appendix-read-pending` | full text obtained but deferred under the user-approved agent-last rule |
| `screened-out` | recorded search hit that does not own a distinct functional cell |

## 2. Direct traffic / PCAP collision set

| ID | Paper | Functional collision | Status | Shared note |
|---|---|---|---|---|
| C01 | CyberSleuth | PCAP/log tools, forensic report, CVE and success inference | `full-read` | `2026-Fumero-CyberSleuth.md` |
| C02 | From Anomaly to Attack Path | suspicious flow/payload -> local LLM -> graph DB -> attack path | `metadata-only` | `2026-Pletzer-From-Anomaly-to-Attack-Path.md` |
| C03 | Holmes | PCAP Evidence Pack, auditable anchors, structured investigation | `full-read` | `2026-Chen-Holmes.md` |
| C04 | Privacy-Preserving PCAP Incident Analysis | local LLM + PCAP + TI/RAG | `metadata-only` | `2026-Rahman-Privacy-Preserving-PCAP-LLM.md` |
| C05 | KLAGE | PCAP/flows -> communication KG -> Graph-BERT/LIME -> LLM report | `extended-publisher-read` | `2025-Belcastro-KLAGE.md` |
| C06 | mmTraffic | byte-grounded multimodal traffic-language reasoning | `full-read` | `2026-Zhang-mmTraffic.md` |
| C07 | TrafficLLM | generic packet/flow representation for LLM tasks | `full-read` | `2025-Cui-TrafficLLM.md` |
| C08 | eX-NIDS | flow + CTI -> LLM explanation | `full-read` | `2025-Houssel-eX-NIDS.md` |
| C09 | Fine-grained traffic retrieval | HTTP traffic -> CTI retrieval -> LLM CVE reranking | `extended-publisher-read` | `2026-Chen-Fine-Grained-Traffic-Retrieval.md` |
| C41 | Traffic2Chain | traffic alerts -> ATT&CK sub-techniques -> LLM event descriptions -> attack chain | `metadata-only` | `2025-Xie-Traffic2Chain.md` |

## 3. Traffic + log dual-source and event/evidence graph set

| ID | Paper | Functional collision | Status | Shared note |
|---|---|---|---|---|
| C10 | Llama-PcapLog | paired PCAP + syslog instruction tuning and joint analysis | `full-read` | `2025-Choi-Llama-PcapLog.md` |
| C11 | Multi-Source Cybersecurity Logs | paired system/network/browser logs with event-level ATT&CK labels | `full-read` | `2026-Niloy-Multi-Source-Cybersecurity-Logs.md` |
| C12 | Retrieval-Augmented LLMs for Security Incident Analysis | multi-source logs + ATT&CK query library + sequence reconstruction | `full-read` | `2026-Cadet-RAG-Security-Incident-Analysis.md` |
| C13 | OntoLogX | honeypot logs -> ontology-grounded session KG -> ATT&CK | `full-read` | `2026-Cotti-OntoLogX.md` |
| C14 | HunterAgent | corrupted heterogeneous logs, generator-verifier trace reconstruction | `full-read` | `2026-Zhao-HunterAgent.md` |
| C15 | PROVSEEK | provenance DB + reports + RAG/agents -> verifiable summaries | `full-read` | `2025-Mukherjee-PROVSEEK.md` |
| C16 | ANANKE | heterogeneous logs + threat knowledge + iterative investigation | `full-read` | `2025-Dai-ANANKE.md` |
| C17 | Security Logs to ATT&CK Insights | Suricata logs -> ATT&CK + cognitive motive candidates | `full-read` | `2025-Hans-Security-Logs-ATTACK-Cognitive-Inference.md` |
| C18 | OCR-APT | provenance subgraphs + LLM validation -> APT story | `full-read` | `2025-Aly-OCR-APT.md` |
| C19 | StageFinder | host/network provenance -> temporal attack-stage probabilities | `full-read` | `2026-Phan-StageFinder.md` |
| C20 | Multi-source log semantic investigation | application + OS logs -> provenance graph -> seven-stage matching | `extended-publisher-read` | `2025-Song-Multi-Source-Log-Investigation.md` |
| C21 | FuseChain | multi-source telemetry -> temporal heterogeneous graph -> stages | `full-read` | `2026-Tan-FuseChain.md` |
| C22 | SynthChain | cross-source observability and chain-level ground truth | `full-read` | `2026-Tan-SynthChain.md` |
| C30 | UTLParser | heterogeneous logs -> triples/subgraphs -> directed multigraph | `full-read` | `2025-Tan-UTLParser.md` |
| C31 | AISL | ontology-based audit integration with expert intent priors | `extended-publisher-read` | `2024-Yue-AISL.md` |
| C34 | Auto-Prov | LLM-generated heterogeneous-log provenance extraction and interpretation | `full-read` | `2026-Ghosh-Auto-Prov.md` |
| C37 | Two-stage multi-datasource ML | synchronous traffic/log/host source models -> technique/lifecycle | `full-read` | `2024-Lin-Two-Stage-Multi-Datasource.md` |
| C38 | Sentient | audit provenance Graph Transformer + latent behavior-intent embedding | `full-read` | `2026-Yan-Sentient.md` |
| C39 | MOLE | LLM-generated provenance parsing templates | `metadata-only` | `2025-Ren-MOLE.md` |
| C40 | MuSAR | network alarms + application logs -> events -> multi-host attack chain | `metadata+artifact-read` | `2025-Liu-MuSAR.md` |

## 4. Graph, knowledge alignment, and trust set

| ID | Paper | Functional collision | Status | Shared note |
|---|---|---|---|---|
| C23 | AttacKG+ | LLM CTI text -> behavior/TTP/state graph | `reused-full-read` | `2024-Zhang-AttacKG-plus.md` |
| C24 | CLIProv | provenance log/CTI contrastive alignment | `reused-full-read` | `2025-Li-CLIProv.md` |
| C25 | MM-AttacKG | text/image CTI -> multimodal attack graph | `reused-full-read` | `2025-Zhang-MM-AttacKG.md` |
| C26 | TracLLM | trace long-context evidence contributing to LLM output | `full-read` | `2025-Wang-TracLLM.md` |
| C27 | LLMs are Unreliable for CTI | consistency, reliability, and calibration red line | `reused-full-read` | `2025-Mezzi-LLMs-Unreliable-CTI.md` |
| C28 | Uncertainty-aware attack stage | evidential uncertainty and OOD stage inference | `full-read` | `2025-Gaudenzi-Uncertainty-Attack-Stage.md` |
| C29 | XAPT | calibrated anomaly scores + Bayesian stage inference + SHAP | `full-read` | `2025-Lu-XAPT.md` |
| C33 | Provenance evaluation survey | evaluation-unit audit and campaign recall definition | `full-read` | `2026-Ipekbayrak-Provenance-Evaluation-Survey.md` |
| C35 | SHIELD | provenance subgraphs + LLM chain summary + heuristic confidence | `full-read` | `2025-Gandhi-SHIELD.md` |

## 5. Second-search direct collision set

| ID | Paper | Functional collision | Status | Shared note |
|---|---|---|---|---|
| C42 | SAURONEYES | audit-only knowledge/interaction dual views, malicious-edge detection and overlapping attack-chain communities | `full-read` | `2025-Qiao-SAURONEYES.md` |
| C43 | ForenGRAF-AI | conceptual signed temporal heterogeneous evidence graph with GNN/Bayesian/causal modules | `full-read` | `2026-Brandao-ForenGRAF-AI.md` |
| C44 | APTGuard | tcpdump PCAP + auditd/config fixed-window fusion, ML stage labels and LLM chain ordering | `full-read` | `2026-Li-APTGuard.md` |
| C45 | From Logs to Tactics | syslog + EDR log graph, graph embedding, LLM summarization and ATT&CK/campaign reconstruction | `extended-publisher-read` | `2026-Ferazza-From-Logs-to-Tactics.md` |
| C46 | M-DUCAG | probabilistic dynamic uncertain causal attack graph and posterior candidate paths | `full-read` | `2025-Dong-MDUCAG.md` |
| C47 | Network Forensics Evidence Graph | packet + program/web logs normalized into evidence events, graph route and raw-packet backtracking | `extended-publisher-read` | `2016-He-Network-Forensics-Evidence-Graph.md` |
| C48 | Clouseau | multi-agent structured-log investigation of source, timeline, kill chain and stated objectives | `full-read` | `2025-Aldaihan-Clouseau.md` |
| C49 | BotFence | eBPF host provenance + SmartNIC DPI network result joined by 5-tuple into network-enhanced TTP graph | `full-read` | `2024-Seo-BotFence.md` |
| C50 | MPCA | audit event triples with semantic branch merge and confidence estimation | `extended-publisher-read` | `2025-Zhang-MPCA.md` |
| C51 | Integrated Evidence Graphs | probabilistic merge of sub-evidence graphs and MulVAL-assisted missing-evidence completion | `full-read` | `2013-Liu-Integrated-Evidence-Graphs.md` |
| C52 | APMP | BERT predicts 14 graph-internal potential relations and writes them into an audit provenance graph | `full-read` | `2026-Li-APMP.md` |
| C53 | Power System APT Graph | PROV-DM event graph, GAT autoencoder edge reconstruction and graph-level detection | `full-read` | `2025-Zhang-Power-Provenance-Graph.md` |
| C54 | Evidence Security Events | Snort/network/web/DB evidence graph, MulVAL paths and expert missing-evidence hypotheses | `full-read` | `2014-Liu-Evidence-Security-Events.md` |
| C55 | T-Trace | system/network-related log correlation, tensor event communities and APT provenance graph | `extended-indexed-read` | `2024-Li-T-Trace.md` |
| C56 | M-IDAS | withdrawn multi-domain IoT feature fusion and attention-based cross-domain trace path | `extended-openreview-read` | `2024-Ge-M-IDAS.md` |
| C57 | ProHunter | CTI query graph, audit threat-subgraph sampling and learned cross-graph matching | `full-read` | `2026-Qiu-ProHunter.md` |
| C58 | SherAgent | production-log agentic query relaxation and backtracking under missing events | `full-read` | `2026-Li-SherAgent.md` |
| C59 | ProvAgent | audit provenance identity-behavior detector followed by four-agent investigation | `full-read` | `2026-Yan-ProvAgent.md` |
| C60 | Citar | CTI/Sigma-guided alert alignment and attack reconstruction over audit provenance | `extended-publisher-read` | `2025-Ghosh-Citar.md` |
| C61 | ANTEATER | raw audit filtering, provenance graph and three-agent attack-subgraph/report generation | `metadata-abstract-only` | `2026-Ren-ANTEATER.md` |

Key correction after C42-C61: broad **traffic + logs + graph**, **probabilistic graph**, **missing evidence**, **relation completion**, **CTI-to-provenance matching**, and **agentic attack investigation** claims are all occupied. The defensible residual is narrower: *source-preserving independent traffic/log subgraphs plus a calibrated, multi-candidate cross-source observation relation and explicit evidence/hypothesis separation*.

## 6. Agent-last appendix

| ID | Paper | Reason retained | Status |
|---|---|---|---|
| C36 | Minos | latest agentic backward-tracking over provenance evidence; needed only after core method boundary | `full-read` |
| C58 | SherAgent | query relaxation and branch pruning under missing log evidence | `full-read` |
| C59 | ProvAgent | provenance detector plus multi-agent IOC/kill-chain narration | `full-read` |
| C61 | ANTEATER | formal filter-then-three-agent audit-log investigation boundary | `metadata-abstract-only` |

## 7. Shared foundations

| ID | Paper | Reuse | Status |
|---|---|---|---|
| F01 | AttacKG | behavior/TTP graph schema | `reused-full-read` |
| F02 | EXTRACTOR | system-behavior extraction schema | `reused-full-read` |
| F03 | KAIROS | whole-system provenance and investigation boundary | `reused-full-read` |
| F04 | TechniqueRAG | CTI-to-ATT&CK retrieval/annotation | `reused-full-read` |
| F05 | CTIBench | LLM/CTI evaluation task design | `reused-full-read` |
| F06 | Event Log Correlation Systematic Review | 120-study taxonomy and evaluation-gap audit for heterogeneous event correlation | `full-read` |

## 8. Screened-out latest hits

| Work/family | Decision | Reason |
|---|---|---|
| C32 / SHAPE | `screened-out` | system-behavior graph detection/localization; no dual-source chain/intent; represented by KAIROS/Sentient |
| EdgeTrace, ORTHRUS, MGDA, Slot | `screened-out` | audit-only provenance detection/chain family; represented by KAIROS/Sentient/SHIELD |
| APT-LLM, Semantic-Aware AE | `screened-out` | ordinary provenance anomaly detection; no distinct dual-source graph/intent cell |
| MultiKG, MCKG | `screened-out` | knowledge-level CTI/code/log fusion, not event-evidence fusion; represented by C23-C25 |
| ReGAIN | `screened-out` | traffic RAG with citation/abstention, but only flood classification; trust cell represented by Holmes/TracLLM/C27 |
| Revelation | `screened-out-for-core` | PCAP agentic QA; agent scope deferred and traffic-only interpretation represented by CyberSleuth/Holmes |
| MalRAG | `screened-out` | open-set malicious-flow classification; no chain, log-side evidence, or intent |
| TracePcap, PCAP Hunter, PCAPGraph | `screened-out-paper-corpus` | engineering artifacts, not peer-reviewed papers; retain only for implementation comparison |
| MGDA, RAS-GNN, ProvGRP | `screened-out` | audit/provenance detection or reconstruction without an independent traffic-log relation cell; represented by C42/C52/C53/F03 |
| CrptAC | `screened-out` | encrypted-traffic attack-chain reconstruction only; no log-side evidence graph |
| Evidence-First RAG | `screened-out` | trustworthy CVE/SOC retrieval, not runtime dual-source chain construction |
| Cyber Defense Benchmark | `screened-out-for-core` | agentic log-hunting evaluation; relevant to appendix, not upstream evidence-graph construction |
| ProGQL | `screened-out` | query language over an assumed audit provenance graph; no cross-source relation learning |
| LateralX, GraphHunter, GLAIVE | `screened-out-paper-corpus` | non-peer-reviewed engineering implementations; retained only as implementation redlines |
| FSG-NID, LFRNet | `screened-out-forward-citation` | forward citations of Traffic2Chain focus on intrusion detection, not dual-source attack evidence graphs |
| ZERO-APT | `screened-out-forward-citation` | forward citation of MuSAR concerns automated penetration testing, not evidence-graph reconstruction |

## 9. Functional boundary after v0.3

Already occupied:

- direct PCAP + syslog LLM analysis;
- traffic-only KG + LLM reporting;
- traffic-only ATT&CK annotation + LLM event description + attack chain;
- network alarms + application logs -> event association -> multi-host attack chain;
- heterogeneous logs -> provenance graph via parsers or LLM-generated rules;
- multi-source telemetry -> stage/lifecycle reconstruction;
- LLM attack summaries, evidence tracing, uncertainty and abstention components.

Residual cells after adversarial second search:

1. **R1 narrowed:** raw PCAP `TrafficObservation` and log `LogObservation` remain independent, immutable evidence records; a union event graph may reference but cannot overwrite either source history.
2. **R2 strongest residual:** multi-candidate traffic-log record links have learned probabilities that are calibrated on campaign-disjoint data and compared against deterministic 5-tuple/PID/time joins.
3. **R3 narrowed:** `candidate/verified/rejected/conflict` states and missing-source indicators propagate to chain confidence and abstention; generic missing-hop recovery is already occupied.
4. **R4 secondary:** high-level goal intent is inferred only from a reconstructed chain and evaluated separately from ATT&CK tactic, malicious-event intent and actor attribution.
5. **R5 trust contribution:** every semantic claim binds to graph node/edge IDs and raw packet/log anchors; unsupported claims are rejected, and replay/entailment is measured.

## 10. Gate result

- [x] Core C01-C61 statuses resolved without silent abstract-only entries.
- [x] C36 Minos appendix full-read note completed.
- [x] C42-C59/F06 legally accessible full texts or extended publisher views read; C55/C56/C60/C61 explicitly downgraded to access-limited boundary notes.
- [x] Residual-cell second search run through the 2026-07-13 cutoff; exact query and exclusion log is recorded separately.
- [x] MuSAR/Traffic2Chain forward-citation sweep checked; found citations do not occupy R1-R5. Backward families are represented in C01-C61/F01-F06 and historical evidence-graph notes.
- [x] Functional collision matrix v0.2 synthesized from all notes.
- [x] Candidate idea(s) and feasibility matrix prepared only after dataset/patent/adversarial checks were recorded; user selection remains pending.
