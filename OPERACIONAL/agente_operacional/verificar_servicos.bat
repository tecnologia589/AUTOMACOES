@echo off
chcp 1252 >nul
setlocal

echo.
echo ============================================================
echo   VERIFICACAO DOS SERVICOS - AGENTE OPERACIONAL (CORBELINO.IA)
echo   %DATE% %TIME%
echo ============================================================
echo.

echo [1/4] AGENTE OPERACIONAL (porta 8787)...
powershell -NoProfile -Command "try { $r = Invoke-RestMethod -Uri 'http://localhost:8787/healthcheck' -TimeoutSec 3; Write-Host ('      OK    -> ' + $r.servico + ' status=' + $r.status) -ForegroundColor Green } catch { Write-Host '      FALHA -> agente nao responde em http://localhost:8787' -ForegroundColor Red }"
echo.

echo [2/4] N8N (porta 5678)...
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:5678' -TimeoutSec 3 -UseBasicParsing; if ($r.StatusCode -eq 200) { Write-Host '      OK    -> n8n respondendo (HTTP 200)' -ForegroundColor Green } else { Write-Host ('      AVISO -> HTTP ' + $r.StatusCode) -ForegroundColor Yellow } } catch { Write-Host '      FALHA -> n8n nao responde em http://localhost:5678' -ForegroundColor Red }"
echo.

echo [3/4] PROCESSOS PYTHON e NODE...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | findstr /I "python.exe" >nul && echo       OK    -^> Python rodando || echo       FALHA -^> Python nao esta rodando
tasklist /FI "IMAGENAME eq node.exe" 2>nul | findstr /I "node.exe" >nul && echo       OK    -^> Node rodando || echo       FALHA -^> Node nao esta rodando
echo.

echo [4/4] ULTIMAS 10 LINHAS DO LOG DO AGENTE...
echo ------------------------------------------------------------
powershell -NoProfile -Command "$log = Get-ChildItem '%~dp0logs\agente_*.log' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if ($log) { Get-Content $log.FullName -Tail 10 } else { Write-Host '      (sem logs ainda)' -ForegroundColor Gray }"
echo ------------------------------------------------------------
echo.

echo URLs UTEIS:
echo   Agente Healthcheck : http://localhost:8787/healthcheck
echo   n8n Editor         : http://localhost:5678
echo.
echo ============================================================
pause
