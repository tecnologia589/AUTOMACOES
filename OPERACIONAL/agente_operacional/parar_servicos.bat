@echo off
chcp 1252 >nul
setlocal

REM =============================================================
REM  PARAR servicos (Agente Operacional CORBELINO.IA + n8n)
REM =============================================================

echo Parando Agente Operacional (python/uvicorn)...
taskkill /F /IM python.exe 2>nul

echo Parando n8n (node)...
taskkill /F /IM node.exe 2>nul

echo.
echo Servicos parados.
timeout /t 2 >nul
endlocal
exit /b 0
