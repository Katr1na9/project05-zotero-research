# P05-L2 Reading Queue

Updated: 2026-07-15
Canonical corpus: [collision-corpus-v0.3-20260713.md](collision-corpus-v0.3-20260713.md)
Canonical matrix: [functional-collision-matrix-v0.2-20260713.md](functional-collision-matrix-v0.2-20260713.md)

## Core reading status

- [x] direct PCAP/traffic collision set resolved;
- [x] traffic + log dual-source/event-graph set resolved;
- [x] graph construction, trust, uncertainty and relation-completion set resolved;
- [x] historical packet/log evidence-graph and missing-evidence works resolved;
- [x] CTI-to-provenance reconstruction works resolved;
- [x] agent-last appendix resolved after the graph/LLM core;
- [x] all inaccessible texts visibly marked as extended/metadata-only boundaries.

## Second-search additions

Full-read notes completed:

- SAURONEYES, ForenGRAF-AI, APTGuard, M-DUCAG, Clouseau, BotFence;
- Integrated Evidence Graphs, APMP, Power System APT Graph, Evidence Security Events;
- ProHunter, SherAgent, ProvAgent;
- Event Log Correlation systematic review.

Access-limited boundary notes completed:

- T-Trace: `extended-indexed-read`;
- M-IDAS: `extended-openreview-read`, withdrawn;
- Citar: `extended-publisher-read`;
- ANTEATER: `metadata-abstract-only`.

## Synthesis result

The broad idea `traffic + logs -> graph -> LLM/Agent chain` is occupied. Remaining candidate cells are:

1. strict source-preserving independent traffic/log subgraphs;
2. calibrated multi-candidate packet-log relation learning;
3. source-conflict/missingness propagation and selective abstention;
4. chain-grounded goal intent as a secondary endpoint;
5. joint packet+log claim-to-record replay.

## Completion gate

- [x] C01-C61/F01-F06 status resolved;
- [x] no silent abstract-only entries;
- [x] every included work mapped to a functional cell;
- [x] second residual search and citation sweep completed;
- [x] dataset and patent redlines completed;
- [x] 3 candidate topics and feasibility matrix prepared;
- [ ] user selects the thesis direction;
- [ ] targeted reading resumes only after selection, driven by the chosen method/dataset rather than a broad queue.
