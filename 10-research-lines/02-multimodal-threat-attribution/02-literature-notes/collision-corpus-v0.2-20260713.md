# Collision Corpus v0.2

Freeze date: 2026-07-13
Scope: traffic/log observations, event/evidence graph construction, LLM investigation, trace/stage/intent, and evidence trust.

This version incorporates the user-confirmed graph-construction contribution and the independent traffic/log dual-line scope. It also records source-access level so that a metadata-only collision cannot silently become a full-method claim.

## 1. Status vocabulary

| Status | Meaning |
|---|---|
| `full-read` | complete paper text read and a 15-section note exists |
| `reused-full-read` | complete note already existed in the shared workspace and was re-audited for this line |
| `extended-publisher-read` | publisher HTML/preview exposed method and results beyond the abstract; PDF unavailable |
| `metadata+artifact-read` | verified metadata plus official code/data artifacts were inspected; PDF unavailable |
| `metadata-only` | title/authors/venue/DOI/abstract verified; no claim beyond accessible metadata |
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

## 5. Agent-last appendix

| ID | Paper | Reason retained | Status |
|---|---|---|---|
| C36 | Minos | latest agentic backward-tracking over provenance evidence; needed only after core method boundary | `full-read` |

## 6. Shared foundations

| ID | Paper | Reuse | Status |
|---|---|---|---|
| F01 | AttacKG | behavior/TTP graph schema | `reused-full-read` |
| F02 | EXTRACTOR | system-behavior extraction schema | `reused-full-read` |
| F03 | KAIROS | whole-system provenance and investigation boundary | `reused-full-read` |
| F04 | TechniqueRAG | CTI-to-ATT&CK retrieval/annotation | `reused-full-read` |
| F05 | CTIBench | LLM/CTI evaluation task design | `reused-full-read` |

## 7. Screened-out latest hits

| Work/family | Decision | Reason |
|---|---|---|
| SHAPE | `screened-out` | system-behavior graph detection/localization; no dual-source chain/intent; represented by KAIROS/Sentient |
| EdgeTrace, ORTHRUS, MGDA, Slot | `screened-out` | audit-only provenance detection/chain family; represented by KAIROS/Sentient/SHIELD |
| APT-LLM, Semantic-Aware AE | `screened-out` | ordinary provenance anomaly detection; no distinct dual-source graph/intent cell |
| MultiKG, MCKG | `screened-out` | knowledge-level CTI/code/log fusion, not event-evidence fusion; represented by C23-C25 |
| ReGAIN | `screened-out` | traffic RAG with citation/abstention, but only flood classification; trust cell represented by Holmes/TracLLM/C27 |
| Revelation | `screened-out-for-core` | PCAP agentic QA; agent scope deferred and traffic-only interpretation represented by CyberSleuth/Holmes |
| MalRAG | `screened-out` | open-set malicious-flow classification; no chain, log-side evidence, or intent |
| TracePcap, PCAP Hunter, PCAPGraph | `screened-out-paper-corpus` | engineering artifacts, not peer-reviewed papers; retain only for implementation comparison |

## 8. Functional boundary after v0.2

Already occupied:

- direct PCAP + syslog LLM analysis;
- traffic-only KG + LLM reporting;
- traffic-only ATT&CK annotation + LLM event description + attack chain;
- network alarms + application logs -> event association -> multi-host attack chain;
- heterogeneous logs -> provenance graph via parsers or LLM-generated rules;
- multi-source telemetry -> stage/lifecycle reconstruction;
- LLM attack summaries, evidence tracing, uncertainty and abstention components.

Residual cells that remain candidates for later synthesis, not yet approved ideas:

1. raw PCAP-level `TrafficObservation` and log-side `LogObservation` as independent evidence records in one provenance-preserving event graph;
2. calibrated multi-candidate cross-source edges with deterministic packet/log query verification and explicit conflict states;
3. chain/intent outputs whose every claim can be traced to raw evidence IDs, with abstention under missing or contradictory sources;
4. evaluation that separates graph fidelity, cross-source link accuracy, campaign recall, intent correctness, calibration and evidence replay success.

## 9. Remaining gate

- [x] Core C01-C35 and C37-C41 statuses resolved without silent abstract-only entries.
- [x] C36 Minos appendix full-read note completed.
- [x] Functional collision matrix synthesized from all notes.
- [ ] Second search and backward/forward citation sweep run using residual-cell wording through 2026-07-13.
- [ ] Candidate idea(s) submitted to the user only after the checks above.
