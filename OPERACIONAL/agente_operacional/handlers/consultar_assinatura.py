"""
Handler: consultar status de assinatura de um documento no ZapSign.

Detecta o token do documento (ou link com /cli/docs/{token}/) na instrucao e
retorna status + signatarios.

Usa 100% INTEGRACOES/zapsign_integration.py.
"""
import re
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'INTEGRACOES'))
from zapsign_integration import buscar_documento  # noqa

log = logging.getLogger('agente_op.consultar_assinatura')


def _extrair_token(texto: str) -> str | None:
    if not texto:
        return None
    padroes = [
        r'/cli/docs/([A-Za-z0-9-]{20,})',
        r'/api/v1/docs/([A-Za-z0-9-]{20,})',
        r'token[=:]\s*([A-Za-z0-9-]{20,})',
    ]
    for p in padroes:
        m = re.search(p, texto)
        if m:
            return m.group(1)
    # fallback: qualquer UUID-like de 30+ chars
    m = re.search(r'\b([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b', texto)
    if m:
        return m.group(1)
    return None


def executar(tipo_tarefa: str, instrucao: str, contexto: dict) -> dict:
    token = _extrair_token(instrucao)
    if not token:
        return {
            'sucesso': False,
            'titulo': 'CONSULTA ZAPSIGN - TOKEN NAO LOCALIZADO',
            'resumo': (
                'Nao foi possivel identificar o token do documento.\n'
                'Inclua o link ZapSign (com /cli/docs/{token}) no notes da tarefa.'
            ),
        }

    doc = buscar_documento(token)
    if not doc:
        return {
            'sucesso': False,
            'titulo': 'DOCUMENTO NAO ENCONTRADO NO ZAPSIGN',
            'resumo': f'Token {token} nao retornou dados.',
        }

    nome = doc.get('name', '(sem nome)')
    status = doc.get('status', '?')
    folder = doc.get('folder_path') or '/'
    signed_file = doc.get('signed_file') or ''

    linhas = [
        f'Documento: **{nome}**',
        f'Status: **{status}**',
        f'Pasta: {folder}',
    ]
    if signed_file:
        linhas.append(f'PDF assinado: {signed_file}')

    signers = doc.get('signers') or []
    if signers:
        linhas += ['', '**Signatarios:**']
        for s in signers:
            st = s.get('status', '?')
            linhas.append(f'- {s.get("name", "?")} ({s.get("email") or s.get("phone_number") or "-"}) -> {st}')

    return {
        'sucesso': True,
        'titulo': f'CONSULTA ZAPSIGN - {nome} ({status})',
        'resumo': '\n'.join(linhas),
        'doc_link': f'https://app.zapsign.com.br/cli/docs/{token}',
    }
