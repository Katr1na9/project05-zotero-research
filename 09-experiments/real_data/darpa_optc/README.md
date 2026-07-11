# DARPA OpTC: C09 Source Preparation

Third true holdout source family (enterprise Windows eCAR telemetry).
Protocol: `08-writing/c09-optc-true-holdout-protocol-v0.1-20260710.md`  
Compiled case: `../../real_cases/C09-darpa-optc-sysclient0201-0923/`  
Freeze-eval: `../../results/c09_holdout_m3a/`

C10 protocol: `../../../08-writing/c10-optc-day3-protocol-v0.1-20260711.md`
C10 status: Ground Truth locked; one 25Sept host shard pending.

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

The 24Sep archive was audited on 2026-07-11: Sysclient0203 coverage ends at
`09:55 EDT`, before the Ground Truth WMI reinfection at `15:42 EDT`; it cannot
serve as C10.

## Locked C10 intake (R07)

- **Day 3** “Malicious Upgrade” — `2019-09-25`
- Primary host: **Sysclient0351**
- Locked local window: **11:20–11:35 EDT**
- Locked UTC window: `15:20Z–15:35Z`
- Official path: `ecar/evaluation/25Sept/AIA-351-375/AIA-351-375.ecar-last.json.gz`
- Drive file ID: `1-yxi3k1Duc5Uuu_gbu1vjtdEU3FoDSIA`
- Status: **not downloaded**

C10 is a parameter-locked cross-day OpTC robustness case. It is not a fourth
independent source family, and it must not be used to retune XGBoost or M3a.

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
