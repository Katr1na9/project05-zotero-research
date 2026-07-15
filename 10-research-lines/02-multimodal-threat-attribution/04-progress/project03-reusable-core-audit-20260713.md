# Project03 Reusable Research Core Audit

Date: 2026-07-13
Status: replaces the research-boundary conclusion in `project03-handoff-audit-20260712.md`; the earlier file is retained as history.

## 1. User-confirmed boundary

Project03 was an engineering delivery for behavior tracing and attack-intent perception on CENI. Controller integration, per-node deployment, tunnel/proxy management, filename-driven modality handling, and local graph fallbacks were largely deployment compromises. They are not the paper line.

The reusable research core is:

```text
flow line: upstream encrypted-traffic result + PCAP -> TrafficObservation
log line: HFish interaction records -> LogObservation / behavior graph
-> construct or augment a unified event-level evidence graph
-> align the event graph with CAPEC/ATT&CK/CTI knowledge
-> locate behavior/attack-pattern candidates
-> produce trace, stage, and intent candidates with evidence
```

The new branch studies how LLMs, dual-source graph construction, and genuinely complementary traffic/log evidence can improve this chain. It does not study how to redeploy Project03 on CENI.

## 2. What the code actually implements

### 2.1 PCAP and upstream-result adapter

`bridge_results_to_api.py` is the clearest reusable asset. It:

- matches a PCAP to a row from `results_variant.csv`;
- extracts packet count, byte count, duration, packet rate, and destination count;
- accepts upstream attack class, confidence, technique, and modality;
- serializes these fields into the `/api/detect` payload.

Research value: this is an initial observation-construction interface between physical traffic evidence and downstream semantic reasoning.

Research limitation: `True_Attack`, `Predicted_Class`, and `Technique` can enter the same payload that is later evaluated. Without a strict feature/label audit, this creates target leakage and self-confirming reasoning.

### 2.2 ThreatObservation is a design concept, not yet a uniform schema

The design material describes:

```text
PCAP features + attack type/confidence + modality label -> ThreatObservation
```

The runtime snapshot is inconsistent:

- malicious samples are stored as a `threat` node and an `attack_stage` node linked by `maps_to`;
- an explicit `threat_observation` node is created only for benign/unknown predictions in `threat_chain.py`;
- no stable observation schema preserves packet/flow evidence anchors, source spans, uncertainty, and transformation lineage for every sample.

Therefore, a unified evidence-grounded ThreatObservation remains an unfinished engineering/research object. It must not be described as a completed Project03 contribution.

### 2.3 Knowledge-graph retrieval and candidate tracing

The reusable graph logic includes:

- keyword retrieval over CAPEC `attack_pattern` names/descriptions;
- optional traversal to technique and tactic nodes when the full graph is available;
- `CanPrecede` traversal for predecessor/successor attack-pattern candidates;
- rule-based ranking and negative-keyword filtering;
- generation of candidate chains and intent candidates.

Research value: the code exposes the exact semantic gap to study: how low-level traffic evidence should retrieve and constrain high-level attack-pattern/TTP knowledge.

Research limitation: the current result is semantic candidate generation, not causal reconstruction of the attack's actual path. A `CanPrecede` edge means that one pattern may precede another in the knowledge base; it does not prove that both occurred in this incident.

### 2.4 The CENI-local graph is much smaller than the design implies

The local intent index contains 130 CAPEC attack patterns. Of these, 127 have descriptions, but none has a populated technique or tactic list. The exported trial subgraph contains 130 nodes and 24 `CanPrecede` relationships; its nodes are attack patterns rather than a complete ATT&CK/CAPEC/CTI graph.

Consequences:

- the local deployment demonstrated CAPEC semantic retrieval and lightweight predecessor/successor reasoning;
- it did not demonstrate full ATT&CK tactic/technique reasoning;
- the full background graph predated the user's Project03 work and must not be claimed as an original construction contribution;
- a new paper may still contribute a newly designed dual-source event/evidence graph constructed from traffic and HFish observations, plus explicit links from those observations to the background CAPEC/ATT&CK/CTI graph;
- that new event-graph construction must be distinguished from exporting a task-scoped subgraph from an existing Neo4j database.

### 2.5 HFish log line: designed but not implemented in this snapshot

Project03 contains a concrete HFish route:

```text
HFish SQLite/logs
-> normalized interaction events
-> HFish behavior graph
-> stage/tactic candidates
-> correlation with traffic-side threat/chain/intent
```

The design identifies `scanners`, `scans`, and `ip_profile` as currently usable tables, with future credential, command, URL, and file events. It proposes attacker, target, service, port, session, credential, URL, command, and file nodes.

