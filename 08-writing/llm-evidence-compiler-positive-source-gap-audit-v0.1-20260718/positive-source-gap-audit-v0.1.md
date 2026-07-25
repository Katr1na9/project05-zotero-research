# Project05 LLM evidence compiler positive-source gap audit v0.1

Date: 2026-07-18  
Status: `metadata_review_complete_remap_implementation_not_yet_authorized`  
Scope: positive G0 source families only; no corpus/model/runtime acquisition or execution

## Executive decision

The current non-token data gate fails because train has only two G0-positive families and training-validation has one. The smallest scientifically defensible repair is:

```text
train:
  Atomic + SOCBED
  + CAM-LDS fresh exact execution remap
  + one new BETH family

training-validation:
  Zeek
  + Loghub fresh exact killed-process remap
```

This route requires only one new corpus family. CAM-LDS and Loghub are already approved and local; their old candidates are not relabeled. New positive candidates would be produced from explicit bound-record strings under new parser IDs. No legacy null row receives negative credit.

LANL Unified Host and Network is the strongest reserve if BETH later fails its artifact-level gate. LID-DS and ProvSec remain conditional reserves. CERT remains unneeded, and ADFA-LD is rejected for the intended reusable adapter route because its official page prohibits commercial use.

## Evidence protocol

- Six Parallel Web searches were frozen before screening: three academic-focused and three official/general.
- Ten one-source extracts captured the primary paper, repository, institutional, or dataset page.
- Decisions use license/terms, explicit record fields, source-family independence, access footprint, and label-shortcut risk.
- Search/extract JSON is preserved beside this report; no candidate corpus was downloaded.
- “No suitable source” claims are not made. Decisions are bounded to the frozen protocol in `search-protocol.md`.

## Why the existing data can repair two family gaps

### CAM-LDS: new positive mapping, not old-label migration

