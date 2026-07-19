#!/usr/bin/env bash
set -euo pipefail
umask 077

readonly ALLOWED_HOME="/home/myy"
readonly RUN_ROOT="${ALLOWED_HOME}/project05-qwen25-4090-v0.1"
readonly BUNDLE_ROOT="${RUN_ROOT}/bundle"
readonly VENV_ROOT="${RUN_ROOT}/local-runtime/venv"
readonly UV_ROOT="${RUN_ROOT}/local-runtime/uv-0.4.29"
readonly UV_BIN="${UV_ROOT}/uv-x86_64-unknown-linux-gnu/uv"
readonly CONTRACT="${BUNDLE_ROOT}/09-experiments/llm_evidence_compiler_mainline/contracts/qwen25-qlora-4090-training-contract-v0.1.json"
readonly CONFIG="${BUNDLE_ROOT}/09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.1/training-config-v0.1.json"
readonly AUTHORITY="${BUNDLE_ROOT}/09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.30.json"
readonly REQUIREMENTS="${BUNDLE_ROOT}/09-experiments/llm_evidence_compiler_mainline/qlora_smoke_v0.1/requirements-linux-cu121-v0.1.txt"
readonly PREPARE_SCRIPT="${BUNDLE_ROOT}/09-experiments/scripts/prepare_qwen_qlora_smoke.py"
readonly EXECUTE_SCRIPT="${BUNDLE_ROOT}/09-experiments/scripts/execute_qwen_qlora_4090.py"
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

