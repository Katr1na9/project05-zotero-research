param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("lo2v2_index_json")]
    [string]$TargetId,

    [Parameter(Mandatory = $true)]
    [ValidateRange(300, 300)]
    [int]$ExternalSupervisorSeconds
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($TargetId -ne "lo2v2_index_json") {
    throw "target_id_mismatch"
}
if ($ExternalSupervisorSeconds -ne 300) {
    throw "external_supervisor_seconds_mismatch"
}

$RepoRoot = [System.IO.Path]::GetFullPath(
    (Join-Path $PSScriptRoot "..\..")
)
$Python = [Environment]::ExpandEnvironmentVariables(
    "%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\python.exe"
)
$AuditScript = Join-Path $RepoRoot "datasets\llm\audit_lo2v2_index_v0_1.py"
$AuditContract = Join-Path $RepoRoot (
    "docs\llm-editor\" +
    "llm-editor-v0.8-l2-lo2v2-index-json-reader-privacy-notice-" +
    "schema-manifest-lineage-label-v1-v2-pointer-audit-contract-" +
    "v0.1-20260723.json"
)
$ReaderAmendment = Join-Path $RepoRoot (
    "docs\llm-editor\" +
    "llm-editor-v0.8-l2-lo2v2-index-json-reader-tool-amendment-" +
    "v0.1-20260723.json"
)
$AttemptOneFailure = Join-Path $RepoRoot (
    "docs\llm-editor\" +
    "llm-editor-v0.8-l2-lo2v2-index-bounded-audit-attempt-1-" +
    "launcher-failure-result-v0.1-20260723.json"
)
$Authority = Join-Path $RepoRoot (
    "docs\llm-editor\" +
    "llm-editor-v0.8-l2-lo2v2-index-bounded-audit-execute-" +
    "attempt-2-authority-v0.1-20260723.json"
)
$ResultJson = Join-Path $RepoRoot (
    "docs\llm-editor\" +
    "llm-editor-v0.8-l2-lo2v2-index-bounded-audit-result-" +
    "v0.1-20260723.json"
)
$ResultMarkdown = Join-Path $RepoRoot (
    "docs\llm-editor\" +
    "llm-editor-v0.8-l2-lo2v2-index-bounded-audit-result-" +
    "v0.1-20260723.md"
)

$ExpectedHashes = @{
    audit_script = "170a2d115e35c080ca3c64d4d01356a0046db5603d86f42d3b04335b288a8c85"
    audit_contract = "055afec2d650a29f007f9ec6d20f61f3609e2992aa4b55bbf1c8f6672dc0ef26"
    reader_amendment = "725baaf4580fb11496d73a4b9b4ce6b35d414928a85dfb8f87841a5249ea76f8"
    attempt_one_failure = "11e6cfc1c9fb61164c2650e96cf43efbe6892c0e6d2b7771da5805b55d61ea5c"
}

foreach ($RequiredFile in @(
    $Python,
    $AuditScript,
    $AuditContract,
    $ReaderAmendment,
    $AttemptOneFailure,
    $Authority
)) {
    if (-not (Test-Path -LiteralPath $RequiredFile -PathType Leaf)) {
        throw "required_file_missing"
    }
}

if (
    (Test-Path -LiteralPath $ResultJson) -or
    (Test-Path -LiteralPath $ResultMarkdown)
) {
    throw "result_already_exists_execute_once_gate"
}

$ActualHashes = @{
    audit_script = (
        Get-FileHash -LiteralPath $AuditScript -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    audit_contract = (
        Get-FileHash -LiteralPath $AuditContract -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    reader_amendment = (
        Get-FileHash -LiteralPath $ReaderAmendment -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    attempt_one_failure = (
        Get-FileHash -LiteralPath $AttemptOneFailure -Algorithm SHA256
    ).Hash.ToLowerInvariant()
}

foreach ($Key in $ExpectedHashes.Keys) {
    if ($ActualHashes[$Key] -ne $ExpectedHashes[$Key]) {
        throw "pinned_artifact_hash_mismatch"
    }
}

$AuthorityObject = Get-Content -LiteralPath $Authority -Raw |
    ConvertFrom-Json
$SelfHash = (
    Get-FileHash -LiteralPath $MyInvocation.MyCommand.Path -Algorithm SHA256
).Hash.ToLowerInvariant()

if ($AuthorityObject.status -ne "authorized_once") {
    throw "execution_authority_status_invalid"
}
if ($AuthorityObject.target_id -ne $TargetId) {
    throw "execution_authority_target_mismatch"
}
if ($AuthorityObject.attempt_number -ne 2) {
    throw "execution_authority_attempt_number_mismatch"
}
if ($AuthorityObject.execution_count_authorized -ne 1) {
    throw "execution_authority_count_mismatch"
}
if ($AuthorityObject.corrected_launcher_sha256 -ne $SelfHash) {
    throw "corrected_launcher_hash_mismatch"
}
if ($AuthorityObject.audit_script_sha256 -ne $ExpectedHashes.audit_script) {
    throw "execution_authority_audit_script_hash_mismatch"
}
if ($AuthorityObject.audit_contract_sha256 -ne $ExpectedHashes.audit_contract) {
    throw "execution_authority_audit_contract_hash_mismatch"
}
if ($AuthorityObject.automatic_retry_authorized -ne $false) {
    throw "automatic_retry_boundary_missing"
}
if ($AuthorityObject.resume_authorized -ne $false) {
    throw "resume_boundary_missing"
}

$Arguments = @(
    $AuditScript,
    "--mode",
    "execute",
    "--authority-json",
    $Authority
)

Push-Location -LiteralPath $RepoRoot
try {
    & $Python @Arguments
    $AuditExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($AuditExitCode -ne 0) {
    exit $AuditExitCode
}
exit 0
