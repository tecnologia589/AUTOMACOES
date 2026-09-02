#!/bin/bash
# Sincronizacao ZapSign -> Drive (Corbelino Advogados Associados)
# Equivalente ao sync_assinados.bat (Windows), para macOS/Linux.
# Agendar via cron ou launchd (3x ao dia) - ver docs/ONBOARDING.md.
PROJETO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJETO"
python3 "$PROJETO/SYNC/sync_assinados.py"
