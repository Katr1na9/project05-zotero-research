# P05-L2 Material Passport

Updated: 2026-07-15

## Identity

- Line ID: P05-L2
- Working name: Traffic-Log Evidence Graph + LLM Threat Tracing
- Created: 2026-07-12
- Active workflow: academic-research-suite / deep-research
- Current stage: Stage 3 synthesis/collision complete; user topic selection pending
- Literature freeze: 2026-07-13

## Verified Project Inputs

- Project03 reusable core: PCAP parsing, ThreatObservation generation, graph query and trace localization.
- Project03 non-reusable engineering scope: CENI controller/network-element deployment and compatibility compromises.
- Log-side design exists but extraction/build code is incomplete in the audited snapshot.
- IPv4/IPv6/MPLS/GeoNetworking/SCION are protocol/environment conditions, not independent evidence modalities.
- Static CAPEC/ATT&CK/CTI knowledge graph, task subgraph and runtime event evidence graph are separate graph types.

## Verified Literature State

- Canonical corpus: [collision-corpus-v0.3-20260713.md](../02-literature-notes/collision-corpus-v0.3-20260713.md)
- Functional matrix: [functional-collision-matrix-v0.2-20260713.md](../02-literature-notes/functional-collision-matrix-v0.2-20260713.md)
- Second search: [second-collision-search-20260713.md](../02-literature-notes/second-collision-search-20260713.md)
- Scope: C01-C61/F01-F06.
- Legal full texts available for new core papers were read and converted to 15-section shared notes.
- T-Trace, M-IDAS, Citar and ANTEATER remain visibly access-limited; they support only boundary-level claims.
- MuSAR/Traffic2Chain citation sweep did not locate a direct R2 equivalent by the freeze date.

## Verified Novelty Boundary

Occupied:

- broad packet/network + log graph construction;
- network-enhanced provenance graph;
- probabilistic evidence/attack graph and missing evidence;
- graph-internal relation completion/confidence;
- CTI-to-provenance matching;
- LLM/multi-agent chain investigation and reports.

Strongest residual:

- campaign-disjoint calibrated multi-candidate packet-log observation linking;
- source-preserving raw anchors and independent subgraph fidelity;
- explicit conflict/missing-source propagation;
- joint packet+log claim-to-record replay.

High-level goal intent is secondary and cannot be conflated with ATT&CK tactic, event maliciousness or actor attribution.

## Candidate State

- Candidate A: complete source-preserving graph + evidence-constrained LLM main line.
- Candidate B: calibrated cross-source relation and uncertainty core.
- Candidate C: trustworthy LLM chain/intent extension.
- Recommendation: A narrative + B mandatory core + C optional.
- Decision: pending user review; no RQ is frozen.

## Data Feasibility

- Primary candidate: ProvICS (raw PCAP + host/PLC provenance + physical state; CC BY-NC 4.0 reported).
- External candidate: AIT Log Dataset 2.0 (PCAP + heterogeneous logs; CC BY-NC-SA 4.0 reported).
- Conditional: CICAPT-IIoT/ProvCon after license verification.
- Auxiliary only: OpTC, because it provides flow summaries rather than raw PCAP.
- Dataset audit: [dataset-feasibility-audit-v0.1-20260715.md](../09-experiments/dataset-feasibility-audit-v0.1-20260715.md)

## Not Yet Verified

- user-selected Primary RQ and final thesis title;
- ProvICS/AIT v2 local manifests, checksums and exact downloadable subsets;
- relation ontology, pilot labels and inter-annotator agreement;
- campaign-level sample size/power and compute budget;
- cross-domain transfer beyond ICS;
- high-level intent class validity and annotator agreement;
- final model, prompt, baseline implementation and venue;
- patent legal status/families through CNIPA review.

## Human-Read State

AI-assisted full-text reading and synthesis are complete for the recorded corpus. This does **not** mean the user has personally read every note. User review is required for candidate selection, relation semantics and all manuscript claims.

## Reproducibility Boundary

- Full-text cache is local/ignored and must not be committed.
- No raw PCAP, malware, private logs or licensed PDF may enter Git.
- Every future dataset snapshot requires source URL, version, license, checksum, extraction command and parser version.
- Candidate edges and LLM hypotheses must never overwrite observed evidence.

## Current Gate

G2 passed; G3 conditional pass; G1 awaits user topic selection. No dataset acquisition, model implementation or paper drafting is authorized before that decision.
