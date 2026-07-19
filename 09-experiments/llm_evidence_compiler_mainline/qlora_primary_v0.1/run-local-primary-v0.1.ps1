$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$RunRoot = Join-Path $RepoRoot ".local-qwen25-smoke"
$Python = Join-Path $RunRoot "local-runtime\venv\Scripts\python.exe"
$CacheRoot = Join-Path $RunRoot "local-cache"
$OutputRoot = Join-Path $RunRoot "local-output\primary-v0.1"
$PairRoot = Join-Path $RepoRoot "09-experiments\llm_evidence_compiler_mainline\candidate_pairs_v0.2\local-data"
$Contract = Join-Path $RepoRoot "09-experiments\llm_evidence_compiler_mainline\contracts\qwen25-primary-training-contract-v0.1.json"
$Config = Join-Path $RepoRoot "09-experiments\llm_evidence_compiler_mainline\qlora_primary_v0.1\training-config-v0.1-local.json"
$Authority = Join-Path $RepoRoot "09-experiments\llm_evidence_compiler_mainline\contracts\authority-lock-v0.25.json"
$Preflight = Join-Path $RunRoot "local-output\primary-preflight-v0.1.json"
$Preparation = Join-Path $RunRoot "local-output\preparation-audit-v0.2.json"
$Script = Join-Path $RepoRoot "09-experiments\scripts\execute_qwen_qlora_primary.py"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Frozen local Python runtime is missing."
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "Refusing to overwrite an existing primary run."
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

& $Python $Script `
    --contract $Contract `
    --config $Config `
    --authority $Authority `
    --preflight-audit $Preflight `
    --preparation-audit $Preparation `
    --pair-root $PairRoot `
    --run-root $RunRoot

if ($LASTEXITCODE -ne 0) {
    throw "Primary QLoRA training exited with code $LASTEXITCODE."
}
