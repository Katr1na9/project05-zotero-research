#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/myy/project05-qwen25-4090-v0.1"
BUNDLE="${ROOT}/bundle-v045"
PYTHON="${ROOT}/local-runtime/venv/bin/python"
AUTHORITY="${BUNDLE}/09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.45.json"
PREPARATION_AUDIT="${ROOT}/server-output/preparation-audit-v0.1.json"
DEPENDENCY_TARGET="${ROOT}/local-runtime/constrained-v0.1"
OUTPUT="${ROOT}/server-output/pointer-bound-constrained-preflight-v0.45.json"
FAILURE_OUTPUT="${ROOT}/server-output/pointer-bound-constrained-preflight-failure-v0.45.json"

cd "${ROOT}"
export PYTHONNOUSERSITE="1"
export CUDA_VISIBLE_DEVICES=""
export HF_HOME="${ROOT}/local-cache/huggingface"
export TRANSFORMERS_CACHE="${ROOT}/local-cache/huggingface"
export HF_DATASETS_CACHE="${ROOT}/local-cache/huggingface/datasets"
export TORCH_HOME="${ROOT}/local-cache/torch"
export TMPDIR="${ROOT}/local-cache/tmp-v0.45"
export TEMP="${ROOT}/local-cache/tmp-v0.45"
export TMP="${ROOT}/local-cache/tmp-v0.45"
export PIP_CACHE_DIR="${ROOT}/local-cache/pip-v0.45"
export HF_HUB_OFFLINE="1"
export TRANSFORMERS_OFFLINE="1"
export TOKENIZERS_PARALLELISM="false"

"${PYTHON}" "${BUNDLE}/09-experiments/scripts/preflight_pointer_bound_constrained_decoder.py" \
  --authority "${AUTHORITY}" \
  --run-root "${ROOT}" \
  --preparation-audit "${PREPARATION_AUDIT}" \
  --dependency-target "${DEPENDENCY_TARGET}" \
  --output "${OUTPUT}" \
  --failure-output "${FAILURE_OUTPUT}"
