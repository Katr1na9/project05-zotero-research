# DARPA OpTC: C09 Source Preparation

Third true holdout source family (enterprise Windows eCAR telemetry).
Protocol: `08-writing/c09-optc-true-holdout-protocol-v0.1-20260710.md`  
Compiled case: `../../real_cases/C09-darpa-optc-sysclient0201-0923/`  
Freeze-eval: `../../results/c09_holdout_m3a/`

## Locked candidate (R06)

- **Day 1** “Plain PowerShell Empire” — `2019-09-23`
- Primary host: **SysClient0201** (`142.20.56.202`)
- Local window: **11:23–15:30** (America/New_York / `-04:00`)
- UTC extract: `2019-09-23T15:23:00Z` → `2019-09-23T19:30:00Z`
- C2: `news.com` / `132.197.158.98:80`
- Trace-backed chain: Empire C2 → windir UAC → Get-Screenshot → WMI to SysClient0402
- Report-only gaps: Mimikatz cleartext, `news.com` hostname, failed LSASS inject, remote-host local chains

## Official Drive path used

`OpTCNCR/ecar/evaluation/23Sep19-red/AIA-201-225/`

| File | Role |
|---|---|
| `AIA-201-225.ecar-last.json.gz` (~2.22 GB, SHA `FAF181CB…`) | **R06 source** — covers afternoon attack window |
| `AIA-201-225.ecar-2019-12-08T11-05-10.046.json.gz` (~110 MB) | Morning shard only; R06 window selects 0 rows |

Extracted window: `extracted/R06_sysclient0201_window.jsonl` — **753,973** SysClient0201 rows.

## Retained non-R06 artifacts

| File | Role |
|---|---|
| `docs/OpTCRedTeamGroundTruth.pdf` | GT locked ✓ |
| `docs/optc-errata.md` | AV-bypass password note (`OPTC2019`) |
| `raw/errata_av_bypass/AIA-351-375.*` | Wrong host batch (0351–0375) |
| `raw/ecar/evaluation/_wrong_day_24Sep19/AIA-201-225/*.zip` | Right hosts, wrong day (2019-09-24) |

## Hard rules

- Do not tune M3a for C09.
- Do not invent claims for report-only observables missing from eCAR.
- Keep `intended ≠ OR(recoverable)` on every non-noise action.
- Do not retarget R06 to Day2 just because a 24Sep AIA-201-225 file is on disk.

## Pipeline (reproducible)

```powershell
python 09-experiments/scripts/stream_ecar_event_window.py `
  --input 09-experiments/real_data/darpa_optc/raw/ecar/evaluation/23Sep19-red/AIA-201-225/AIA-201-225.ecar-last.json.gz `
  --hostname-contains SysClient0201 `
  --start-utc 2019-09-23T15:23:00Z `
  --end-utc 2019-09-23T19:30:00Z `
  --output 09-experiments/real_data/darpa_optc/extracted/R06_sysclient0201_window.jsonl `
  --summary 09-experiments/real_data/darpa_optc/derived/R06_extraction_summary.json

python 09-experiments/scripts/compile_ecar_motifs.py `
  --spec 09-experiments/real_cases/C09-darpa-optc-sysclient0201-0923/motif_spec.json `
  --events 09-experiments/real_data/darpa_optc/extracted/R06_sysclient0201_window.jsonl `
  --output 09-experiments/real_cases/C09-darpa-optc-sysclient0201-0923/evidence_claims.json `
  --report 09-experiments/real_cases/C09-darpa-optc-sysclient0201-0923/motif_report.json

python 09-experiments/scripts/run_mvp.py `
  --case-dir 09-experiments/real_cases/C09-darpa-optc-sysclient0201-0923 `
  --output-dir 09-experiments/results/c09_holdout_m3a
```
