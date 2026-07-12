# OTRF APT29 Day 1: R08 / C11 Source Preparation

Protocol: `../../../08-writing/c11-otrf-apt29-day1-intake-protocol-v0.1-20260712.md`
Screening record: `../../../08-writing/third-data-family-screening-v0.1-20260712.md`
Status: D1-D5 complete; C11 AND primary result and OR sensitivity frozen.

## Locked source

- Repository: `OTRF/Security-Datasets`
- Commit: `d9d40ef123d2c87d5d3df28c96bcab4f0faccc87`
- Scenario: APT29 Day 1 emulation
- Primary host: `SCRANTON`
- Lateral target: `NASHUA`
- Host package: `apt29_evals_day1_manual.zip`
- Network package for first pass: `combined_zeek.log`
- License recorded by the repository: MIT

## Frozen interpretation

C11 is a third telemetry/data-packaging family relative to DARPA TC and OpTC. It is an adversary-emulation trace, not an operational incident and not an unknown-actor attribution benchmark.

The main compilation uses AND node semantics. At least three critical nodes must have two event-backed claims from different sensor families. If that gate fails, the failure is retained; OR sensitivity cannot replace the AND primary result.

## Acquisition result

- Host ZIP: 13,944,973 bytes; SHA-256 `98A07314...D0FDBE5`; Git blob hash matches the fixed commit.
- Host JSONL: 196,081 valid rows, 0 malformed; SCRANTON 131,119, NASHUA 29,056.
- Zeek JSONL: 2,140 valid rows, 0 malformed.
- ZIP path/CRC checks pass; inventory is in `derived/R08_archive_inventory.json`.
- Host events cover `2020-05-02T02:55:26Z-03:28:20Z`; Zeek covers `2020-04-30T00:06:38Z-00:45:00Z`. They do not overlap.

Because the two packages represent different replay windows, Zeek must not be merged with host events as event-level corroboration. The frozen protocol already permits a second Windows provider as the second evidence family, so D3 will first use Sysmon, Security, PowerShell and WMI within the host archive. Zeek remains a separate scenario-level diagnostic source.

## Compilation and evaluation result

- D3 PASS: 4 of 5 preregistered critical nodes have at least two claims from different Windows provider families; the threshold was 3.
- The frozen `3aka3.doc` anchor matched no record. N01 remains a natural gap and was not replaced.
- N02-N05 compile to 8 event-backed claims from PowerShell, Sysmon and Security.
- The missing critical node downgrades the compiled target and support ceiling from G3 to `G2_tactic_intent`.
- D4 PASS: every action has `intended_cti_node_ids != OR(recoverable_claim_ids)`, and the planner view hides the recovery set.
- D5 PASS: the frozen AND run and one-field OR sensitivity are complete.
- AND M2: success 1.0000, mean cost 3.6667; Oracle mean cost 3.0000. M2 is not the lowest-cost non-Oracle method on C11.
- OR M2: success 1.0000, mean cost 1.0222. The `-2.6445` cost difference shows why AND remains the main analysis.

Result brief: `../../../08-writing/c11-otrf-apt29-day1-results-v0.1-20260712.md`
Primary result: `../../results/c11_holdout_v0.1/`
OR sensitivity: `../../results/c11_or_sensitivity_v0.1/`

## Local-only files

```text
docs/apt29.xlsx
raw/apt29_evals_day1_manual.zip
raw/combined_zeek.log
raw/pcaps/                 # optional, only after the documented PCAP gate
extracted/
```

`raw/`, `extracted/`, ZIP, XLSX and other large/binary artifacts are excluded by the repository `.gitignore`. Commit only checksums, inventories, extraction summaries, event locators and compact compiled cases.

## Hard rules

- Do not inspect host or Zeek events before the R08 and C11 protocol files are frozen.
- Do not tune any existing planner on C11.
- Do not count mask/seed repeats as new attacks.
- Do not report APT29 emulation labels as actor attribution accuracy.
- Do not split fields from one record into artificial corroborating claims.
- Do not download PCAP merely to rescue a failed prelocked motif; first record the Zeek insufficiency and apply the protocol gate.
