[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$targetId = 'lo2v2_index_json'
$expectedBytes = 31028530
$expectedMd5 = '2efcff67820ba1df40fae362919271eb'
$downloadUrl = 'https://zenodo.org/api/records/18937117/files/LO2v2_index.json/content'
$curlPath = 'C:\WINDOWS\system32\curl.exe'
$rawRoot = Join-Path $PSScriptRoot 'local_audit_cache\lo2v2-bounded-v0.1\raw'
$targetPath = Join-Path $rawRoot 'LO2v2_index.json'

if (-not (Test-Path -LiteralPath $curlPath)) {
    throw 'Frozen curl executable is unavailable.'
}

if (Test-Path -LiteralPath $targetPath) {
    throw 'Frozen target already exists; refusing another acquisition attempt.'
}

$drive = [System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot($targetPath))
if ($drive.AvailableFreeSpace -le $expectedBytes) {
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
    throw "curl terminated with exit code $curlExitCode; no retry is authorized."
}

$actualBytes = (Get-Item -LiteralPath $targetPath).Length
if ($actualBytes -ne $expectedBytes) {
    throw "Exact size mismatch: expected $expectedBytes bytes, observed $actualBytes bytes."
}

$actualMd5 = (Get-FileHash -LiteralPath $targetPath -Algorithm MD5).Hash.ToLowerInvariant()
if ($actualMd5 -cne $expectedMd5) {
    throw 'MD5 mismatch after exact-size pass.'
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
    json_opened = $false
    json_parsed = $false
    audit_started = $false
} | ConvertTo-Json -Compress
