[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ActivationJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$targetId = 'toyota_hsr_place_action_validation_archive'
$recordId = [int64]4578539
$recordRevision = [int64]3
$expectedBytes = [int64]365983836
$minimumFreeBytes = [int64]365983837
$expectedMd5 = '76cb0cab741c3a55eaf662df979f4637'
$downloadUrl = 'https://zenodo.org/api/records/4578539/files/place_action_validation.tar.gz/content'
$contractSha256 = '90e746c609bd60aeff2a85a48c925c6fc46b54dd55de506e4e806bfd1f58547b'
$authoritySha256 = '5552f0c7d2abda7d91a1b196a37a5bfdde99ad90098e128794e840032b7dca95'
$curlSha256 = '73d24149ff289afc49ec41f08918ef9faa727d39ad993e929757dc2ddafab805'
$powershellSha256 = '7600ffe12da441fe89d035b13801e8e91d064bc544a27b19a5cf49f6ab8b18f5'

$curlPath = 'C:\WINDOWS\system32\curl.exe'
$powershellPath = 'C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe'
$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$contractPath = Join-Path $repositoryRoot 'docs\llm-editor\llm-editor-v0.8-l2-toyota-hsr-validation-exact-bounded-acquisition-contract-v0.1-20260724.json'
$authorityPath = Join-Path $repositoryRoot 'docs\llm-editor\llm-editor-v0.8-l2-toyota-hsr-validation-acquisition-execution-authority-v0.1-20260724.json'
$expectedActivationPath = Join-Path $repositoryRoot 'docs\llm-editor\llm-editor-v0.8-l2-toyota-hsr-validation-acquisition-activation-v0.1-20260724.json'
$rawRoot = Join-Path $PSScriptRoot 'local_audit_cache\toyota-hsr-placement-bounded-v0.1\raw'
$targetPath = Join-Path $rawRoot 'place_action_validation.tar.gz'

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

function Assert-PathIsDirectChild {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ChildPath,
        [Parameter(Mandatory = $true)]
        [string]$ParentPath
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
        throw 'Frozen target escaped its isolated raw root.'
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
if (-not [System.StringComparer]::OrdinalIgnoreCase.Equals(
    $activationCandidatePath,
    [System.IO.Path]::GetFullPath($expectedActivationPath)
)) {
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
Assert-EqualString $activation.status 'activated_single_initial_attempt_authorized' 'Activation status is not active.'
Assert-EqualString $activation.activation_id 'toyota_hsr_validation_initial_attempt_v0_1' 'Activation identifier mismatch.'
Assert-EqualString $activation.authority_chain.contract_sha256 $actualContractSha256 'Activation contract SHA-256 mismatch.'
Assert-EqualString $activation.authority_chain.execution_authority_sha256 $actualAuthoritySha256 'Activation execution-authority SHA-256 mismatch.'
Assert-EqualString $activation.authority_chain.launcher_sha256 $actualLauncherSha256 'Activation launcher SHA-256 mismatch.'
Assert-EqualString $activation.authority_chain.curl_sha256 $actualCurlSha256 'Activation curl SHA-256 mismatch.'
Assert-EqualString $activation.authority_chain.powershell_sha256 $actualPowerShellSha256 'Activation PowerShell SHA-256 mismatch.'

Assert-EqualString $activation.target_activation.target_id $targetId 'Activation target identifier mismatch.'
Assert-JsonInteger $activation.target_activation.maximum_initial_attempts 1 'Activation maximum initial attempt count must equal one.'
Assert-JsonInteger $activation.target_activation.initial_attempts_authorized_now 1 'Activation must authorize exactly one initial attempt.'

Assert-JsonBoolean $activation.preflight_attestations.contract_authority_launcher_and_executable_hashes_rechecked $true 'Activation hash recheck attestation is false.'
Assert-JsonBoolean $activation.preflight_attestations.target_absent $true 'Activation target-absence attestation is false.'
if (
    ($activation.preflight_attestations.available_bytes -isnot [int] -and
        $activation.preflight_attestations.available_bytes -isnot [long]) -or
    [int64]$activation.preflight_attestations.available_bytes -lt $minimumFreeBytes
) {
    throw 'Activation capacity attestation is below the frozen minimum.'
}
Assert-JsonInteger $activation.preflight_attestations.record_id $recordId 'Activation record identifier mismatch.'
Assert-JsonInteger $activation.preflight_attestations.record_revision $recordRevision 'Activation record revision mismatch.'
Assert-JsonBoolean $activation.preflight_attestations.record_revision_rechecked $true 'Activation record-revision recheck attestation is false.'
Assert-JsonBoolean $activation.preflight_attestations.network_request_performed_during_preflight $false 'Activation reports a network request during preflight.'

Assert-JsonBoolean $activation.permissions.network_request_authorized $true 'Activation does not authorize the frozen network request.'
Assert-JsonBoolean $activation.permissions.download_authorized $true 'Activation does not authorize the frozen download.'
Assert-JsonBoolean $activation.permissions.automatic_retry_authorized $false 'Activation cannot authorize automatic retry.'
Assert-JsonBoolean $activation.permissions.resume_authorized $false 'Activation cannot authorize resume.'
Assert-JsonBoolean $activation.permissions.other_target_source_revision_mirror_range_or_slice_authorized $false 'Activation cannot authorize another object or retrieval surface.'
Assert-JsonBoolean $activation.permissions.payload_open_read_or_parse_authorized $false 'Activation cannot authorize payload access.'
Assert-JsonBoolean $activation.permissions.audit_authorized $false 'Activation cannot authorize an audit.'

Assert-PathIsDirectChild $targetPath $rawRoot
Assert-NoExistingReparsePoint $rawRoot
if (Test-Path -LiteralPath $targetPath) {
    throw 'Frozen target already exists; refusing overwrite, reuse, retry, or resume.'
}

$drive = [System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot($rawRoot))
$availableBytes = [int64]$drive.AvailableFreeSpace
if ($availableBytes -lt $minimumFreeBytes) {
    throw 'Insufficient free space for the frozen target and hard ceiling.'
}

New-Item -ItemType Directory -Path $rawRoot -Force | Out-Null

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
    "$expectedBytes"
    '--output'
    $targetPath
    '--url'
    $downloadUrl
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
    throw "Target '$targetId' curl attempt terminated with exit code $curlExitCode; no retry is authorized."
}

$actualBytes = [int64](Get-Item -LiteralPath $targetPath).Length
if ($actualBytes -ne $expectedBytes) {
    throw "Target '$targetId' exact-size mismatch: expected $expectedBytes bytes, observed $actualBytes bytes."
}

$actualMd5 = (Get-FileHash -LiteralPath $targetPath -Algorithm MD5).Hash.ToLowerInvariant()
if ($actualMd5 -cne $expectedMd5) {
    throw "Target '$targetId' MD5 mismatch after exact-size pass."
}

[pscustomobject]@{
    target_id = $targetId
    curl_exit_code = $curlExitCode
    expected_bytes = $expectedBytes
    actual_bytes = $actualBytes
    expected_md5 = $expectedMd5
    actual_md5 = $actualMd5
    exact_size_passed = $true
    md5_passed = $true
    verified = $true
    gzip_or_tar_opened = $false
    archive_member_listed_or_read = $false
    audit_started = $false
    source_role_changed = $false
    quota_credit_awarded = 0
    hard_stop_required = $true
} | ConvertTo-Json -Compress
