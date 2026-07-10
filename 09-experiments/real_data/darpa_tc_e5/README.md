# DARPA TC E5: C07 / C08 Source Preparation

This directory records the source boundary and bounded trace extraction for the
E5 true holdouts. Evaluated cases are compiled separately under
`../../real_cases/C07-darpa-e5-theia-0515/` and
`../../real_cases/C08-darpa-e5-clearscope-0515/`.

## Locked candidates

### R04 / C07 — THEIA

- Case: `R04`, THEIA Firefox Drakon APT BinFmt-Elevate Inject.
- Local time: `2019-05-15 14:48-15:07 EDT`.
- UTC extraction window: `2019-05-15 18:48:00Z` to `2019-05-15 19:07:00Z`.
- Target: `ta1-theia-target-1` (`128.55.12.110`, Ubuntu 12.04).
- Ground truth: TA5.1 final report, section 8.6, PDF pages 79-81.

The window was chosen from the report before inspecting event-level records. The
E5 operational event log reports that THEIA publishing restarted around 14:30 EDT
on the same day; the subsequent catch-up behavior remains an explicit data-quality
check during extraction.

### R05 / C08 — ClearScope

- Case: `R05`, ClearScope Appstarter APK Micro APT Elevate.
- Local time: `2019-05-15 15:38-16:19 EDT`.
- UTC extraction window: `2019-05-15 19:38:00Z` to `2019-05-15 20:19:00Z`.
- Target: `ta1-clearscope-translate-test` (`128.55.12.114`, Android 8).
- Ground truth: TA5.1 final report, section 8.7, PDF pages 81-85.
- Cross-check: PIDSMaker `CLEARSCOPE_E5` / `appstarter_0515`.

Earlier ClearScope attempts on 05/13 and 05/15 14:14 failed and are not used.

## Local-only raw data

`raw/pidsmaker/theia_e5.dump` (6,187,437,078 bytes) and
`raw/pidsmaker/clearscope_e5.dump` (6,630,620,258 bytes) are PostgreSQL custom
archives (`PGDMP`). SHA-256 values are recorded in `manifest.json`. Raw and
extracted telemetry are ignored by Git for every real-data family.

No PostgreSQL client tool is installed on this workstation. Instead, the project
uses a temporary `pgdumplib==4.0.0` dependency to inspect the custom archive and
stream only the required COPY payloads without materializing the full graph.

### R04 extraction

```powershell
uv run --no-project --with pgdumplib==4.0.0 python `
  ../../scripts/stream_pgdump_event_window.py `
  --archive raw/pidsmaker/theia_e5.dump `
  --start-utc 2019-05-15T18:48:00Z `
  --end-utc 2019-05-15T19:07:00Z `
  --output extracted/R04_event_table.tsv `
  --summary derived/R04_extraction_summary.json `
  --catalog-json derived/R04_postgres_catalog.json

uv run --no-project --with pgdumplib==4.0.0 python `
  ../../scripts/resolve_pgdump_nodes.py `
  --archive raw/pidsmaker/theia_e5.dump `
  --events extracted/R04_event_table.tsv `
  --output extracted/R04_nodes.jsonl `
  --summary derived/R04_node_resolution_summary.json
```

The extraction scanned all 140,994,662 event rows because `timestamp_rec` is not
globally monotonic. It yielded 256,297 rows in the locked window and resolved all
7,043 referenced node hashes. Do not tune M3a based on this extraction.

### R05 extraction

```powershell
uv run --no-project --with pgdumplib==4.0.0 python `
  ../../scripts/stream_pgdump_event_window.py `
  --archive raw/pidsmaker/clearscope_e5.dump `
  --start-utc 2019-05-15T19:38:00Z `
  --end-utc 2019-05-15T20:19:00Z `
  --output extracted/R05_event_table.tsv `
  --summary derived/R05_extraction_summary.json `
  --catalog-json derived/R05_postgres_catalog.json

uv run --no-project --with pgdumplib==4.0.0 python `
  ../../scripts/resolve_pgdump_nodes.py `
  --archive raw/pidsmaker/clearscope_e5.dump `
  --events extracted/R05_event_table.tsv `
  --output extracted/R05_nodes.jsonl `
  --summary derived/R05_node_resolution_summary.json
```

The extraction scanned all 198,794,211 event rows because `timestamp_rec` is not
globally monotonic. It yielded 694,872 rows in the locked window and resolved all
4,968 referenced node hashes. Do not tune M3a based on this extraction.
