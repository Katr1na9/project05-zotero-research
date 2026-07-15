# Functional Collision Matrix v0.2

Date: 2026-07-13
Source corpus: [collision-corpus-v0.3-20260713.md](collision-corpus-v0.3-20260713.md)

This matrix records what each work actually consumes, constructs and predicts. `Intent` is split from ATT&CK stage/tactic and from malicious-event assessment. A graph database, a communication KG and an event/provenance evidence graph are not treated as equivalent. v0.2 adds C42-C61 and converts the broad idea into five falsifiable residual cells.

## 1. Legend

- Input: `P` raw packet/PCAP; `F` flow/network alert; `L` host/application/system log; `PG` prebuilt provenance graph; `CTI` threat reports/knowledge.
- Graph: `none`; `comm-KG`; `event/prov`; `CTI-KG`; `vector/text`.
- Anchor: whether conclusions can return to raw source record IDs/packet artifacts.
- X-edge: whether cross-source links are explicit, multi-candidate, confidence-calibrated and conflict-preserving.
- Endpoint: `cls` classification; `stage`; `chain`; `event-intent` malicious purpose of one event; `goal-intent` attack objective/motive; `report`; `actor`.

## 2. Direct traffic / PCAP works

| ID | Work | Input | Representation / graph | LLM role | Endpoint | Anchor | X-edge | Collision verdict |
|---|---|---|---|---|---|---|---|---|
| C01 | CyberSleuth | P + tool logs | agent workspace, no unified evidence graph | tool planning and forensic synthesis | report, success/CVE | partial artifact citations | none | PCAP-agent investigation occupied; not dual-source graph construction |
| C02 | From Anomaly to Attack Path | F/payload | graph database | interpret anomalous traffic | attack path | unverified | none | traffic + LLM + graph path occupied at metadata level |
| C03 | Holmes | P | structured Evidence Pack | evidence-grounded DDoS investigation | report/verdict | strong PCAP anchors | none | auditable PCAP reasoning occupied; no host-log graph |
| C04 | Privacy-Preserving PCAP Analysis | P + CTI | vector/RAG corpus | local conversational analysis | report/reconstruction | unverified | none | local PCAP-RAG occupied; no graph/chain truth |
| C05 | KLAGE | P -> F | comm-KG | report generation after Graph-BERT/LIME | cls + report | no raw packet anchor reported | none | traffic graph + LLM report occupied |
| C06 | mmTraffic | P/bytes + traffic features | multimodal traffic-language representation | traffic interpretation | cls/report | byte grounding, not dual-source | none | traffic-language multimodality occupied |
| C07 | TrafficLLM | P/F | generic traffic representation | fine-tuned multi-task analysis | cls/QA | weak | none | generic traffic-LLM representation occupied |
| C08 | eX-NIDS | F + CTI | text/RAG | explain NIDS verdict | cls + report | flow-level | none | flow+CTI explanation occupied |
| C09 | Fine-grained traffic retrieval | HTTP F + CTI | hybrid index | rerank CVE candidates | CVE cls | request-level | none | traffic knowledge enrichment occupied; not chain/intent |
| C41 | Traffic2Chain | F | alert/phase chain | generate event descriptions | stage/TTP + chain | not reported in accessible metadata | none | traffic-only ATT&CK + LLM + chain directly occupied |

## 3. Dual-source, log and event/provenance works

