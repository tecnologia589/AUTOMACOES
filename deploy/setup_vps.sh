#!/usr/bin/env bash
# =============================================================================
#  setup_vps.sh - Provisionamento da VPS (Ubuntu 22.04/24.04) p/ CORBELINO.IA
#  Roda UMA vez, como o usuario de deploy (com sudo). Idempotente.
# =============================================================================
set -euo pipefail

PROJ_DIR="${1:-$HOME/corbelino-advogados}"

echo ">> 1/5 Atualizando sistema e instalando dependencias de SO..."
sudo apt-get update -y
sudo apt-get install -y \
  python3 python3-venv python3-pip git \
  tesseract-ocr tesseract-ocr-por \
  libgl1 libglib2.0-0

echo ">> 2/5 Criando virtualenv em $PROJ_DIR/.venv ..."
cd "$PROJ_DIR"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip wheel

echo ">> 3/5 Instalando dependencias Python (requirements.txt)..."
pip install -r requirements.txt

echo ">> 4/5 Instalando Chromium do Playwright (+ libs de SO)..."
python -m playwright install --with-deps chromium

echo ">> 5/5 Verificando config/.env ..."
if [ ! -f config/.env ]; then
  echo "   ATENCAO: config/.env NAO existe. Copie via scp a partir da maquina local"
  echo "   (junto com credentials.json, oauth_credentials.json, token.json,"
  echo "    config/timbrado_modelo.docx). Veja docs/DEPLOY_VPS.md (Fase 5)."
else
  echo "   OK: config/.env encontrado."
fi

echo ""
echo ">> Provisionamento concluido. Proximo passo: instalar o servico systemd"
echo "   (docs/DEPLOY_VPS.md - Fase 6)."
