# Citation and search audit

Audit date: 2026-07-18 (Asia/Shanghai)

## Source accounting

- Crossref discovery batch: 13 exact-title queries × top 3 candidates = 39 returned candidate records.
- Core unique-source matrix after manual screening and deduplication: 24.
- Full-text level: 16 (13 extractable local PDFs, 1 visually checked scanned PDF, RFC official full text, Altman author PDF read in memory).
- Official public scope pages: 3 (ISO/IEC 27037, ISO/IEC 27043, ISO/IEC/IEEE 15939).
- Pending primary full text: 5 (Howard 1966; Greiner et al. 2002; Ji & Carin 2007; Elbaum et al. 2001; Kitchenham et al. 1995).
- Invalid local full text: 1 zero-byte Elbaum download; excluded from the full-text count.

The 39 Crossref records are a discovery count, not 39 included studies. OpenAlex and Semantic Scholar checks were used only as supplementary metadata/full-text-location attempts and are not added again to the unique-source count.

## DOI audit

- Unique DOI links in the evidence matrix: 18.
- Crossref resolutions passed: 18.
- Crossref resolution failures: 0.
- Title mismatches requiring correction: 0 after the final directed audit.

Notable correction made before matrix freeze: the PDDL2.1 DOI is `10.1613/jair.1129`; earlier exploratory notes that guessed another JAIR identifier were not retained.

## Retrieval failures and claim restrictions

| Route | Result | Governance consequence |
|---|---|---|
| Semantic Scholar API | HTTP 429 | No returned metadata or abstract used as evidence |
| OpenAlex targeted lookups | partial/unstable coverage | API absence not treated as source absence |
| IEEE similarity-checking PDF endpoints | HTTP 418 | Howard, Elbaum, and Kitchenham remain below primary-full-text level |
| Elsevier text-mining endpoints | HTTP 400 without API access | Greiner and Ji–Carin remain metadata-only |
| Unpaywall | requires a real contact email | Service not used; no fabricated email supplied |
| `parallel-web` | CLI and API key absent | Direct DOI registries, official pages, author repositories, and local PDFs used instead |

No metadata-only source is allowed to support verbatim equations, numeric assignment rules, or claims about units that were not visible in primary text.

## Scope limitation

This is a rigorous cross-domain scoping review for experimental governance, not a completed PRISMA systematic review of every cost paper in computer science. Its strongest conclusion is nevertheless supported independently by standards, planning, RL, databases, robotics, AFA, software testing, CMDP, and multi-objective decision making: there is no universal numeric action-cost table; defensibility comes from frozen action semantics, raw measurement, explicit decision roles, calibrated models, and sensitivity/validity checks.
