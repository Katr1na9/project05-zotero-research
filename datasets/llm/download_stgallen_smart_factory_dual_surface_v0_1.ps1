[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ActivationJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$contractSha256 = 'f7a794e0774ecd1df58da98d487369892109644c706728cc23bc9ccf2b12af20'
$authoritySha256 = 'b8ab19fe2f46990ef617123a073419394f40a771064e067be2996f879b1ea7d8'
$curlSha256 = '73d24149ff289afc49ec41f08918ef9faa727d39ad993e929757dc2ddafab805'
$powershellSha256 = '7600ffe12da441fe89d035b13801e8e91d064bc544a27b19a5cf49f6ab8b18f5'
$recordId = 14441997
$recordRevision = 8
$combinedExpectedBytes = [int64]60012779
$minimumFreeBytes = [int64]120025558

$manifestTargetId = 'stgallen_camunda_process_manifest_surface'
$manifestExpectedBytes = [int64]111548
$manifestExpectedMd5 = 'a56fb7b92ad99a8106ff3c75a2d94c6f'
$manifestUrl = 'https://zenodo.org/api/records/14441997/files/camunda-process.json/content'

$sensorTargetId = 'stgallen_training_sensor_log_surface'
$sensorExpectedBytes = [int64]59901231
$sensorExpectedMd5 = '1b310fe1bbbbe53511db015375df8a41'
$sensorUrl = 'https://zenodo.org/api/records/14441997/files/training_tenhertz_log_20230411-095748.txt/content'

$curlPath = 'C:\WINDOWS\system32\curl.exe'
$powershellPath = 'C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe'
$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$contractPath = Join-Path $repositoryRoot 'docs\llm-editor\llm-editor-v0.8-l2-stgallen-smart-factory-exact-bounded-dual-surface-acquisition-contract-v0.1-20260724.json'
$authorityPath = Join-Path $repositoryRoot 'docs\llm-editor\llm-editor-v0.8-l2-stgallen-smart-factory-dual-surface-acquisition-execution-authority-v0.1-20260724.json'
$expectedActivationPath = Join-Path $repositoryRoot 'docs\llm-editor\llm-editor-v0.8-l2-stgallen-smart-factory-dual-surface-acquisition-activation-v0.1-20260724.json'
$rawRoot = Join-Path $PSScriptRoot 'local_audit_cache\stgallen-smart-factory-bounded-v0.1\raw'
$protectedRoot = Join-Path $rawRoot 'protected_manifest'
$modelCandidateRoot = Join-Path $rawRoot 'model_candidate'
$manifestTargetPath = Join-Path $protectedRoot 'camunda-process.json'
$sensorTargetPath = Join-Path $modelCandidateRoot 'training_tenhertz_log_20230411-095748.txt'

function Assert-EqualString {
    param(
        [Parameter(Mandatory = $true)]
        [AllowNull()]
        [object]$Actual,
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Expected,
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    if ($Actual -isnot [string] -or [string]$Actual -cne $Expected) {
        throw $Message
    }
}

function Assert-JsonBoolean {
    param(
        [Parameter(Mandatory = $true)]
        [AllowNull()]
        [object]$Actual,
        [Parameter(Mandatory = $true)]
        [bool]$Expected,
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    if ($Actual -isnot [bool] -or [bool]$Actual -ne $Expected) {
        throw $Message
    }
}

function Assert-JsonInteger {
    param(
        [Parameter(Mandatory = $true)]
        [AllowNull()]
        [object]$Actual,
        [Parameter(Mandatory = $true)]
        [int64]$Expected,
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    if (
        ($Actual -isnot [int] -and $Actual -isnot [long]) -or
        [int64]$Actual -ne $Expected
    ) {
        throw $Message
    }
}

function Assert-ExactTargetArray {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Actual
    )

    $expected = @($manifestTargetId, $sensorTargetId)
    if ($Actual.Count -ne $expected.Count) {
        throw 'Activation must name exactly the two frozen target identifiers.'
    }

    for ($index = 0; $index -lt $expected.Count; $index++) {
        if ($Actual[$index] -isnot [string] -or [string]$Actual[$index] -cne $expected[$index]) {
            throw 'Activation target identifiers or order do not match the frozen atomic pair.'
        }
    }
}

function Assert-PathIsDirectChild {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ChildPath,
        [Parameter(Mandatory = $true)]
        [string]$ParentPath,
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $childFull = [System.IO.Path]::GetFullPath($ChildPath)
    $parentFull = [System.IO.Path]::GetFullPath($ParentPath).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
    $childParent = [System.IO.Path]::GetDirectoryName($childFull).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )

    if (-not [System.StringComparer]::OrdinalIgnoreCase.Equals($childParent, $parentFull)) {
        throw $Message
    }
}

function Assert-NoExistingReparsePoint {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PathToCheck
    )

    $cursor = [System.IO.Path]::GetFullPath($PathToCheck)
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw 'An existing acquisition-path component is a reparse point; refusing execution.'
            }
        }

        $parent = [System.IO.Path]::GetDirectoryName($cursor)
        if ([string]::IsNullOrEmpty($parent) -or $parent -eq $cursor) {
            break
        }
        $cursor = $parent
    }
}

