#!/bin/bash
# =============================================================
#  VERIFICACAO DOS SERVICOS (macOS/Linux) - AGENTE OPERACIONAL (CORBELINO.IA)
#  Equivalente ao verificar_servicos.bat (Windows).
# =============================================================

echo ""
echo "============================================================"
echo "  VERIFICACAO DOS SERVICOS - AGENTE OPERACIONAL (CORBELINO.IA)"
echo "  $(date)"
echo "============================================================"
echo ""

echo "[1/4] AGENTE OPERACIONAL (porta 8787)..."
if curl -s -m 3 http://localhost:8787/healthcheck > /tmp/_corbelino_advogados_health.json 2>/dev/null; then
  echo "      OK    -> $(cat /tmp/_corbelino_advogados_health.json)"
else
  echo "      FALHA -> agente nao responde em http://localhost:8787"
fi
echo ""

echo "[2/4] N8N (porta 5678)..."
if curl -s -o /dev/null -m 3 -w "%{http_code}" http://localhost:5678 | grep -q "200"; then
  echo "      OK    -> n8n respondendo (HTTP 200)"
else
  echo "      FALHA -> n8n nao responde em http://localhost:5678"
fi
echo ""

echo "[3/4] PROCESSOS..."
pgrep -f "uvicorn OPERACIONAL.agente_operacional.webhook:app" > /dev/null \
  && echo "      OK    -> Agente (uvicorn) rodando" \
  || echo "      FALHA -> Agente (uvicorn) nao esta rodando"
pgrep -f "n8n start" > /dev/null \
  && echo "      OK    -> n8n rodando" \
  || echo "      FALHA -> n8n nao esta rodando"
echo ""

echo "[4/4] ULTIMAS 10 LINHAS DO LOG DO AGENTE..."
echo "------------------------------------------------------------"
LOGDIR="$(dirname "${BASH_SOURCE[0]}")/logs"
LATEST=$(ls -t "$LOGDIR"/agente_*.log 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
  tail -10 "$LATEST"
else
  echo "      (sem logs ainda)"
fi
echo "------------------------------------------------------------"
echo ""

echo "URLs UTEIS:"
echo "  Agente Healthcheck : http://localhost:8787/healthcheck"
echo "  n8n Editor         : http://localhost:5678"
echo ""
echo "============================================================"
