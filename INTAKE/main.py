import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'INTEGRACOES'))

from pdf_extractor import extrair_texto_pdf
from llm_processor import analisar_transcricao
from google_integration import autenticar_google, duplicar_template, preencher_documento, criar_pasta_cliente, gerar_documentos_cliente
from zapsign_integration import enviar_para_zapsign
from atendedireito_integration import enviar_mensagem_contratacao

# Cadastro automatico de cliente/processo no ADVBOX (opcional - habilitar via INTEGRACOES).
try:
    from advbox_integration import cadastrar_cliente, cadastrar_processo  # noqa: F401
except ImportError:
    cadastrar_cliente = cadastrar_processo = None

def run_intake(pdf_path: str, docs_extras: list = None):
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

    print("\n--- INICIANDO INTAKE JURIDICO ---")

    # 1. Extração
    print(f"1. Abrindo PDF da Transcricao: {pdf_path}")
    texto_transcricao = extrair_texto_pdf(pdf_path)

    # 1.1 Documentos extras (CNH, RG, comprovante endereco, ficha antiga, etc.)
    texto_documentos = ""
    if docs_extras:
        for doc_path in docs_extras:
            print(f"   Lendo documento extra: {doc_path}")
            texto_documentos += f"\n--- DOCUMENTO: {doc_path} ---\n"
            if doc_path.endswith('.txt'):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    texto_documentos += f.read()
            elif doc_path.endswith('.docx'):
                from docx import Document as DocxDoc
                doc = DocxDoc(doc_path)
                texto_documentos += '\n'.join([p.text for p in doc.paragraphs])
            else:
                texto_documentos += extrair_texto_pdf(doc_path)

    # 2. IA - Análise de Transcrição
    print("\n2. Passando a transcricao para Analise da Inteligencia Artificial...")
    dados_extraidos = analisar_transcricao(texto_transcricao, texto_documentos)

    print("\n[Resumo Rápido da IA]")
    print(f"Cliente Identificado: {dados_extraidos.get('nome', 'N/A')}")
    print(f"Tipo de Ação: {dados_extraidos.get('tipo_acao', 'N/A')}")

    # 3. Google Services
    print("\n3. Autenticando com Google Service Account...")
    drive_service, docs_service = autenticar_google()

    # Buscamos a variavel de template do env
    template_id = os.getenv("GOOGLE_TEMPLATE_ID")
    if not template_id or template_id == "SUA-ID-DO-TEMPLATE-AQUI":
        print("ERRO: Preencha o 'GOOGLE_TEMPLATE_ID' de forma válida no arquivo .env!")
        sys.exit(1)

    # Extraímos informações úteis para nomear a ficha (evitando vazio)
    nome_ficha = dados_extraidos.get("nome", "Desconhecido")
    data_reuniao = dados_extraidos.get("data_reuniao", "S/D")

    # 4. Criar pasta do cliente no Drive (RECLAMANTE > NOME > subpastas)
    print("\n4. Criando pasta do cliente no Google Drive...")
    pasta_cliente_id = criar_pasta_cliente(drive_service, nome_ficha)

    # 5. Duplicar template na pasta do cliente
    novo_doc_id = duplicar_template(drive_service, template_id, nome_ficha, data_reuniao, pasta_cliente_id)

    # 6. Preencher os Replaceables
    preencher_documento(docs_service, novo_doc_id, dados_extraidos)

    # 7. Gerar Contrato, Procuracao e Declaracao de Hipossuficiencia
    print("\n7. Gerando documentos de contratacao...")
    docs_gerados = gerar_documentos_cliente(drive_service, docs_service, nome_ficha, dados_extraidos)

    # 8. Enviar para ZapSign para assinatura digital
    links = enviar_para_zapsign(drive_service, nome_ficha, docs_gerados, dados_extraidos)

    print("\n--- INTAKE FINALIZADO! ---")
    print(f"Pasta do cliente criada em: RECLAMANTE > {nome_ficha.upper()}")
    print(f"Ficha gerada: https://docs.google.com/document/d/{novo_doc_id}/edit")
    for doc in docs_gerados:
        print(f"Documento: https://docs.google.com/document/d/{doc['id']}/edit")

    if links:
        print("\nLinks de assinatura ZapSign:")
        for link in links:
            print(f"  {link['documento']} ({link['signatario']}): {link['link']}")

    # 9. Enviar mensagem ao cliente via Atende Direito (WhatsApp)
    telefone = dados_extraidos.get("telefone", "")
    if telefone and links:
        print("\n9. Enviando mensagem ao cliente via Atende Direito...")
        enviar_mensagem_contratacao(telefone, nome_ficha, links)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso correto:")
        print("  py main.py transcricao.pdf")
        print("  py main.py transcricao.pdf CNH.pdf RG.pdf")
        sys.exit(1)

    caminho_pdf = sys.argv[1]
    docs_extras = sys.argv[2:] if len(sys.argv) > 2 else None
    run_intake(caminho_pdf, docs_extras)
