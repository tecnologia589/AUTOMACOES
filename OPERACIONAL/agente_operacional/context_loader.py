"""
Carrega todo o contexto necessario para o agente executar uma tarefa:
- Dados do processo (ADVBOX)
- Dados do cliente
- Pasta do cliente no Drive (lista de arquivos + conteudo textual dos principais)
- POP aplicavel (buscado no Drive por nome)
"""
import io
import logging
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'INTEGRACOES'))
from advbox_integration import _request as advbox_request  # noqa
from google_integration import autenticar_google  # noqa

log = logging.getLogger('agente_op.context')

# Limite de texto extraido por documento (em chars) para nao estourar contexto
MAX_CHARS_POR_DOC = 200000  # ate ~200K chars por arquivo (cobre processos PJe completos)
MAX_DOCS_CONTEUDO = 20      # baixa e extrai conteudo de no maximo N documentos
MAX_TOTAL_CHARS = 800000    # contexto total pode chegar a 800K chars


def _buscar_processo_advbox(lawsuit_id):
    if not lawsuit_id:
        return None
    try:
        r = advbox_request('GET', f'/lawsuits/{lawsuit_id}')
        return r.get('data') or r if isinstance(r, dict) else r
    except Exception as e:
        log.warning(f'falha ao buscar processo {lawsuit_id}: {e}')
        return None


def _buscar_cliente_advbox(customer_id):
    if not customer_id:
        return None
    try:
        r = advbox_request('GET', f'/customers/{customer_id}')
        return r.get('data') or r if isinstance(r, dict) else r
    except Exception as e:
        log.warning(f'falha ao buscar cliente {customer_id}: {e}')
        return None


def _localizar_pasta_cliente(drive, nome_cliente):
    """
    Procura a pasta do cliente no Drive em qualquer area:
    RECLAMANTE / RECLAMADA / CIVEL / ASSESSORIA / etc.
    Busca por substring do nome - independe da pasta-mae.
    """
    if not nome_cliente:
        return None
    partes = [p for p in re.split(r'\s+', nome_cliente.strip().upper()) if len(p) > 2][:3]
    query = ' and '.join([f"name contains '{p}'" for p in partes])
    q = f"mimeType='application/vnd.google-apps.folder' and trashed=false and ({query})"
    try:
        r = drive.files().list(
            q=q, fields='files(id,name,parents)', pageSize=20,
            supportsAllDrives=True, includeItemsFromAllDrives=True,
        ).execute()
        files = r.get('files', [])
        return files[0] if files else None
    except Exception as e:
        log.warning(f'falha ao localizar pasta do cliente "{nome_cliente}": {e}')
        return None


def _localizar_subpasta_atos(drive, pasta_cliente_id):
    """
    Procura a subpasta 'ATOS INTERNOS' dentro da pasta do cliente.
    E ai que peças juridicas geradas pelo agente devem ser salvas.
    Fallback: retorna a propria pasta do cliente se nao encontrar.
    """
    if not pasta_cliente_id:
        return None
    try:
        r = drive.files().list(
            q=(f"'{pasta_cliente_id}' in parents and trashed=false "
               f"and mimeType='application/vnd.google-apps.folder'"),
            fields='files(id,name)', pageSize=50,
            supportsAllDrives=True, includeItemsFromAllDrives=True,
        ).execute()
        for f in r.get('files', []):
            nome = f['name'].upper()
            if 'ATOS INTERNOS' in nome or 'ATOS' in nome:
                return f
    except Exception as e:
        log.warning(f'falha ao buscar ATOS INTERNOS em {pasta_cliente_id}: {e}')
    return None


def _listar_arquivos_recursivo(drive, pasta_id, depth=4):
    """Lista todos os arquivos dentro de uma pasta (e subpastas ate depth).
    Profundidade 4 cobre RECLAMANTE/CLIENTE/SUBPASTA/SUB-SUBPASTA."""
    arquivos = []
    try:
        r = drive.files().list(
            q=f"'{pasta_id}' in parents and trashed=false",
            fields='files(id,name,mimeType)', pageSize=500,
            supportsAllDrives=True, includeItemsFromAllDrives=True,
        ).execute()
        for f in r.get('files', []):
            if f['mimeType'] == 'application/vnd.google-apps.folder' and depth > 0:
                arquivos.extend(_listar_arquivos_recursivo(drive, f['id'], depth - 1))
            else:
                arquivos.append(f)
    except Exception as e:
        log.warning(f'falha ao listar pasta {pasta_id}: {e}')
    return arquivos


