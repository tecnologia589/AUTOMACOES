"""Helpers comuns aos handlers."""
import os
import sys
import tempfile
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'INTEGRACOES'))
from google_integration import autenticar_google  # noqa

from ..template_engine import gerar_peca_no_template

log = logging.getLogger('agente_op.handler')

DOCX_MIME = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'


def salvar_docx_no_drive(titulo: str, corpo_markdown: str, pasta_destino_id: str,
                         imagens=None) -> dict:
    """
    Gera um DOCX no timbrado do escritorio e sobe no Drive.
    O arquivo fica como .docx (permite editar no Word com formatacao preservada).
    pasta_destino_id: ATOS INTERNOS da pasta do cliente (vem do contexto).
    imagens: lista de {id, name, mime} para inserir como ANEXOS no final do docx.
    Retorna {'id', 'nome', 'link'}.
    """
    from googleapiclient.http import MediaFileUpload
    drive, _ = autenticar_google()

    if not pasta_destino_id:
        raise RuntimeError('pasta_destino_id obrigatorio (pasta do cliente nao localizada?)')

    nome = f'{titulo} - {datetime.now():%Y-%m-%d %H%M}.docx'

    # Gera DOCX no timbrado (com imagens anexas se houver)
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        gerar_peca_no_template(corpo_markdown, tmp_path,
                               imagens=imagens, drive_service=drive)
        media = MediaFileUpload(tmp_path, mimetype=DOCX_MIME, resumable=False)
        metadata = {
            'name': nome,
            'parents': [pasta_destino_id],
            # Mantem como .docx - nao converte pra Google Doc (preserva formatacao)
        }
        arq = drive.files().create(
            body=metadata, media_body=media, fields='id,name,webViewLink',
            supportsAllDrives=True,
        ).execute()
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    return {'id': arq['id'], 'nome': arq['name'], 'link': arq.get('webViewLink')}


def montar_bloco_contexto(contexto: dict) -> str:
    """Serializa o contexto em texto para enviar ao LLM."""
    linhas = []
    p = contexto.get('processo') or {}
    if p:
        linhas += [
            '=== PROCESSO ===',
            f'Numero: {p.get("process_number") or p.get("numero") or "-"}',
            f'Vara/Comarca: {p.get("court") or p.get("vara") or "-"}',
            f'Reclamada: {p.get("opposing_name") or p.get("reclamada") or "-"}',
            f'Tipo de acao: {p.get("action_type") or p.get("tipo_acao") or "-"}',
            f'Fase: {p.get("stage_name") or p.get("fase") or "-"}',
            '',
        ]

    c = contexto.get('cliente') or {}
    if c:
        linhas += [
            '=== CLIENTE ===',
            f'Nome: {c.get("name") or c.get("nome") or "-"}',
            f'CPF: {c.get("cpf") or "-"}',
            f'Telefone: {c.get("phone") or c.get("telefone") or "-"}',
            f'Email: {c.get("email") or "-"}',
            '',
        ]

    if contexto.get('pasta_cliente'):
        linhas += [
            '=== PASTA DO CLIENTE (Drive) ===',
            f'Nome: {contexto["pasta_cliente"].get("name")}',
            f'ID: {contexto["pasta_cliente"].get("id")}',
            f'Arquivos listados: {len(contexto.get("arquivos") or [])}',
            '',
        ]

    if contexto.get('arquivos'):
        linhas += ['=== ARQUIVOS NA PASTA ===']
        for a in contexto['arquivos'][:30]:
            linhas.append(f'- {a["name"]}')
        linhas.append('')

    for doc in contexto.get('docs_conteudo') or []:
        linhas += [
            f'=== CONTEUDO: {doc["nome"]} ===',
            doc['texto'],
            '',
        ]

    return '\n'.join(linhas)
