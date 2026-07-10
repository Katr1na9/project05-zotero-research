# DARPA OpTC: C09 Source Preparation

Third true holdout source family (enterprise Windows eCAR telemetry).
Protocol: `08-writing/c09-optc-true-holdout-protocol-v0.1-20260710.md`

## Locked candidate (R06)

- **Day 1** “Plain PowerShell Empire” — `2019-09-23`
- Primary host: **Sysclient0201** (`142.20.56.202`)
- Local window: **11:23–15:30** (engagement local; recorded as America/New_York pending eCAR epoch check)
- UTC extract hint: `2019-09-23T15:23:00Z` → `2019-09-23T19:30:00Z`
- C2: `news.com` / `132.197.158.98:80`
- Chain: stager `runme.bat` → UAC bypass → Mimikatz → screenshot → discovery → WMI to Sysclient0402

Day 2 / Day 3 are **not** R06.

## What you already have

| File | Role |
|---|---|
| `docs/OpTCRedTeamGroundTruth.pdf` | GT locked ✓ |
| `docs/optc-errata.md` | AV-bypass password note (`OPTC2019`) |
| `raw/errata_av_bypass/AIA-351-375.*` | **Wrong batch for R06** (hosts 0351–0375 only) |

## Next download (required)

From the OpTC Google Drive (`ecar/evaluation/23Sep19-red/`):

1. **Must**: folder **`AIA-201-225`** (should contain Sysclient0201)  
   - Prefer `.json.gz`; if AV blocks it, take the `.zip.passwdOPTC2019` / `.cryptOPTC2019` twin (password **`OPTC2019`**)
2. **Recommended**: **`AIA-401-425`** (Sysclient0402 lateral pivot)
3. Optional later: DC1 batch only if we need DC claims after 0201/0402 compile

Put under:
`09-experiments/real_data/darpa_optc/raw/ecar/evaluation/23Sep19-red/`

Do **not** download full benign or all AIA folders.

## Hard rules

- Do not tune M3a for C09.
- Do not invent claims for report-only observables missing from eCAR.
- Keep `intended ≠ OR(recoverable)` on every non-noise action.