The official Linux Audit field dictionary defines `argc` and `a[...]` as EXECVE arguments, `comm` as the program name, `exe` as the executable name, `pid/ppid` as process identifiers, and `proctitle` as the process title plus command-line parameters ([linux-audit field dictionary](https://github.com/linux-audit/audit-documentation/blob/main/specs/fields/field-dictionary.csv)). These are sufficient for a frozen parser to emit:

```text
process(a0 or decoded proctitle[0])
  --executed-->
command(joined explicit arguments)
```

The local exclusion-passed sample contains:

- 59 parseable `type=EXECVE` records with explicit `a0`;
- 107 parseable hex `type=PROCTITLE` records;
- 0 overlapping audit-event IDs between these two sets;
- 166 conservative unique execution events.

The current 800 `system/host --recorded--> event` proposals remain rejected because `host` is not bound to an explicit source field. The remap creates a new parser/version and does not modify those rejected rows.

### Loghub: explicit killed-process edges

Loghub Linux contains 25,567 lines over 263.9 days and is described as a Linux system-log corpus; the repository states that datasets are freely available for research or academic work with repository reference and citation ([Loghub repository](https://github.com/logpai/loghub), [Linux README](https://github.com/logpai/loghub/blob/master/Linux/README.md), [Zhu et al., 2023](https://arxiv.org/abs/2008.06448)).

In the existing 500-record validation sample, 193 messages exactly match:

```text
kernel: Out of Memory: Killed process <PID> (<process_name>).
```

A frozen parser can bind PID, process name, predicate and full source pointer without reading the old `null_eligible_candidate` value. The proposed edge is a record-scoped event such as `system/kernel --terminated--> process(name,pid)`; it is not an assertion that the host is benign or that other events are absent.

The 193 candidates exceed the 150 validation-positive lower bound needed for a balanced 300-pair design, while Zeek provides the second validation family. This remains a projected count until a tested parser and read-only remap audit reproduce it.

## New-family candidates

### BETH — recommended primary new train family

The BETH paper reports 8,004,918 events across 23 honeypots and describes 14-field kernel process records plus DNS logs. Process fields include `timestamp`, `processId`, `parentProcessId`, `userId`, `processName`, `hostName`, `eventId`, `eventName`, `argsNum`, and `args`; DNS fields include timestamp, source/destination IP, query and answer ([Highnam et al., 2021](https://ceur-ws.org/Vol-3095/paper1.pdf)). The current Kaggle page reports dataset version 3, 928.19 MB, and CC0 ([BETH dataset page](https://www.kaggle.com/datasets/katehighnam/beth-dataset)).

This is suitable for exact candidate-edge supervision because process creation/clone/kill and DNS records expose the values required by the edge. The hand-authored `sus` and `evil` flags, original anomaly split, filenames and attack narrative must be stripped from both input supervision metadata and target. They may not select records, predicates or labels.

There is a license-metadata discrepancy: the 2021 paper says CC BY 4.0, while the current Kaggle version reports CC0. Therefore BETH is only `candidate_for_source_gate`: a future metadata-only gate must pin the exact Kaggle version/API metadata and license bytes before any download request.

### LANL Unified Host and Network — reserve

LANL’s official page describes approximately 90 days of deidentified enterprise host and network events. Network CSV fields include time, duration, source/destination devices, protocol, ports, packets and bytes; host JSON includes process and parent-process fields. Cross-file identities are consistent, and the page declares CC0 plus public-release approval LA-UR-17-20763 ([LANL Unified Host and Network](https://csr.lanl.gov/data/2017/), [Turcotte et al., 2017](https://arxiv.org/abs/1708.07518)).

It is scientifically strong but operationally heavier: daily files are served through a data-fence form requesting email and intended use. It remains a reserve until file-level bytes and a bounded one-day acquisition plan are known.

### LID-DS and ProvSec — conditional reserves

LID-DS 2021 is a published system-call HIDS dataset ([Grimmer et al., 2023](https://doi.org/10.1007/978-3-031-35190-7_6)); its repository is GPL-3.0-or-later and points to a separate Proton-hosted dataset ([LID-DS repository](https://github.com/LID-DS/LID-DS)). The artifact’s own license, immutable hash, size and exact raw schema were not frozen, so it is not promoted.

ProvSec reports full system calls and parameters, 11 benign/adversarial scenario pairs, 341.7K benign and 987.7K adversarial events ([Shrestha et al., 2023](https://doi.org/10.1007/s44227-023-00014-9)). The article is CC BY 4.0, but the supplementary dataset’s independent license was not established by the extracted page. Its recorder also supplements missing fields from metadata/history, which requires a separate truth-contract audit. It remains conditional.

## Rejections and holds

- CERT Insider Threat is a legitimate synthetic dataset with DOI and multiple releases, but the official page excerpt did not establish dataset-license terms; scenario/answer-key leakage would need strong exclusion ([SEI dataset page](https://www.sei.cmu.edu/library/insider-threat-test-dataset/)). It is held, not needed.
- ADFA-LD’s official page grants perpetual academic research use but explicitly prohibits commercial use ([UNSW ADFA IDS](https://research.unsw.edu.au/projects/adfa-ids-datasets)). It is rejected for the reusable adapter/product path.
- ProvSec article licensing is not treated as dataset licensing.
- GPL framework licensing is not silently treated as a license for separately hosted data.
- No source is approved merely because it has attack/benign labels.

## Revised feasibility projection

| split | family | current G0 | projected exact remap/new-source status |
|---|---|---:|---|
| train | SOCBED | 683 | retained |
| train | Atomic | 798 | retained |
| train | CAM-LDS | 0 | projected 166 exact execution candidates |
| train | BETH | absent | candidate; expected to exceed the needed bounded sample after source gate |
| training-validation | Zeek | 483 | retained |
| training-validation | Loghub | 0 | projected 193 exact killed-process candidates |

With CAM/Loghub remaps, existing data would satisfy validation 2-family diversity and raise train to 3 families. BETH would supply the fourth train family. Formal feasibility is still `false` until:

1. CAM/Loghub parsers pass dependency-free tests and a read-only remap audit;
2. BETH passes metadata-only source review;
3. the user separately authorizes bounded BETH acquisition;
4. payload exclusion and final non-token/token gates pass.

## Next authorized-safe work

The next step can remain model-free and download-free:

1. create v0.2 field-map/parser contracts for CAM EXECVE/PROCTITLE and Loghub killed-process messages;
2. write red-green tests for quoting, hex decode, malformed messages, pointer preservation and zero legacy-null credit;
3. run a read-only remap audit and freeze actual counts;
4. prepare a BETH metadata-only source decision row, without downloading it.

Tokenizer, Qwen weights, environment changes, pair construction, training, formal inference and M3 runtime integration remain prohibited.

## Sources

### Academic / peer-reviewed

- [Highnam et al., 2021 — BETH Dataset](https://ceur-ws.org/Vol-3095/paper1.pdf)
- [Grimmer et al., 2023 — Dataset Report: LID-DS 2021](https://doi.org/10.1007/978-3-031-35190-7_6)
- [Shrestha et al., 2023 — ProvSec](https://doi.org/10.1007/s44227-023-00014-9)
- [Turcotte et al., 2017 — Unified Host and Network Data Set](https://arxiv.org/abs/1708.07518)
- [Zhu et al., 2023 — Loghub](https://arxiv.org/abs/2008.06448)

### Official / primary dataset sources

- [BETH Kaggle dataset](https://www.kaggle.com/datasets/katehighnam/beth-dataset)
- [LANL Unified Host and Network](https://csr.lanl.gov/data/2017/)
- [LID-DS repository](https://github.com/LID-DS/LID-DS)
- [Linux Audit field dictionary](https://github.com/linux-audit/audit-documentation/blob/main/specs/fields/field-dictionary.csv)
- [Loghub repository](https://github.com/logpai/loghub)
- [SEI CERT Insider Threat dataset](https://www.sei.cmu.edu/library/insider-threat-test-dataset/)
- [UNSW ADFA IDS datasets](https://research.unsw.edu.au/projects/adfa-ids-datasets)

Search and extraction outputs are stored in:

`08-writing/llm-evidence-compiler-positive-source-gap-audit-v0.1-20260718/`