function Invoke-FrozenAcquisition {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TargetId,
        [Parameter(Mandatory = $true)]
        [string]$DownloadUrl,
        [Parameter(Mandatory = $true)]
        [string]$OutputPath,
        [Parameter(Mandatory = $true)]
        [int64]$ExpectedBytes,
        [Parameter(Mandatory = $true)]
        [string]$ExpectedMd5
    )

    if (Test-Path -LiteralPath $OutputPath) {
        throw "Frozen target '$TargetId' already exists; refusing overwrite, reuse, or resume."
    }

    $curlArguments = @(
        '--fail'
        '--location'
        '--silent'
        '--show-error'
        '--retry'
        '0'
        '--connect-timeout'
        '60'
        '--max-filesize'
        "$ExpectedBytes"
        '--output'
        $OutputPath
        '--url'
        $DownloadUrl
    )

    if ($curlArguments -contains '--write-out') {
        throw 'Ambiguous --write-out is forbidden.'
    }
    if ($curlArguments -contains '--continue-at') {
        throw 'Resume is not authorized.'
    }
    if ($curlArguments -contains '--range') {
        throw 'Byte-range acquisition is not authorized.'
    }

    & $curlPath @curlArguments
    $curlExitCode = $LASTEXITCODE
    if ($curlExitCode -ne 0) {
        throw "Target '$TargetId' curl attempt terminated with exit code $curlExitCode; no retry is authorized."
    }

    $actualBytes = [int64](Get-Item -LiteralPath $OutputPath).Length
    if ($actualBytes -ne $ExpectedBytes) {
        throw "Target '$TargetId' exact-size mismatch: expected $ExpectedBytes bytes, observed $actualBytes bytes."
    }

    $actualMd5 = (Get-FileHash -LiteralPath $OutputPath -Algorithm MD5).Hash.ToLowerInvariant()
    if ($actualMd5 -cne $ExpectedMd5) {
        throw "Target '$TargetId' MD5 mismatch after exact-size pass."
    }

    return [pscustomobject]@{
        target_id = $TargetId
        curl_exit_code = $curlExitCode
        expected_bytes = $ExpectedBytes
        actual_bytes = $actualBytes
        expected_md5 = $ExpectedMd5
        actual_md5 = $actualMd5
        exact_size_passed = $true
        md5_passed = $true
        verified = $true
        payload_opened_or_parsed = $false
        audit_started = $false
    }
}

if (-not (Test-Path -LiteralPath $contractPath -PathType Leaf)) {
    throw 'Frozen acquisition contract is unavailable.'
}
if (-not (Test-Path -LiteralPath $authorityPath -PathType Leaf)) {
    throw 'Frozen execution authority is unavailable.'
}
if (-not (Test-Path -LiteralPath $curlPath -PathType Leaf)) {
    throw 'Frozen curl executable is unavailable.'
}
if (-not (Test-Path -LiteralPath $powershellPath -PathType Leaf)) {
    throw 'Frozen Windows PowerShell executable is unavailable.'
}

$activationCandidatePath = if ([System.IO.Path]::IsPathRooted($ActivationJson)) {
    [System.IO.Path]::GetFullPath($ActivationJson)
}
else {
    [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot $ActivationJson))
}
if (-not [System.StringComparer]::OrdinalIgnoreCase.Equals($activationCandidatePath, [System.IO.Path]::GetFullPath($expectedActivationPath))) {
    throw 'Activation document path does not match the frozen future activation path.'
}
if (-not (Test-Path -LiteralPath $activationCandidatePath -PathType Leaf)) {
    throw 'The separately authorized activation document is absent.'
}

