# Collision Corpus v0.1

Freeze date: 2026-07-13
Scope: traffic/log observations, event/evidence graph construction, LLM investigation, trace/stage/intent, and evidence trust.

This corpus freezes papers whose full methods can change the final idea. Search noise is recorded separately and does not count as an included paper. Every item below must reach `full-read`, `reused-full-read`, or an explicit `metadata-only` status before idea submission.

## A. Direct PCAP / traffic investigation collisions

| ID | Paper | Year | Functional collision | Status |
|---|---|---:|---|---|
| C01 | [CyberSleuth: Autonomous Blue-Team LLM Agent for Web Attack Forensics](https://arxiv.org/abs/2508.20643) | 2025 | PCAP/log tool use, forensic report, CVE and attack-success inference | queued-full-read |
| C02 | [From Anomaly to Attack Path: LLM-Based Network Traffic Investigation for APT Detection](https://doi.org/10.1145/3803525.3804991) | 2026 | suspicious flows/payload -> graph database -> attack path | full-text-retrieval-pending |
| C03 | [Holmes: An Evidence-Grounded LLM Agent for Auditable DDoS Investigation](https://arxiv.org/abs/2601.14601) | 2026 | PCAP Evidence Pack, auditable anchors, structured agent protocol | queued-full-read |
| C04 | [A Privacy-Preserving Framework for Cyber Incident Analysis from Network Packets Using Large Language Models](https://doi.org/10.1109/CAI68641.2026.11536475) | 2026 | local LLM + PCAP summary/artifacts + RAG for incident reconstruction | full-text-retrieval-pending |
| C05 | [Enhancing network security using knowledge graphs and large language models for explainable threat detection (KLAGE)](https://doi.org/10.1016/j.future.2025.108160) | 2026 | PCAP/flows -> KG -> Graph-BERT/LIME -> LLM report | queued-full-read; OA |
| C06 | [Multimodal Reasoning with LLM for Encrypted Traffic Interpretation](https://arxiv.org/abs/2604.08140) | 2026 | byte-grounded traffic description, multimodal traffic-language reasoning, evidence reports | queued-full-read |
| C07 | [TrafficLLM: Enhancing Large Language Models for Network Traffic Analysis with Generic Traffic Representation](https://arxiv.org/abs/2504.04222) | 2025 | raw packet/flow tokenizer and generic traffic-language representation | queued-full-read |
| C08 | [eX-NIDS: A framework for explainable network intrusion detection leveraging Large Language Models](https://doi.org/10.1016/j.compeleceng.2025.110826) | 2026 | malicious flow + CTI context -> LLM explanation | queued-full-read; OA |
| C09 | [Fine-grained network traffic classification with hybrid retrieval and LLM re-ranking](https://doi.org/10.1016/j.comnet.2026.112433) | 2026 | HTTP attack traffic -> CTI retrieval -> LLM CVE attribution | extended-HTML-read-pending |

## B. Traffic + log dual-source and event/evidence graph collisions

| ID | Paper | Year | Functional collision | Status |
|---|---|---:|---|---|
| C10 | [Fine-tuning Llama3 for Integrated Analysis of Network Packet and System Log Data (Llama-PcapLog)](https://doi.org/10.34385/proc.97.T3.3.4) | 2025 | joint PCAP + syslog LLM analysis | queued-full-read; PDF available |
| C11 | [Multi-Source Cybersecurity Logs: An ATT&CK-Labeled Dataset and SLM Evaluation](https://arxiv.org/abs/2606.18190) | 2026 | paired system/network/browser logs with event-level ATT&CK labels | queued-full-read |
| C12 | [Retrieval-Augmented LLMs for Security Incident Analysis](https://arxiv.org/abs/2603.18196) | 2026 | multi-source logs + ATT&CK query library + attack-sequence reconstruction | queued-full-read |
| C13 | [OntoLogX: Ontology-Guided Knowledge Graph Extraction from Cybersecurity Logs with Large Language Models](https://arxiv.org/abs/2510.01409) | 2025 | honeypot logs -> ontology-grounded session KG -> ATT&CK tactics | queued-full-read |
| C14 | [HunterAgent: Neuro-Symbolic Attack Trace Reconstruction under Anti-Forensics](https://arxiv.org/abs/2605.29269) | 2026 | heterogeneous corrupted logs, generator-verifier, grounded missing-hop reconstruction | queued-full-read |
| C15 | [LLM-driven Provenance Forensics for Threat Investigation and Detection (PROVSEEK)](https://arxiv.org/abs/2508.21323) | 2025 | provenance DB + threat reports + RAG/agents -> verifiable forensic summaries | queued-full-read |
| C16 | [An Automated Attack Investigation Approach Leveraging Threat-Knowledge-Augmented Large Language Models](https://arxiv.org/abs/2509.01271) | 2025 | heterogeneous logs + kill-chain knowledge + iterative retrieval/reasoning | queued-full-read |
| C17 | [Security Logs to ATT&CK Insights: Leveraging LLMs for High-Level Threat Understanding and Cognitive Trait Inference](https://arxiv.org/abs/2510.20930) | 2025 | Suricata logs -> ATT&CK phase/technique -> cognitive motive candidates | queued-full-read |
| C18 | [OCR-APT: Reconstructing APT Stories from Audit Logs using Subgraph Anomaly Detection and LLMs](https://arxiv.org/abs/2510.15188) | 2025 | provenance subgraphs + stage-wise LLM validation -> attack story | queued-full-read |
| C19 | [Learning the APT Kill Chain: Temporal Reasoning over Provenance Data for Attack Stage Estimation](https://arxiv.org/abs/2603.07560) | 2026 | fused host/network provenance -> temporal stage probabilities | queued-full-read |
| C20 | [A multi-source log semantic analysis-based attack investigation approach](https://doi.org/10.1016/j.cose.2024.104303) | 2025 | application + OS logs -> unified provenance graph -> staged graph matching | extended-HTML-read-pending; closed PDF |
| C21 | [FuseChain: Runtime Evidence Reconstruction for Software Supply-Chain Attacks](https://arxiv.org/abs/2606.15811) | 2026 | multi-source telemetry -> temporal heterogeneous provenance graph -> stage reconstruction | queued-full-read; transfer baseline |
| C22 | [SynthChain: A Synthetic Benchmark and Forensic Analysis of Advanced and Stealthy Software Supply Chain Attacks](https://arxiv.org/abs/2603.16694) | 2026 | chain-level ground truth and cross-source observability/coverage | queued-full-read; dataset baseline |

## C. Knowledge alignment, graph construction, and trust red lines

| ID | Paper | Year | Functional collision | Status |
|---|---|---:|---|---|
| C23 | [AttacKG+: Boosting Attack Knowledge Graph Construction with Large Language Models](https://arxiv.org/abs/2405.04753) | 2024 | LLM text -> multilayer behavior/TTP/state graph | reused-full-read |
| C24 | [CLIProv: A Contrastive Log-to-Intelligence Multimodal Approach](https://arxiv.org/abs/2507.09133) | 2025 | provenance log/CTI alignment and semantic search | reused-full-read |
| C25 | [MM-AttacKG: A Multimodal Approach to Attack Graph Construction with Large Language Models](https://arxiv.org/abs/2506.16968) | 2025 | text/image CTI -> multimodal attack graph | reused-full-read |
| C26 | [TracLLM: Context Traceback for Long-Context Large Language Models](https://www.usenix.org/conference/usenixsecurity25/presentation/wang-yanting) | 2025 | identify context evidence contributing to forensic LLM output | queued-full-read |
| C27 | [Large Language Models are Unreliable for Cyber Threat Intelligence](https://arxiv.org/abs/2503.23175) | 2025 | consistency and calibration red line | reused-full-read |
| C28 | [Preliminary Investigation into Uncertainty-Aware Attack Stage Classification](https://arxiv.org/abs/2508.00368) | 2025 | evidential uncertainty and OOD for stage inference | queued-full-read |
| C29 | [XAPT: Explainable Anomaly-Driven Prediction of Threat Stages in APT Campaigns](https://doi.org/10.1109/ACCESS.2025.3636501) | 2025 | calibrated anomaly scores, Bayesian stage inference, explanation | queued-full-read |

## D. Shared foundations already read

| ID | Paper | Reuse in this line | Status |
|---|---|---|---|
| F01 | AttacKG | behavior/TTP graph schema and text-to-technique mapping baseline | reused-full-read |
| F02 | EXTRACTOR | system-behavior extraction and graph schema baseline | reused-full-read |
| F03 | KAIROS | whole-system provenance and investigation boundary | reused-full-read |
| F04 | TechniqueRAG | CTI-to-ATT&CK retrieval/annotation baseline | reused-full-read |
| F05 | CTIBench | LLM/CTI evaluation task design | reused-full-read |

## E. Screened out from full-reading corpus

| Work/family | Reason |
|---|---|
| EPIC, ID-INT, P4Prime, SecTracer, path-signature patents | relevant to the superseded CENI/path-consistency line, not the corrected dual-source evidence-graph line |
| NEXUS-IDS, ContextualGraph-LLM, MET-LLM | primarily ordinary detection/classification or explanation; no attack trace, dual-source event graph, or intent output |
| protocol-agnostic packet IDS | classification baseline only; represented by stronger TrafficLLM/mmTraffic items |
| TracePcap, PCAP Hunter, PCAPGraph | useful engineering artifacts but not peer-reviewed papers; track separately for implementation comparison |
| generic LLM-agent cybersecurity surveys | used only for query expansion; no unique functional collision |

## F. Freeze rule

New papers discovered after v0.1 enter only if they cover a cell absent from C01-C29 or are newer direct replications. Adding papers requires recording the reason; the queue must not grow merely because a search result shares keywords.
