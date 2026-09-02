#!/bin/bash
# =============================================================
#  AUTO-START (macOS/Linux): Agente Operacional (CORBELINO.IA) + n8n
#  Equivalente ao iniciar_servicos.bat (Windows). Agendar via
#  launchd (macOS) ou cron/systemd (Linux) - ver docs/ONBOARDING.md.
# =============================================================
set -e

PROJETO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOGDIR="$(dirname "${BASH_SOURCE[0]}")/logs"
mkdir -p "$LOGDIR"

# --- 1. AGENTE OPERACIONAL (FastAPI porta 8787) ---
cd "$PROJETO"
nohup python3 -m uvicorn OPERACIONAL.agente_operacional.webhook:app \
  --host 0.0.0.0 --port 8787 \
  >> "$LOGDIR/agente_stdout.log" 2>> "$LOGDIR/agente_stderr.log" &
echo "Agente Operacional iniciado (PID $!)"

# --- 2. N8N (porta 5678) ---
nohup n8n start \
  >> "$LOGDIR/n8n_stdout.log" 2>> "$LOGDIR/n8n_stderr.log" &
echo "n8n iniciado (PID $!)"