However, the repository contains no `hfish_log_bridge.py` or equivalent extractor. The log line is therefore reusable design and data-access knowledge, not a completed implementation. It can become a first-class part of the new research line if paired events and ground truth can be recovered or regenerated.

### 2.6 Existing graph-construction assets

Project03 has three different graph operations that must not be conflated:

1. `export_intent_subgraph.py` extracts a task-scoped CAPEC/ATT&CK subgraph from an existing Neo4j graph;
2. `build_local_intent_index.py` converts that export into a retrieval index;
3. `threat_context.py` constructs a presentation graph from threat, candidate chain, and intent outputs.

None currently constructs a persistent, evidence-anchored event graph jointly from PCAP and HFish logs. That missing operation is eligible for the new paper, subject to collision review.

## 3. Reuse matrix

| Project03 asset | Reuse level | New-line role | Required repair |
|---|---|---|---|
| PCAP parsing and flow statistics | direct | physical evidence extraction baseline | preserve packet/flow anchors and parser version |
| Upstream classifier output adapter | conditional | one evidence view, never ground truth by default | separate inputs, labels, and derived claims |
| ThreatObservation concept | redesign | central intermediate representation candidate | make it uniform, typed, evidence-linked, and uncertainty-aware |
| CAPEC/ATT&CK query interface | direct with replacement backend | graph retrieval baseline | version the graph and return evidence paths |
| `CanPrecede` candidate traversal | baseline only | weak structural prior | distinguish possibility from incident evidence |
| Stage/intent heuristics | baseline only | comparison method | remove attack-type self-confirmation and calibrate |
| HFish log-side schema and graph design | redesign and implement | independent log evidence line | recover data, build extractor, define time/entity alignment |
| Task-scoped graph export/index | direct baseline | background-knowledge retrieval | separate static knowledge from incident evidence |
| Dual-source event/evidence graph | new construction | possible central contribution | define ontology, provenance, alignment, conflicts, and ground truth |
| CENI controller/node deployment | no | out of scope | retain only as provenance of data collection |
| IPv4/IPv6/MPLS/Geo/SCION mode handling | conditional | environment/domain-shift variable | do not call five re-encodings five independent modalities |

## 4. Multimodal definition for this line

The term `multimodal` is reserved for evidence views with non-redundant information and a documented alignment relation. Candidate evidence views are:

1. packet bytes or packet sequences;
2. protocol/header and session metadata;
3. aggregate flow statistics;
4. upstream encrypted-traffic model outputs and model explanations;
5. graph-retrieved CAPEC/ATT&CK/CTI evidence;
6. HFish or other independent interaction/system/IDS logs when paired ground truth exists.

IPv4, IPv6, MPLS, GeoNetworking, and SCION are initially treated as network environments or protocol transformations. They become separate evidence modalities only if the experiment proves that each exposes independently useful observations after controlling for duplicated source traffic.

## 5. Corrected research object

The current object of study, before novelty verification, is:

> A dual-source, evidence-grounded observation graph that converts PCAP-derived traffic views, upstream detector outputs, and HFish/log events into auditable incident observations, links them to CAPEC/ATT&CK/CTI knowledge, and constrains LLM-generated trace, stage, and intent candidates to claims supported by source evidence.

This is a problem statement, not a final idea. The following possible contributions must be tested separately rather than bundled:

- observation representation and evidence anchoring;
- traffic/log entity-time alignment and event-graph construction;
- cross-view alignment under missing/conflicting evidence;
- graph retrieval and candidate reranking;
- grounded reasoning, abstention, and claim-level verification;
- cross-protocol/domain generalization.

## 6. Immediate collision risks

The broad formulation already collides with 2025-2026 work on:

- LLM agents that inspect PCAP and application logs;
- PCAP-to-attack-path reconstruction;
- packet/flow knowledge graphs plus LLM explanations;
- evidence-pack abstractions for auditable network investigation;
- multimodal traffic-language models with byte-grounded reports;
- low-level IDS logs to ATT&CK and cognitive/intent inference.

Therefore the next gate is not method design. It is a full-text collision review that identifies which functional cell, if any, remains uncovered.

## 7. Audit conclusion

Project03 contributes a credible starting pipeline and a concrete failure surface, but not yet a publishable novelty claim. The branch will proceed with this boundary:

```text
retain: PCAP observation construction + graph alignment/query + candidate trace/intent
extend: HFish/log observation extraction + dual-source event/evidence graph construction
repair: evidence schema, leakage, alignment, grounding, uncertainty, and evaluation
exclude: CENI deployment architecture and controller/node compatibility work
verify: whether any remaining functional combination is novel after 2026-07-13
```
