"""Constantes e configuracao do Agente Operacional - Corbelino Advogados Associados.

Nenhum ID/credencial vem hardcoded: tudo e lido de config/.env (ou config/equipe.py).
O escritorio preenche os valores DELE no onboarding.
"""
import json
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / 'config' / '.env')

# Permite ler os papeis funcionais (RESPONSAVEL/OPERACIONAL/FINANCEIRO) de config/equipe.py
try:
    import sys
    sys.path.insert(0, str(ROOT / 'config'))
    from equipe import id_usuario  # noqa
except Exception:  # pragma: no cover - fallback se equipe.py ainda nao existir
    def id_usuario(papel):
        return None


def _env_int(nome, default=None):
    valor = os.getenv(nome)
    if valor in (None, ''):
        return default
    try:
        return int(valor)
    except (TypeError, ValueError):
        return default


# ============================================================
# ADVBOX
# ============================================================
# ID do usuario-agente (CORBELINO.IA) no ADVBOX - a conta a quem as tarefas sao atribuidas.
AGENTE_IA_ID = _env_int('ADVBOX_USER_AGENTE')

# Papel funcional que recebe os retornos quando a tarefa so tem o agente como destinatario.
# (fallback de co-destinatarios). Lido de config/equipe.py.
OPERACIONAL_ID = id_usuario('OPERACIONAL')
RESPONSAVEL_ID = id_usuario('RESPONSAVEL')

# Tipo de tarefa (settings['tasks'] do ADVBOX) para os retornos do agente.
TASK_TYPE_ACOMPANHAMENTO = _env_int('ADVBOX_TASK_TYPE_ACOMPANHAMENTO')

# Marcador maquina-legivel inserido no comentario de retorno quando o agente conclui
# uma tarefa COM SUCESSO. E a base da idempotencia via ADVBOX: antes de (re)executar
# uma tarefa, o agente varre os andamentos do processo e, se achar este marcador
# referenciando a tarefa original (ex: "[CORBELINOIA-FEITO #12345]"), NAO refaz o trabalho.
# Como a API ADVBOX nao permite concluir tarefa via /posts, este marcador no processo
# e a fonte da verdade (sobrevive a restart/troca de maquina).
MARCADOR_CONCLUSAO = 'CORBELINOIA-FEITO'

# Telefones internos (por user_id ADVBOX) - usados para notificar via WhatsApp quando
# o agente termina uma tarefa (resolve "tarefa fantasma" no ADVBOX). Configuravel via
# AGENTE_OP_USER_PHONES no .env (JSON {"<user_id>": "<telefone>"}). Vazio = nenhum.
def _carregar_user_phones():
    raw = os.getenv('AGENTE_OP_USER_PHONES', '').strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return {int(k): str(v) for k, v in data.items()}
    except Exception:
        return {}


USER_PHONES = _carregar_user_phones()

# Liga/desliga notificacao WhatsApp ao concluir tarefa
NOTIFICAR_WHATSAPP = os.getenv('AGENTE_OP_NOTIFICAR_WHATSAPP', '1') != '0'

# ============================================================
# CLAUDE / LLM
# ============================================================
LLM_MODEL_PECA = 'claude-opus-4-6'      # Pecas juridicas (regra do escritorio)
LLM_MODEL_TRIAGEM = 'claude-sonnet-4-6' # Triagem de tipo / mensagens curtas
LLM_MAX_TOKENS = 16000
LLM_THINKING_BUDGET = 10000

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# ============================================================
# WEBHOOK
# ============================================================
AGENTE_OP_TOKEN = os.getenv('AGENTE_OP_TOKEN', '')
AGENTE_OP_PORT = int(os.getenv('AGENTE_OP_PORT', '8787'))

# ============================================================
# ESCRITORIO / FORMATACAO
# ============================================================
ESCRITORIO_NOME = os.getenv('ESCRITORIO_NOME', 'Corbelino Advogados Associados')
ESCRITORIO_CIDADE = os.getenv('ESCRITORIO_CIDADE', 'Cáceres/MT e Pontes Lacerda/MT')
# Assinatura padrao das pecas geradas (previdenciario - Dr. Paulo Alexandre).
ESCRITORIO_ASSINATURA = os.getenv(
    'ESCRITORIO_ASSINATURA',
    'Dr. Paulo Alexandre Soares Corbelino - OAB/MT 33.267 - Cáceres/MT',
)
# E-mail do advogado responsavel (signatario padrao no ZapSign).
ESCRITORIO_EMAIL_RESPONSAVEL = os.getenv('ESCRITORIO_EMAIL_RESPONSAVEL', '')

# Timbrado: o escritorio fornece o timbrado DELE em config/timbrado_modelo.docx.
TIMBRADO_PATH = ROOT / 'config' / 'timbrado_modelo.docx'

# ============================================================
# DRIVE
# ============================================================
# Nao precisa de pasta de saida fixa: pecas vao direto para 'ATOS INTERNOS'
# dentro da pasta do cliente (localizada via Drive search).

# ============================================================
# PATHS LOCAIS
# ============================================================
LOG_DIR = ROOT / 'OPERACIONAL' / 'agente_operacional' / 'logs'
LOG_DIR.mkdir(exist_ok=True)

POPS_CACHE = ROOT / 'OPERACIONAL' / 'agente_operacional' / 'pops_cache'
POPS_CACHE.mkdir(exist_ok=True)
