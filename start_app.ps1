# PowerShell script to start FoodLink Connect
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

Write-Host "Starting FoodLink Connect..." -ForegroundColor Green
$env:PYTHONIOENCODING = 'utf-8'
python run.py

