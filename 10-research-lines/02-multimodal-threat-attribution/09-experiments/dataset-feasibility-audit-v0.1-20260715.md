# Dataset Feasibility Audit v0.1

Audit date: 2026-07-15
Research cutoff: 2026-07-13
Target task: independent traffic/log observation graphs, packet-log relation truth, attack-chain reconstruction and optional high-level intent.

## 1. Required dataset properties

A useful primary dataset must expose more than “network features + labels.” Minimum properties are:

1. synchronized network and host/system telemetry;
2. raw PCAP or packet-level records, not only derived flows;
3. host process/file/socket or audit lineage;
4. scenario/campaign ground truth and timestamps;
5. enough record identifiers to annotate traffic-log relations;
6. a license that permits academic processing and derived annotations.

No located dataset provides ready-made packet-log edge truth plus high-level intent truth. A limited manual/weak-supervision annotation layer is therefore unavoidable.

## 2. Candidate comparison

| Dataset | Traffic side | Log/provenance side | Chain/ground truth | License/access | Main risk | Rank |
|---|---|---|---|---|---|---|
| ProvICS | raw PCAP + decoded Modbus + physical state | host and PLC provenance | synchronized ICS scenarios with rich ground truth | Hugging Face; CC BY-NC 4.0 | recent dataset, domain is ICS and storage about 30.2 GB | 1 |
| AIT Log Dataset 2.0 | PCAP + Suricata/DNS/VPN | Apache/auth/audit/syslog and attack log | multi-source attack schedule/labels | about 130.6 GB; CC BY-NC-SA 4.0 | very large; relation truth must be derived | 2 |
| CICAPT-IIoT | PCAP/features | auditd/SPADE provenance with timestamp/PID/ATT&CK fields | APT/IIoT scenario labels | about 10 GB; license not yet confirmed | roughly 99.5% benign; license and exact synchronization need audit | 3 |
| ProvCon | per-host PCAP | Sysdig/Auditd/Sysmon + provenance | APT1/17/29/32/41 emulation scenarios | public access reported; license unclear | scenario packaging and legal reuse need verification | 4 |
| DARPA OpTC | Zeek/network flow summaries | endpoint eCAR/provenance | red-team campaign ground truth | established research access | no raw PCAP, so cannot prove packet-level R1/R2 | auxiliary only |

Primary links:

- ProvICS paper: https://arxiv.org/abs/2607.05989
- ProvICS dataset: https://huggingface.co/datasets/trucyberlab/multimodal-ICS-provenance
- AIT datasets portal: https://ait-aecid.github.io/ait-log-data/

For CICAPT-IIoT and ProvCon, do not download or redistribute until the official license page is recorded in the Material Passport.

## 3. Recommended experimental staging

### Stage A: relation-task proof of concept

Use a compact subset of ProvICS:

- select 2-3 campaigns with both PCAP and host/PLC provenance;
- keep original packet index/timestamp/hash and log record ID;
- construct candidate pairs by host/IP/port/time with deliberately broad windows;
- label `same-action`, `causal-support`, `context-only`, `conflict`, `unrelated` on a stratified sample;
- reserve entire campaigns for test, never random pair splitting.

### Stage B: external validity

Use AIT v2 for cross-environment evaluation:

- test parser portability and time synchronization;
- evaluate missing-source and clock-drift corruption;
- report transfer without fine-tuning and with small calibration-only adaptation.

### Stage C: provenance-heavy comparison

Use CICAPT-IIoT or ProvCon only after license confirmation. Compare against graph-internal relation completion and provenance baselines. OpTC remains useful for log-only/flow-only ablations but cannot validate raw packet-log relation claims.

## 4. Annotation unit

The core annotation is a **cross-source relation**, not a generic attack label.

```text
traffic_observation_id
log_observation_id
relation_type
evidence_state = candidate | verified | rejected | conflict
time_delta_ms
shared_keys = {host, ip, port, pid, socket, protocol}
annotator_confidence
adjudication_note
campaign_id
```

Positive and negative examples must include:

- true same-connection/process relations;
- same 5-tuple in a different process/time interval;
- NAT/shared-IP ambiguity;
- benign background traffic interleaved with attack logs;
- missing packet or missing log side;
- contradictory timestamps/identifiers;
- hard negatives from adjacent attack stages.

## 5. Dataset-derived evaluation

| Level | Required metrics |
|---|---|
| traffic/log subgraphs | node/edge precision, recall, provenance-anchor survival |
| cross-source relation | AUROC/AUPRC, macro-F1, Hits@k/MRR, Brier, ECE, reliability diagram |
| selective relation | risk-coverage, abstention accuracy, conflict recall |
| attack chain | edge precision/recall/F1, stage order consistency, campaign recall, graph edit distance |
| LLM interpretation | supported-claim precision, claim-to-record entailment, unsupported claim rate, evidence replay success |
| optional intent | expert agreement, macro-F1, calibration and abstention by goal-intent class |
| operation | alerts/campaign, graph size, latency, memory and analyst verification time |

## 6. Feasibility verdict

- **Feasible MSc core:** graph construction + R2 calibrated relation on ProvICS, with AIT v2 external test.
- **Feasible extension:** downstream chain reconstruction and evidence-grounded LLM summary.
- **High-risk extension:** independently annotated high-level goal intent; retain only if inter-annotator agreement and class support are adequate.
- **Not acceptable as primary proof:** OpTC alone, flow-only tables, random record splits or synthetic relation labels derived from the same deterministic rule used as baseline.

## 7. Immediate pre-experiment gate

- [ ] Confirm ProvICS file manifest, checksums and exact license.
- [ ] Download only a pilot campaign and estimate relation-labeling cost.
- [ ] Define positive relation semantics before viewing model outputs.
- [ ] Double-annotate at least 100 pilot pairs and compute Cohen's kappa/Krippendorff's alpha.
- [ ] Freeze campaign-disjoint train/calibration/test split.
- [ ] Obtain user approval of one candidate topic before implementation.
