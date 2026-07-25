# Project05 cost/action construct scoping review protocol v0.1

Status: internal experimental-governance research; not paper or patent text.

Search date: 2026-07-18 (Asia/Shanghai).

## Research questions

1. How do authoritative computer-science formalisms define an action, including its boundary, preconditions, effects, outcome, and decision epoch?
2. What does action/acquisition/query/test cost mean in each field: measured resource use, monetary/time burden, risk, constraint, negative reward, or elicited preference?
3. How is cost obtained: direct measurement, analytical model, market/resource price, expert elicitation, fixed benchmark convention, or learned predictor?
4. When is cost additive, state-dependent, outcome-dependent, grouped, delayed, uncertain, or multi-objective?
5. What validation is required before action count or cumulative cost can support a comparative algorithmic claim?

## Scope

Included domains:

- digital forensics and incident response;
- Markov decision processes and partially observable control;
- classical/temporal AI planning and PDDL;
- active feature acquisition, active learning, diagnostic test selection, and value of information;
- database query optimization;
- robotic motion/path planning;
- software-test prioritization and resource-aware computing.

Source priority:

1. official standards/specifications and books recognized as field references;
2. seminal peer-reviewed papers and highly cited surveys;
3. later peer-reviewed work that explicitly relaxes fixed/additive cost assumptions;
4. preprints only when no peer-reviewed substitute exists, clearly marked.

## Search sources

- Crossref metadata and DOI registry;
- OpenAlex metadata, concepts, citation counts, and open-access links;
- Semantic Scholar metadata/citation graph when available;
- official RFC Editor, NIST, ISO, ICAPS/PDDL, and standards-body pages;
- local Zotero database and locally archived full text.

## Query families

- `action cost definition MDP POMDP state dependent transition cost`
- `PDDL action cost total-cost precondition effect planning`
- `cost-sensitive feature acquisition test cost grouped conditional cost`
- `active learning query cost label acquisition cost survey`
- `Bayesian experimental design expected information gain experiment cost utility`
- `database query optimizer cost model CPU I/O cardinality Selinger`
- `robot motion planning action cost energy time risk motion primitive`
- `test case prioritization cost cognizant APFDc execution time`
- `digital evidence acquisition collection effort volatility NIST RFC ISO 27037`

## Inclusion criteria

A source must contribute at least one of:

- an explicit formal or operational definition of action;
- an explicit interpretation or unit for cost;
- a method for assigning, measuring, learning, or validating cost;
- a counterexample to fixed, scalar, additive action cost;
- a standard taxonomy directly relevant to evidence-acquisition operations.

## Exclusion criteria

- papers using `cost` only as generic loss without defining its semantics;
- papers mentioning actions but not defining their boundary or consequences;
- application papers that copy arbitrary benchmark costs without methodological discussion;
- non-authoritative web summaries when the original standard or paper is available;
- citations whose title, venue, year, or DOI cannot be independently verified.

## Extraction fields

- source identity, type, venue/issuer, year, DOI/URL, citation count where available;
- action definition and granularity rule;
- cost construct, unit, and decision role;
- assignment/calibration source;
- additivity and context dependence;
- uncertainty treatment;
- validation method;
- transferable implication and non-transferable limitation for Project05.

## Claim discipline

No source will be treated as establishing a universal numeric cost scale unless it actually specifies and validates one. Expert agreement is reliability evidence only; it is not field-wide construct validity. Project05 legacy costs and planner outcomes are excluded from construct selection and calibration.
