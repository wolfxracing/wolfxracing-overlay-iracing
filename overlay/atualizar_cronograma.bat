@echo off
chcp 65001 >nul
rem Converte o PDF "Season Schedule" do iRacing em cronograma.json (usado pelo aviso de corridas).
rem Uso: arraste o PDF para este arquivo, ou:  atualizar_cronograma.bat "C:\caminho\SeasonSchedule.pdf"
cd /d "%~dp0"
if "%~1"=="" (echo Arraste o PDF SeasonSchedule para este arquivo. & pause & exit /b 1)
py -3.12 -m pip install --quiet pypdf
py -3.12 importar_cronograma.py "%~1" cronograma.json
echo.
echo Pronto. Reinicie o overlay (ou aguarde ate 20 s) para usar o novo cronograma.
pause
