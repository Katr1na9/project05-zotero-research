# Toyota HSR placement trials metadata candidate review

## Verdict

**Approve as a metadata candidate, not as a source role.**

The family has sufficient immutable identity and curator-declared execution capacity for continued review:

- one inspected Zenodo release;
- record-scope CC-BY-4.0;
- three immutable archives with exact bytes and MD5;
- 121 curator-declared placement trials.

It remains outside the effective catalog, model view, train, development, source role, lineage, sample, quota, pointer binding, and L2.

## Why the trial count is admissible only at metadata level

The curator names `trial` as the execution unit and declares:

| External archive | Curator declaration |
|---|---:|
| train | 48 successful trials |
| validation | 6 successful trials |
| test | 60 anomalous + 7 successful trials |
| total | 121 trials |

The 121 count is a sum of curator-declared trials, not a count of files, directories, frames, sensors, splits, or outcome categories.

However, no stable label-independent trial identifier or complete trial manifest has been verified. No duplicate, retry, partial, interruption, collision, reset, repeated-state, or statistical-independence policy is available. Consequently, the 121 trials are candidate capacity, not 121 admitted lineages or samples.

## External split and outcome boundary

The curator's `train`, `validation`, and `test` names have no Project05 authority. Likewise, `successful`, `failed`, `anomalous`, and frame-level anomaly annotations may not:

- enter model input, prompt, or target;
- define a Project05 split, lineage, pointer, or sample;
- generate negative, null, abstention, or candidate-q supervision;
- be used to select a convenient post hoc clean subset.

Any future trial identity must be recoverable without reading or using split, outcome, anomaly, collision, or frame-annotation information.

## Declared surfaces

The official metadata declares:

- RGB head-camera images;
- depth images;
- rendered robot-body images;
- wrist force-torque readings;
- joint efforts, velocities, and positions;
- camera calibration;
- frame-level anomaly annotations.

There is no separately published top-level trial manifest, non-visual telemetry object, or annotation-free object. All model visibility therefore remains closed.

The possible author repository confirms only that the dataset includes rendered robot-body images. Its README does not mention Zenodo record `4578539`, the dataset DOI, the three archive keys, or a trial manifest. The repository is not an authoritative dataset manifest, and its GPL-3.0 code license does not replace the dataset's CC-BY-4.0 record license.

## Scientific fit

This is a physical-robot task-monitoring benchmark, not malware, APT, honeypot, host-forensics, or incident-response evidence.

A future admissible surface would likely be limited to outcome-blind non-visual telemetry such as joint and force-torque records. That surface may support candidate relations about reported effort, velocity, position, force, or torque. It may not support an observed claim that a trial succeeded, failed, was anomalous, or had a particular cause.

Because the declared candidate surface is mostly numeric telemetry, Rule/Reuse parsing is a strong baseline. The family cannot receive a source role unless an LLM demonstrates measurable evidence-safe semantic normalization or candidate-q value beyond deterministic parsing.

## Future bounded acquisition recommendation

No acquisition is authorized by this review.

If separately authorized, the only recommended first object is:

| Target | Bytes | MD5 | Declared trials |
|---|---:|---|---:|
| `place_action_validation.tar.gz` | 365,983,836 | `76cb0cab741c3a55eaf662df979f4637` | 6 successful trials |

It is recommended only because it is the smallest immutable object and contains at least four curator-declared trials. Its external `validation` name and all-successful composition do not make it Project05 validation data, a clean source, a label-free source, or representative training material.

Before any archive open, a separate contract must freeze:

1. exact URL, bytes, MD5, one attempt, and no automatic resume;
2. gzip/tar reader identity and member/byte/wall-time caps;
3. nested notice and license handling;
4. image, depth, rendered-model, calibration, outcome, split, and annotation exclusion;
5. outcome-blind trial manifest and lineage rules;
6. privacy and raw-path persistence boundaries;
7. unbound pointer suggestion and source round trip;
8. sanitized aggregate-only output.

Acquisition would verify identity only. Archive opening and audit would still require separate authority.

## Scope

This review read only public registry, publication, repository, and README metadata. It did not download or open any archive, read code, models, images, trial data, telemetry, annotations, private gold, or model output. It did not write the catalog, assign a role or credit, design St.Gallen v0.2, generate samples, run a baseline or fine-tuning job, modify Kernel/Gamma/M3, pass L2, commit the review, or push.

## Sources

- [Zenodo record 4578539](https://zenodo.org/records/4578539)
- [Zenodo Records API](https://zenodo.org/api/records/4578539)
- [Zenodo version chain](https://zenodo.org/api/records/4578539/versions)
- [DataCite DOI metadata](https://api.datacite.org/dois/10.5281/zenodo.4578539)
- [Thoduka et al., 2021 — Using Visual Anomaly Detection for Task Execution Monitoring](https://doi.org/10.1109/IROS51168.2021.9636133) — plausible bibliographic match, not an explicit dataset binding
- [Possible author repository](https://github.com/sthoduka/motion_anomaly_detection) — not an authoritative dataset manifest
