"""
=============================================================================
  GERADOR DE PETICAO INICIAL - SQUAD OPERACIONAL (Corbelino Advogados Associados)
=============================================================================

  Dois comandos:
    baixar  - Baixa docs do Drive e extrai textos para arquivo local
    subir   - Cria Google Docs formatado na subpasta PETICAO INICIAL AUTOMACAO

  Uso:
    python OPERACIONAL/gerar_peticao.py baixar "NOME DO CLIENTE"
    python OPERACIONAL/gerar_peticao.py baixar --id 1AbCdEfGhIjKlMnOpQrStUvWxYz
    python OPERACIONAL/gerar_peticao.py subir "NOME DO CLIENTE" --arquivo peticao.txt
    python OPERACIONAL/gerar_peticao.py subir --id 1AbCd --arquivo peticao.txt

  Observacao: o ID da pasta RECLAMANTE no Drive deve ser configurado no
  config/.env (GOOGLE_PASTA_RECLAMANTE). Sem ID configurado, use sempre --id.
=============================================================================
"""
import os
import sys
import io
import json
import tempfile
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

from INTEGRACOES.google_integration import autenticar_google  # noqa: E402


# ID da pasta RECLAMANTE no Drive - configurar no config/.env (vazio por padrao).
PASTA_RECLAMANTE_ID = os.getenv("GOOGLE_PASTA_RECLAMANTE", "")

# Subpastas a ignorar
PASTAS_IGNORAR = ['ATOS INTERNOS', 'PETICAO INICIAL']

# Baixar APENAS arquivos que contenham estas palavras no nome
NOMES_ESSENCIAIS = [
    'TRANSCRI', 'REUNIAO', 'REUNIÃO', 'AUDIO', 'ÁUDIO',
    'FICHA', 'CADASTRO', 'DADOS',
    'CNH', 'HABILITAC',
    'CTPS', 'CARTEIRA DE TRABALHO', 'CONTRATO',
    'TRCT', 'RESCIS',
    'ANALISE', 'ANÁLISE', 'ESTRATEG',
    'RECLAMAC', 'PETICAO', 'PETIÇÃO',
    'MEMORIA', 'MEMÓRIA', 'CALCULO', 'CÁLCULO',
]


def buscar_pasta_cliente(drive_service, nome_cliente: str) -> tuple:
    """Busca pasta do cliente em RECLAMANTE. Retorna (id, nome) ou (None, None)."""
    if not PASTA_RECLAMANTE_ID:
        print("  ERRO: GOOGLE_PASTA_RECLAMANTE nao configurado no config/.env. Use --id.")
        return None, None

    query = (
        f"'{PASTA_RECLAMANTE_ID}' in parents "
        f"and mimeType='application/vnd.google-apps.folder' "
        f"and trashed=false"
    )
    results = drive_service.files().list(
        q=query, fields='files(id, name)', pageSize=500
    ).execute()

    for pasta in results.get('files', []):
        if pasta['name'].upper() == nome_cliente.upper():
            return pasta['id'], pasta['name']
    for pasta in results.get('files', []):
        if nome_cliente.upper() in pasta['name'].upper():
            return pasta['id'], pasta['name']
    return None, None


def listar_arquivos_drive(drive_service, pasta_id: str) -> list:
    """Lista arquivos relevantes da pasta (recursivo, pula subpastas desnecessarias)."""
    arquivos = []
    pastas_pendentes = [pasta_id]

    while pastas_pendentes:
        pid = pastas_pendentes.pop()
        query = f"'{pid}' in parents and trashed=false"
        results = drive_service.files().list(
            q=query, fields='files(id, name, mimeType)', pageSize=200
        ).execute()

        for f in results.get('files', []):
            if f['mimeType'] == 'application/vnd.google-apps.folder':
                if not any(ign in f['name'].upper() for ign in PASTAS_IGNORAR):
                    pastas_pendentes.append(f['id'])
            else:
                # Baixar apenas arquivos essenciais
                nome_upper = f['name'].upper()
                if any(ess in nome_upper for ess in NOMES_ESSENCIAIS):
                    arquivos.append(f)
                # Google Docs sempre inclui (podem ser fichas, analises)
                elif f['mimeType'] == 'application/vnd.google-apps.document':
                    arquivos.append(f)

    return arquivos