| ID | Work | Input | Representation / graph | LLM role | Endpoint | Anchor | X-edge | Collision verdict |
|---|---|---|---|---|---|---|---|---|
| C10 | Llama-PcapLog | P + L | paired instruction text | joint QA/classification | cls/report | source segments only | implicit, no edge | direct PCAP+syslog LLM fusion occupied; graph absent |
| C11 | Multi-Source Cybersecurity Logs | network/system/browser L | event-level labeled dataset | SLM evaluation | ATT&CK label | event IDs/labels | paired data, no calibrated edge | dataset and event labels occupied |
| C12 | RAG Security Incident Analysis | multi-source L + ATT&CK | retrieval corpus | sequence reconstruction | stage/chain/report | retrieved log chunks | implicit | log-RAG chain occupied; no raw PCAP graph |
| C13 | OntoLogX | honeypot L | ontology session KG | ontology-guided extraction | ATT&CK/session report | log/session level | deterministic extraction | log-to-KG occupied; traffic line absent |
| C14 | HunterAgent | corrupted heterogeneous L | reconstructed trace state | generator-verifier | missing-hop chain | partial | models corruption, not calibrated source links | anti-forensic trace occupied; cross-source graph creation not solved |
| C15 | PROVSEEK | PG + CTI | provenance DB + RAG | agentic query/synthesis | report/trace | provenance queries | graph assumed | verifiable provenance investigation occupied |
| C16 | ANANKE | heterogeneous L + knowledge | investigation state | iterative retrieval/reasoning | chain/report | log evidence | implicit | knowledge-augmented log investigation occupied |
| C17 | Logs to ATT&CK Insights | network alert L | text/ATT&CK mapping | infer techniques and cognitive traits | stage + goal-intent candidate | log-level | none | motive candidate from one source occupied; no chain-grounded truth |
| C18 | OCR-APT | audit L -> PG | anomalous provenance subgraphs | validate and narrate stage subgraphs | stage/chain/report | provenance events | graph assumed | provenance story generation occupied |
| C19 | StageFinder | host/network provenance | fused temporal provenance | stage estimator | stage probability | event-level | no explicit calibrated cross-source edge | stage probability occupied; construction uncertainty absent |
| C20 | Multi-source log investigation | application + OS L | unified provenance graph | none in core method | seven-stage chain | log event lineage, details pending | deterministic log integration | multi-log graph + staged investigation occupied |
| C21 | FuseChain | multi-source telemetry | temporal heterogeneous provenance graph | reasoning/annotation support | stage/chain | telemetry-level | source-aware but not candidate/conflict calibrated | multi-source graph + stages occupied, transfer domain |
| C22 | SynthChain | multi-source telemetry | benchmark evidence/chain graph | forensic analysis | chain benchmark | strong ground truth | observability, not edge calibration | chain-level benchmark and source coverage occupied |
| C30 | UTLParser | heterogeneous L | directed multigraph of triples/subgraphs | none | query/investigation substrate | source fields partially retained | last-write merge, no conflict preservation | heterogeneous-log graph occupied; edge conflict remains |
| C31 | AISL | heterogeneous audit L | ontology graph | none | detection with intent priors | audit-level | deterministic | intent is expert input, not inferred output |
| C34 | Auto-Prov | heterogeneous L | LLM-generated provenance graph | extraction, enrichment, attack summary | cls/report/stage | no robust raw ID/hash schema | single accepted relation | automatic LLM log graph construction occupied |
| C37 | Two-stage multi-datasource | F + syslog + host stats | 1-second decision fusion | none | technique + lifecycle | source-window level | no event edges | true synchronous multisource gain occupied; graph absent |
| C38 | Sentient | audit L -> PG | provenance graph + latent behavior embedding | none | detection/latent event-intent | audit events | none | “intent” is latent representation, not semantic goal |
| C39 | MOLE | L | LLM-generated provenance templates | template generation | graph substrate | unknown | unknown | automatic parser/template generation occupied at metadata level |
| C40 | MuSAR | network alerts + application L | unified event graph/attack graph | tactic choice for ambiguous host behavior | stage + multi-host chain | alert IDs and command IDs | deterministic IP/time/stage/keyword match | closest direct collision; raw PCAP, calibrated/conflict edges and goal-intent remain |

## 4. Knowledge graph, trust and Agent appendix

| ID | Work | Input | Representation / graph | LLM role | Endpoint | Anchor / uncertainty | Collision verdict |
|---|---|---|---|---|---|---|---|
| C23 | AttacKG+ | CTI text | behavior/TTP/state CTI-KG | graph extraction | knowledge graph | report spans | text-to-attack-KG occupied, not runtime evidence |
| C24 | CLIProv | PG logs + CTI | contrastive shared space | representation/alignment | retrieval/alignment | sample-level | runtime-to-CTI alignment occupied |
| C25 | MM-AttacKG | CTI text + image | multimodal CTI-KG | multimodal extraction | knowledge graph | document/image spans | document multimodality occupied, not traffic/log evidence |
| C26 | TracLLM | long LLM context | contribution traces | trace output contributors | evidence attribution | context spans | LLM evidence tracing occupied; not graph-edge correctness |
| C27 | LLMs Unreliable for CTI | CTI prompts | evaluation benchmark | evaluated object | reliability/calibration | consistency metrics | generic LLM trust red line occupied |
| C28 | Uncertainty-aware stage | stage features | evidential classifier | none | stage + OOD | uncertainty score | uncertainty component occupied, not cross-source relation calibration |
| C29 | XAPT | anomaly scores | calibrated Bayesian/GNB stage model | none | stage + explanation | Platt probabilities/SHAP | calibrated stage prediction occupied |
| C32 | SHAPE | system behavior graph | heterogeneous autoencoder | embeddings | cls/localization | no chain/dual source | screened out as ordinary graph detection |
| C33 | Provenance evaluation survey | 76 papers | evaluation taxonomy | none | measurement guidance | campaign recall | establishes need for alert-unit and edge-level evaluation |
| C35 | SHIELD | PG | pruned attack subgraph | chain summary + heuristic confidence | chain/report | uncalibrated confidence | LLM chain summary occupied; confidence remains weak |
| C36 | Minos | prebuilt PG + POI + CTI | queried attack subgraph | multi-agent planning/query/event-intent | chain + event-intent | citation-ID verification; no calibrated edge | agentic backward tracking occupied; upstream graph construction remains |

