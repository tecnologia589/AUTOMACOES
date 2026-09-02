"""
Handler de envio para assinatura digital (ZapSign).

Detecta link de Google Doc/Drive no notes da tarefa, exporta/baixa como PDF,
cria no ZapSign e retorna os links de assinatura. Signatarios:
  - Advogado responsavel do escritorio sempre (contratos e peticoes)
  - Cliente principal do ADVBOX (com telefone/email se disponiveis)
  - Signatarios extras podem ser inferidos no futuro

Usa 100% INTEGRACOES/zapsign_integration.py.
"""
import re
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'INTEGRACOES'))
from google_integration import autenticar_google  # noqa
from zapsign_integration import (  # noqa
    enviar_documento,
    criar_signatario,
)

from ..config import ESCRITORIO_ASSINATURA, ESCRITORIO_EMAIL_RESPONSAVEL

log = logging.getLogger('agente_op.assinatura')

# Nome do signatario responsavel do escritorio (extraido da assinatura padrao).
RESPONSAVEL_NOME = ESCRITORIO_ASSINATURA.split('-')[0].strip() or 'Advogado Responsavel'
RESPONSAVEL_EMAIL = ESCRITORIO_EMAIL_RESPONSAVEL


def _extrair_doc_id(texto: str) -> str | None:
    """Extrai o ID de um Google Doc/Drive a partir de URL no texto."""
    if not texto:
        return None
    padroes = [
        r'docs\.google\.com/document/d/([A-Za-z0-9_-]+)',
        r'drive\.google\.com/file/d/([A-Za-z0-9_-]+)',
        r'drive\.google\.com/.*?id=([A-Za-z0-9_-]+)',
    ]
    for p in padroes:
        m = re.search(p, texto)
        if m:
            return m.group(1)
    return None


def executar(tipo_tarefa: str, instrucao: str, contexto: dict) -> dict:
    cliente = contexto.get('cliente') or {}
    nome_cliente = cliente.get('name') or cliente.get('nome') or 'CLIENTE'

    # 1. Localizar o documento a assinar
    doc_id = _extrair_doc_id(instrucao)
    if not doc_id:
        # Fallback: tenta achar nos arquivos da pasta do cliente
        for arq in contexto.get('arquivos', []):
            if ('CONTRATO' in arq['name'].upper()
                    and arq['mime'] == 'application/vnd.google-apps.document'):
                doc_id = arq['id']
                break

    if not doc_id:
        return {
            'sucesso': False,
            'titulo': 'ENVIO PARA ASSINATURA - DOCUMENTO NAO LOCALIZADO',
            'resumo': (
                'Nao foi possivel identificar o documento a ser assinado.\n'
                'Inclua o link do Google Doc/Drive no campo notes da tarefa, '
                'ou garanta que ha um arquivo "Contrato" na pasta do cliente.'
            ),
        }

    # 2. Autenticar Google Drive
    try:
        drive, _ = autenticar_google()
    except Exception as e:
        log.exception(f'falha ao autenticar Google: {e}')
        return {
            'sucesso': False,
            'titulo': 'FALHA AO AUTENTICAR GOOGLE',
            'resumo': f'Erro: {e}',
        }

    # 3. Montar signatarios
    email_c = cliente.get('email') or cliente.get('emails')
    if isinstance(email_c, list):
        email_c = email_c[0] if email_c else None
    tel_c = cliente.get('phone') or cliente.get('telefone') or cliente.get('mobile')
    if isinstance(tel_c, list):
        tel_c = tel_c[0] if tel_c else None

    signatarios = [criar_signatario(RESPONSAVEL_NOME, email=RESPONSAVEL_EMAIL or None)]
    if email_c or tel_c:
        signatarios.append(criar_signatario(nome_cliente, email=email_c, telefone=tel_c))

    # 4. Enviar
    try:
        resultado = enviar_documento(
            drive_service=drive,
            doc_id=doc_id,
            signers=signatarios,
            folder_path=f'/{nome_cliente.upper()}/',
        )
    except Exception as e:
        log.exception(f'falha ZapSign: {e}')
        return {
            'sucesso': False,
            'titulo': 'FALHA AO ENVIAR PARA ZAPSIGN',
            'resumo': f'Erro na API ZapSign: {e}',
        }

    nome_doc = resultado.get('nome_doc') or 'documento'
    doc_url = resultado.get('doc_url')

    # 5. Montar resposta
    linhas = [
        f'Documento: **{nome_doc}**',
        f'Cliente: **{nome_cliente}**',
        '',
        f'Documento criado no ZapSign: {doc_url}',
        '',
        '**Links de assinatura por signatario:**',
    ]
    for s in resultado['sign_urls']:
        linhas.append(f'- {s["signatario"]}: {s["link"]}')

    if not (email_c or tel_c):
        linhas += [
            '',
            'OBS: Cliente sem email/telefone cadastrados no ADVBOX.',
            f'Apenas {RESPONSAVEL_NOME} foi adicionado(a) como signatario(a).',
            'Adicione manualmente os signatarios faltantes pelo painel ZapSign.',
        ]

    return {
        'sucesso': True,
        'titulo': f'ENVIO PARA ASSINATURA - {nome_cliente}',
        'resumo': '\n'.join(linhas),
        'doc_link': doc_url,
        'doc_nome': nome_doc,
    }
