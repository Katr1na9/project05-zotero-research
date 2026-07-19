Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$RunRoot = Join-Path $RepoRoot '.local-qwen25-smoke'
$Python = Join-Path $RunRoot 'local-runtime\venv\Scripts\python.exe'
$Contract = Join-Path $RepoRoot '09-experiments\llm_evidence_compiler_mainline\contracts\qwen25-primary-preflight-contract-v0.1.json'
$Authority = Join-Path $RepoRoot '09-experiments\llm_evidence_compiler_mainline\contracts\authority-lock-v0.23.json'
$PrimaryContract = Join-Path $RepoRoot '09-experiments\llm_evidence_compiler_mainline\contracts\qwen25-primary-training-contract-v0.1.json'
$Config = Join-Path $RepoRoot '09-experiments\llm_evidence_compiler_mainline\qlora_primary_v0.1\training-config-v0.1-local.json'
$Script = Join-Path $RepoRoot '09-experiments\scripts\preflight_qwen_qlora_primary.py'
$Output = Join-Path $RunRoot 'local-output\primary-preflight-v0.1.json'

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw 'The locked local runtime is missing; preflight cannot install or repair it.'
}
if (Test-Path -LiteralPath $Output) {
    throw 'The preflight output already exists; overwrite is prohibited.'
}

$env:PIP_CACHE_DIR = Join-Path $RunRoot 'local-cache\pip'
$env:TEMP = Join-Path $RunRoot 'local-cache\tmp'
$env:TMP = Join-Path $RunRoot 'local-cache\tmp'
$env:TMPDIR = Join-Path $RunRoot 'local-cache\tmp'
$env:HF_HOME = Join-Path $RunRoot 'local-cache\huggingface-home'
$env:HF_HUB_CACHE = Join-Path $RunRoot 'local-cache\huggingface-hub'
$env:TRANSFORMERS_CACHE = Join-Path $RunRoot 'local-cache\transformers'
$env:XDG_CACHE_HOME = Join-Path $RunRoot 'local-cache\xdg'
$env:PYTHONPYCACHEPREFIX = Join-Path $RunRoot 'local-cache\pycache'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:TOKENIZERS_PARALLELISM = 'false'
$env:PYTHONNOUSERSITE = '1'
$env:CUDA_VISIBLE_DEVICES = '0'

& $Python $Script --contract $Contract --authority $Authority --primary-contract $PrimaryContract --config $Config --run-root $RunRoot --output $Output
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Output 'hard stop: zero-step primary preflight completed; primary training remains unauthorized'