# Marcadores que delimitam a SENTENCA dentro de um PDF do PJe completo
MARCADORES_SENTENCA = [
    'DISPOSITIVO', 'ISTO POSTO', 'ANTE O EXPOSTO', 'POSTO ISTO',
    'POSTO ISSO', 'PELO EXPOSTO', 'EM FACE DO EXPOSTO',
    'JULGO PROCEDENTE', 'JULGO IMPROCEDENTE', 'JULGO PARCIALMENTE',
    'S E N T E N C A', 'SENTENÇA', 'FUNDAMENTAÇÃO',
]


def _extrair_partes_relevantes_pje(texto: str, nome_arquivo: str) -> str:
    """
    Para PDFs do PJe (Processo_*.pdf) que costumam ter 100+ paginas,
    extrai as partes mais relevantes:
      - inicio (10K chars): cabecalho, peticao inicial, identificacao
      - trechos com marcadores de sentenca (5K chars antes/depois de cada match)
      - final (50K chars): tipicamente onde fica a sentenca
    Concatena tudo respeitando MAX_CHARS_POR_DOC.
    """
    if not texto or len(texto) <= MAX_CHARS_POR_DOC:
        return texto[:MAX_CHARS_POR_DOC]

    nome_upper = (nome_arquivo or '').upper()
    eh_pje = (nome_upper.startswith('PROCESSO_') or nome_upper.startswith('PROCESSO ')
              or 'AUTOS' in nome_upper)
    if not eh_pje:
        return texto[:MAX_CHARS_POR_DOC]

    partes = []
    # 1. inicio (10K)
    partes.append(('=== INICIO DO PROCESSO ===', texto[:10000]))

    # 2. trechos ao redor de marcadores de sentenca
    texto_upper = texto.upper()
    posicoes_vistas = set()
    for marc in MARCADORES_SENTENCA:
        pos = texto_upper.find(marc)
        if pos == -1:
            continue
        # janela 3K antes + 7K depois
        ini = max(0, pos - 3000)
        fim = min(len(texto), pos + 7000)
        # evita duplicar trechos
        chave = (ini // 5000, fim // 5000)
        if chave in posicoes_vistas:
            continue
        posicoes_vistas.add(chave)
        partes.append((f'=== TRECHO COM "{marc}" ===', texto[ini:fim]))

    # 3. final do documento (50K)
    partes.append(('=== FINAL DO PROCESSO (sentenca/dispositivo costuma estar aqui) ===',
                   texto[-50000:]))

    # concatena respeitando limite
    out = []
    total = 0
    for titulo, trecho in partes:
        bloco = f'\n\n{titulo}\n{trecho}'
        if total + len(bloco) > MAX_CHARS_POR_DOC:
            sobra = MAX_CHARS_POR_DOC - total
            if sobra > 1000:
                out.append(bloco[:sobra])
            break
        out.append(bloco)
        total += len(bloco)
    return ''.join(out).strip()


def _baixar_texto(drive, file_id, mime, nome=''):
    """Baixa e extrai texto de um arquivo do Drive.
    Para PDFs grandes do PJe, aplica extracao inteligente (sentenca + inicio + fim)."""
    from googleapiclient.http import MediaIoBaseDownload
    try:
        if mime == 'application/vnd.google-apps.document':
            data = drive.files().export(fileId=file_id, mimeType='text/plain').execute()
            return _extrair_partes_relevantes_pje(data.decode('utf-8', errors='ignore'), nome)
        buf = io.BytesIO()
        request = drive.files().get_media(fileId=file_id, supportsAllDrives=True)
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        raw = buf.getvalue()
        if mime == 'application/pdf':
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(raw))
                texto = '\n'.join((p.extract_text() or '') for p in reader.pages)
                return _extrair_partes_relevantes_pje(texto, nome)
            except Exception:
                return ''
        if 'wordprocessingml' in mime:
            try:
                from docx import Document
                doc = Document(io.BytesIO(raw))
                texto = '\n'.join(p.text for p in doc.paragraphs)
                return _extrair_partes_relevantes_pje(texto, nome)
            except Exception:
                return ''
        if mime.startswith('text/'):
            return _extrair_partes_relevantes_pje(raw.decode('utf-8', errors='ignore'), nome)
    except Exception as e:
        log.warning(f'falha ao baixar {file_id}: {e}')
    return ''


