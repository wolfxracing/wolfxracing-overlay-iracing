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
echo.
echo TODOS OS TESTES PASSARAM.
goto fim
:falhou
echo.
echo ALGUM TESTE FALHOU - envie esta tela ao Claude.
:fim
pause
