"""
Equipe / usuarios do escritorio - Corbelino Advogados Associados.

Centraliza os IDs de usuario do ADVBOX e os papeis funcionais.
NUNCA hardcode IDs no codigo das automacoes: leia sempre deste arquivo.

TODO (onboarding): ainda NAO se confirmou se o escritorio usa ADVBOX, e nao temos
nenhum ID de usuario (nem o do Dr. Paulo Alexandre Soares Corbelino, OAB/MT 33.267).
Enquanto estiverem None, as automacoes que dependem desses IDs ficam inativas/seguras.
"""
import os

# IDs de usuario no ADVBOX (preencher no onboarding, se o escritorio usar ADVBOX).
# Podem vir do .env (recomendado) ou ser definidos direto aqui.
USUARIOS_ADVBOX = {
    # TODO: confirmar se ha ADVBOX e pegar ID real no painel ADVBOX > Usuarios
    # (Dr. Paulo Alexandre Soares Corbelino, OAB/MT 33.267).
    "RESPONSAVEL": os.getenv("ADVBOX_USER_RESPONSAVEL") or None,
    "OPERACIONAL": os.getenv("ADVBOX_USER_OPERACIONAL") or None,   # quem recebe tarefas operacionais
    "FINANCEIRO": os.getenv("ADVBOX_USER_FINANCEIRO") or None,     # quem lanca transacoes financeiras
}

# Papel usado no campo 'from' das tarefas (/posts).
USUARIO_PADRAO_TAREFAS = "RESPONSAVEL"


def id_usuario(papel):
    """Retorna o ID ADVBOX do papel informado (ou None se nao configurado)."""
    valor = USUARIOS_ADVBOX.get(papel)
    if valor in (None, ""):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return valor
