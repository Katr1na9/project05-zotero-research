# DARPA TC E5 THEIA: C07 Source Preparation

This directory records the source boundary and bounded trace extraction for the
C07 true holdout. The evaluated C07 case is compiled separately under
`../../real_cases/C07-darpa-e5-theia-0515/`.

## Locked candidate

- Case: `R04`, THEIA Firefox Drakon APT BinFmt-Elevate Inject.
- Local time: `2019-05-15 14:48-15:07 EDT`.
- UTC extraction window: `2019-05-15 18:48:00Z` to `2019-05-15 19:07:00Z`.
- Target: `ta1-theia-target-1` (`128.55.12.110`, Ubuntu 12.04).
- Ground truth: TA5.1 final report, section 8.6, PDF pages 79-81.

The window was chosen from the report before inspecting event-level records. The
E5 operational event log reports that THEIA publishing restarted around 14:30 EDT
on the same day; the subsequent catch-up behavior remains an explicit data-quality
check during extraction.

## Local-only raw data

`raw/pidsmaker/theia_e5.dump` is a 6,187,437,078-byte PostgreSQL custom archive
(`PGDMP`). Its SHA-256 is recorded in `manifest.json`. Raw and extracted telemetry
are ignored by Git for every real-data family.

No PostgreSQL client tool is installed on this workstation. Instead, the project
uses a temporary `pgdumplib==4.0.0` dependency to inspect the custom archive and
stream only the required COPY payloads without materializing the full graph. The
reproducible extraction commands are:

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