for path in "${RUN_ROOT}" "${BUNDLE_ROOT}" "${CONTRACT}" "${CONFIG}" "${AUTHORITY}" \
  "${REQUIREMENTS}" "${PREPARE_SCRIPT}" "${EXECUTE_SCRIPT}" "${PAIR_ROOT}"; do
  case "${path}" in
    "${RUN_ROOT}"|"${RUN_ROOT}"/*) ;;
    *) echo "contracted path escapes the run root: ${path}" >&2; exit 2 ;;
  esac
done

for required in "${CONTRACT}" "${CONFIG}" "${AUTHORITY}" "${REQUIREMENTS}" \
  "${PREPARE_SCRIPT}" "${EXECUTE_SCRIPT}" \
  "${PAIR_ROOT}/train.jsonl.gz" "${PAIR_ROOT}/training-validation.jsonl.gz"; do
  if [[ ! -f "${required}" ]]; then
    echo "required bundle file is missing: ${required}" >&2
    exit 2
  fi
done

mkdir -p "${RUN_ROOT}/local-runtime" "${RUN_ROOT}/local-cache" "${RUN_ROOT}/server-output"
chmod 700 "${RUN_ROOT}" "${RUN_ROOT}/local-runtime" "${RUN_ROOT}/local-cache" "${RUN_ROOT}/server-output"

gpu_line="$(nvidia-smi --query-gpu=index,uuid,name,memory.free,memory.used \
  --format=csv,noheader,nounits | \
  awk -F', ' '$3 == "NVIDIA GeForce RTX 4090" && $4 >= 23000 && $5 <= 512 {print $1 "," $2 "," $4; exit}')"
if [[ -z "${gpu_line}" ]]; then
  echo "no sufficiently idle RTX 4090 is available" >&2
  exit 3
fi
IFS=',' read -r physical_gpu_index physical_gpu_uuid initial_free_mib <<<"${gpu_line}"
if [[ -z "${physical_gpu_index}" || "${physical_gpu_uuid}" != GPU-* ]]; then
  echo "failed to parse the selected GPU identity" >&2
  exit 3
fi

export CUDA_VISIBLE_DEVICES="${physical_gpu_uuid}"
export PROJECT05_PHYSICAL_GPU_INDEX="${physical_gpu_index}"
export PROJECT05_PHYSICAL_GPU_UUID="${physical_gpu_uuid}"
export HF_HOME="${RUN_ROOT}/local-cache/huggingface-home"
export HF_HUB_CACHE="${RUN_ROOT}/local-cache/huggingface-hub"
export TRANSFORMERS_CACHE="${RUN_ROOT}/local-cache/transformers"
export XDG_CACHE_HOME="${RUN_ROOT}/local-cache/xdg"
export PYTHONPYCACHEPREFIX="${RUN_ROOT}/local-cache/pycache"
export PIP_CACHE_DIR="${RUN_ROOT}/local-cache/pip"
export UV_CACHE_DIR="${RUN_ROOT}/local-cache/uv"
export UV_PYTHON_INSTALL_DIR="${RUN_ROOT}/local-runtime/uv-python"
export TOKENIZERS_PARALLELISM="false"
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:128,garbage_collection_threshold:0.8"
export PIP_DISABLE_PIP_VERSION_CHECK="1"

echo "selected RTX 4090 index=${physical_gpu_index} free_mib=${initial_free_mib}"

phase="${1:-all}"
if [[ "${phase}" != "all" && "${phase}" != "prepare" && "${phase}" != "smoke" && "${phase}" != "primary" ]]; then
  echo "usage: $0 [all|prepare|smoke|primary]" >&2
  exit 2
fi

prepare_runtime() {
  if [[ ! -x "${VENV_ROOT}/bin/python" ]]; then
    available_bytes="$(df --output=avail -B1 "${RUN_ROOT}" | tail -n 1 | tr -d ' ')"
    if [[ "${available_bytes}" -lt 32000000000 ]]; then
      echo "initial disk-free Gate failed: ${available_bytes}" >&2
      exit 4
    fi
    if [[ ! -x "${UV_BIN}" ]]; then
      mkdir -p "${UV_ROOT}"
      curl --fail --location --silent --show-error \
        "https://github.com/astral-sh/uv/releases/download/0.4.29/uv-x86_64-unknown-linux-gnu.tar.gz" \
        --output "${UV_ROOT}/uv.tar.gz"
      tar -xzf "${UV_ROOT}/uv.tar.gz" -C "${UV_ROOT}"
      rm -f "${UV_ROOT}/uv.tar.gz"
    fi
    if [[ "$("${UV_BIN}" --version)" != "uv 0.4.29" ]]; then
      echo "uv version Gate failed" >&2
      exit 4
    fi
    "${UV_BIN}" python install 3.11.15
    "${UV_BIN}" venv --python 3.11.15 "${VENV_ROOT}"
    "${UV_BIN}" pip install --python "${VENV_ROOT}/bin/python" -r "${REQUIREMENTS}"
  fi

  if [[ ! -f "${PREPARATION_AUDIT}" ]]; then
    "${VENV_ROOT}/bin/python" "${PREPARE_SCRIPT}" \
      --contract "${CONTRACT}" \
      --run-root "${RUN_ROOT}" \
      --output "${PREPARATION_AUDIT}"
  fi
}

run_smoke() {
  if [[ ! -f "${SMOKE_AUDIT}" ]]; then
    "${VENV_ROOT}/bin/python" "${EXECUTE_SCRIPT}" \
      --phase smoke \
      --contract "${CONTRACT}" \
      --config "${CONFIG}" \
      --authority "${AUTHORITY}" \
      --preparation-audit "${PREPARATION_AUDIT}" \
      --pair-root "${PAIR_ROOT}" \
      --run-root "${RUN_ROOT}" \
      --output "${SMOKE_AUDIT}"
  fi
}

run_primary() {
  "${VENV_ROOT}/bin/python" "${EXECUTE_SCRIPT}" \
    --phase primary \
    --contract "${CONTRACT}" \
    --config "${CONFIG}" \
    --authority "${AUTHORITY}" \
    --preparation-audit "${PREPARATION_AUDIT}" \
    --pair-root "${PAIR_ROOT}" \
    --run-root "${RUN_ROOT}" \
    --smoke-audit "${SMOKE_AUDIT}"
}

case "${phase}" in
  prepare) prepare_runtime ;;
  smoke) prepare_runtime; run_smoke ;;
  primary) prepare_runtime; run_smoke; run_primary ;;
  all) prepare_runtime; run_smoke; run_primary ;;
esac
