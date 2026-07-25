#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/myy/project05-qwen25-4090-v0.1"
BUNDLE="${ROOT}/bundle"
PYTHON="${ROOT}/local-runtime/venv/bin/python"
CONTRACT="${BUNDLE}/09-experiments/llm_evidence_compiler_mainline/contracts/qwen25-general-adapted-paired-contract-v0.1.json"
CONFIG="${BUNDLE}/09-experiments/llm_evidence_compiler_mainline/paired_evaluation_v0.1/paired-evaluation-config-v0.1.json"
IMPLEMENTATION_AUTHORITY="${BUNDLE}/09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.41.json"
EXECUTION_AUTHORITY="${BUNDLE}/09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.42.json"
PAIR_ROOT="${BUNDLE}/09-experiments/llm_evidence_compiler_mainline/candidate_pairs_v0.2/local-data"
PREPARATION_AUDIT="${ROOT}/server-output/preparation-audit-v0.1.json"

cd "${ROOT}"
export CUDA_VISIBLE_DEVICES="2"
export PROJECT05_PHYSICAL_GPU_INDEX="2"
export PROJECT05_PHYSICAL_GPU_UUID="GPU-b0302acd-64e2-8218-7b5c-07a152007357"
export HF_HOME="${ROOT}/local-cache/huggingface"
export TRANSFORMERS_CACHE="${ROOT}/local-cache/huggingface"
export HF_DATASETS_CACHE="${ROOT}/local-cache/huggingface/datasets"
export TORCH_HOME="${ROOT}/local-cache/torch"
export TMPDIR="${ROOT}/local-cache/tmp"
export TEMP="${ROOT}/local-cache/tmp"
export TMP="${ROOT}/local-cache/tmp"
export TOKENIZERS_PARALLELISM="false"

"${PYTHON}" "${BUNDLE}/09-experiments/scripts/run_qwen_general_adapted_paired.py" \
  --contract "${CONTRACT}" \
  --config "${CONFIG}" \
  --implementation-authority "${IMPLEMENTATION_AUTHORITY}" \
  --execution-authority "${EXECUTION_AUTHORITY}" \
  --pair-root "${PAIR_ROOT}" \
  --run-root "${ROOT}" \
  --preparation-audit "${PREPARATION_AUDIT}"

"${PYTHON}" "${BUNDLE}/09-experiments/scripts/score_qwen_general_adapted_paired.py" \
  --contract "${CONTRACT}" \
  --config "${CONFIG}" \
  --implementation-authority "${IMPLEMENTATION_AUTHORITY}" \
  --execution-authority "${EXECUTION_AUTHORITY}" \
  --pair-root "${PAIR_ROOT}" \
  --run-root "${ROOT}"
