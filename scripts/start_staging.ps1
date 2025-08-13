# Script PowerShell para staging
Write-Host "🚀 Iniciando ambiente de STAGING..." -ForegroundColor Yellow
$env:FLASK_ENV="staging"
python app.py