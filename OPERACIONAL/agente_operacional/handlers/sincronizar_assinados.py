"""
Handler: sincronizar documentos assinados do ZapSign -> Google Drive.

Percorre os docs com status 'signed' no ZapSign, baixa o PDF assinado e
sobe na pasta 'DOCUMENTOS DO CLIENTE' (ou pasta do cliente) correspondente.

Mantem um log JSON em agente_operacional/logs/ para nao repetir.

Quando usar:
  - Tarefa diz "sincronizar assinados", "puxar zapsign", "baixar assinados".
  - Pode ser acionado como tarefa "operacional periodica" sem lawsuit_id.
"""
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'INTEGRACOES'))
from google_integration import autenticar_google  # noqa
from zapsign_integration import sincronizar_assinados_para_drive  # noqa

from ..config import LOG_DIR

log = logging.getLogger('agente_op.sync_assinados')

SYNC_LOG_PATH = LOG_DIR / 'sync_assinados_log.json'

# ID da pasta-mae de clientes no Drive do escritorio (preencher no onboarding via .env).
# Vazio = a busca usa apenas o nome do cliente em todo o Drive.
PASTA_CLIENTES_ID_DEFAULT = os.getenv('DRIVE_PASTA_CLIENTES_ID', '')


def _buscar_pasta_cliente(drive, nome_cliente):
    """
    Busca a pasta 'DOCUMENTOS DO CLIENTE' dentro da pasta do cliente.
    Procura em qualquer area (RECLAMANTE / RECLAMADA / CIVEL / etc).
    """
    import re
    partes = [p for p in re.split(r'\s+', nome_cliente.strip().upper()) if len(p) > 2][:3]
    if not partes:
        return None
    query = ' and '.join([f"name contains '{p}'" for p in partes])
    q = (f"mimeType='application/vnd.google-apps.folder' and trashed=false "
         f"and ({query})")
    try:
        r = drive.files().list(
            q=q, fields='files(id,name)', pageSize=10,
            supportsAllDrives=True, includeItemsFromAllDrives=True,
        ).execute()
        pastas = r.get('files', [])
        if not pastas:
            return None
        pasta_cliente_id = pastas[0]['id']
        # Procura subpasta DOCUMENTOS DO CLIENTE
        r2 = drive.files().list(
            q=(f"'{pasta_cliente_id}' in parents and trashed=false "
               f"and mimeType='application/vnd.google-apps.folder' "
               f"and name contains 'DOCUMENTOS'"),
            fields='files(id,name)', pageSize=5,
            supportsAllDrives=True, includeItemsFromAllDrives=True,
        ).execute()
        for f in r2.get('files', []):
            if 'DOCUMENTOS' in f['name'].upper():
                return f['id']
        # fallback: a propria pasta do cliente
        return pasta_cliente_id
    except Exception as e:
        log.warning(f'buscar_pasta_cliente "{nome_cliente}" falhou: {e}')
        return None


def executar(tipo_tarefa: str, instrucao: str, contexto: dict) -> dict:
    try:
        drive, _ = autenticar_google()
    except Exception as e:
        log.exception(f'falha ao autenticar Google: {e}')
        return {
            'sucesso': False,
            'titulo': 'FALHA GOOGLE',
            'resumo': f'Erro: {e}',
        }

    try:
        resumo = sincronizar_assinados_para_drive(
            drive_service=drive,
            log_path=str(SYNC_LOG_PATH),
            buscar_pasta_cliente_fn=_buscar_pasta_cliente,
        )
    except Exception as e:
        log.exception(f'falha sync: {e}')
        return {
            'sucesso': False,
            'titulo': 'FALHA SYNC ZAPSIGN',
            'resumo': f'Erro: {e}',
        }

    linhas = [
        f'Novos sincronizados: **{resumo["novos"]}**',
        f'Ja sincronizados: {resumo["ja_sincronizados"]}',
        f'Ignorados: {resumo["ignorados"]}',
    ]
    if resumo['itens_novos']:
        linhas += ['', '**Novos documentos:**']
        for item in resumo['itens_novos']:
            linhas.append(f'- {item["nome_doc"]} -> {item["nome_cliente"]}')
    if resumo['erros']:
        linhas += ['', '**Erros / avisos:**']
        for e in resumo['erros'][:20]:
            linhas.append(f'- {e}')

    return {
        'sucesso': True,
        'titulo': f'SYNC ZAPSIGN -> DRIVE ({resumo["novos"]} novos)',
        'resumo': '\n'.join(linhas),
    }
