#!/usr/bin/env bash
set -euo pipefail
umask 077

readonly ALLOWED_HOME="/home/myy"
readonly RUN_ROOT="${ALLOWED_HOME}/project05-qwen25-smoke-v0.1"
readonly REPO_ROOT="${ALLOWED_HOME}/Project05-Zotero"
readonly VENV_ROOT="${RUN_ROOT}/local-runtime/venv"
readonly CONTRACT="${REPO_ROOT}/09-experiments/llm_evidence_compiler_mainline/contracts/qwen25-qlora-smoke-contract-v0.1.json"
readonly CONFIG="${REPO_ROOT}/09-experiments/llm_evidence_compiler_mainline/qlora_smoke_v0.1/training-config-v0.1.json"
readonly REQUIREMENTS="${REPO_ROOT}/09-experiments/llm_evidence_compiler_mainline/qlora_smoke_v0.1/requirements-linux-cu121-v0.1.txt"
readonly PAIR_ROOT="${REPO_ROOT}/09-experiments/llm_evidence_compiler_mainline/candidate_pairs_v0.2/local-data"
readonly PREPARE_SCRIPT="${REPO_ROOT}/09-experiments/scripts/prepare_qwen_qlora_smoke.py"
readonly TRAIN_SCRIPT="${REPO_ROOT}/09-experiments/scripts/train_qwen_qlora_smoke.py"
readonly PREPARATION_AUDIT="${RUN_ROOT}/local-output/preparation-audit-v0.1.json"
readonly SMOKE_AUDIT="${RUN_ROOT}/local-output/smoke-audit-v0.1.json"

case "$(pwd -P)" in
  "${ALLOWED_HOME}"|"${ALLOWED_HOME}"/*) ;;
  *) echo "refusing to run outside /home/myy" >&2; exit 2 ;;
esac

case "${REPO_ROOT}" in
  "${ALLOWED_HOME}"/*) ;;
  *) echo "repository boundary failure" >&2; exit 2 ;;
esac

if [[ "$(id -un)" != "myy" ]]; then
  echo "refusing to run as a user other than myy" >&2
  exit 2
fi

mkdir -p "${RUN_ROOT}/local-runtime" "${RUN_ROOT}/local-cache" "${RUN_ROOT}/local-output"
export PIP_CACHE_DIR="${RUN_ROOT}/local-cache/pip"
export PIP_DISABLE_PIP_VERSION_CHECK="1"
python3 -m venv "${VENV_ROOT}"
"${VENV_ROOT}/bin/python" -m pip install --disable-pip-version-check --no-input --upgrade "pip==24.2"
"${VENV_ROOT}/bin/python" -m pip install --disable-pip-version-check --no-input -r "${REQUIREMENTS}"

export HF_HOME="${RUN_ROOT}/local-cache/huggingface-home"
export HF_HUB_CACHE="${RUN_ROOT}/local-cache/huggingface-hub"
export TRANSFORMERS_CACHE="${RUN_ROOT}/local-cache/transformers"
export XDG_CACHE_HOME="${RUN_ROOT}/local-cache/xdg"
export PYTHONPYCACHEPREFIX="${RUN_ROOT}/local-cache/pycache"
export TOKENIZERS_PARALLELISM="false"
export CUDA_VISIBLE_DEVICES="0"

"${VENV_ROOT}/bin/python" "${PREPARE_SCRIPT}" \
  --contract "${CONTRACT}" \
  --run-root "${RUN_ROOT}" \
  --output "${PREPARATION_AUDIT}"

"${VENV_ROOT}/bin/python" "${TRAIN_SCRIPT}" \
  --contract "${CONTRACT}" \
  --config "${CONFIG}" \
  --preparation-audit "${PREPARATION_AUDIT}" \
  --pair-root "${PAIR_ROOT}" \
  --run-root "${RUN_ROOT}" \
  --output "${SMOKE_AUDIT}"

echo "hard stop: smoke completed; primary training remains unauthorized"
