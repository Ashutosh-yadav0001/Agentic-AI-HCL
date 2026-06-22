Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
.\.venv\Scripts\python.exe -m uvicorn bgv_app.main:app --reload
