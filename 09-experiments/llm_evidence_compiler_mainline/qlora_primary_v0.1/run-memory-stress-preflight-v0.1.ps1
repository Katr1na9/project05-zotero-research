$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$RunRoot = Join-Path $RepoRoot ".local-qwen25-smoke"
$Python = Join-Path $RunRoot "local-runtime\venv\Scripts\python.exe"
$CacheRoot = Join-Path $RunRoot "local-cache"
$Contract = Join-Path $RepoRoot "09-experiments\llm_evidence_compiler_mainline\contracts\qwen25-memory-stress-preflight-contract-v0.1.json"
$Authority = Join-Path $RepoRoot "09-experiments\llm_evidence_compiler_mainline\contracts\authority-lock-v0.27.json"
$Output = Join-Path $RunRoot "local-output\memory-stress-preflight-v0.1.json"
$Script = Join-Path $RepoRoot "09-experiments\scripts\preflight_qwen_qlora_memory_stress.py"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Frozen local Python runtime is missing."
}
if (Test-Path -LiteralPath $Output) {
    throw "Refusing to overwrite the memory stress preflight result."
}

$env:CUDA_VISIBLE_DEVICES = "0"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:HF_HOME = Join-Path $CacheRoot "huggingface"
$env:HUGGINGFACE_HUB_CACHE = Join-Path $CacheRoot "huggingface\hub"
$env:TRANSFORMERS_CACHE = Join-Path $CacheRoot "huggingface\hub"
$env:HF_DATASETS_CACHE = Join-Path $CacheRoot "datasets"
$env:TEMP = Join-Path $CacheRoot "temp"
$env:TMP = Join-Path $CacheRoot "temp"
$env:PYTHONUNBUFFERED = "1"
$env:PYTORCH_CUDA_ALLOC_CONF = "max_split_size_mb:128,garbage_collection_threshold:0.8"

& $Python $Script `
    --contract $Contract `
    --authority $Authority `
    --run-root $RunRoot `
    --output $Output

if ($LASTEXITCODE -ne 0) {
    throw "Memory stress preflight exited with code $LASTEXITCODE."
}
