@echo off
setlocal
cd /d "%~dp0"
title Gerar EXE - Overlay iRacing
echo ============================================================
echo  GERAR A VERSAO EXE (sem precisar de Python) - Overlay iRacing
echo  Roda uma vez neste computador e leva uns 3 a 6 minutos.
echo ============================================================
where py >nul 2>nul
if errorlevel 1 goto sempython
py -3.12 --version >nul 2>nul
if errorlevel 1 goto semversao
echo.
echo [1/5] Instalando os componentes de compilacao...
py -3.12 -m pip install --upgrade pip
py -3.12 -m pip install --only-binary=:all: pyirsdk PySide6-Essentials pyinstaller
if errorlevel 1 goto erro
echo.
echo [2/5] Conferindo o programa (teste automatico)...
py -3.12 testes\teste_classif_foto.py
if errorlevel 1 goto erro
echo.
echo [3/5] Gerando o EXE...
if exist "exe\WolfxRacing_iRacing" rmdir /S /Q "exe\WolfxRacing_iRacing"
py -3.12 -m PyInstaller --noconfirm --clean --distpath exe --workpath exe\_build wolfx_iracing.spec
if errorlevel 1 goto erro
set "DEST=exe\WolfxRacing_iRacing"
echo.
echo [4/5] Copiando as pastas e arquivos que ficam ao lado do EXE...
if exist "marca" xcopy /E /I /Y /Q "marca" "%DEST%\marca" >nul
if exist "emblemas" xcopy /E /I /Y /Q "emblemas" "%DEST%\emblemas" >nul
if exist "bandeiras" xcopy /E /I /Y /Q "bandeiras" "%DEST%\bandeiras" >nul
if exist "config.json" if not exist "%DEST%\config.json" copy /Y "config.json" "%DEST%\config.json" >nul
if exist "mapas_pistas.json" if not exist "%DEST%\mapas_pistas.json" copy /Y "mapas_pistas.json" "%DEST%\mapas_pistas.json" >nul
if exist "recordes_pessoais.json" if not exist "%DEST%\recordes_pessoais.json" copy /Y "recordes_pessoais.json" "%DEST%\recordes_pessoais.json" >nul
if exist "calibracao_pneus.json" if not exist "%DEST%\calibracao_pneus.json" copy /Y "calibracao_pneus.json" "%DEST%\calibracao_pneus.json" >nul
if exist "pit_entradas.json" if not exist "%DEST%\pit_entradas.json" copy /Y "pit_entradas.json" "%DEST%\pit_entradas.json" >nul
if exist "historico_projecoes.csv" if not exist "%DEST%\historico_projecoes.csv" copy /Y "historico_projecoes.csv" "%DEST%\historico_projecoes.csv" >nul
copy /Y "exe_modelo\*" "%DEST%\" >nul
echo.
echo [5/5] Compactando (para levar para outro computador)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%DEST%' -DestinationPath 'exe\WolfxRacing_iRacing.zip' -Force"
if exist "exe\_build" rmdir /S /Q "exe\_build"
echo.
echo ============================================================
echo  PRONTO!  Programa:  %CD%\%DEST%\WolfxRacing_iRacing.exe
echo           Para outro PC: %CD%\exe\WolfxRacing_iRacing.zip
echo  Leia o arquivo LEIA-ME_EXE.txt dentro da pasta do programa.
echo ============================================================
pause
exit /b 0
:sempython
echo Python nao encontrado. Este passo (so para GERAR o EXE) precisa do Python 3.12 instalado neste computador.
echo Depois de gerado, o EXE roda em qualquer PC Windows sem Python.
pause
exit /b 1
:semversao
echo Python 3.12 nao encontrado. Abra o Prompt de Comando, digite:  py install 3.12  e execute este arquivo novamente.
pause
exit /b 1
:erro
echo.
echo Ocorreu um erro. Tire um print desta tela e envie para o Claude.
pause
exit /b 1
