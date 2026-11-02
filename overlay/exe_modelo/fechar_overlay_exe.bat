@echo off
rem Fecha o overlay (versao EXE) a forca. Nao mexe no iRacing nem em outros programas.
taskkill /IM WolfxRacing_iRacing.exe /F >nul 2>nul
if errorlevel 1 (echo O overlay nao estava em execucao.) else (echo Overlay encerrado.)
timeout /t 2 >nul
