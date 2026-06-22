Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (Test-Path ".env") {
    Write-Host ".env already exists. Leaving it unchanged."
    exit 0
}

Copy-Item ".env.example" ".env"
Write-Host "Created .env from .env.example. Add your Microsoft tenant, client, secret, and sender email."
