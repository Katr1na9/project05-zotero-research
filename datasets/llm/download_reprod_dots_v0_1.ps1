[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedBytes = 10928971753
$expectedMd5 = 'd9e3f24ba36a9b9503a55eb1cf677345'
$downloadUrl = 'https://zenodo.org/api/records/8123115/files/dots.zip/content'
$curlPath = 'C:\WINDOWS\system32\curl.exe'
$rawRoot = Join-Path $PSScriptRoot 'local_audit_cache\reprod-bounded-v0.1\raw'
$targetPath = Join-Path $rawRoot 'dots.zip'

if (-not (Test-Path -LiteralPath $curlPath)) {
    throw "Frozen curl executable is unavailable: $curlPath"
}

if (Test-Path -LiteralPath $targetPath) {
    throw "Frozen target already exists; refusing a second acquisition attempt: $targetPath"
}

$drive = [System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot($targetPath))
if ($drive.AvailableFreeSpace -le $expectedBytes) {
    throw "Insufficient free space for the frozen target and hard ceiling."
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
    throw "MD5 mismatch after exact-size pass."
}

[pscustomobject]@{
    target_id = 'reprod_dots_derived_provenance_archive'
    target = $targetPath
    curl_exit_code = $curlExitCode
    expected_bytes = $expectedBytes
    actual_bytes = $actualBytes
    expected_md5 = $expectedMd5
    actual_md5 = $actualMd5
    exact_size_passed = $true
    md5_passed = $true
    verified = $true
    archive_opened = $false
} | ConvertTo-Json -Compress
