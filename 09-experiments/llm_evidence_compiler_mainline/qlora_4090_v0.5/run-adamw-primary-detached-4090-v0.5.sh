#!/usr/bin/env bash
set -euo pipefail
umask 077

readonly ALLOWED_HOME="/home/myy"
readonly RUN_ROOT="${ALLOWED_HOME}/project05-qwen25-4090-v0.1"
readonly BUNDLE_ROOT="${RUN_ROOT}/bundle"
readonly VENV_ROOT="${RUN_ROOT}/local-runtime/venv"
readonly CONTRACT="${BUNDLE_ROOT}/09-experiments/llm_evidence_compiler_mainline/contracts/qwen25-qlora-4090-training-contract-v0.5.json"
readonly CONFIG="${BUNDLE_ROOT}/09-experiments/llm_evidence_compiler_mainline/qlora_4090_v0.5/training-config-v0.5.json"
readonly AUTHORITY="${BUNDLE_ROOT}/09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.37.json"
readonly SCRIPT="${BUNDLE_ROOT}/09-experiments/scripts/execute_qwen_qlora_4090_adamw_primary.py"
readonly PAIR_ROOT="${BUNDLE_ROOT}/09-experiments/llm_evidence_compiler_mainline/candidate_pairs_v0.2/local-data"
readonly PREPARATION_AUDIT="${RUN_ROOT}/server-output/preparation-audit-v0.1.json"
readonly SMOKE_AUDIT="${RUN_ROOT}/server-output/4090-longest-sequence-smoke-v0.1.json"
readonly OUTPUT_ROOT="${RUN_ROOT}/server-output/primary-adamw-detached-v0.37"
readonly LAUNCH_ROOT="${RUN_ROOT}/server-output/primary-adamw-detached-v0.37-launch"
readonly LOG_PATH="${LAUNCH_ROOT}/worker.log"
readonly PID_PATH="${LAUNCH_ROOT}/worker.pid"

case "$(pwd -P)" in "${ALLOWED_HOME}"|"${ALLOWED_HOME}"/*) ;; *) echo "outside /home/myy" >&2; exit 2;; esac
if [[ "$(id -un)" != "myy" ]]; then echo "wrong user" >&2; exit 2; fi

mode="${1:-start}"
if [[ "${mode}" == "start" ]]; then
  [[ ! -e "${OUTPUT_ROOT}" ]] || { echo "refusing to overwrite or resume ${OUTPUT_ROOT}" >&2; exit 4; }
  [[ ! -e "${LAUNCH_ROOT}" ]] || { echo "detached launch record already exists" >&2; exit 4; }
  mkdir -p "${LAUNCH_ROOT}"
  /usr/bin/nohup /usr/bin/setsid /bin/bash "$0" worker >"${LOG_PATH}" 2>&1 < /dev/null &
  worker_pid="$!"
  printf '%s\n' "${worker_pid}" > "${PID_PATH}"
  printf 'started_at_utc=%s\nworker_pid=%s\nlog=%s\noutput=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${worker_pid}" "${LOG_PATH}" "${OUTPUT_ROOT}"
  exit 0
fi
[[ "${mode}" == "worker" ]] || { echo "usage: $0 [start|worker]" >&2; exit 2; }

if [[ "${PROJECT05_CLEAN_ENVIRONMENT:-0}" != "1" ]]; then
  exec /usr/bin/env -i HOME="${ALLOWED_HOME}" USER="myy" LOGNAME="myy" SHELL="/bin/bash" PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" PROJECT05_CLEAN_ENVIRONMENT="1" /bin/bash "$0" worker
fi
for p in "${VENV_ROOT}/bin/python" "${CONTRACT}" "${CONFIG}" "${AUTHORITY}" "${SCRIPT}" "${PREPARATION_AUDIT}" "${SMOKE_AUDIT}" "${PAIR_ROOT}/train.jsonl.gz" "${PAIR_ROOT}/training-validation.jsonl.gz"; do [[ -e "${p}" ]] || { echo "missing ${p}" >&2; exit 2; }; done
[[ ! -e "${OUTPUT_ROOT}" ]] || { echo "refusing to overwrite or resume ${OUTPUT_ROOT}" >&2; exit 4; }
smoke_gpu_uuid="$("${VENV_ROOT}/bin/python" -c 'import json,sys; print(json.load(open(sys.argv[1]))["gpu"]["physical_uuid"])' "${SMOKE_AUDIT}")"
gpu_line="$(nvidia-smi --query-gpu=index,uuid,name,memory.free,memory.used --format=csv,noheader,nounits | awk -F', ' -v expected="${smoke_gpu_uuid}" '$2 == expected && $3 == "NVIDIA GeForce RTX 4090" && $4 >= 23000 && $5 <= 512 {print $1 "," $2 "," $4; exit}')"
[[ -n "${gpu_line}" ]] || { echo "smoke-bound GPU unavailable" >&2; exit 3; }
IFS=',' read -r physical_gpu_index physical_gpu_uuid initial_free_mib <<<"${gpu_line}"
export CUDA_VISIBLE_DEVICES="${physical_gpu_uuid}" PROJECT05_PHYSICAL_GPU_INDEX="${physical_gpu_index}" PROJECT05_PHYSICAL_GPU_UUID="${physical_gpu_uuid}"
export HF_HOME="${RUN_ROOT}/local-cache/huggingface-home" HF_HUB_CACHE="${RUN_ROOT}/local-cache/huggingface-hub" TRANSFORMERS_CACHE="${RUN_ROOT}/local-cache/transformers" XDG_CACHE_HOME="${RUN_ROOT}/local-cache/xdg" PYTHONPYCACHEPREFIX="${RUN_ROOT}/local-cache/pycache" TOKENIZERS_PARALLELISM="false" PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:128,garbage_collection_threshold:0.8"
echo "selected RTX 4090 index=${physical_gpu_index} free_mib=${initial_free_mib} detached_worker_pid=$$"
exec "${VENV_ROOT}/bin/python" "${SCRIPT}" --contract "${CONTRACT}" --config "${CONFIG}" --authority "${AUTHORITY}" --preparation-audit "${PREPARATION_AUDIT}" --pair-root "${PAIR_ROOT}" --run-root "${RUN_ROOT}" --smoke-audit "${SMOKE_AUDIT}"