$actualContractSha256 = (Get-FileHash -LiteralPath $contractPath -Algorithm SHA256).Hash.ToLowerInvariant()
$actualAuthoritySha256 = (Get-FileHash -LiteralPath $authorityPath -Algorithm SHA256).Hash.ToLowerInvariant()
$actualLauncherSha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
$actualCurlSha256 = (Get-FileHash -LiteralPath $curlPath -Algorithm SHA256).Hash.ToLowerInvariant()
$actualPowerShellSha256 = (Get-FileHash -LiteralPath $powershellPath -Algorithm SHA256).Hash.ToLowerInvariant()

Assert-EqualString $actualContractSha256 $contractSha256 'Frozen acquisition-contract SHA-256 mismatch.'
Assert-EqualString $actualAuthoritySha256 $authoritySha256 'Frozen execution-authority SHA-256 mismatch.'
Assert-EqualString $actualCurlSha256 $curlSha256 'Frozen curl executable SHA-256 mismatch.'
Assert-EqualString $actualPowerShellSha256 $powershellSha256 'Frozen Windows PowerShell executable SHA-256 mismatch.'

$currentProcessPath = (Get-Process -Id $PID).Path
if (-not [System.StringComparer]::OrdinalIgnoreCase.Equals(
    [System.IO.Path]::GetFullPath($currentProcessPath),
    [System.IO.Path]::GetFullPath($powershellPath)
)) {
    throw 'Launcher is not running under the frozen Windows PowerShell executable.'
}

$activation = Get-Content -Raw -LiteralPath $activationCandidatePath | ConvertFrom-Json
Assert-EqualString $activation.status 'activated_dual_surface_initial_attempts_authorized' 'Activation status is not active.'
Assert-EqualString $activation.activation_id 'stgallen_dual_surface_initial_attempts_v0_1' 'Activation identifier mismatch.'
Assert-EqualString $activation.authority_chain.contract_sha256 $actualContractSha256 'Activation contract SHA-256 mismatch.'
Assert-EqualString $activation.authority_chain.execution_authority_sha256 $actualAuthoritySha256 'Activation execution-authority SHA-256 mismatch.'
Assert-EqualString $activation.authority_chain.launcher_sha256 $actualLauncherSha256 'Activation launcher SHA-256 mismatch.'
Assert-EqualString $activation.authority_chain.curl_sha256 $actualCurlSha256 'Activation curl SHA-256 mismatch.'
Assert-EqualString $activation.authority_chain.powershell_sha256 $actualPowerShellSha256 'Activation PowerShell SHA-256 mismatch.'

Assert-ExactTargetArray @($activation.target_activation.required_target_ids)
Assert-JsonInteger $activation.target_activation.maximum_initial_attempts_per_target 1 'Activation must authorize at most one initial attempt per target.'
Assert-JsonInteger $activation.target_activation.combined_maximum_initial_attempts 2 'Activation combined attempt ceiling must equal two.'

$attempts = @($activation.target_activation.attempts_authorized_now)
if ($attempts.Count -ne 2) {
    throw 'Activation must contain exactly two per-target attempt grants.'
}
if (
    $attempts[0].target_id -isnot [string] -or
    [string]$attempts[0].target_id -cne $manifestTargetId -or
    $attempts[0].initial_attempts -isnot [int] -or
    [int]$attempts[0].initial_attempts -ne 1 -or
    $attempts[1].target_id -isnot [string] -or
    [string]$attempts[1].target_id -cne $sensorTargetId -or
    $attempts[1].initial_attempts -isnot [int] -or
    [int]$attempts[1].initial_attempts -ne 1
) {
    throw 'Activation per-target attempt grants do not match the frozen atomic pair.'
}

Assert-JsonBoolean $activation.preflight_attestations.contract_authority_launcher_and_executable_hashes_rechecked $true 'Activation hash recheck attestation is false.'
Assert-JsonBoolean $activation.preflight_attestations.both_targets_absent $true 'Activation target-absence attestation is false.'
if (
    ($activation.preflight_attestations.available_bytes_at_least -isnot [int] -and
        $activation.preflight_attestations.available_bytes_at_least -isnot [long]) -or
    [int64]$activation.preflight_attestations.available_bytes_at_least -lt $minimumFreeBytes
) {
    throw 'Activation capacity attestation is below the frozen minimum.'
}
Assert-JsonInteger $activation.preflight_attestations.record_id $recordId 'Activation record identifier mismatch.'
Assert-JsonInteger $activation.preflight_attestations.record_revision $recordRevision 'Activation record revision mismatch.'
Assert-JsonBoolean $activation.preflight_attestations.record_revision_rechecked $true 'Activation record-revision recheck attestation is false.'
Assert-JsonBoolean $activation.preflight_attestations.payload_or_acquisition_network_request_performed_during_preflight $false 'Activation reports a payload or acquisition request during preflight.'