## 5. Second-search rows

| ID | Work | Input | Representation / graph | LLM role | Endpoint | Anchor / X-edge | Collision verdict |
|---|---|---|---|---|---|---|---|
| C42 | SAURONEYES | audit L | attribute KG + interaction graph | none | malicious edge + overlapping chains | audit events; no independent cross-source edge | audit dual-view and chain communities occupied; not high-level intent |
| C43 | ForenGRAF-AI | proposed heterogeneous artifacts | signed temporal evidence graph | proposed explanation layer | forensic chain/report | conceptual source/evidence links | broad architecture occupied, but no implementation or experiment |
| C44 | APTGuard | raw P + auditd L + config | 0.01 s feature-window fusion | orders stage labels, checks continuity and ATT&CK mapping | stage + chain | raw inputs exist; no explicit event graph/X-edge truth | direct PCAP+logs+LLM chain broadly occupied |
| C45 | From Logs to Tactics | syslog + EDR L | PID/host/time log-entry graph + meta-alerts | summary and high-level sequence interpretation | tactic + campaign + report | log events; deterministic graph links | multi-log graph+LLM+ATT&CK occupied; no independent packet line |
| C46 | M-DUCAG | topology/vulnerability/alert state | probabilistic dynamic uncertain causal attack graph | none | posterior attack path | graph-path probabilities, not packet-log calibration | probabilistic path reasoning occupied |
| C47 | Network Forensics Evidence Graph | P + program/web L | event/evidence graph | none | attack route | can backtrack raw packets; deterministic event links | historical packet+log evidence graph occupied; strict dual lineage/calibration absent |
| C48 | Clouseau | structured L | multi-agent query/investigation state | chief/investigator/source agents | source + timeline + kill chain + objectives | retrieved events; no edge calibration | agent objective reporting occupied; intent correctness not isolated |
| C49 | BotFence | eBPF host L + SmartNIC DPI P | network-enhanced TTP provenance graph | none | inspect/block + TTP chain | 5-tuple/PID deterministic join; no calibration/conflict | strongest direct graph-construction collision; no learned X-edge |
| C50 | MPCA | audit L | confidence-weighted event triples | none | APT detection/investigation | event confidence; not relation calibration | broad confidence provenance occupied |
| C51 | Integrated Evidence Graphs | multi-source evidence | probabilistically merged evidence graph + MulVAL | none | integrated forensic graph | expert coefficients; observed/hypothesis not cleanly split | probabilistic merge and missing evidence occupied |
| C52 | APMP | audit PG | BERT-completed provenance graph | none | relation + attack entity detection | graph-internal softmax, uncalibrated | learned relation completion occupied; packet-log link remains |
| C53 | Power APT Graph | provenance event records | PROV-DM graph + GAT edge reconstruction | none | graph-level detection | random negative edge task; no raw dual-source link | edge reconstruction wording occupied; X-edge task absent |
| C54 | Evidence Security Events | Snort/network/web/DB L | global evidence/attack graph | none | path + hypotheses | source class/expert reasoning; no calibration | missing evidence and alternative hypotheses occupied historically |
| C55 | T-Trace | system/network-related L | event communities -> provenance graph | none | APT graph/chain | source fields; no verified raw PCAP lineage | multi-log correlation graph occupied; full details access-limited |
| C56 | M-IDAS | network/system/host/device features | fused vectors + attention dependency graph | pretrained transformer-like model | IDS + trace path | attention path, no raw record anchor/X-edge | multimodal detection/traceability occupied; withdrawn, not evidence graph |
| C57 | ProHunter | audit L/PG + CTI | sampled threat graph + CTI query graph | none | graph match/hunt | audit lineage; CTI graph manually corrected | CTI-to-provenance matching occupied |
| C58 | SherAgent | production process/file/network L | iterative query/backtracking tree | query, relaxation, pruning and audit | entrypoint + investigation result | potential-correlation edges, uncalibrated | missing-log agent backtracking occupied |
| C59 | ProvAgent | audit L/PG | identity-behavior embeddings + agent state | four-agent IOC/kill-chain narration | anomaly + report | audit events; hypothesized missing steps | provenance+multi-agent pipeline occupied; operational precision weak |
| C60 | Citar | initial alert + audit PG + CTI/Sigma | alert alignment + tagged graph traversal | none | attack reconstruction + actor candidate | audit path; CTI hypothesis not calibrated | CTI-guided provenance reconstruction occupied |
| C61 | ANTEATER | raw audit L | filtered provenance graph | three-agent graph exploration/report | attack subgraph + report | metadata-only; X-edge not reported | filter-then-agent investigation occupied at abstract boundary |

