$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$example = Join-Path $root '.env.production.example'
$target = Join-Path $root '.env.production'
$content = Get-Content -LiteralPath $example
$content = $content -replace '^ORVILLE_DOMAIN=.*$', 'ORVILLE_DOMAIN=localhost'
$content = $content -replace '^ORVILLE_ALLOWED_ORIGINS=.*$', 'ORVILLE_ALLOWED_ORIGINS=http://localhost'
$content = $content | Where-Object { $_ -notmatch '^ORVILLE_API_TOKEN=' }
$bytes = New-Object byte[] 48
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$rng.Dispose()
$token = [Convert]::ToBase64String($bytes)
Set-Content -LiteralPath $target -Value ($content + "ORVILLE_API_TOKEN=$token") -Encoding utf8
Write-Output 'Created .env.production for local deployment.'
