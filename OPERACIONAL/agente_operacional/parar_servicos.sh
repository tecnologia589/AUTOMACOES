#!/bin/bash
# =============================================================
#  PARAR servicos (macOS/Linux): Agente Operacional (CORBELINO.IA) + n8n
#  Equivalente ao parar_servicos.bat (Windows).
# =============================================================

echo "Parando Agente Operacional (uvicorn)..."
pkill -f "uvicorn OPERACIONAL.agente_operacional.webhook:app" 2>/dev/null || true

echo "Parando n8n..."
pkill -f "n8n start" 2>/dev/null || true

echo ""
echo "Servicos parados."