## 6. Shared foundations

| ID | Work | Functional ownership | Boundary for this line |
|---|---|---|---|
| F01 | AttacKG | CTI report -> ATT&CK technique KG | knowledge graph, not runtime evidence graph |
| F02 | EXTRACTOR | threat report -> system behavior graph | text-derived behavior, not observed packet/log event |
| F03 | KAIROS | whole-system provenance detection/investigation | audit side only; assumes provenance collection |
| F04 | TechniqueRAG | CTI text -> ATT&CK annotation via retrieval | semantic enrichment module, not graph/chain contribution |
| F05 | CTIBench | LLM evaluation on CTI tasks | benchmark design foundation, not runtime investigation |
| F06 | Event Log Correlation Review | 120-study event-correlation taxonomy | confirms heterogeneous correlation, causal validity and benchmark gaps |

## 7. Functional occupancy summary

| Functional cell | Occupied by | Status |
|---|---|---|
| PCAP + syslog in one LLM context | C10 | occupied |
| traffic-only KG + LLM report | C05 | occupied |
| traffic-only ATT&CK + LLM event description + attack chain | C41 | occupied |
| packet/network evidence + program/web logs -> evidence graph and route | C47/C54 | occupied historically |
| network alarms + application logs -> events -> multi-host chain | C40/C55 | occupied |
| raw PCAP + auditd/config -> feature fusion + LLM chain | C44 | occupied |
| eBPF host provenance + DPI packet result -> network-enhanced TTP graph | C49 | occupied |
| application + OS logs -> provenance graph -> staged investigation | C20 | occupied |
| heterogeneous logs -> automatic LLM provenance graph | C34/C39 | occupied |
| multi-source telemetry -> stage/chain graph | C19/C21/C22 | occupied |
| probabilistic evidence/attack graph and missing-evidence hypotheses | C46/C51/C54 | occupied |
| learned graph-internal relation completion | C52/C53 | occupied |
| CTI query graph/Sigma -> audit provenance reconstruction | C57/C60 | occupied |
| LLM/Agent over prebuilt provenance graph/log DB | C15/C18/C35/C36/C48/C58/C59/C61 | occupied |
| ATT&CK/CTI enrichment and retrieval | C09/C12/C13/C23/F04 | occupied |
| event/stage uncertainty or evidence tracing | C26-C29/C33 | partially occupied |
| independently evaluated high-level goal intent | none found | residual, but annotation-heavy and secondary |

## 8. Residual functional cells after second search

These are evidence-supported residuals, still awaiting user approval as thesis ideas.

| Residual cell | Nearest works | What is still absent in the corpus |
|---|---|---|
| R1 Source-preserving dual graph | C44, C47, C49, C55 | broad dual-source graph is occupied; strict residual is independent raw packet/log observations, immutable anchors and source-specific subgraph quality |
| R2 Calibrated cross-source relation | C49-C53 | no located work defines packet-log record pairing as multi-candidate link prediction and reports both discrimination and probability calibration on campaign-disjoint data |
| R3 Conflict/missing-source propagation | C14, C51, C54, C58 | missing-hop recovery exists; source disagreement states propagated into downstream risk/abstention remain absent |
| R4 Chain-grounded semantic intent | C17, C38, C48, C59 | objectives/latent intent are mentioned, but no located work isolates high-level goal-intent truth and measures it against reconstructed-chain evidence |
| R5 Joint evidence replay | C03, C15, C26, C47 | packet backtracking and graph citations exist separately; no located benchmark jointly measures packet+log claim-to-record entailment/replay with chain correctness |

## 9. Completed second-search wording

Use combinations of the following exact concepts instead of broad “LLM + cybersecurity” queries:

1. `raw PCAP system logs cross-source event evidence graph attack chain`
2. `packet log provenance graph cross-source link confidence calibration`
3. `network traffic host logs evidence graph missing modality conflict attack reconstruction`
4. `attack intent inference reconstructed attack chain packet logs`
5. `source-aware provenance graph evidence lineage packet index log record`
6. `LLM evidence-grounded attack chain claim citation raw security telemetry`

## 10. Gate result

- [x] Every C01-C61 included or screened item is mapped.
- [x] Foundations F01-F06 are mapped.
- [x] Broad novelty claims are converted into occupied functional cells.
- [x] R1-R5 second-search queries completed through the 2026-07-13 freeze date.
- [x] Forward citation sweep for C40 MuSAR and C41 Traffic2Chain completed; found citations are IDS/penetration-testing work and do not occupy R1-R5.
- [x] Backward families cross-checked against historical packet/log evidence graphs, probabilistic evidence merging, provenance completion and event-correlation review.
- [x] Remaining R1-R5 are worded as measurable residuals rather than “first system” claims.
