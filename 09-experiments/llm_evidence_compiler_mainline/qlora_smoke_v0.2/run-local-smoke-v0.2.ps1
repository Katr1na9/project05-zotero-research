Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$RunRoot = Join-Path $RepoRoot '.local-qwen25-smoke'
$VenvRoot = Join-Path $RunRoot 'local-runtime\venv'
$Python = Join-Path $VenvRoot 'Scripts\python.exe'
$Contract = Join-Path $RepoRoot '09-experiments\llm_evidence_compiler_mainline\contracts\qwen25-qlora-local-smoke-contract-v0.2.json'
$Config = Join-Path $RepoRoot '09-experiments\llm_evidence_compiler_mainline\qlora_smoke_v0.2\training-config-v0.2-local.json'
$Requirements = Join-Path $RepoRoot '09-experiments\llm_evidence_compiler_mainline\qlora_smoke_v0.2\requirements-windows-cu121-v0.2.txt'
$PairRoot = Join-Path $RepoRoot '09-experiments\llm_evidence_compiler_mainline\candidate_pairs_v0.2\local-data'
$PrepareScript = Join-Path $RepoRoot '09-experiments\scripts\prepare_qwen_qlora_smoke.py'
$TrainScript = Join-Path $RepoRoot '09-experiments\scripts\train_qwen_qlora_smoke.py'
$PreparationAudit = Join-Path $RunRoot 'local-output\preparation-audit-v0.2.json'
$SmokeAudit = Join-Path $RunRoot 'local-output\smoke-audit-v0.2.json'

$ExpectedRunRoot = (Join-Path $RepoRoot '.local-qwen25-smoke')
if ([IO.Path]::GetFullPath($RunRoot) -ne [IO.Path]::GetFullPath($ExpectedRunRoot)) {
    throw 'Local run root escaped the repository boundary.'
}

$Drive = [System.IO.DriveInfo]::new([IO.Path]::GetPathRoot($RepoRoot))
if ($Drive.AvailableFreeSpace -lt 40000000000) {
    throw 'Less than 40 GB is available for the bounded local runtime.'
}

New-Item -ItemType Directory -Force -Path (Join-Path $RunRoot 'local-runtime'), (Join-Path $RunRoot 'local-cache'), (Join-Path $RunRoot 'local-output') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RunRoot 'local-cache\tmp') | Out-Null
$env:PIP_CACHE_DIR = Join-Path $RunRoot 'local-cache\pip'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
$env:TEMP = Join-Path $RunRoot 'local-cache\tmp'
$env:TMP = Join-Path $RunRoot 'local-cache\tmp'
$env:TMPDIR = Join-Path $RunRoot 'local-cache\tmp'
$env:HF_HOME = Join-Path $RunRoot 'local-cache\huggingface-home'
$env:HF_HUB_CACHE = Join-Path $RunRoot 'local-cache\huggingface-hub'
$env:TRANSFORMERS_CACHE = Join-Path $RunRoot 'local-cache\transformers'
$env:XDG_CACHE_HOME = Join-Path $RunRoot 'local-cache\xdg'
$env:PYTHONPYCACHEPREFIX = Join-Path $RunRoot 'local-cache\pycache'
$env:TOKENIZERS_PARALLELISM = 'false'
$env:CUDA_VISIBLE_DEVICES = '0'

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    python -m venv $VenvRoot
}
& $Python -m pip install --disable-pip-version-check --no-input --upgrade 'pip==24.2'
& $Python -m pip install --disable-pip-version-check --no-input -r $Requirements

& $Python $PrepareScript --contract $Contract --run-root $RunRoot --output $PreparationAudit
& $Python $TrainScript --contract $Contract --config $Config --preparation-audit $PreparationAudit --pair-root $PairRoot --run-root $RunRoot --output $SmokeAudit

Write-Output 'hard stop: local smoke completed; primary training remains unauthorized'