def baixar_e_extrair(drive_service, arquivos: list) -> dict:
    """Baixa arquivos do Drive e extrai texto. Retorna {nome: texto}."""
    textos = {}

    for arq in arquivos:
        nome = arq['name']
        mime = arq['mimeType']
        file_id = arq['id']

        try:
            if mime == 'application/vnd.google-apps.document':
                print(f"  Lendo (Google Docs): {nome}")
                content = drive_service.files().export(
                    fileId=file_id, mimeType='text/plain'
                ).execute()
                textos[nome] = content.decode('utf-8', errors='replace')
                continue

            if mime == 'application/vnd.google-apps.spreadsheet':
                continue

            ext = os.path.splitext(nome)[1].lower()
            suportados_ext = ['.pdf', '.txt', '.docx']
            suportados_mime = ['application/pdf', 'text/plain',
                               'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

            if ext not in suportados_ext and mime not in suportados_mime:
                continue

            print(f"  Baixando: {nome}")
            content = drive_service.files().get_media(fileId=file_id).execute()

            if ext == '.txt' or mime == 'text/plain':
                textos[nome] = content.decode('utf-8', errors='replace')
            elif ext == '.docx' or 'wordprocessing' in mime:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                from docx import Document as DocxDoc
                doc = DocxDoc(tmp_path)
                textos[nome] = '\n'.join([p.text for p in doc.paragraphs])
                os.unlink(tmp_path)
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                from INTAKE.pdf_extractor import extrair_texto_pdf
                textos[nome] = extrair_texto_pdf(tmp_path)
                os.unlink(tmp_path)

        except Exception as e:
            print(f"  AVISO: Erro ao processar {nome}: {e}")

    return textos


# ============================================================
# COMANDO: baixar
# ============================================================

def cmd_baixar(args):
    """Baixa docs do Drive, extrai textos e salva em arquivo local."""
    print("\n" + "=" * 70)
    print("  BAIXAR DOCUMENTOS DO DRIVE")
    print("=" * 70)

    drive_service, _ = autenticar_google()

    pasta_id = args.pasta_id
    nome_encontrado = args.cliente or "CLIENTE"

    if not pasta_id:
        print(f"\n  Buscando pasta: {args.cliente}")
        pasta_id, nome_encontrado = buscar_pasta_cliente(drive_service, args.cliente)
        if not pasta_id:
            print(f"  ERRO: Pasta '{args.cliente}' nao encontrada em RECLAMANTE.")
            sys.exit(1)
        print(f"  Encontrada: {nome_encontrado}")

    print(f"\n  Listando arquivos...")
    arquivos = listar_arquivos_drive(drive_service, pasta_id)
    print(f"  {len(arquivos)} arquivo(s) relevante(s)")

    textos = baixar_e_extrair(drive_service, arquivos)
    print(f"  {len(textos)} documento(s) com texto extraido")

    # Salvar em arquivo
    saida = args.saida or os.path.join(
        os.path.dirname(__file__), '..', '_temp_docs_cliente.json'
    )
    dados = {
        'cliente': nome_encontrado,
        'pasta_id': pasta_id,
        'documentos': {nome: texto[:15000] for nome, texto in textos.items()}
    }
    with open(saida, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f"\n  Salvo em: {saida}")
    print(f"  Total: {len(textos)} documentos extraidos")
    print("=" * 70)


# ============================================================
# COMANDO: subir
# ============================================================

def cmd_subir(args):
    """Cria Google Docs formatado na subpasta PETICAO INICIAL AUTOMACAO."""
    from googleapiclient.errors import HttpError

    if not args.arquivo or not os.path.exists(args.arquivo):
        print(f"ERRO: Arquivo '{args.arquivo}' nao encontrado.")
        sys.exit(1)

    with open(args.arquivo, 'r', encoding='utf-8') as f:
        texto_peticao = f.read()

    print("\n" + "=" * 70)
    print("  SUBIR PETICAO PARA O DRIVE")
    print("=" * 70)

    drive_service, docs_service = autenticar_google()

    pasta_id = args.pasta_id
    nome_cliente = args.cliente or "CLIENTE"

    if not pasta_id:
        print(f"\n  Buscando pasta: {args.cliente}")
        pasta_id, nome_encontrado = buscar_pasta_cliente(drive_service, args.cliente)
        if not pasta_id:
            print(f"  ERRO: Pasta '{args.cliente}' nao encontrada.")
            sys.exit(1)
        nome_cliente = nome_encontrado

    # Criar subpasta
    try:
        pasta_peticao = drive_service.files().create(body={
            'name': 'PETICAO INICIAL AUTOMACAO',
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [pasta_id]
        }, fields='id').execute()
        pasta_dest = pasta_peticao['id']
        print(f"  Subpasta criada: PETICAO INICIAL AUTOMACAO")
    except HttpError as e:
        print(f"  AVISO: {e}")
        pasta_dest = pasta_id

    # Criar documento
    nome_doc = f"{nome_cliente} - Peticao Inicial"
    doc = drive_service.files().create(body={
        'name': nome_doc,
        'mimeType': 'application/vnd.google-apps.document',
        'parents': [pasta_dest]
    }, fields='id, webViewLink').execute()

    doc_id = doc['id']
    doc_link = doc.get('webViewLink', '')

    # Inserir texto
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': [{'insertText': {'location': {'index': 1}, 'text': texto_peticao}}]}
    ).execute()

    # Buscar tamanho
    doc_content = docs_service.documents().get(documentId=doc_id).execute()
    end_index = 1
    for element in doc_content.get('body', {}).get('content', []):
        if 'endIndex' in element:
            end_index = max(end_index, element['endIndex'])

    # Formatacao
    format_requests = [
        {
            'updateTextStyle': {
                'range': {'startIndex': 1, 'endIndex': end_index - 1},
                'textStyle': {
                    'fontSize': {'magnitude': 11, 'unit': 'PT'},
                    'weightedFontFamily': {'fontFamily': 'Montserrat'},
                },
                'fields': 'fontSize,weightedFontFamily'
            }
        },
        {
            'updateParagraphStyle': {
                'range': {'startIndex': 1, 'endIndex': end_index - 1},
                'paragraphStyle': {
                    'alignment': 'JUSTIFIED',
                    'lineSpacing': 150,
                    'spaceBelow': {'magnitude': 6, 'unit': 'PT'},
                    'indentFirstLine': {'magnitude': 49.6, 'unit': 'PT'},
                },
                'fields': 'alignment,lineSpacing,spaceBelow,indentFirstLine'
            }
        }
    ]

    # Titulos em negrito e centralizados
    linhas = texto_peticao.split('\n')
    offset = 1
    for linha in linhas:
        if linha.strip() and linha.strip() == linha.strip().upper() and len(linha.strip()) > 3:
            inicio = offset
            fim = offset + len(linha)
            if fim < end_index:
                format_requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': inicio, 'endIndex': fim},
                        'textStyle': {'bold': True},
                        'fields': 'bold'
                    }
                })
                if any(k in linha.upper() for k in [
                    'EXCELENTISSIMO', 'RECLAMATORIA', 'DOS FATOS',
                    'DO DIREITO', 'DOS PEDIDOS', 'DO VALOR', 'DOS REQUERIMENTOS'
                ]):
                    format_requests.append({
                        'updateParagraphStyle': {
                            'range': {'startIndex': inicio, 'endIndex': fim},
                            'paragraphStyle': {
                                'alignment': 'CENTER',
                                'indentFirstLine': {'magnitude': 0, 'unit': 'PT'},
                            },
                            'fields': 'alignment,indentFirstLine'
                        }
                    })
        offset += len(linha) + 1

    docs_service.documents().batchUpdate(
        documentId=doc_id, body={'requests': format_requests}
    ).execute()

    print(f"\n  Documento criado: {nome_doc}")
    print(f"  Link: {doc_link}")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gerador de Peticao Inicial')
    subparsers = parser.add_subparsers(dest='comando')

    # baixar
    p_baixar = subparsers.add_parser('baixar', help='Baixar docs do Drive e extrair textos')
    p_baixar.add_argument('cliente', nargs='?', help='Nome do cliente')
    p_baixar.add_argument('--id', dest='pasta_id', help='ID da pasta no Drive')
    p_baixar.add_argument('--saida', '-o', help='Arquivo de saida (default: _temp_docs_cliente.json)')

    # subir
    p_subir = subparsers.add_parser('subir', help='Criar Google Docs com a peticao')
    p_subir.add_argument('cliente', nargs='?', help='Nome do cliente')
    p_subir.add_argument('--id', dest='pasta_id', help='ID da pasta no Drive')
    p_subir.add_argument('--arquivo', '-a', required=True, help='Arquivo .txt com texto da peticao')

    args = parser.parse_args()

    if args.comando == 'baixar':
        if not args.cliente and not args.pasta_id:
            print("ERRO: Informe nome do cliente ou --id da pasta.")
            sys.exit(1)
        cmd_baixar(args)
    elif args.comando == 'subir':
        if not args.cliente and not args.pasta_id:
            print("ERRO: Informe nome do cliente ou --id da pasta.")
            sys.exit(1)
        cmd_subir(args)
    else:
        parser.print_help()
