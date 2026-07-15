# P05-L2 Zotero Sync Summary

Date: 2026-07-15
Target collection: `Threat_Attribution_LLM_Agents_with_PDF.no_existing_duplicates`
Collection key: `NN9VN4TG`

## Result

- 20 new parent items were imported into the target collection.
- 12 items contain stored Zotero PDF attachments; every local file exists and has a valid PDF header.
- 8 items are metadata-only because no lawful, verified full text was available during this pass.
- All 20 new titles occur exactly once in the local library; no duplicate parent item was created.
- The machine-readable record is [`zotero-sync-report-20260715.json`](zotero-sync-report-20260715.json).

## Metadata-only Records

- C44 APTGuard
- C47 Network Forensics Method Based on Evidence Graph and Vulnerability Reasoning
- C50 MPCA
- C55 T-Trace
- C56 M-IDAS, retained with its withdrawn/access-limited boundary
- C60 Citar
- C61 ANTEATER
- F06 Event Log Correlation for Multi-Step Attack Detection

## Existing-item Exception

SherAgent already existed globally as Zotero item `HDUGH6TI` with PDF attachment `X4IQGNUM`, so it was not imported again. It currently belongs to another collection, not the P05-L2 target collection. The local API is read-only and the connector import route cannot attach an existing item to another collection without creating a duplicate. If one-folder membership is required, manually drag the existing SherAgent item into the target collection; do not re-import it.

## Verification Basis

Verification used the Zotero Desktop local API after import, not the importer's console output:

- 20/20 new parent keys were returned by the target collection.
- 12/12 expected parent items returned a PDF child.
- 12/12 attachment `file/view/url` paths existed locally and began with `%PDF-`.
- 20/20 new titles had a global exact-title count of one.
