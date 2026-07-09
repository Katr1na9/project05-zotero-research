# DARPA TC E3 Pilot Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create an auditable Phase 0 manifest for the R01 FiveDirections and R02 CADETS development traces.

**Architecture:** Store source metadata and ground-truth slices as small JSON artifacts. Validate cross-references, UTC windows, hashes, development-only status, and ignored raw-data paths before any large archive is downloaded.

**Tech Stack:** Python 3 standard library, `unittest`, JSON.

## Global Constraints

- Do not download the two large event archives in Phase 0.
- Do not commit raw archives or extracted event streams.
- Treat R01 and R02 as development cases.

### Task 1: Manifest Contract

- [ ] Write failing tests for required source IDs, unique case IDs, UTC windows, and development-only status.
- [ ] Confirm RED.
- [ ] Add `manifest.json`, `R01.json`, and `R02.json`.
- [ ] Confirm GREEN.

### Task 2: Validator and Raw-data Guard

- [ ] Write failing tests for missing source references, invalid windows, and raw paths not covered by `.gitignore`.
- [ ] Confirm RED.
- [ ] Implement `validate_real_manifest.py` and add raw-data ignore rules.
- [ ] Confirm GREEN.

### Task 3: Documentation and Verification

- [ ] Document the exact selected topics and the no-download Phase 0 boundary.
- [ ] Run unit tests, JSON parsing, manifest validation, and `git diff --check`.
