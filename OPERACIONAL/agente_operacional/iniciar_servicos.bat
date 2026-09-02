@echo off
chcp 1252 >nul
setlocal

REM =============================================================
REM  AUTO-START: Agente Operacional (CORBELINO.IA) + n8n
REM  Executado automaticamente no logon (Task Scheduler)
REM =============================================================

set "PROJETO=%~dp0..\.."
set "LOGDIR=%~dp0logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

REM --- 1. AGENTE OPERACIONAL (FastAPI porta 8787) ---
REM Sobe em janela oculta, log em agente_stdout.log
powershell -NoProfile -WindowStyle Hidden -Command ^
  "Start-Process -FilePath 'python' ^
   -ArgumentList '-m','uvicorn','OPERACIONAL.agente_operacional.webhook:app','--host','0.0.0.0','--port','8787' ^
   -WorkingDirectory '%PROJETO%' ^
   -WindowStyle Hidden ^
   -RedirectStandardOutput '%LOGDIR%\agente_stdout.log' ^
   -RedirectStandardError '%LOGDIR%\agente_stderr.log'"

REM --- 2. N8N (porta 5678) ---
REM Sobe em janela oculta, log em n8n_stdout.log
powershell -NoProfile -WindowStyle Hidden -Command ^
  "Start-Process -FilePath '%APPDATA%\npm\n8n.cmd' ^
   -ArgumentList 'start' ^
   -WindowStyle Hidden ^
   -RedirectStandardOutput '%LOGDIR%\n8n_stdout.log' ^
   -RedirectStandardError '%LOGDIR%\n8n_stderr.log'"

endlocal
exit /b 0
