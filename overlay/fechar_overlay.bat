@echo off
rem Fecha o overlay a forca (use se o overlay travar ou se o atalho do Stream Deck nao responder).
rem Encerra SOMENTE processos cujo comando contem overlay_iracing.py; nao mexe no iRacing nem em outros Python.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$n=0; Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*overlay_iracing.py*' -and $_.Name -match '^(pythonw?|pyw?)\.exe$' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; $n++ }; if ($n -gt 0) { Write-Host 'Overlay encerrado.' } else { Write-Host 'O overlay nao estava em execucao.' }"
timeout /t 2 >nul
