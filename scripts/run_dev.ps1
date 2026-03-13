<#
Mini README:
Windows PowerShell helper script for local development startup.
#>
param([int]$Port = 8000)
uvicorn app.main:app --host 0.0.0.0 --port $Port --reload