def _arquivos_prioritarios(arquivos, categoria):
    """Retorna os arquivos mais relevantes primeiro, baseado no tipo de peca.
    Lista completa de termos comuns em pastas processuais do escritorio."""
    prefs = {
        'peca': [
            # pecas processuais (PRIORIDADE MAXIMA - sempre necessarias)
            'SENTENCA', 'SENTENÇA', 'SENTE',
            'INICIAL', 'PETICAO INICIAL', 'PETIÇÃO INICIAL', 'RT ', 'RECLAM',
            'CONTESTAC', 'CONTESTAÇÃO',
            'REPLICA', 'RÉPLICA',
            'RAZOES FINAIS', 'RAZÕES FINAIS', 'MEMORIAIS',
            'ATA DE AUDIENC', 'ATA DE AUDIÊNC', 'AUDIENC',
            'RECURSO ORDINARIO', 'RECURSO ORDINÁRIO',
            'RECURSO ESPECIAL', 'RECURSO EXTRAORDINARIO',
            'CONTRARRAZ',
            'EMBARGOS', 'MANIFESTAC', 'MANIFESTAÇÃO',
            'PARECER', 'DESPACHO', 'DECISAO', 'DECISÃO',
            'ACORDAO', 'ACÓRDÃO',
            'TRANSCRIC', 'TRANSCRIÇÃO',
            'PROCESSO_',   # PDFs baixados direto do PJe (tipo "Processo_0001234-...pdf")
            'AUTOS', 'AUTOS DO PROCESSO',
            # documentos do cliente
            'CTPS', 'HOLERITE', 'CARTAO PONTO', 'CARTÃO PONTO',
            'CONTRATO', 'DEMONSTRATIVO', 'FOLHA PAGAMENTO',
            'RG', 'CNH', 'CPF', 'COMPROVANTE',
            'FICHA', 'CADASTRO', 'QUALIFICA',
            'POP', 'PROCEDIMENTO OPERACIONAL',
        ],
        'notificacao': ['CADASTRO', 'FICHA'],
        'assinatura': ['CONTRATO', 'MINUTA'],
        'movimentacao': [],
    }.get(categoria, [])

    def score(arq):
        nome = arq['name'].upper()
        for i, p in enumerate(prefs):
            if p in nome:
                return i
        return 999

    docs_uteis = [a for a in arquivos if a['mimeType'] in (
        'application/pdf',
        'application/vnd.google-apps.document',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
    )]
    docs_uteis.sort(key=score)
    return docs_uteis


def _buscar_pop(drive, tipo_tarefa, instrucao):
    """Procura o POP correspondente ao tipo de peca."""
    texto = f'{tipo_tarefa} {instrucao}'.upper()
    chaves = []
    mapping = {
        'CONTESTAC': 'POP CONTESTACAO',
        'REPLICA': 'POP REPLICA',
        'INICIAL': 'POP INICIAL',
        'RAZOES': 'POP RAZOES FINAIS',
        'RECURSO ORDINARIO': 'POP RECURSO ORDINARIO',
        'RECURSO ESPECIAL': 'POP RECURSO ESPECIAL',
        'CONTRARRAZ': 'POP CONTRARRAZOES',
    }
    for k, v in mapping.items():
        if k in texto.replace('Ç', 'C').replace('Á', 'A').replace('Ó', 'O').replace('Õ', 'O'):
            chaves.append(v)
    if not chaves:
        chaves = ['POP']

    for chave in chaves:
        termos = chave.split()
        q_parts = [f"name contains '{t}'" for t in termos]
        q = ' and '.join(q_parts) + ' and trashed=false'
        try:
            r = drive.files().list(
                q=q, fields='files(id,name,mimeType)', pageSize=5,
                supportsAllDrives=True, includeItemsFromAllDrives=True,
            ).execute()
            for f in r.get('files', []):
                if f['mimeType'] in (
                    'application/vnd.google-apps.document',
                    'application/pdf',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                ):
                    texto_pop = _baixar_texto(drive, f['id'], f['mimeType'], f['name'])
                    if texto_pop:
                        return {'nome': f['name'], 'id': f['id'], 'texto': texto_pop[:MAX_CHARS_POR_DOC]}
        except Exception as e:
            log.warning(f'busca POP "{chave}" falhou: {e}')
    return None


