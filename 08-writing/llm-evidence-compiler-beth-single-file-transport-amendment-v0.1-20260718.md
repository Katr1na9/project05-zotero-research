# LLM evidence compiler BETH single-file transport amendment v0.1

Status: `authorized_exact_transport_wrapper_only`
Date: 2026-07-18
Parent authority: `authority-lock-v0.7.json`

## Observed transport fact

The authenticated Kaggle single-file endpoint returned HTTP 200 for the exact
version-3 file request. The response was not the 928,188,305-byte dataset
archive. It was a 3,997,971-byte ZIP transport wrapper named exactly:

`labelled_2021may-ip-10-100-1-105.csv.zip`

Kaggle uses this wrapper to deliver the one requested CSV. The v0.7
implementation rejected it before reading the response body because v0.7
allowed only a direct CSV response. At that point corpus bytes remained zero.

## Narrow authorization

This amendment allows either the already-authorized direct CSV response or one
exact Kaggle transport wrapper. The wrapper is admissible only when all of the
following hold:

1. the response transport name is exactly
   `labelled_2021may-ip-10-100-1-105.csv.zip`;
2. the ZIP contains exactly one member;
3. that member is exactly `labelled_2021may-ip-10-100-1-105.csv` at the archive
   root;
4. the member is a regular, unencrypted, non-directory, non-symbolic-link
   entry;
5. the compression method is stored or deflated;
6. compressed and uncompressed byte counts are each no more than 512 MiB;
7. the declared compression ratio is no more than 100:1;
8. extraction reads the complete member so the ZIP CRC is checked;
9. archive acquisition and member extraction are atomic and fail closed.

A second member, directory entry, path component, path traversal, encrypted
member, symbolic link, unsupported compression, CRC failure, excess size or
excess compression ratio invalidates the response. On failure, the archive,
CSV and partial files are deleted.

## Manifest boundary

The top-level `bytes`, `sha256` and `path` fields bind the extracted CSV. ZIP
transport evidence is recorded separately under `transport`, including the
archive byte count, archive SHA-256, archive path and member count. Signed URL
query material and Kaggle credentials are never written to the manifest.

## Unchanged prohibitions

This amendment does not authorize the full BETH archive, a second BETH file,
normalized records, candidate-pair construction, tokenizer or Qwen downloads,
dependency changes, training, inference, C07-C12 model execution, M3 runtime
integration, `run_mvp.py` changes, or frozen result rewrites.
