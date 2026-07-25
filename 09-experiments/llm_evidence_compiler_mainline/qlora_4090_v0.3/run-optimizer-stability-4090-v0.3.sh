#!/usr/bin/env bash
set -euo pipefail
umask 077

readonly ALLOWED_HOME="/home/myy"
readonly RUN_ROOT="${ALLOWED_HOME}/project05-qwen25-4090-v0.1"
readonly BUNDLE_ROOT="${RUN_ROOT}/bundle"
readonly VENV_ROOT="${RUN_ROOT}/local-runtime/venv"
readonly RUNTIME_READY_MARKER="${RUN_ROOT}/local-runtime/runtime-ready-v0.1"
readonly CONTRACT="${BUNDLE_ROOT}/09-experiments/llm_evidence_compiler_mainline/contracts/qwen25-qlora-4090-training-contract-v0.3.json"
readonly CONFIG="${BUNDLE_ROOT}/09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.3/training-config-v0.3.json"
readonly AUTHORITY="${BUNDLE_ROOT}/09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.33.json"
readonly DIAGNOSTIC_SCRIPT="${BUNDLE_ROOT}/09-experiments/scripts/diagnose_qwen_qlora_optimizer_4090.py"
readonly PAIR_ROOT="${BUNDLE_ROOT}/09-experiments/llm_evidence_compiler_mainline/candidate_pairs_v0.2/local-data"
readonly PREPARATION_AUDIT="${RUN_ROOT}/server-output/preparation-audit-v0.1.json"
readonly SMOKE_AUDIT="${RUN_ROOT}/server-output/4090-longest-sequence-smoke-v0.1.json"

if [[ "${PROJECT05_CLEAN_ENVIRONMENT:-0}" != "1" ]]; then
  exec /usr/bin/env -i \
    HOME="${ALLOWED_HOME}" USER="myy" LOGNAME="myy" SHELL="/bin/bash" \
    PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    PROJECT05_CLEAN_ENVIRONMENT="1" \
    /bin/bash "$0" "$@"
fi

if [[ "$(id -un)" != "myy" ]]; then
  echo "refusing to run as a user other than myy" >&2
  exit 2
fi

case "$(pwd -P)" in
  "${ALLOWED_HOME}"|"${ALLOWED_HOME}"/*) ;;
  *) echo "refusing to run outside /home/myy" >&2; exit 2 ;;
esac

for required in "${RUN_ROOT}" "${BUNDLE_ROOT}" "${VENV_ROOT}/bin/python" \
  "${RUNTIME_READY_MARKER}" "${CONTRACT}" "${CONFIG}" "${AUTHORITY}" \
  "${DIAGNOSTIC_SCRIPT}" "${PREPARATION_AUDIT}" "${SMOKE_AUDIT}" \
  "${PAIR_ROOT}/train.jsonl.gz" "${PAIR_ROOT}/training-validation.jsonl.gz"; do
  case "${required}" in
    "${RUN_ROOT}"|"${RUN_ROOT}"/*) ;;
    *) echo "contracted path escapes the run root: ${required}" >&2; exit 2 ;;
  esac
  if [[ ! -e "${required}" ]]; then
    echo "required pre-existing artifact is missing: ${required}" >&2
    exit 2
  fi
done

smoke_gpu_uuid="$("${VENV_ROOT}/bin/python" -c \
  'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["gpu"]["physical_uuid"])' \
  "${SMOKE_AUDIT}")"
if [[ "${smoke_gpu_uuid}" != GPU-* ]]; then
  echo "failed to read the passed smoke GPU UUID" >&2
  exit 3
fi

gpu_line="$(nvidia-smi --query-gpu=index,uuid,name,memory.free,memory.used \
  --format=csv,noheader,nounits | \
  awk -F', ' -v expected="${smoke_gpu_uuid}" \
  '$2 == expected && $3 == "NVIDIA GeForce RTX 4090" && $4 >= 23000 && $5 <= 512 {print $1 "," $2 "," $4; exit}')"
if [[ -z "${gpu_line}" ]]; then
  echo "the smoke-bound RTX 4090 is not sufficiently idle" >&2
  exit 3
fi
IFS=',' read -r physical_gpu_index physical_gpu_uuid initial_free_mib <<<"${gpu_line}"

export CUDA_VISIBLE_DEVICES="${physical_gpu_uuid}"
export CUDA_LAUNCH_BLOCKING="1"
export PROJECT05_PHYSICAL_GPU_INDEX="${physical_gpu_index}"
export PROJECT05_PHYSICAL_GPU_UUID="${physical_gpu_uuid}"
export HF_HOME="${RUN_ROOT}/local-cache/huggingface-home"
export HF_HUB_CACHE="${RUN_ROOT}/local-cache/huggingface-hub"
export TRANSFORMERS_CACHE="${RUN_ROOT}/local-cache/transformers"
export XDG_CACHE_HOME="${RUN_ROOT}/local-cache/xdg"
export PYTHONPYCACHEPREFIX="${RUN_ROOT}/local-cache/pycache"
export TOKENIZERS_PARALLELISM="false"
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:128,garbage_collection_threshold:0.8"

if [[ "${1:-diagnostic}" != "diagnostic" ]]; then
  echo "usage: $0 diagnostic" >&2
  exit 2
fi

echo "selected RTX 4090 index=${physical_gpu_index} free_mib=${initial_free_mib}"
"${VENV_ROOT}/bin/python" "${DIAGNOSTIC_SCRIPT}" \
  --contract "${CONTRACT}" \
  --config "${CONFIG}" \
  --authority "${AUTHORITY}" \
  --preparation-audit "${PREPARATION_AUDIT}" \
  --pair-root "${PAIR_ROOT}" \
  --run-root "${RUN_ROOT}" \
  --smoke-audit "${SMOKE_AUDIT}"
