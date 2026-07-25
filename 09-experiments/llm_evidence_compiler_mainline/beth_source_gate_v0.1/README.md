# BETH v3 single-file source Gate v0.1

This directory contains only contracts and count/hash audit outputs for the
authorized BETH source Gate. Raw downloaded bytes must stay under
`quarantine/`, which is Git-ignored.

The only allowlisted object is Kaggle dataset `katehighnam/beth-dataset`,
version `3`, file `labelled_2021may-ip-10-100-1-105.csv`, with a 512 MiB cap.
No second file or whole-dataset fallback is allowed.

Current status is recorded in `generated/acquisition-status.json`. The exact
single file was retrieved through Kaggle's official one-member ZIP transport;
license, schema, protected-payload and read-only G0 audits passed. BETH is now
eligible as the fourth *candidate* G0-positive training family.

This is not a formal data-Gate pass. Raw CSV/ZIP/legalcode bytes remain under
Git-ignored `quarantine/`. This directory never stores normalized records,
candidate records or training pairs, and no tokenizer, model, training,
inference or M3 action is authorized by this source Gate.
