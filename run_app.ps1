Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting EvoVariant-TR Next.js Platform on port 3000..." -ForegroundColor Green
Write-Host "Connecting to Modal H100 Cloud GPU (Evo 2 7B)..." -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

Set-Location "$PSScriptRoot\apps\web"
Start-Process "http://localhost:3000"
node ./node_modules/next/dist/bin/next dev -p 3000
