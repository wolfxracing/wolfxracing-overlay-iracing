@echo off
title Desativar inicio automatico - Overlay iRacing
cd /d "%~dp0"
py -3.12 overlay_iracing.py --desativar-inicio
echo.
pause
