@echo off
cd /d "%~dp0"
echo Rodando os testes automaticos (nao precisa do iRacing)...
py -3.12 testes\teste_fase20.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_fase201.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_fase202.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_fase2021.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_fase2022.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_classif_foto.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_marcas.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_v163.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_v170.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_v170_import.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_v170_previas.py
py -3.12 testes\teste_v170_elementos.py
py -3.12 testes\teste_v170_central_real.py
py -3.12 testes\teste_v170_estados_vazios.py
py -3.12 testes\teste_v170_coach_ciclo_real.py
py -3.12 testes\teste_v170_ritmo_ideal.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_v170_coach_real.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_v170_ritmo_voz.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_v170_backup.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_v170_amigos.py
if errorlevel 1 goto falhou
py -3.12 testes\teste_v170_ibt.py
if errorlevel 1 goto falhou
echo.
echo TODOS OS TESTES PASSARAM.
goto fim
:falhou
echo.
echo ALGUM TESTE FALHOU - envie esta tela ao Claude.
:fim
pause
