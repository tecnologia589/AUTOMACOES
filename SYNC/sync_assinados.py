"""
Sincronizador ZapSign -> Google Drive
Verifica documentos assinados no ZapSign e salva na pasta do cliente no Drive.
Rodar 3x ao dia via cron/launchd (macOS/Linux) - ver sync_assinados.sh.

Corbelino Advogados Associados.
"""
import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

# Arquivo para rastrear docs ja sincronizados
SYNC_LOG = "sync_assinados_log.json"

def carregar_log():
    if os.path.exists(SYNC_LOG):
        with open(SYNC_LOG, 'r') as f:
            return json.load(f)
    return {"sincronizados": []}

def salvar_log(log):
    with open(SYNC_LOG, 'w') as f:
        json.dump(log, f, indent=2)

def autenticar_drive():
    token_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'token.json')
    creds = Credentials.from_authorized_user_file(token_path, [
        'https://www.googleapis.com/auth/drive'
    ])
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, 'w') as f:
                f.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def buscar_pasta_cliente(drive, nome_cliente):
    """Busca a pasta do cliente em RECLAMANTE pelo nome."""
    # ID da pasta RECLAMANTE no Drive do escritorio -> definir em config/.env
    pasta_reclamante = os.getenv("GOOGLE_PASTA_RECLAMANTE", "")

    results = drive.files().list(
        q=f"'{pasta_reclamante}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false and name contains '{nome_cliente}'",
        fields='files(id, name)').execute()

    if results.get('files'):
        return results['files'][0]['id']
    return None

def buscar_subpasta_documentos(drive, pasta_cliente_id):
    """Busca a subpasta DOCUMENTOS DO CLIENTE."""
    results = drive.files().list(
        q=f"'{pasta_cliente_id}' in parents and mimeType='application/vnd.google-apps.folder' and name='DOCUMENTOS DO CLIENTE' and trashed=false",
        fields='files(id)').execute()

    if results.get('files'):
        return results['files'][0]['id']
    return pasta_cliente_id

def sincronizar():
    print(f"\n=== SYNC ZAPSIGN -> DRIVE | {datetime.now().strftime('%d/%m/%Y %H:%M')} ===\n")

    token = os.getenv("ZAPSIGN_API_TOKEN")
    if not token:
        print("ERRO: ZAPSIGN_API_TOKEN nao encontrado")
        return

    headers = {"Authorization": f"Bearer {token}"}
    log = carregar_log()
    drive = autenticar_drive()

    # Buscar documentos assinados no ZapSign
    page = 1
    novos = 0

    while True:
        resp = requests.get(
            f"https://api.zapsign.com.br/api/v1/docs/?page={page}",
            headers=headers, timeout=30)

        if resp.status_code != 200:
            print(f"Erro na API ZapSign: {resp.status_code}")
            break

        data = resp.json()
        docs = data.get("results", [])

        if not docs:
            break

        for doc in docs:
            doc_token = doc.get("token", "")
            doc_status = doc.get("status", "")
            doc_nome = doc.get("name", "")
            signed_file = doc.get("signed_file", "")
            folder_path = doc.get("folder_path", "")

            # Pular docs nao assinados ou ja sincronizados
            if doc_status != "signed":
                continue
            if doc_token in log["sincronizados"]:
                continue
            if not signed_file:
                continue

            # Extrair nome do cliente da pasta do ZapSign
            nome_cliente = folder_path.strip("/").strip()
            if not nome_cliente:
                # Tentar extrair do nome do documento
                parts = doc_nome.split(" - ")
                if len(parts) > 0:
                    nome_cliente = parts[0].strip()

            if not nome_cliente:
                print(f"  Pulando {doc_nome} - nao conseguiu identificar cliente")
                continue

            # Buscar pasta do cliente no Drive
            pasta_cliente = buscar_pasta_cliente(drive, nome_cliente)
            if not pasta_cliente:
                print(f"  Pulando {doc_nome} - pasta '{nome_cliente}' nao encontrada no Drive")
                continue

            pasta_docs = buscar_subpasta_documentos(drive, pasta_cliente)

            # Baixar PDF assinado
            print(f"  Baixando: {doc_nome} (assinado)")
            try:
                pdf_resp = requests.get(signed_file, timeout=60)
                if pdf_resp.status_code != 200:
                    print(f"    Erro ao baixar PDF: {pdf_resp.status_code}")
                    continue

                pdf_bytes = pdf_resp.content

                # Upload para o Drive
                nome_arquivo = f"{doc_nome} (ASSINADO).pdf"
                media = MediaInMemoryUpload(pdf_bytes, mimetype='application/pdf')

                drive.files().create(
                    body={
                        'name': nome_arquivo,
                        'parents': [pasta_docs]
                    },
                    media_body=media
                ).execute()

                print(f"  Salvo no Drive: {nome_arquivo}")
                log["sincronizados"].append(doc_token)
                novos += 1

            except Exception as e:
                print(f"    Erro: {str(e)}")

        # Proxima pagina
        if not data.get("next"):
            break
        page += 1

    salvar_log(log)
    print(f"\n=== {novos} documentos sincronizados ===\n")


if __name__ == "__main__":
    sincronizar()