def carregar_contexto(lawsuit_id=None, tipo_tarefa='', instrucao='', categoria='peca',
                      tarefa_advbox=None):
    """Monta o dicionario de contexto que vai ser passado pro handler.
    tarefa_advbox: payload completo da tarefa (vem do n8n) - permite extrair
    cliente direto sem precisar GET /lawsuits."""
    ctx = {
        'lawsuit_id': lawsuit_id,
        'tipo_tarefa': tipo_tarefa,
        'instrucao': instrucao,
        'categoria': categoria,
        'processo': None,
        'cliente': None,
        'pasta_cliente': None,
        'pasta_atos_internos': None,
        'pasta_destino_doc': None,
        'arquivos': [],
        'docs_conteudo': [],
        'imagens': [],   # lista de {id, name, mime} - inseridas como anexo no docx
        'pop': None,
    }

    # 1) Tenta extrair cliente direto da tarefa (vem em tarefa.lawsuit.customers[])
    nome_cliente = None
    if tarefa_advbox and isinstance(tarefa_advbox, dict):
        lw = tarefa_advbox.get('lawsuit') or {}
        if lw:
            ctx['processo'] = {
                'id': lw.get('id'),
                'process_number': lw.get('process_number'),
                'protocol_number': lw.get('protocol_number'),
            }
            customers = lw.get('customers') or []
            if customers:
                ctx['cliente'] = customers[0]
                nome_cliente = customers[0].get('name')

    # 2) Fallback: se nao veio cliente na tarefa, tenta GET /lawsuits/{id}
    if not nome_cliente and lawsuit_id:
        processo = _buscar_processo_advbox(lawsuit_id)
        if processo:
            ctx['processo'] = processo
            cliente_id = None
            if isinstance(processo.get('customer'), dict):
                cliente_id = processo['customer'].get('id')
            cliente_id = cliente_id or processo.get('customer_id')
            cliente = _buscar_cliente_advbox(cliente_id) if cliente_id else processo.get('customer')
            ctx['cliente'] = cliente
            if isinstance(cliente, dict):
                nome_cliente = cliente.get('name') or cliente.get('nome')

    try:
        drive, _ = autenticar_google()
    except Exception as e:
        log.warning(f'falha ao autenticar Google: {e}')
        return ctx

    if nome_cliente:
        pasta = _localizar_pasta_cliente(drive, nome_cliente)
        ctx['pasta_cliente'] = pasta
        if pasta:
            atos = _localizar_subpasta_atos(drive, pasta['id'])
            ctx['pasta_atos_internos'] = atos
            ctx['pasta_destino_doc'] = atos or pasta
            arquivos = _listar_arquivos_recursivo(drive, pasta['id'])
            ctx['arquivos'] = [{'id': a['id'], 'name': a['name'], 'mime': a['mimeType']}
                               for a in arquivos]
            # imagens detectadas - usadas como anexos no docx final
            ctx['imagens'] = [
                {'id': a['id'], 'name': a['name'], 'mime': a['mimeType']}
                for a in arquivos if a['mimeType'].startswith('image/')
            ][:15]  # max 15 imagens (evita docx gigante)
            if ctx['imagens']:
                log.info(f'imagens detectadas: {len(ctx["imagens"])}')
            prioritarios = _arquivos_prioritarios(arquivos, categoria)[:MAX_DOCS_CONTEUDO]
            log.info(f'arquivos prioritarios selecionados ({len(prioritarios)}):')
            for arq in prioritarios:
                log.info(f'  - {arq["name"]}')
            total = 0
            for arq in prioritarios:
                if total >= MAX_TOTAL_CHARS:
                    log.info(f'  limite total atingido ({total} chars), parando download')
                    break
                texto = _baixar_texto(drive, arq['id'], arq['mimeType'], arq['name'])
                if texto:
                    texto = texto[:MAX_CHARS_POR_DOC]
                    ctx['docs_conteudo'].append({
                        'nome': arq['name'], 'id': arq['id'], 'texto': texto,
                    })
                    total += len(texto)
                    log.info(f'  OK extraido: {arq["name"]} ({len(texto)} chars)')
                else:
                    log.warning(f'  FALHOU extracao: {arq["name"]} (mime {arq["mimeType"]})')

    if categoria == 'peca':
        ctx['pop'] = _buscar_pop(drive, tipo_tarefa, instrucao)

    log.info(
        f'contexto: processo={bool(ctx["processo"])} cliente={nome_cliente} '
        f'pasta={bool(ctx["pasta_cliente"])} arquivos={len(ctx["arquivos"])} '
        f'docs_conteudo={len(ctx["docs_conteudo"])} pop={bool(ctx["pop"])}'
    )
    return ctx