Assert-JsonBoolean $activation.permissions.network_request_authorized $true 'Activation does not authorize the frozen network requests.'
Assert-JsonBoolean $activation.permissions.download_authorized $true 'Activation does not authorize the frozen downloads.'
Assert-JsonBoolean $activation.permissions.automatic_retry_authorized $false 'Activation cannot authorize automatic retry.'
Assert-JsonBoolean $activation.permissions.resume_authorized $false 'Activation cannot authorize resume.'
Assert-JsonBoolean $activation.permissions.other_target_or_source_authorized $false 'Activation cannot authorize another target or source.'
Assert-JsonBoolean $activation.permissions.payload_open_read_or_parse_authorized $false 'Activation cannot authorize payload access.'
Assert-JsonBoolean $activation.permissions.audit_authorized $false 'Activation cannot authorize an audit.'

Assert-PathIsDirectChild $manifestTargetPath $protectedRoot 'Protected manifest target escaped its frozen isolated root.'
Assert-PathIsDirectChild $sensorTargetPath $modelCandidateRoot 'Sensor target escaped its frozen isolated root.'
$protectedRootFull = [System.IO.Path]::GetFullPath($protectedRoot).TrimEnd('\')
$modelCandidateRootFull = [System.IO.Path]::GetFullPath($modelCandidateRoot).TrimEnd('\')
if (
    [System.StringComparer]::OrdinalIgnoreCase.Equals($protectedRootFull, $modelCandidateRootFull) -or
    $protectedRootFull.StartsWith($modelCandidateRootFull + '\', [System.StringComparison]::OrdinalIgnoreCase) -or
    $modelCandidateRootFull.StartsWith($protectedRootFull + '\', [System.StringComparison]::OrdinalIgnoreCase)
) {
    throw 'Frozen protected and model-candidate roots are identical or nested.'
}

Assert-NoExistingReparsePoint $protectedRoot
Assert-NoExistingReparsePoint $modelCandidateRoot
if (Test-Path -LiteralPath $manifestTargetPath) {
    throw 'Protected manifest target already exists; refusing overwrite, reuse, or resume.'
}
if (Test-Path -LiteralPath $sensorTargetPath) {
    throw 'Sensor target already exists; refusing overwrite, reuse, or resume.'
}

$drive = [System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot($rawRoot))
$availableBytes = [int64]$drive.AvailableFreeSpace
if ($availableBytes -lt $minimumFreeBytes) {
    throw 'Insufficient free space for the frozen dual-surface acquisition.'
}

New-Item -ItemType Directory -Path $protectedRoot -Force | Out-Null
$manifestResult = Invoke-FrozenAcquisition `
    -TargetId $manifestTargetId `
    -DownloadUrl $manifestUrl `
    -OutputPath $manifestTargetPath `
    -ExpectedBytes $manifestExpectedBytes `
    -ExpectedMd5 $manifestExpectedMd5

New-Item -ItemType Directory -Path $modelCandidateRoot -Force | Out-Null
$sensorResult = Invoke-FrozenAcquisition `
    -TargetId $sensorTargetId `
    -DownloadUrl $sensorUrl `
    -OutputPath $sensorTargetPath `
    -ExpectedBytes $sensorExpectedBytes `
    -ExpectedMd5 $sensorExpectedMd5

$actualCombinedBytes = [int64]$manifestResult.actual_bytes + [int64]$sensorResult.actual_bytes
if ($actualCombinedBytes -ne $combinedExpectedBytes) {
    throw 'Combined exact-size invariant failed after both per-target identity checks.'
}

[pscustomobject]@{
    target_set_id = 'stgallen_dual_surface_identity_pair_v0_1'
    required_target_ids = @($manifestTargetId, $sensorTargetId)
    target_count = 2
    combined_expected_bytes = $combinedExpectedBytes
    combined_actual_bytes = $actualCombinedBytes
    protected_manifest_verified = [bool]$manifestResult.verified
    sensor_surface_verified = [bool]$sensorResult.verified
    dual_surface_verified = $true
    payload_opened_or_parsed = $false
    audit_started = $false
    source_role_changed = $false
    quota_credit_awarded = 0
    hard_stop_required = $true
} | ConvertTo-Json -Compress
