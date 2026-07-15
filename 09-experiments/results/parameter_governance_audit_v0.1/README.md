# Project05 parameter-governance post-run audit v0.1

This directory is an audit overlay. It does not modify the frozen v0.1 results and does not update any paper or patent.

## Main correction

The v0.1 W6 `channel ×0.75` arm mixed planner belief with execution-channel degradation. Its 51 Project05-M2 losses are therefore not valid evidence of channel-prior sensitivity. In the corrected v0.2 run, execution reliability is fixed and channel multipliers are planner-belief-only. Built-in planners do not consume that field, so both channel arms have zero outcome differences from `dev_measured_base`.

The remaining corrected W6 effect comes from the development-derived expected-effects profile: 3 losses among 270 repeated conditions, all within one of six independent cases (C11). Expert-prior ×1.25 repairs those three conditions; ×0.75 adds no further losses. These are descriptive case-level findings, not an inferential sample of 270 attacks.

## Project05-M2 robustness envelopes

| Family | Success-rate range | Max flip vs baseline | Min action-sequence agreement |
|---|---:|---:|---:|
| C cost | 1.0000–1.0000 | 0.0000 | 0.9111 |
| W1 thresholds | 1.0000–1.0000 | 0.0000 | 1.0000 |
| W7 corroboration | 1.0000–1.0000 | 0.0000 | 0.8148 |
| W2 alpha | 1.0000–1.0000 | 0.0000 | 0.8407 |
| W6 corrected priors | 0.9889–1.0000 | 0.0111 | 0.8148 |

## Open gates

- Rubric cost awaits two real independent raters and agreement statistics.
- Measured cost awaits action-level operational measurements.
- W3 Round 2 awaits two real independent annotators.
- External actor/selective accuracy awaits external actor or analyst-utility ground truth.
- Channel-prior sensitivity still requires AFA/depth-2 runners with fixed execution reliability.

`all_experiments_complete=false`; the paper/patent gate remains closed.
