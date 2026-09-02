"""
Handler de notificacao de cliente via Atende Direito (WhatsApp).

Detecta se ha arquivo a enviar (link Drive no notes) -> manda como arquivo.
Caso contrario -> gera mensagem curta via LLM e envia texto puro.

Usa 100% INTEGRACOES/atendedireito_integration.py.
"""
import re
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'INTEGRACOES'))
from atendedireito_integration import (  # noqa
    buscar_contato_por_telefone,
    extrair_user_ns,
    enviar_mensagem_texto,
    enviar_arquivo,
)

from ..config import ESCRITORIO_NOME
from ..llm_client import triagem

log = logging.getLogger('agente_op.notificar')


def _gerar_mensagem(instrucao: str, contexto: dict) -> str:
    cliente = contexto.get('cliente') or {}
    processo = contexto.get('processo') or {}
    nome = (cliente.get('name') or cliente.get('nome') or '').split()[0].title() or 'cliente'

    prompt = f"""
Voce e a assistente do escritorio {ESCRITORIO_NOME}.
Gere uma mensagem curta e cordial de WhatsApp para o cliente {nome}, em portugues brasileiro,
com base na instrucao abaixo. Use linguagem acessivel (o cliente nao e advogado).
Nao use juridiques. Nao inclua saudacoes muito longas. Nao mencione valores.
Finalize com "Qualquer duvida estamos a disposicao. - Equipe {ESCRITORIO_NOME}".

INSTRUCAO DO ADVOGADO:
{instrucao}

DADOS DO PROCESSO (para contexto, so mencione se relevante):
Numero: {processo.get('process_number') or '-'}
Reclamada: {processo.get('opposing_name') or '-'}

Retorne APENAS o texto da mensagem, pronto para envio.
""".strip()
    return triagem(prompt)


def _detectar_url_arquivo(texto: str) -> str | None:
    """Extrai URL publica de arquivo do notes (drive, dropbox, etc)."""
    if not texto:
        return None
    # qualquer URL http(s)
    m = re.search(r'https?://[^\s\)\]\>]+', texto)
    return m.group(0) if m else None


def executar(tipo_tarefa: str, instrucao: str, contexto: dict) -> dict:
    cliente = contexto.get('cliente') or {}
    telefone = cliente.get('phone') or cliente.get('telefone') or cliente.get('mobile')
    if isinstance(telefone, list):
        telefone = telefone[0] if telefone else None
    nome = cliente.get('name') or cliente.get('nome') or 'cliente'

    if not telefone:
        return {
            'sucesso': False,
            'titulo': 'NOTIFICACAO NAO ENVIADA',
            'resumo': f'Telefone do cliente {nome} nao encontrado no ADVBOX.',
        }

    contato = buscar_contato_por_telefone(telefone)
    if not contato:
        return {
            'sucesso': False,
            'titulo': 'CONTATO NAO LOCALIZADO',
            'resumo': (
                f'Telefone {telefone} nao localizado no Atende Direito.\n'
                f'Cadastrar cliente {nome} antes de enviar mensagem.'
            ),
        }
    user_ns = extrair_user_ns(contato)
    if not user_ns:
        return {
            'sucesso': False,
            'titulo': 'CONTATO SEM USER_NS',
            'resumo': f'Contato localizado mas sem user_ns ({contato}).',
        }

    try:
        mensagem = _gerar_mensagem(instrucao, contexto)
    except Exception as e:
        return {
            'sucesso': False,
            'titulo': 'FALHA AO GERAR MENSAGEM',
            'resumo': f'Nao foi possivel gerar mensagem para {nome}.',
            'detalhes': str(e),
        }

    # Decide: texto puro ou arquivo+legenda
    url_arquivo = _detectar_url_arquivo(instrucao)
    if url_arquivo:
        enviado = enviar_arquivo(user_ns, url_arquivo, legenda=mensagem, tipo='file')
        modo = f'arquivo ({url_arquivo})'
    else:
        enviado = enviar_mensagem_texto(user_ns, mensagem)
        modo = 'texto'

    return {
        'sucesso': enviado,
        'titulo': 'NOTIFICACAO DO CLIENTE',
        'resumo': (
            f'Mensagem {"enviada" if enviado else "NAO enviada"} '
            f'para {nome} ({telefone}) via {modo}.\n\n'
            f'--- Conteudo ---\n{mensagem}'
        ),
    }
