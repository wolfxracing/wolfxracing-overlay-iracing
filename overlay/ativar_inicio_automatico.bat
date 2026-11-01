@echo off
title Ativar inicio automatico - Overlay iRacing
cd /d "%~dp0"
echo Configurando o overlay para abrir junto com o Windows...
py -3.12 overlay_iracing.py --ativar-inicio
echo.
echo Pronto. As janelas vao aparecer sozinhas quando voce entrar no carro no iRacing.
echo (Lembre-se de marcar "Travar posicao" no icone da bandeja para o modo automatico funcionar.)
pause
