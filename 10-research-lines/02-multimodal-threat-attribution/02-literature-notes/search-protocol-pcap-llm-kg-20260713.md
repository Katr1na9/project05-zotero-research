# Search Protocol: PCAP + LLM + Knowledge Graph + Trace/Intent

Date opened: 2026-07-13
Coverage deadline: 2026-07-13
Workflow: `academic-research-suite / deep-research / literature investigation`

## 1. Collision question

Which functional parts of the following chain have already been published, and which combinations remain unverified?

```text
PCAP-derived traffic evidence + HFish/system/IDS log evidence
-> structured TrafficObservation and LogObservation
-> incident/evidence graph construction
-> CAPEC/ATT&CK/CTI graph alignment and retrieval
-> behavior trace / attack-stage / intent candidates
-> evidence-grounded LLM reasoning, verification, calibration, or abstention
```

## 2. Search dimensions

| Dimension | Terms |
|---|---|
| Raw evidence | PCAP, packet capture, network packet, network flow, encrypted traffic, HFish, honeypot, Suricata, Zeek, system log, audit log |
| Semantic bridge | observation, evidence pack, traffic description, log-to-intelligence, TTP alignment, ATT&CK mapping |
| Structured knowledge | knowledge graph, attack graph, provenance graph, CAPEC, MITRE ATT&CK, CTI, GraphRAG |
| LLM role | LLM, traffic-language model, agent, RAG, reranking, structured generation, tool use |
| Output task | investigation, forensics, reconstruction, attack path, provenance, attribution, stage, intent |
| Trust | grounding, auditable, verifiable, evidence anchor, uncertainty, calibration, abstention, hallucination |
| Environment | IPv4, IPv6, MPLS, SCION, cross-protocol, domain shift, heterogeneous network |

## 3. Query families

```text
"large language model" AND (PCAP OR "network traffic") AND (investigation OR forensics)
(PCAP OR flow) AND "attack path" AND (LLM OR "knowledge graph")
"encrypted traffic" AND (multimodal OR language) AND (evidence OR explanation)
(provenance OR telemetry) AND LLM AND (threat investigation OR ATT&CK)
(Suricata OR Zeek OR "security logs") AND ATT&CK AND (intent OR cognitive)
((PCAP OR "network traffic") AND (system log OR honeypot OR HFish)) AND (LLM OR "knowledge graph")
"multi-source security logs" AND ATT&CK AND (attack chain OR investigation)
"knowledge graph" AND "network traffic" AND LLM
(evidence-grounded OR auditable) AND LLM AND cyber investigation
(IPv4 OR IPv6 OR MPLS OR SCION) AND attack tracing AND multimodal
```

## 4. Sources and verification order

1. Primary publisher/conference pages, DOI records, arXiv, USENIX, IEEE, ACM, Elsevier, Springer.
2. Semantic discovery through Exa/OpenAlex/Semantic Scholar when primary indexes are insufficient.
3. Zotero local library for metadata, attachments, and indexed full text.
4. GitHub only for released artifacts and dataset/code verification, never as a substitute for a paper's claims.

## 5. Inclusion criteria

A work enters the collision corpus when it directly covers at least one functional link and is needed to distinguish the final idea from prior work:

- PCAP/network-flow evidence is transformed for LLM reasoning or graph analysis;
- low-level telemetry is aligned to CTI, ATT&CK, CAPEC, provenance, or attack paths;
- traffic and log observations are jointly aligned or used to construct an incident/evidence graph;
- an LLM generates, verifies, or explains attack investigation outputs;
- multimodal traffic representation targets interpretation rather than ordinary IDS classification alone;
- evidence grounding, auditability, uncertainty, or claim verification constrains security conclusions.

Priority is 2024-2026, but earlier foundational papers are included when a new paper directly builds on them.

## 6. Exclusion criteria

- ordinary IDS classification with no trace, investigation, semantic alignment, or evidence output;
- generic LLM-for-cybersecurity surveys after they have served query expansion;
- offensive agents and penetration testing unrelated to defensive investigation;
- papers where “multimodal” only means duplicate feature formats without a cross-view task;
- unverified secondary summaries when a primary source cannot be located;
- Project03 deployment technologies whose only relevance is CENI compatibility.

## 7. Meaning of “all scanned papers will be intensively read”

Search engines return substantial noise. To keep the promise operational and auditable:

- `discovered`: appeared in search results;
- `screened-out`: excluded at title/abstract level with a recorded reason;
- `included`: entered the functional collision corpus;
- `full-read`: available full text was read and a structured note was completed;
- `metadata-only`: full text remained unavailable after retrieval attempts; claims are limited to verified metadata/abstract and the item cannot support a final novelty conclusion.

Every `included` paper must reach `full-read` or be explicitly marked `metadata-only` before a final idea is submitted to the user. No included paper may remain at abstract-only status silently.

## 8. Required note fields

Each included paper receives:

1. verified metadata and source;
2. problem and threat model;
3. input evidence and true modality definition;
4. intermediate representation;
5. LLM/graph role;
6. output task and evidence linkage;
7. data, baselines, metrics, and main results;
8. limitations and unsupported claims;
9. exact collision with Project03-derived functions;
10. residual white space, if any;
11. reusable method, dataset, and evaluation ideas;
12. reading status and source provenance.

## 9. Gate rule

No final title or method is proposed until:

- the included corpus is frozen;
- every included work is full-read or transparently unavailable;
- the collision matrix maps functions rather than keywords;
- at least one residual cell has an executable dataset path and falsifiable evaluation;
- the residual cell survives a second current-date search using its final wording.
